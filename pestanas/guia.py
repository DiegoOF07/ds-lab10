"""Pestaña Guía: glosario, limitaciones de los datos y cómo usar el tablero (solo texto)."""
from dash import html

from comun import tarjeta

GLOSARIO = [
    ("Turista", "Visitante que pernocta al menos una noche en Guatemala."),
    ("Excursionista", "Visitante que entra y sale del país el mismo día, sin pernoctar."),
    ("Crucerista", "Pasajero que llega en un crucero y desembarca durante la escala del barco."),
    ("«Viajero»", "Categoría del registro migratorio para quienes no se clasifican como turistas, excursionistas "
                  "ni cruceristas. Desde 2022 dejó de incluir a los viajeros no turísticos de alta frecuencia, por "
                  "lo que su caída a partir de ese año no indica por sí sola menos llegadas."),
    ("Estacionalidad", "Patrón que se repite cada año en los mismos meses, como la temporada alta de diciembre, "
                       "Semana Santa y julio."),
    ("Pronóstico", "Estimación de cuántos viajeros llegarían en meses futuros, calculada por un modelo a partir "
                   "de los meses anteriores. Es una estimación, no un dato registrado."),
    ("Periodo de prueba", "Meses que el modelo no vio al aprender (abril 2021 a junio 2026). Se usan para comparar "
                          "lo que estimó con lo que se registró."),
    ("MAE (error absoluto medio)", "En promedio, por cuántos viajeros se equivocó el pronóstico cada mes. "
                                   "Mientras más bajo, mejor."),
    ("RMSE (raíz del error cuadrático medio)", "Igual que el MAE, pero castiga más los errores grandes. Si es mucho "
                                               "mayor que el MAE, hubo meses con fallos muy grandes."),
    ("Intervalo o rango de confianza", "Rango donde el modelo espera que caiga el dato real con cierta "
                                       "probabilidad (aquí, 95 %). Un rango amplio indica mucha incertidumbre."),
    ("Escala logarítmica", "Escala en la que cada paso multiplica por 10 (1, 10, 100, 1 000…). El mapa de origen "
                           "la usa para que los países con pocos viajeros no se vean todos iguales frente a los "
                           "que envían millones."),
]

LIMITACIONES = [
    "Entre marzo de 2020 y marzo de 2021 las fronteras estuvieron cerradas por COVID-19; las cifras de ese periodo "
    "no son comparables con el resto y se marcan con una franja roja.",
    "2026 incluye solo de enero a junio, por lo que su total anual se ve más bajo que el de años completos.",
    "Desde 2022 la categoría «Viajero» cambió de definición; para comparar años conviene usar turistas y "
    "excursionistas. Desde 2023 el registro ya no incluye viajeros con residencia en Guatemala.",
    "El 2.9 % de los viajeros no tiene un país identificable (cruceristas y «otros países»), por lo que no "
    "aparece en el mapa de origen.",
    "La fuente es el registro migratorio de ingresos: no contiene ocupación hotelera, gasto ni destinos internos.",
    "Los pronósticos son de los modelos del Laboratorio 1, entrenados hasta marzo de 2021; sirven para comparar "
    "modelos, no como pronóstico oficial.",
    "El tablero muestra lo que se registró y lo que estimaron los modelos; no permite afirmar las causas de un "
    "aumento o una caída.",
]

PASOS = [
    ("Elija el periodo, el tipo de viajero y la vía", " en los filtros de arriba. Se aplican a todas las pestañas "
                                                     "y se conservan al cambiar de pestaña."),
    ("Recorra las pestañas en orden", ": Panorama da la vista general; Mercados de origen y Fronteras y vías "
                                      "detallan de dónde y por dónde llegan los viajeros; Pronósticos y modelos "
                                      "compara las estimaciones con lo registrado."),
    ("Haga clic en las gráficas", " para enlazarlas: un año, una región, un país, una vía o un modelo actualizan "
                                  "las demás gráficas de la pestaña. Un segundo clic o el botón de la tarjeta quita "
                                  "la selección."),
    ("Cambie el nivel de detalle", " con los selectores de cada tarjeta (anual o mensual, viajeros o porcentaje) "
                                   "y bajando de región a país o de vía a puesto fronterizo."),
    ("Use «Gráficas visibles»", " para mostrar solo las gráficas que le interesan, y lea la nota al pie de cada "
                                "una antes de sacar conclusiones."),
]


def layout():
    return html.Div(className="grid", children=[
        tarjeta(className="tarjeta ancha guia", children=[
            html.H2("Glosario"),
            html.Dl([elem for termino, definicion in GLOSARIO for elem in (html.Dt(termino), html.Dd(definicion))]),
        ]),
        html.Div(className="guia-col", children=[
            tarjeta(className="tarjeta guia", children=[
                html.H2("Cómo usar el tablero"),
                html.Ol([html.Li([html.B(titulo), texto]) for titulo, texto in PASOS]),
            ]),
            tarjeta(className="tarjeta guia", children=[
                html.H2("Limitaciones de los datos"),
                html.Ul([html.Li(texto) for texto in LIMITACIONES]),
            ]),
        ]),
    ])
