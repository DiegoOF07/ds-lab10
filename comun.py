from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import ALL, MATCH, Input, Output, callback, callback_context, dcc, html

# Cada color tiene un único significado en toda la app.
COLOR = {
    "primario": "#0F4C5C",   # datos observados
    "seleccion": "#2A9D8F",  # selección del usuario
    "estimado": "#E9A23B",   # pronósticos
    "alerta": "#C8553D",     # eventos atípicos (pandemia)
    "neutro": "#9AA5B1",     # contexto / no seleccionado
    "texto": "#1F2933",
    "texto_sec": "#52606D",
    "fondo": "#F5F7F8",
    "tarjeta": "#FFFFFF",
    "borde": "#E1E5E9",
}
# Colores de identidad por tipo de viajero, validados para daltonismo en este orden.
TIPO_COLOR = {"Turista": "#2A78D6", "Excursionista": "#D55181", "Cruceristas": "#7B5FC4", "Viajero": "#8A7A1E"}
FUENTE = "Inter, 'Segoe UI', Roboto, Arial, sans-serif"
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

DATOS = Path(__file__).parent / "data"
df = pd.read_csv(DATOS / "viajeros_agregado.csv", parse_dates=["Fecha"])
# Algunos países aparecen con distinta capitalización según el año ("Antigua Y Barbuda").
_canon = df.groupby(df["Pais"].str.lower())["Pais"].agg(lambda s: s.value_counts().idxmax())
df["Pais"] = df["Pais"].str.lower().map(_canon)
df = df.merge(pd.read_csv(DATOS / "paises_iso.csv"), on="Pais", how="left")
ANIOS = sorted(int(a) for a in df["Año"].unique())
TIPOS = ["Turista", "Excursionista", "Cruceristas", "Viajero"]
VIAS = ["Aérea", "Terrestre", "Marítima"]


def fmt(n):
    return f"{n:,.0f}".replace(",", " ")


def base_layout(fig, alto=380):
    fig.update_layout(
        height=alto,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor=COLOR["tarjeta"],
        plot_bgcolor=COLOR["tarjeta"],
        font=dict(family=FUENTE, size=13, color=COLOR["texto"]),
        hoverlabel=dict(font=dict(family=FUENTE, size=13)),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=False, linecolor=COLOR["borde"], tickfont=dict(color=COLOR["texto_sec"]))
    fig.update_yaxes(gridcolor=COLOR["borde"], zeroline=False, tickfont=dict(color=COLOR["texto_sec"]),
                     tickformat="~s")
    return fig


def figura_vacia(mensaje):
    fig = go.Figure()
    fig.add_annotation(text=mensaje, showarrow=False, font=dict(size=15, color=COLOR["texto_sec"]),
                       xref="paper", yref="paper", x=0.5, y=0.5)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return base_layout(fig)


def filtrar(rango, tipos, vias):
    d = df[(df["Año"] >= rango[0]) & (df["Año"] <= rango[1])]
    return d[d["Tipo"].isin(tipos) & d["Via"].isin(vias)]


def tarjeta(children, className="tarjeta", **kwargs):
    return html.Div(children, className=className, **kwargs)


def id_grafica(pestana, graf):
    return {"tipo": "grafica", "pestana": pestana, "graf": graf}


def selector_graficas(pestana, opciones):
    """Checklist para que el usuario elija qué gráficas de la pestaña quiere ver."""
    return html.Div(className="selector", children=[
        html.Span("Gráficas visibles", className="selector-tit"),
        dcc.Checklist(id={"tipo": "selector", "pestana": pestana},
                      options=[{"label": etiqueta, "value": valor} for valor, etiqueta in opciones],
                      value=[valor for valor, _ in opciones], inline=True, className="chips"),
        html.Div(id={"tipo": "sin-graficas", "pestana": pestana}, className="aviso-vacio"),
    ])


@callback(
    Output({"tipo": "grafica", "pestana": MATCH, "graf": ALL}, "style"),
    Output({"tipo": "sin-graficas", "pestana": MATCH}, "children"),
    Input({"tipo": "selector", "pestana": MATCH}, "value"),
)
def mostrar_graficas(visibles):
    salidas = callback_context.outputs_list[0]
    estilos = [{} if s["id"]["graf"] in visibles else {"display": "none"} for s in salidas]
    return estilos, "" if visibles else "Seleccione al menos una gráfica para mostrarla."
