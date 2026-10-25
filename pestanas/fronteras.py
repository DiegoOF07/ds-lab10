import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, callback_context, dcc, html, no_update

from comun import COLOR, DATOS, base_layout, figura_vacia, id_grafica, selector_graficas, tarjeta

fr = pd.read_csv(DATOS / "viajeros_frontera.csv", parse_dates=["Fecha"])


def filtrar_fr(rango, tipos, vias):
    d = fr[(fr["Año"] >= rango[0]) & (fr["Año"] <= rango[1])]
    return d[d["Tipo"].isin(tipos) & d["Via"].isin(vias)]


def layout():
    return html.Div([
        dcc.Store(id="sel-via", data=None),
        dcc.Store(id="sel-frontera", data=None),
        dcc.Store(id="sel-anio-front", data=None),

        selector_graficas("fronteras", [("ranking", "6. Puestos de ingreso"), ("serie", "7. Evolución")]),
        html.Div(id="aviso-fronteras", className="aviso"),

        html.Div(className="grid", children=[
            tarjeta(id=id_grafica("fronteras", "ranking"), children=[
                html.Div(className="tarjeta-cab", children=[
                    html.Div([
                        html.H2(id="titulo-ranking"),
                        html.P(id="ayuda-ranking", className="ayuda"),
                    ]),
                    html.Button("Todas las vías", id="btn-todas-vias", n_clicks=0, className="boton"),
                ]),
                dcc.Graph(id="g-fronteras", config={"displayModeBar": False}),
                html.P("Cifras observadas. Algunos puestos registran pocos ingresos en una vía distinta a la "
                       "habitual (por ejemplo, La Aurora en vía terrestre); se muestran tal como vienen en el "
                       "registro migratorio.", className="nota"),
            ]),
            tarjeta(className="tarjeta ancha", id=id_grafica("fronteras", "serie"), children=[
                html.Div(className="tarjeta-cab", children=[
                    html.Div([
                        html.H2(id="titulo-serie-frontera"),
                        html.P("Haga clic en un año para ver solo ese año en el gráfico 6. «% del total» muestra "
                               "qué parte de todos los ingresos del país pasó por la selección.",
                               className="ayuda"),
                    ]),
                    html.Div([
                        dcc.RadioItems(id="granularidad-front", options=[{"label": "Anual", "value": "A"},
                                                                         {"label": "Mensual", "value": "M"}],
                                       value="A", inline=True, className="segmentado"),
                        dcc.RadioItems(id="medida-front", options=[{"label": "Viajeros", "value": "abs"},
                                                                   {"label": "% del total", "value": "pct"}],
                                       value="abs", inline=True, className="segmentado"),
                    ]),
                ]),
                dcc.Graph(id="g-serie-frontera", config={"displayModeBar": False}),
                html.P(["La franja ", html.Span("roja", style={"color": COLOR["alerta"], "fontWeight": 600}),
                        " marca el cierre de fronteras por COVID-19 (mar 2020 a mar 2021). "
                        "2026 incluye solo enero a junio."], className="nota"),
            ]),
        ]),
    ])


@callback(
    Output("sel-via", "data"),
    Output("sel-frontera", "data"),
    Input("g-fronteras", "clickData"),
    Input("btn-todas-vias", "n_clicks"),
    State("sel-via", "data"),
    State("sel-frontera", "data"),
    prevent_initial_call=True,
)
def seleccionar_ruta(click, _n, via, frontera):
    if callback_context.triggered_id == "btn-todas-vias":
        return None, None
    if not click:
        return no_update, no_update
    etiqueta = click["points"][0]["y"]
    if via is None:
        return etiqueta, None  # primer nivel: baja de la vía a sus puestos
    return no_update, None if etiqueta == frontera else etiqueta


@callback(
    Output("sel-anio-front", "data"),
    Input("g-serie-frontera", "clickData"),
    Input("f-anios", "value"),
    State("sel-anio-front", "data"),
    prevent_initial_call=True,
)
def seleccionar_anio_front(click, rango, actual):
    if callback_context.triggered_id == "g-serie-frontera" and click:
        anio = int(str(click["points"][0]["x"])[:4])  # anual: 2019, mensual: "2019-05-01"
        return None if anio == actual else anio
    if actual is not None and not (rango[0] <= actual <= rango[1]):
        return None
    return no_update


@callback(
    Output("g-fronteras", "figure"),
    Output("titulo-ranking", "children"),
    Output("ayuda-ranking", "children"),
    Output("btn-todas-vias", "style"),
    Input("f-anios", "value"), Input("f-tipos", "value"), Input("f-vias", "value"),
    Input("sel-via", "data"), Input("sel-frontera", "data"), Input("sel-anio-front", "data"),
)
def fig_fronteras(rango, tipos, vias, via, frontera, anio_sel):
    d = filtrar_fr(rango, tipos, vias)
    if anio_sel:
        d = d[d["Año"] == anio_sel]
    periodo = str(anio_sel) if anio_sel else f"{rango[0]} a {rango[1]}"
    estilo_btn = {"visibility": "visible" if via else "hidden"}

    if via:
        d = d[d["Via"] == via]
        titulo = f"6. Puestos de ingreso · vía {via.lower()} · {periodo}"
        ayuda = "Haga clic en un puesto para ver su evolución en el gráfico 7. Use «Todas las vías» para subir " \
                "de nivel."
        if d.empty:
            return figura_vacia(f"No hay ingresos por vía {via.lower()} con estos filtros."), titulo, ayuda, estilo_btn
        g = d.groupby("Frontera", as_index=False)["Viajeros"].sum()
        etiqueta, color = "Frontera", COLOR["seleccion"]
    else:
        titulo = f"6. ¿Por qué vía ingresan los viajeros? · {periodo}"
        ayuda = "Haga clic en una vía para ver sus puestos fronterizos y su evolución en el gráfico 7."
        if d.empty:
            return figura_vacia("No hay datos para esta combinación de filtros."), titulo, ayuda, estilo_btn
        g = d.groupby("Via", as_index=False)["Viajeros"].sum()
        etiqueta, color = "Via", COLOR["primario"]

    g = g[g["Viajeros"] > 0].sort_values("Viajeros")
    g["pct"] = g["Viajeros"] / g["Viajeros"].sum() * 100
    fig = go.Figure(go.Bar(
        x=g["Viajeros"], y=g[etiqueta], orientation="h",
        marker_color=[COLOR["neutro"] if frontera and e != frontera else color for e in g[etiqueta]],
        text=[f"{p:.1f} %" if p >= 0.1 else "<0.1 %" for p in g["pct"]], textposition="outside",
        cliponaxis=False, textfont=dict(color=COLOR["texto_sec"], size=12),
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} viajeros<extra></extra>",
    ))
    base_layout(fig, alto=max(380, 26 * len(g) + 60))
    fig.update_xaxes(gridcolor=COLOR["borde"], showgrid=True, tickformat="~s", title_text="Viajeros",
                     title_font=dict(color=COLOR["texto_sec"]))
    fig.update_yaxes(showgrid=False, tickfont=dict(color=COLOR["texto"]))
    fig.update_layout(margin=dict(r=55))
    return fig, titulo, ayuda, estilo_btn


@callback(
    Output("g-serie-frontera", "figure"),
    Output("titulo-serie-frontera", "children"),
    Input("f-anios", "value"), Input("f-tipos", "value"), Input("f-vias", "value"),
    Input("granularidad-front", "value"), Input("medida-front", "value"),
    Input("sel-via", "data"), Input("sel-frontera", "data"), Input("sel-anio-front", "data"),
)
def fig_serie_frontera(rango, tipos, vias, gran, medida, via, frontera, anio_sel):
    d = filtrar_fr(rango, tipos, vias)
    if frontera:
        sel, nombre, color = d[(d["Via"] == via) & (d["Frontera"] == frontera)], frontera, COLOR["seleccion"]
    elif via:
        sel, nombre, color = d[d["Via"] == via], f"vía {via.lower()}", COLOR["seleccion"]
    else:
        sel, nombre, color = d, "todas las vías", COLOR["primario"]
    titulo = f"7. ¿Cómo ha evolucionado el ingreso? · {nombre}"
    if sel.empty:
        return figura_vacia(f"No hay ingresos registrados por {nombre} con estos filtros."), titulo

    eje = "Año" if gran == "A" else "Fecha"
    serie = sel.groupby(eje)["Viajeros"].sum()
    if medida == "pct":
        # El total incluye todas las vías y tipos para que el porcentaje no dependa de los filtros.
        total = fr[(fr["Año"] >= rango[0]) & (fr["Año"] <= rango[1])].groupby(eje)["Viajeros"].sum()
        serie = (serie / total * 100).dropna()
        plantilla = "%{y:.1f} % del total"
    else:
        plantilla = "%{y:,.0f} viajeros"
    formato_x = "%{x}" if gran == "A" else "%{x|%b %Y}"

    fig = go.Figure(go.Scatter(
        x=serie.index, y=serie.values, mode="lines+markers" if gran == "A" else "lines",
        line=dict(color=color, width=2.5),
        marker=dict(size=8, color=color, line=dict(color=COLOR["tarjeta"], width=2)),
        hovertemplate=f"<b>{formato_x}</b><br>{plantilla}<extra></extra>",
    ))
    if gran == "A":
        covid = (2019.5, 2021.5)
        seleccion = (anio_sel - 0.5, anio_sel + 0.5) if anio_sel else None
        fig.update_xaxes(dtick=1, tickangle=-45, range=[rango[0] - 0.5, rango[1] + 0.5])
    else:
        covid = ("2020-03-01", "2021-03-31")
        seleccion = (f"{anio_sel}-01-01", f"{anio_sel}-12-31") if anio_sel else None
    if rango[0] <= 2021 and rango[1] >= 2020:
        fig.add_vrect(x0=covid[0], x1=covid[1], fillcolor=COLOR["alerta"], opacity=0.08, line_width=0)
    if seleccion:
        fig.add_vrect(x0=seleccion[0], x1=seleccion[1], fillcolor=COLOR["seleccion"], opacity=0.15,
                      line_width=0)

    base_layout(fig)
    fig.update_yaxes(rangemode="tozero", title=dict(text="Viajeros" if medida == "abs" else "% del total",
                                                    font=dict(color=COLOR["texto_sec"])))
    if medida == "pct":
        fig.update_yaxes(ticksuffix=" %", tickformat=None)
    return fig, titulo


@callback(
    Output("aviso-fronteras", "children"),
    Input("sel-via", "data"), Input("sel-frontera", "data"), Input("sel-anio-front", "data"),
)
def aviso_fronteras(via, frontera, anio):
    partes = [texto for texto in (via and f"Vía {via.lower()}", frontera and f"Puesto {frontera}",
                                  anio and f"Año {anio}") if texto]
    if not partes:
        return ""
    return [html.Span("Selección activa: ", className="aviso-tit"), " · ".join(partes),
            html.Span(" (haga clic de nuevo en el puesto o el año, o use «Todas las vías»)",
                      className="aviso-sec")]
