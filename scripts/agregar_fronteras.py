"""Agrega los datos crudos del Lab 1 por mes, vía, puesto fronterizo y tipo de viajero.

Uso: python scripts/agregar_fronteras.py <ruta a series_tiempo_2009-2026.csv>
El CSV crudo está en el repositorio del Lab 1 (data/series_tiempo_2009-2026.csv).
"""
import sys
from pathlib import Path

import pandas as pd

SALIDA = Path(__file__).resolve().parent.parent / "data" / "viajeros_frontera.csv"


def main(ruta):
    d = pd.read_csv(ruta, encoding="utf-8-sig", low_memory=False)
    d = d.drop(columns="Mes").rename(columns={"Mes cod": "Mes", "Vía": "Via", "Tipo de Viajero": "Tipo",
                                              "Viajero": "Viajeros"})
    # "07 Valle Nuevo" pasa a "Valle Nuevo"; el número solo ordena la lista original.
    d["Frontera"] = d["Frontera"].str.replace(r"^\d+\s+", "", regex=True)
    g = d.groupby(["Año", "Mes", "Via", "Frontera", "Tipo"], as_index=False)["Viajeros"].sum()
    g = g[g["Viajeros"] > 0]
    g.insert(0, "Fecha", pd.to_datetime(dict(year=g["Año"], month=g["Mes"], day=1)).dt.strftime("%Y-%m-%d"))
    g.to_csv(SALIDA, index=False)
    print(f"{len(g)} filas, {g['Viajeros'].sum():,.0f} viajeros en {SALIDA}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
