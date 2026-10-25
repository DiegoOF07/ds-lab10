from dash import Dash, dcc, html

from comun import ANIOS, TIPOS, VIAS, tarjeta
from pestanas import fronteras, mercados, panorama

app = Dash(__name__, title="Observatorio de Turismo · Guatemala")

app.index_string = """<!DOCTYPE html>
<html><head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head><body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body></html>"""

PESTANAS = [
    ("panorama", "Panorama", panorama),
    ("mercados", "Mercados de origen", mercados),
    ("fronteras", "Fronteras y vías", fronteras),
]

app.layout = html.Div(className="pagina", children=[
    html.Header(className="encabezado", children=[
        html.H1("Observatorio de Turismo Sostenible · Guatemala"),
        html.P("Registro migratorio de ingresos de viajeros · enero 2009 a junio 2026", className="subtitulo"),
    ]),

    tarjeta(className="tarjeta filtros", children=[
        html.Div([html.Label("Periodo"),
                  dcc.RangeSlider(id="f-anios", min=ANIOS[0], max=ANIOS[-1], step=1,
                                  value=[ANIOS[0], ANIOS[-1]],
                                  marks={a: str(a) for a in ANIOS if (a - ANIOS[0]) % 3 == 0 or a == ANIOS[-1]},
                                  allowCross=False)], className="filtro ancho"),
        html.Div([html.Label("Tipo de viajero"),
                  dcc.Checklist(id="f-tipos", options=TIPOS, value=TIPOS, inline=True,
                                className="chips")], className="filtro"),
        html.Div([html.Label("Vía de ingreso"),
                  dcc.Checklist(id="f-vias", options=VIAS, value=VIAS, inline=True,
                                className="chips")], className="filtro"),
    ]),

    # Los filtros quedan fuera de las pestañas para que se conserven al navegar.
    dcc.Tabs(id="pestanas", value=PESTANAS[0][0], className="pestanas", children=[
        dcc.Tab(label=nombre, value=valor, className="pestana", selected_className="pestana--activa",
                children=modulo.layout())
        for valor, nombre, modulo in PESTANAS
    ]),
])


if __name__ == "__main__":
    app.run(debug=False)
