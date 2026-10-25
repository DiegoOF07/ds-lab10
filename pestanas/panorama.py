import plotly.graph_objects as go
from dash import Input, Output, State, callback, callback_context, dcc, html, no_update

from comun import COLOR, base_layout, figura_vacia, filtrar, id_grafica, selector_graficas, tarjeta


def layout():
    return html.Div([
        dcc.Store(id="sel-anio", data=None),
        dcc.Store(id="sel-region", data=None),

        selector_graficas("panorama", [("tendencia", "1. Evolución"), ("mercados", "2. Origen")]),
        html.Div(id="aviso-seleccion", className="aviso"),

        html.Div(className="grid", children=[
            tarjeta(className="tarjeta ancha", id=id_grafica("panorama", "tendencia"), children=[
                html.Div(className="tarjeta-cab", children=[
                    html.Div([
                        html.H2("1. ¿Cómo ha evolucionado la llegada de viajeros?"),
                        html.P("Haga clic en un año para ver sus mercados de origen en el gráfico 2. "
                               "Cambie a «Mensual» para ver la estacionalidad.", className="ayuda"),
                    ]),
                    dcc.RadioItems(id="granularidad", options=[{"label": "Anual", "value": "A"},
                                                               {"label": "Mensual", "value": "M"}],
                                   value="A", inline=True, className="segmentado"),
                ]),
                dcc.Graph(id="g-tendencia", config={"displayModeBar": False}),
                html.P(["La franja ", html.Span("roja", style={"color": COLOR["alerta"], "fontWeight": 600}),
                        " marca el cierre de fronteras por COVID-19 (mar 2020 – mar 2021). "
                        "2026 incluye solo enero a junio. Desde 2022 la categoría «Viajero» cambió de definición."],
                       className="nota"),
            ]),
            tarjeta(id=id_grafica("panorama", "mercados"), children=[
                html.Div(className="tarjeta-cab", children=[
                    html.Div([
                        html.H2(id="titulo-mercados"),
                        html.P(id="ayuda-mercados", className="ayuda"),
                    ]),
                    html.Button("← Todas las regiones", id="btn-volver", n_clicks=0, className="boton"),
                ]),
                dcc.Graph(id="g-mercados", config={"displayModeBar": False}),
                html.P("Cifras observadas (no estimadas). El origen se basa en el país de residencia declarado.",
                       className="nota"),
            ]),
        ]),
    ])


@callback(
    Output("sel-anio", "data"),
    Input("g-tendencia", "clickData"),
    Input("granularidad", "value"),
    Input("f-anios", "value"),
    State("sel-anio", "data"),
    prevent_initial_call=True,
)
def seleccionar_anio(click, gran, rango, actual):
    disparo = callback_context.triggered_id
    if disparo == "g-tendencia" and click:
        x = click["points"][0]["x"]
        anio = int(str(x)[:4])  # anual: 2019, mensual: "2019-05-01"
        return None if anio == actual else anio  # segundo clic deselecciona
    if actual is not None and not (rango[0] <= actual <= rango[1]):
        return None
    return actual if disparo != "g-tendencia" else no_update


@callback(
    Output("sel-region", "data"),
    Input("g-mercados", "clickData"),
    Input("btn-volver", "n_clicks"),
    State("sel-region", "data"),
    prevent_initial_call=True,
)
def seleccionar_region(click, _n, actual):
    if callback_context.triggered_id == "btn-volver":
        return None
    if click and actual is None:
        return click["points"][0]["y"]
    return no_update


@callback(
    Output("g-tendencia", "figure"),
    Input("f-anios", "value"), Input("f-tipos", "value"), Input("f-vias", "value"),
    Input("granularidad", "value"), Input("sel-anio", "data"), Input("sel-region", "data"),
)
def fig_tendencia(rango, tipos, vias, gran, anio_sel, region):
    d = filtrar(rango, tipos, vias)
    if d.empty:
        return figura_vacia("No hay datos para esta combinación de filtros.<br>Seleccione al menos un tipo de viajero y una vía.")

    fig = go.Figure()
    reg = d[d["Region"] == region] if region else None

    if gran == "A":
        tot = d.groupby("Año", as_index=False)["Viajeros"].sum()
        colores = [COLOR["seleccion"] if a == anio_sel else (COLOR["neutro"] if (anio_sel or region) else COLOR["primario"])
                   for a in tot["Año"]]
        fig.add_bar(x=tot["Año"], y=tot["Viajeros"], marker_color=colores, customdata=tot[["Año"]],
                    name="Total", hovertemplate="<b>%{x}</b><br>Total: %{y:,.0f} viajeros<extra></extra>")
        if region:
            r = reg.groupby("Año", as_index=False)["Viajeros"].sum()
            fig.add_scatter(x=r["Año"], y=r["Viajeros"], mode="lines+markers", name=region,
                            line=dict(color=COLOR["seleccion"], width=3), customdata=r[["Año"]], yaxis="y2",
                            hovertemplate=f"<b>%{{x}}</b><br>{region}: %{{y:,.0f}}<extra></extra>")
        fig.add_vrect(x0=2019.5, x1=2021.5, fillcolor=COLOR["alerta"], opacity=0.08, line_width=0) \
            if rango[0] <= 2021 and rango[1] >= 2020 else None
        fig.update_xaxes(dtick=1, tickangle=-45, range=[rango[0] - 0.6, rango[1] + 0.6])
    else:
        tot = d.groupby("Fecha", as_index=False)["Viajeros"].sum()
        tot["Año"] = tot["Fecha"].dt.year
        color_linea = COLOR["neutro"] if region else COLOR["primario"]
        fig.add_scatter(x=tot["Fecha"], y=tot["Viajeros"], mode="lines", name="Total",
                        line=dict(color=color_linea, width=2), customdata=tot[["Año"]],
                        hovertemplate="<b>%{x|%b %Y}</b><br>Total: %{y:,.0f}<extra></extra>")
        if region:
            r = reg.groupby("Fecha", as_index=False)["Viajeros"].sum()
            r["Año"] = r["Fecha"].dt.year
            fig.add_scatter(x=r["Fecha"], y=r["Viajeros"], mode="lines", name=region,
                            line=dict(color=COLOR["seleccion"], width=2.5), customdata=r[["Año"]], yaxis="y2",
                            hovertemplate=f"<b>%{{x|%b %Y}}</b><br>{region}: %{{y:,.0f}}<extra></extra>")
        if anio_sel:
            fig.add_vrect(x0=f"{anio_sel}-01-01", x1=f"{anio_sel}-12-31",
                          fillcolor=COLOR["seleccion"], opacity=0.12, line_width=0)
        if rango[0] <= 2021 and rango[1] >= 2020:
            fig.add_vrect(x0="2020-03-01", x1="2021-03-31", fillcolor=COLOR["alerta"], opacity=0.08, line_width=0)

    base_layout(fig)
    if region:
        fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.08, x=0),
                          yaxis2=dict(overlaying="y", side="right", rangemode="tozero", tickformat=".2s",
                                      showgrid=False, title=dict(text=f"Viajeros · {region}",
                                      font=dict(color=COLOR["seleccion"])),
                                      tickfont=dict(color=COLOR["seleccion"])))
    fig.update_layout(yaxis_title=dict(text="Viajeros · total", font=dict(color=COLOR["texto_sec"])))
    return fig


@callback(
    Output("g-mercados", "figure"),
    Output("titulo-mercados", "children"),
    Output("ayuda-mercados", "children"),
    Output("btn-volver", "style"),
    Input("f-anios", "value"), Input("f-tipos", "value"), Input("f-vias", "value"),
    Input("sel-anio", "data"), Input("sel-region", "data"),
)
def fig_mercados(rango, tipos, vias, anio_sel, region):
    d = filtrar(rango, tipos, vias)
    if anio_sel:
        d = d[d["Año"] == anio_sel]
    periodo = str(anio_sel) if anio_sel else f"{rango[0]}–{rango[1]}"
    estilo_btn = {"visibility": "visible" if region else "hidden"}

    if region:
        d = d[d["Region"] == region]
        titulo = f"2. Países de origen · {region} · {periodo}"
        ayuda = "Top 15 países de la región. Use «Todas las regiones» para subir de nivel."
        if d.empty:
            return figura_vacia(f"No se registraron viajeros de {region} con estos filtros."), titulo, ayuda, estilo_btn
        g = d.groupby("Pais", as_index=False)["Viajeros"].sum().nlargest(15, "Viajeros")
        etiqueta, color = "Pais", COLOR["seleccion"]
    else:
        titulo = f"2. ¿De dónde vienen los viajeros? · {periodo}"
        ayuda = "Haga clic en una región para ver sus países y resaltar su evolución en el gráfico 1."
        if d.empty:
            return figura_vacia("No hay datos para esta combinación de filtros."), titulo, ayuda, estilo_btn
        g = d.groupby("Region", as_index=False)["Viajeros"].sum()
        g = g[g["Viajeros"] > 0]
        etiqueta, color = "Region", COLOR["primario"]

    g = g.sort_values("Viajeros")
    total = g["Viajeros"].sum()
    g["pct"] = g["Viajeros"] / total * 100
    fig = go.Figure(go.Bar(
        x=g["Viajeros"], y=g[etiqueta], orientation="h", marker_color=color,
        text=[f"{p:.1f}%" for p in g["pct"]], textposition="outside", cliponaxis=False,
        textfont=dict(color=COLOR["texto_sec"], size=12),
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} viajeros<extra></extra>",
    ))
    base_layout(fig, alto=max(380, 26 * len(g) + 60))
    fig.update_xaxes(gridcolor=COLOR["borde"], showgrid=True, tickformat="~s", title_text="Viajeros",
                     title_font=dict(color=COLOR["texto_sec"]))
    fig.update_yaxes(showgrid=False, tickfont=dict(color=COLOR["texto"]))
    fig.update_layout(margin=dict(r=50))
    return fig, titulo, ayuda, estilo_btn


@callback(
    Output("aviso-seleccion", "children"),
    Input("sel-anio", "data"), Input("sel-region", "data"),
)
def aviso(anio, region):
    partes = []
    if anio:
        partes.append(f"Año {anio}")
    if region:
        partes.append(f"Región {region}")
    if not partes:
        return ""
    return [html.Span("Selección activa: ", className="aviso-tit"), " · ".join(partes),
            html.Span(" (haga clic de nuevo en el año o use «Todas las regiones» para quitarla)",
                      className="aviso-sec")]
