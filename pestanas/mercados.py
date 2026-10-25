import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, State, callback, callback_context, dcc, html, no_update

from comun import (COLOR, TIPO_COLOR, TIPOS, base_layout, df, figura_vacia, filtrar, id_grafica,
                   selector_graficas, tarjeta)

# Marcas de la barra de color del mapa, que usa escala logarítmica.
POTENCIAS = ["1", "10", "100", "1 mil", "10 mil", "100 mil", "1 millón", "10 millones", "100 millones"]


def layout():
    return html.Div([
        dcc.Store(id="sel-pais", data=None),
        dcc.Store(id="sel-anio-merc", data=None),

        selector_graficas("mercados", [("mapa", "4. Mapa de origen"), ("composicion", "5. Tipo de viajero")]),
        html.Div(id="aviso-mercados", className="aviso"),

        html.Div(className="grid", children=[
            tarjeta(className="tarjeta ancha", id=id_grafica("mercados", "mapa"), children=[
                html.Div(className="tarjeta-cab", children=[
                    html.Div([
                        html.H2(id="titulo-mapa"),
                        html.P("Haga clic en un país para ver qué tipo de viajeros envía en el gráfico 5. "
                               "Use la rueda del ratón o los botones del mapa para acercarse a una región.",
                               className="ayuda"),
                    ]),
                    html.Button("Quitar selección", id="btn-limpiar-mercados", n_clicks=0, className="boton"),
                ]),
                dcc.Graph(id="g-mapa", config={"displayModeBar": True, "scrollZoom": True, "displaylogo": False,
                                               "modeBarButtonsToRemove": ["select2d", "lasso2d", "toImage", "hoverClosestGeo"]}),
                html.P(id="nota-mapa", className="nota"),
            ]),
            tarjeta(id=id_grafica("mercados", "composicion"), children=[
                html.Div(className="tarjeta-cab", children=[
                    html.Div([
                        html.H2(id="titulo-composicion"),
                        html.P("Haga clic en un año para ver solo ese año en el mapa. Haga clic en la leyenda "
                               "para ocultar o mostrar un tipo.", className="ayuda"),
                    ]),
                    html.Div([
                        dcc.RadioItems(id="granularidad-comp", options=[{"label": "Anual", "value": "A"},
                                                                        {"label": "Mensual", "value": "M"}],
                                       value="A", inline=True, className="segmentado"),
                        dcc.RadioItems(id="medida-comp", options=[{"label": "Viajeros", "value": "abs"},
                                                                  {"label": "% del total", "value": "pct"}],
                                       value="abs", inline=True, className="segmentado"),
                    ]),
                ]),
                dcc.Graph(id="g-composicion", config={"displayModeBar": False}),
                html.P(["Cifras observadas. ", html.B("Turista"), ": pernocta al menos una noche. ",
                        html.B("Excursionista"), ": entra y sale el mismo día. ",
                        html.B("Crucerista"), ": llega en crucero. Desde 2022 la categoría «Viajero» cambió de "
                        "definición, por lo que su caída no indica por sí sola menos llegadas."],
                       className="nota"),
            ]),
        ]),
    ])


def nombre_pais(iso):
    nombres = df.loc[df["ISO3"] == iso, "Pais"]
    return nombres.iloc[0] if not nombres.empty else iso


@callback(
    Output("sel-pais", "data"),
    Input("g-mapa", "clickData"),
    Input("btn-limpiar-mercados", "n_clicks"),
    State("sel-pais", "data"),
    prevent_initial_call=True,
)
def seleccionar_pais(click, _n, actual):
    if callback_context.triggered_id == "btn-limpiar-mercados":
        return None
    if click:
        iso = click["points"][0]["location"]
        return None if iso == actual else iso  # segundo clic deselecciona
    return no_update


@callback(
    Output("sel-anio-merc", "data"),
    Input("g-composicion", "clickData"),
    Input("btn-limpiar-mercados", "n_clicks"),
    Input("f-anios", "value"),
    State("sel-anio-merc", "data"),
    prevent_initial_call=True,
)
def seleccionar_anio_merc(click, _n, rango, actual):
    disparo = callback_context.triggered_id
    if disparo == "btn-limpiar-mercados":
        return None
    if disparo == "g-composicion" and click:
        anio = int(str(click["points"][0]["x"])[:4])  # anual: 2019, mensual: "2019-05-01"
        return None if anio == actual else anio
    if actual is not None and not (rango[0] <= actual <= rango[1]):
        return None
    return no_update


@callback(
    Output("g-mapa", "figure"),
    Output("titulo-mapa", "children"),
    Output("nota-mapa", "children"),
    Input("f-anios", "value"), Input("f-tipos", "value"), Input("f-vias", "value"),
    Input("sel-pais", "data"), Input("sel-anio-merc", "data"),
)
def fig_mapa(rango, tipos, vias, iso_sel, anio_sel):
    d = filtrar(rango, tipos, vias)
    if anio_sel:
        d = d[d["Año"] == anio_sel]
    periodo = str(anio_sel) if anio_sel else f"{rango[0]} a {rango[1]}"
    titulo = f"4. ¿Desde qué países llegan los viajeros? · {periodo}"
    if d.empty:
        return figura_vacia("No hay datos para esta combinación de filtros."), titulo, ""

    total = d["Viajeros"].sum()
    sin_pais = d.loc[d["ISO3"].isna(), "Viajeros"].sum()
    nota = (f"Cifras observadas. Más oscuro significa más viajeros; cada tono de la escala equivale a diez veces "
            f"más viajeros, para que también se distingan los mercados pequeños. "
            f"El {sin_pais / total * 100:.1f} % de los viajeros del periodo no tiene un país identificable "
            f"(cruceristas y categorías «otros países») y no aparece en el mapa.")

    g = d.dropna(subset=["ISO3"]).groupby("ISO3", as_index=False).agg(Viajeros=("Viajeros", "sum"),
                                                                      Pais=("Pais", "first"))
    g = g[g["Viajeros"] > 0]
    if g.empty:
        return figura_vacia("Los viajeros seleccionados no tienen un país identificable."), titulo, nota
    g["pct"] = g["Viajeros"] / total * 100
    maximo = np.log10(g["Viajeros"].max())
    marcas = list(range(int(maximo) + 1))

    fig = go.Figure(go.Choropleth(
        locations=g["ISO3"], z=np.log10(g["Viajeros"]), customdata=g[["Pais", "Viajeros", "pct"]],
        zmin=0, zmax=maximo, colorscale=[[0, "#E6F0F2"], [1, COLOR["primario"]]],
        marker_line_color=COLOR["tarjeta"], marker_line_width=0.5,
        colorbar=dict(thickness=12, len=0.8, outlinewidth=0, tickvals=marcas,
                      ticktext=[POTENCIAS[k] for k in marcas], tickfont=dict(color=COLOR["texto_sec"])),
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]:,.0f} viajeros<br>"
                      "%{customdata[2]:.2f} % del total<extra></extra>",
    ))
    if iso_sel:
        # Contorno del país seleccionado sin cambiar su relleno, para no perder la lectura del tono.
        fig.add_choropleth(locations=[iso_sel], z=[0], showscale=False, hoverinfo="skip",
                           colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                           marker_line_color=COLOR["seleccion"], marker_line_width=3)
    base_layout(fig, alto=460)
    fig.update_geos(projection_type="natural earth", showframe=False, showcoastlines=False,
                    showcountries=True, countrycolor=COLOR["tarjeta"], landcolor="#F0F2F4",
                    bgcolor=COLOR["tarjeta"], lataxis_range=[-58, 85])
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), dragmode="pan")
    return fig, titulo, nota


@callback(
    Output("g-composicion", "figure"),
    Output("titulo-composicion", "children"),
    Input("f-anios", "value"), Input("f-tipos", "value"), Input("f-vias", "value"),
    Input("granularidad-comp", "value"), Input("medida-comp", "value"),
    Input("sel-pais", "data"), Input("sel-anio-merc", "data"),
)
def fig_composicion(rango, tipos, vias, gran, medida, iso_sel, anio_sel):
    d = filtrar(rango, tipos, vias)
    origen = nombre_pais(iso_sel) if iso_sel else "todos los países"
    titulo = f"5. ¿Qué tipo de viajeros llegan? · {origen}"
    if iso_sel:
        d = d[d["ISO3"] == iso_sel]
    if d.empty:
        mensaje = f"No se registraron viajeros de {origen} con estos filtros." if iso_sel \
            else "No hay datos para esta combinación de filtros."
        return figura_vacia(mensaje), titulo

    eje = "Año" if gran == "A" else "Fecha"
    tabla = d.pivot_table(index=eje, columns="Tipo", values="Viajeros", aggfunc="sum", fill_value=0)
    fig = go.Figure()
    for tipo in TIPOS:
        if tipo not in tabla.columns:
            continue
        fig.add_scatter(
            x=tabla.index, y=tabla[tipo], name=tipo, mode="lines", stackgroup="tipos",
            groupnorm="percent" if medida == "pct" else "",
            line=dict(color=COLOR["tarjeta"], width=1), fillcolor=TIPO_COLOR[tipo],
            hovertemplate=f"{tipo}: %{{y:,.0f}}<extra></extra>" if medida == "abs"
            else f"{tipo}: %{{y:.1f}} %<extra></extra>",
        )

    if gran == "A":
        covid = (2019.5, 2021.5)
        seleccion = (anio_sel - 0.5, anio_sel + 0.5) if anio_sel else None
        fig.update_xaxes(dtick=2, range=[tabla.index.min(), tabla.index.max()])
    else:
        covid = ("2020-03-01", "2021-03-31")
        seleccion = (f"{anio_sel}-01-01", f"{anio_sel}-12-31") if anio_sel else None
    if rango[0] <= 2021 and rango[1] >= 2020:
        fig.add_vrect(x0=covid[0], x1=covid[1], fillcolor=COLOR["alerta"], opacity=0.08, line_width=0)
    if seleccion:
        fig.add_vrect(x0=seleccion[0], x1=seleccion[1], fillcolor=COLOR["seleccion"], opacity=0.15,
                      line_width=0)

    base_layout(fig, alto=460)
    fig.update_layout(showlegend=True, hovermode="x unified",
                      legend=dict(orientation="h", y=1.1, x=0, traceorder="normal"))
    if medida == "pct":
        fig.update_yaxes(ticksuffix=" %", tickformat=None, range=[0, 100])
    fig.update_yaxes(title=dict(text="Viajeros" if medida == "abs" else "% del total",
                                font=dict(color=COLOR["texto_sec"])))
    return fig, titulo


@callback(
    Output("aviso-mercados", "children"),
    Output("btn-limpiar-mercados", "style"),
    Input("sel-pais", "data"), Input("sel-anio-merc", "data"),
)
def aviso_mercados(iso, anio):
    partes = []
    if iso:
        partes.append(f"País {nombre_pais(iso)}")
    if anio:
        partes.append(f"Año {anio}")
    if not partes:
        return "", {"visibility": "hidden"}
    return [html.Span("Selección activa: ", className="aviso-tit"), " · ".join(partes),
            html.Span(" (haga clic de nuevo en el país o el año, o use «Quitar selección»)",
                      className="aviso-sec")], {"visibility": "visible"}
