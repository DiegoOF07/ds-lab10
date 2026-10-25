"""Pestaña Pronósticos y modelos: V8 (registrado vs. pronóstico), V9 (error por modelo),
V10 (error mes a mes) y tabla comparativa.

Los datos vienen de scripts/exportar_modelos.py, que vuelve a ejecutar los modelos del Lab 1 sin
reentrenarlos con otros parámetros. Enlace V9 -> V8 y V10: clic en un modelo lo guarda en
`sel-modelo`; V8 lo resalta y V10 muestra sus errores. Sin selección, V10 usa el de menor error.
"""
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, callback_context, dcc, html, no_update

from comun import COLOR, DATOS, MESES, base_layout, figura_vacia, fmt, id_grafica, selector_graficas, tarjeta

pron = pd.read_csv(DATOS / "pronosticos.csv", parse_dates=["Fecha"])
metricas = pd.read_csv(DATOS / "metricas_modelos.csv")
reales = pd.read_csv(DATOS / "series_modelos.csv", parse_dates=["Fecha"])

SERIES = {"Total": "Total de viajeros", "Turista": "Turistas",
          "Turista + Excursionista": "Turistas y excursionistas"}
MODELOS = ["Seasonal Naïve", "Holt-Winters", "SARIMA"]
# Mismo ámbar para todos los pronósticos; el tipo de línea distingue a cada modelo.
TRAZO = {"Seasonal Naïve": "dot", "Holt-Winters": "dash", "SARIMA": "solid"}
PARA_QUE = {
    "Seasonal Naïve": "Punto de comparación: repite lo que se registró el mismo mes del año anterior. "
                      "Un modelo que no le gana no aporta.",
    "Holt-Winters": "Combina la tendencia reciente con el patrón de temporada alta y baja. Es simple y "
                    "rápido de actualizar.",
    "SARIMA": "Aprende de los meses recientes y del mismo mes en años anteriores. Además del pronóstico, "
              "da un rango de confianza.",
}
FIN_ENTRENAMIENTO = pd.Timestamp("2021-03-01")
INICIO_PRUEBA, FIN_PRUEBA = pd.Timestamp("2021-04-01"), pd.Timestamp("2026-06-01")


def mes_anio(fecha):
    return f"{MESES[fecha.month - 1]} {fecha.year}"


def rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}, {alpha})"


def metricas_serie(serie, marcados):
    m = metricas[(metricas["Serie"] == serie) & (metricas["Modelo"].isin(marcados or []))]
    return m.sort_values("RMSE")


def modelo_activo(serie, marcados, seleccion):
    """El modelo que eligió el usuario; si no eligió ninguno, el de menor error."""
    m = metricas_serie(serie, marcados)
    if m.empty:
        return None
    return seleccion if seleccion in set(m["Modelo"]) else m.iloc[0]["Modelo"]


def recorte(d, rango):
    return d[(d["Fecha"].dt.year >= rango[0]) & (d["Fecha"].dt.year <= rango[1])]


def layout():
    return html.Div([
        dcc.Store(id="sel-modelo", data=None),

        tarjeta(className="tarjeta filtros", children=[
            html.Div([html.Label("Serie"),
                      dcc.Dropdown(id="pro-serie", options=[{"label": v, "value": k} for k, v in SERIES.items()],
                                   value="Total", clearable=False, searchable=False)], className="filtro"),
            html.Div([html.Label("Modelos"),
                      dcc.Checklist(id="pro-modelos", options=MODELOS, value=MODELOS, inline=True,
                                    className="chips")], className="filtro"),
            html.Div([html.Label("Detalle"),
                      dcc.Checklist(id="pro-opciones",
                                    options=[{"label": "Rango de confianza del SARIMA", "value": "ic"}],
                                    value=[], inline=True, className="chips")], className="filtro"),
            html.P("En esta pestaña el filtro de periodo acerca o aleja las gráficas 8 y 10; los filtros de tipo "
                   "y vía no aplican, porque los modelos se evaluaron sobre series fijas del Laboratorio 1.",
                   className="nota nota-filtros"),
        ]),

        selector_graficas("pronosticos", [("real", "8. Registrado vs. pronóstico"), ("errores", "9. Error por modelo"),
                                          ("mensual", "10. Error mes a mes")]),
        html.Div(id="aviso-pronosticos", className="aviso"),

        html.Div(className="grid", children=[
            tarjeta(className="tarjeta completa", id=id_grafica("pronosticos", "real"), children=[
                html.H2(id="titulo-real-pron"),
                html.P("La línea azul es lo que se registró; las líneas ámbar, lo que estimó cada modelo para el "
                       "periodo de prueba sin conocer esos meses. Pase el cursor para ver las cifras de cada mes.",
                       className="ayuda"),
                dcc.Graph(id="g-real-pron", config={"displayModeBar": False}),
                html.P(id="nota-real-pron", className="nota"),
            ]),
            tarjeta(id=id_grafica("pronosticos", "errores"), children=[
                html.H2("9. ¿Qué modelo se equivoca menos?"),
                html.P(id="ayuda-errores", className="ayuda"),
                dcc.Graph(id="g-errores", config={"displayModeBar": False}),
                html.P("MAE: en promedio, por cuántos viajeros se equivocó el pronóstico cada mes. RMSE: igual que el "
                       "MAE, pero castiga más los errores grandes; si es mucho mayor que el MAE, hubo meses con "
                       "fallos muy grandes. Ambos se calculan sobre todo el periodo de prueba "
                       "(abril 2021 a junio 2026).", className="nota"),
            ]),
            tarjeta(id=id_grafica("pronosticos", "mensual"), children=[
                html.H2(id="titulo-mensual"),
                html.P("Barra hacia arriba: se registraron más viajeros de los que el modelo estimó (se quedó corto). "
                       "Hacia abajo: estimó más de los que llegaron (se pasó). Elija otro modelo en el gráfico 9.",
                       className="ayuda"),
                dcc.Graph(id="g-mensual", config={"displayModeBar": False}),
                html.P(id="nota-mensual", className="nota"),
            ]),
        ]),

        html.Div(className="grid", style={"marginTop": "16px"}, children=[
            tarjeta(className="tarjeta ancha", children=[
                html.H2(id="titulo-tabla-modelos"),
                html.P("Complemento de los gráficos 8 a 10. Los modelos están ordenados de menor a mayor error.",
                       className="ayuda"),
                html.Div(id="tabla-modelos"),
            ]),
            tarjeta(className="tarjeta limitaciones", children=[
                html.H2("Cómo leer estos resultados"),
                html.Ul([
                    html.Li("Son los modelos del Laboratorio 1: se entrenaron con datos de enero de 2009 a marzo de "
                            "2021 y se evaluaron de abril de 2021 a junio de 2026."),
                    html.Li("El entrenamiento terminó en plena pandemia y la evaluación cubre la recuperación, un "
                            "periodo distinto a todo lo que los modelos habían visto. Por eso el error es alto."),
                    html.Li("Sirven para comparar modelos entre sí, no como pronóstico oficial de llegadas, y no "
                            "permiten afirmar por qué subió o bajó el flujo."),
                    html.Li("Lo azul se registró; lo ámbar es estimado."),
                ]),
            ]),
        ]),
    ])


@callback(
    Output("sel-modelo", "data"),
    Input("g-errores", "clickData"),
    Input("pro-serie", "value"),
    State("sel-modelo", "data"),
    prevent_initial_call=True,
)
def seleccionar_modelo(click, _serie, actual):
    if callback_context.triggered_id == "pro-serie":
        return None
    if not click:
        return no_update
    modelo = click["points"][0]["y"]
    return None if modelo == actual else modelo  # segundo clic quita la selección


@callback(
    Output("aviso-pronosticos", "children"),
    Input("sel-modelo", "data"), Input("pro-serie", "value"), Input("pro-modelos", "value"),
)
def aviso_pronosticos(modelo, serie, marcados):
    if not modelo or modelo not in (marcados or []):
        return ""
    return [html.Span("Modelo seleccionado: ", className="aviso-tit"), f"{modelo} · {SERIES[serie]}",
            html.Span(" (haga clic de nuevo en el modelo del gráfico 9 para quitarlo)", className="aviso-sec")]


@callback(
    Output("g-real-pron", "figure"), Output("titulo-real-pron", "children"), Output("nota-real-pron", "children"),
    Input("pro-serie", "value"), Input("pro-modelos", "value"), Input("pro-opciones", "value"),
    Input("sel-modelo", "data"), Input("f-anios", "value"),
)
def fig_real_pron(serie, marcados, opciones, seleccion, rango):
    titulo = f"8. ¿Qué tan cerca estuvo cada modelo de lo que realmente pasó? · {SERIES[serie]}"
    real = recorte(reales[reales["Serie"] == serie], rango).sort_values("Fecha")
    if real.empty:
        return figura_vacia("No hay datos de esta serie en el periodo elegido."), titulo, ""
    p = recorte(pron[pron["Serie"] == serie], rango)
    visibles = [m for m in MODELOS if m in (marcados or [])]

    fig = go.Figure()
    if rango[0] <= 2021 and rango[1] >= 2020:
        fig.add_vrect(x0="2020-03-01", x1="2021-03-31", fillcolor=COLOR["alerta"], opacity=0.08, line_width=0)
    if "ic" in (opciones or []) and "SARIMA" in visibles and not p.empty:
        ic = p[p["Modelo"] == "SARIMA"].sort_values("Fecha")
        fig.add_scatter(x=pd.concat([ic["Fecha"], ic["Fecha"][::-1]]),
                        y=pd.concat([ic["Superior"], ic["Inferior"][::-1]]),
                        fill="toself", fillcolor=rgba(COLOR["estimado"], 0.15), line=dict(width=0),
                        name="Rango de confianza del SARIMA (95 %)", hoverinfo="skip")

    fig.add_scatter(x=real["Fecha"], y=real["Real"], mode="lines", name="Registrado",
                    line=dict(color=COLOR["primario"], width=2.4), customdata=[mes_anio(f) for f in real["Fecha"]],
                    hovertemplate="<b>%{customdata}</b><br>Se registraron: %{y:,.0f}<extra></extra>")
    for m in visibles:
        d = p[p["Modelo"] == m].sort_values("Fecha")
        if d.empty:
            continue
        resaltado = m == seleccion
        fig.add_scatter(
            x=d["Fecha"], y=d["Pronostico"], mode="lines", name=f"{m} (estimado)",
            line=dict(color=COLOR["seleccion"] if resaltado else COLOR["estimado"],
                      width=4 if resaltado else 2.2, dash=TRAZO[m]),
            opacity=1 if (resaltado or not seleccion) else 0.5,
            customdata=[mes_anio(f) for f in d["Fecha"]],
            hovertemplate=f"<b>%{{customdata}}</b><br>{m} estimó: %{{y:,.0f}}<extra></extra>",
        )

    if rango[0] <= 2021 <= rango[1]:
        fig.add_vline(x=FIN_ENTRENAMIENTO, line=dict(color=COLOR["texto_sec"], width=1.5, dash="dot"))
        fig.add_annotation(x=FIN_ENTRENAMIENTO, y=1, yref="paper", text="Fin del entrenamiento (mar 2021)",
                           showarrow=False, xanchor="right", yanchor="bottom", xshift=-4,
                           font=dict(size=12, color=COLOR["texto_sec"]))
    if rango[1] < INICIO_PRUEBA.year:
        fig.add_annotation(text="El periodo de prueba (abr 2021 a jun 2026) queda fuera del periodo elegido.",
                           showarrow=False, xref="paper", yref="paper", x=0.5, y=0.95,
                           font=dict(size=13, color=COLOR["texto_sec"]))
    elif not visibles:
        fig.add_annotation(text="Marque al menos un modelo para compararlo con lo registrado.",
                           showarrow=False, xref="paper", yref="paper", x=0.5, y=0.95,
                           font=dict(size=13, color=COLOR["texto_sec"]))

    base_layout(fig, alto=430)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.14, x=0), margin=dict(t=30))
    fig.update_xaxes(dtick="M12" if rango[1] - rango[0] < 10 else "M24", tickformat="%Y")
    fig.update_yaxes(rangemode="tozero", title=dict(text="Viajeros al mes", font=dict(color=COLOR["texto_sec"])))

    nota = ("La franja roja marca el cierre de fronteras por COVID-19 (mar 2020 a mar 2021). "
            "Junio de 2026 es el último mes con datos.")
    if "ic" in (opciones or []):
        nota += (" La banda ámbar es el rango donde el SARIMA esperaba que cayera el dato con 95 % de confianza; "
                 "es muy amplia porque el modelo aprendió de un periodo con cambios bruscos.")
    if serie == "Total":
        nota += (" La serie Total incluye la categoría «Viajero», que cambió de definición en 2022; desde 2023 "
                 "parte de la diferencia coincide con ese cambio.")
    return fig, titulo, nota


@callback(
    Output("g-errores", "figure"), Output("ayuda-errores", "children"),
    Input("pro-serie", "value"), Input("pro-modelos", "value"), Input("sel-modelo", "data"),
)
def fig_errores(serie, marcados, seleccion):
    m = metricas_serie(serie, marcados)
    if m.empty:
        return (figura_vacia("Marque al menos un modelo para comparar su error."),
                "Haga clic en un modelo para resaltarlo en el gráfico 8 y ver sus errores en el gráfico 10.")
    mejor = m.iloc[0]
    ayuda = (f"Haga clic en un modelo para resaltarlo en el gráfico 8 y ver sus errores mes a mes en el gráfico 10. "
             f"El que menos se equivocó fue {mejor['Modelo']}: en promedio, su pronóstico falló por "
             f"{fmt(mejor['MAE'])} viajeros al mes.")

    m = m.iloc[::-1]  # el de menor error queda arriba
    color_mae = [COLOR["seleccion"] if x == seleccion else COLOR["estimado"] for x in m["Modelo"]]
    fig = go.Figure()
    fig.add_bar(y=m["Modelo"], x=m["MAE"], orientation="h", name="MAE (error promedio al mes)",
                marker_color=color_mae, text=[fmt(v) for v in m["MAE"]], textposition="outside", cliponaxis=False,
                textfont=dict(color=COLOR["texto_sec"], size=12),
                hovertemplate="<b>%{y}</b><br>Error promedio: %{x:,.0f} viajeros al mes<extra></extra>")
    fig.add_bar(y=m["Modelo"], x=m["RMSE"], orientation="h", name="RMSE",
                marker_color=[rgba(c, 0.45) for c in color_mae], text=[fmt(v) for v in m["RMSE"]],
                textposition="outside", cliponaxis=False, textfont=dict(color=COLOR["texto_sec"], size=12),
                hovertemplate="<b>%{y}</b><br>RMSE: %{x:,.0f} viajeros<extra></extra>")
    base_layout(fig, alto=380)
    fig.update_layout(barmode="group", bargap=0.3, showlegend=True, margin=dict(r=70),
                      legend=dict(orientation="h", y=1.12, x=0, traceorder="normal"))
    fig.update_xaxes(showgrid=True, gridcolor=COLOR["borde"], tickformat="~s", rangemode="tozero",
                     title=dict(text="Viajeros por mes", font=dict(color=COLOR["texto_sec"])))
    fig.update_yaxes(showgrid=False, tickfont=dict(color=COLOR["texto"], size=13))
    return fig, ayuda


@callback(
    Output("g-mensual", "figure"), Output("titulo-mensual", "children"), Output("nota-mensual", "children"),
    Input("pro-serie", "value"), Input("pro-modelos", "value"), Input("sel-modelo", "data"),
    Input("f-anios", "value"),
)
def fig_mensual(serie, marcados, seleccion, rango):
    modelo = modelo_activo(serie, marcados, seleccion)
    if modelo is None:
        return (figura_vacia("Marque al menos un modelo para ver sus errores."),
                "10. ¿En qué meses falló más el modelo?", "")
    titulo = f"10. ¿En qué meses falló más {modelo}?"
    d = recorte(pron[(pron["Serie"] == serie) & (pron["Modelo"] == modelo)], rango).sort_values("Fecha")
    if d.empty:
        return (figura_vacia("El periodo de prueba (abr 2021 a jun 2026) queda fuera del periodo elegido.<br>"
                             "Amplíe el filtro de periodo para ver los errores."), titulo, "")

    d = d.assign(Error=d["Real"] - d["Pronostico"])
    sentido = ["se quedó corto" if e > 0 else "se pasó" for e in d["Error"]]
    fig = go.Figure(go.Bar(
        x=d["Fecha"], y=d["Error"],
        marker_color=[COLOR["alerta"] if e > 0 else rgba(COLOR["alerta"], 0.5) for e in d["Error"]],
        customdata=list(zip([mes_anio(f) for f in d["Fecha"]], d["Real"], d["Pronostico"], sentido)),
        hovertemplate=("<b>%{customdata[0]}</b><br>Se registraron: %{customdata[1]:,.0f}"
                       "<br>El modelo estimó: %{customdata[2]:,.0f}"
                       "<br>Diferencia: %{y:+,.0f} (%{customdata[3]})<extra></extra>"),
    ))
    base_layout(fig, alto=380)
    fig.add_hline(y=0, line=dict(color=COLOR["texto_sec"], width=1))
    fig.update_xaxes(dtick="M12", tickformat="%Y")
    fig.update_yaxes(title=dict(text="Registrado menos estimado", font=dict(color=COLOR["texto_sec"])))

    peor = d.loc[d["Error"].abs().idxmax()]
    cortos = int((d["Error"] > 0).sum())
    origen = "seleccionado" if modelo == seleccion else "con menor error"
    nota = (f"Modelo {origen}. En {cortos} de {len(d)} meses el modelo se quedó corto. La mayor diferencia fue en "
            f"{mes_anio(peor['Fecha'])}: se registraron {fmt(peor['Real'])} viajeros y el modelo estimó "
            f"{fmt(peor['Pronostico'])}.")
    return fig, titulo, nota


@callback(
    Output("tabla-modelos", "children"), Output("titulo-tabla-modelos", "children"),
    Input("pro-serie", "value"),
)
def tabla_modelos(serie):
    m = metricas[metricas["Serie"] == serie].sort_values("RMSE")
    mejor = m.iloc[0]["Modelo"]
    filas = [
        html.Tr([html.Td([r["Modelo"]] + ([html.Span("menor error", className="etiqueta")] if r["Modelo"] == mejor
                                          else []), className="col-modelo"),
                 html.Td(fmt(r["MAE"]), className="num"), html.Td(fmt(r["RMSE"]), className="num"),
                 html.Td(PARA_QUE[r["Modelo"]])], className="mejor" if r["Modelo"] == mejor else None)
        for _, r in m.iterrows()
    ]
    cabecera = html.Tr([html.Th("Modelo"), html.Th("MAE (viajeros al mes)", className="num"),
                        html.Th("RMSE", className="num"), html.Th("¿Para qué sirve?")])
    return (html.Table([html.Thead(cabecera), html.Tbody(filas)], className="tabla"),
            f"Comparación de modelos · {SERIES[serie]}")
