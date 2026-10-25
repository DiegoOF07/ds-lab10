# Lab 10 · Observatorio de Turismo Sostenible (Guatemala)

Tablero interactivo en Plotly Dash (CC3066 Data Science, UVG).

## Ejecutar
```bash
pip install -r requirements.txt
python app.py      # abrir http://127.0.0.1:8050
```

## Estructura
- `app.py` · encabezado, filtros globales y navegación por pestañas
- `comun.py` · paleta, carga de datos y funciones compartidas (filtros, figura vacía, selector de gráficas)
- `pestanas/` · una pestaña por archivo
  - `panorama.py` · tarjetas de indicadores, V1 tendencia, V2 mercados y V3 estacionalidad (enlazadas)
  - `mercados.py` · V4 mapa de origen y V5 composición por tipo de viajero (enlazadas)
  - `fronteras.py` · V6 vías y puestos de ingreso y V7 evolución del puesto (enlazadas)
  - `pronosticos.py` · V8 registrado vs. pronóstico, V9 error por modelo y V10 error mes a mes (enlazadas),
    tabla comparativa de modelos
  - `guia.py` · glosario, limitaciones de los datos y cómo usar el tablero
- `assets/style.css` · paleta y tipografía
- `data/viajeros_agregado.csv` · datos del Lab 1 agregados por mes, región, país, vía y tipo de viajero
- `data/viajeros_frontera.csv` · datos del Lab 1 agregados por mes, vía, puesto fronterizo y tipo de viajero
- `data/paises_iso.csv` · código ISO de cada país para el mapa
- `data/pronosticos.csv`, `data/metricas_modelos.csv`, `data/series_modelos.csv` · resultados de los modelos
  del Lab 1 (pronósticos del periodo de prueba, MAE y RMSE, y la serie observada completa)
- `scripts/agregar_fronteras.py` · genera `viajeros_frontera.csv` a partir del CSV crudo del Lab 1
- `scripts/exportar_modelos.py` · genera los CSV de modelos a partir de los datos procesados del Lab 1
- `docs/` · imágenes del documento de diseño (paleta, bosquejo, mapa de navegación y capturas)

## Regenerar los datos por frontera
El CSV crudo (`data/series_tiempo_2009-2026.csv`) está en el [repositorio del Lab 1](https://github.com/JuanDsm04/ds-lab1).
```bash
python scripts/agregar_fronteras.py <ruta>/series_tiempo_2009-2026.csv
```

## Modelos (pestaña Pronósticos y modelos)
No se entrenan modelos nuevos: `scripts/exportar_modelos.py` vuelve a ejecutar, con los mismos parámetros, los
modelos de `04_05_analisis_series.ipynb` del [Lab 1](https://github.com/JuanDsm04/ds-lab1) y comprueba que el
MAE y el RMSE coincidan con los del notebook.

| Modelo | Parámetros del Lab 1 |
|---|---|
| Seasonal Naïve | Mismo mes del año anterior (línea base) |
| Holt-Winters | Tendencia aditiva amortiguada y estacionalidad multiplicativa de 12 meses |
| SARIMA | ARIMA(0,d,1)(0,1,1)[12] con `d` de auto_arima (0 en las tres series) sobre el logaritmo de la serie; incluye intervalo de confianza del 95 % |

- Series: Total, Turista y Turista + Excursionista, las únicas donde se pueden comparar los tres modelos.
  Holt-Winters no se ajusta a series con meses en cero, y la serie de residentes en Guatemala se descartó porque
  desde enero de 2023 el registro ya no los incluye.
- Entrenamiento: enero 2009 a marzo 2021. Prueba: abril 2021 a junio 2026.

```bash
pip install -r requirements-modelos.txt
python scripts/exportar_modelos.py <ruta>/ds-lab1/data/procesado
```

## Agregar una pestaña
1. Crear `pestanas/<nombre>.py` con una función `layout()` y sus callbacks (`from dash import callback`).
2. Registrarla en la lista `PESTANAS` de `app.py`.
3. Para que el usuario pueda ocultar gráficas, usar `selector_graficas()` y dar a cada tarjeta el id
   `id_grafica("<pestaña>", "<gráfica>")` (ver `pestanas/mercados.py`).

Los colores tienen un significado fijo en toda la app (`COLOR` en `comun.py`): azul petróleo para datos
observados, turquesa para la selección del usuario, ámbar para pronósticos y terracota para la pandemia.

## Documento de diseño
[Documento de diseño del avance (Google Docs)](https://docs.google.com/document/d/1n_98zcrawd3x-nWvB_Nb1vEYhk5fa4GnEQxWIs63NVw/edit?usp=sharing)
