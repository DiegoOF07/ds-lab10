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
- `assets/style.css` · paleta y tipografía
- `data/viajeros_agregado.csv` · datos del Lab 1 agregados por mes, región, país, vía y tipo de viajero
- `data/viajeros_frontera.csv` · datos del Lab 1 agregados por mes, vía, puesto fronterizo y tipo de viajero
- `data/paises_iso.csv` · código ISO de cada país para el mapa
- `scripts/agregar_fronteras.py` · genera `viajeros_frontera.csv` a partir del CSV crudo del Lab 1
- `docs/` · imágenes del documento de diseño (paleta, bosquejo, mapa de navegación y capturas)

## Regenerar los datos por frontera
El CSV crudo (`data/series_tiempo_2009-2026.csv`) está en el [repositorio del Lab 1](https://github.com/JuanDsm04/ds-lab1).
```bash
python scripts/agregar_fronteras.py <ruta>/series_tiempo_2009-2026.csv
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
