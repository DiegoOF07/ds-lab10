"""Exporta las predicciones y métricas de los modelos del Laboratorio 1.

No entrena modelos nuevos: vuelve a ejecutar, con los mismos parámetros, los modelos de
`04_05_analisis_series.ipynb` (repositorio del Lab 1) y guarda lo que en el notebook solo quedaba
en las salidas de las celdas.

Modelos (parámetros del Lab 1):
  - Seasonal Naïve: el valor del mismo mes del año anterior; si ese mes no está en el
    entrenamiento, el último valor de ese mismo mes en el entrenamiento (función del notebook).
  - Holt-Winters: tendencia aditiva amortiguada y estacionalidad multiplicativa de 12 meses.
  - SARIMA ARIMA(0,d,1)(0,1,1)[12]: el de menor RMSE en prueba para la serie Total. `d` es el que
    propuso auto_arima en el Lab 1, y la serie se pasa a logaritmo cuando la varianza de la segunda
    mitad supera 4 veces la de la primera (misma regla del notebook).

Series: Total, Turista y Turista + Excursionista. Son las series donde se pueden comparar los tres
modelos: Holt-Winters falla en las que tienen meses con cero viajeros (Excursionista, Cruceristas,
Viajero, El Salvador, EE. UU.), y Guatemala no se usa porque desde enero de 2023 el registro ya no
incluye residentes en Guatemala y su serie de prueba queda en cero.

Entrenamiento: series_mensuales_train.csv (ene 2009 – mar 2021).
Prueba: abr 2021 – jun 2026, agregando test_filas.csv igual que en el notebook.
Ambos archivos están en data/procesado/ del repositorio del Lab 1.

Salidas (data/):
  - pronosticos.csv       Serie, Modelo, Fecha, Real, Pronostico, Inferior, Superior
                          (Inferior y Superior: intervalo de confianza del 95 % del SARIMA)
  - metricas_modelos.csv  Serie, Modelo, MAE, RMSE
  - series_modelos.csv    Serie, Fecha, Real, Periodo  (serie observada completa, 2009 – 2026)

Uso:  python scripts/exportar_modelos.py <ruta a ds-lab1/data/procesado>
Requiere: pip install -r requirements-modelos.txt
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

warnings.filterwarnings("ignore")

SALIDA = Path(__file__).resolve().parent.parent / "data"
SERIES = ["Total", "Turista", "Turista + Excursionista"]
# d propuesto por auto_arima en el Lab 1 (salidas del notebook 04_05, inciso f).
D_AUTO = {"Total": 0, "Turista": 0, "Turista + Excursionista": 0}

# MAE y RMSE del Lab 1 (salidas del notebook 04_05) para comprobar que se reproducen.
LAB1 = {
    ("Total", "Seasonal Naïve"): (235_730.91, 253_203.39),
    ("Total", "Holt-Winters"): (178_639.87, 197_742.72),
    ("Total", "SARIMA"): (100_904.37, 112_078.02),
    ("Turista", "Seasonal Naïve"): (155_607.78, 164_460.37),
    ("Turista", "Holt-Winters"): (111_365.98, 121_527.97),
    ("Turista", "SARIMA"): (53_627.34, 58_865.50),
    ("Turista + Excursionista", "Seasonal Naïve"): (207_321.64, 219_663.87),
    ("Turista + Excursionista", "Holt-Winters"): (163_878.72, 177_765.86),
    ("Turista + Excursionista", "SARIMA"): (83_404.78, 87_818.90),
}
TOLERANCIA = 0.001  # 0.1 % de diferencia relativa


def cargar_series(carpeta):
    train = pd.read_csv(carpeta / "series_mensuales_train.csv", index_col=0, parse_dates=True)
    train.index.freq = pd.tseries.frequencies.to_offset("MS")

    df_test = pd.read_csv(carpeta / "test_filas.csv", parse_dates=["Fecha"])
    total = df_test.groupby("Fecha")["Viajero"].sum().rename("Total")
    tipo = (df_test.pivot_table(index="Fecha", columns="Tipo de Viajero", values="Viajero",
                                aggfunc="sum", observed=True).fillna(0).sort_index())
    tipo["Turista + Excursionista"] = tipo["Turista"] + tipo["Excursionista"]
    return train, pd.concat([total, tipo], axis=1)


def necesita_log(s):
    mitad = len(s) // 2
    v1, v2 = s.iloc[:mitad].var(), s.iloc[mitad:].var()
    ratio = max(v1, v2) / min(v1, v2) if min(v1, v2) > 0 else np.inf
    return ratio > 4 and (s > 0).all()


def seasonal_naive(s, s_test):
    pred = pd.Series(index=s_test.index, dtype=float)
    for fecha in s_test.index:
        ref = fecha - pd.DateOffset(years=1)
        if ref in s.index:
            pred[fecha] = s.loc[ref]
        else:
            mismo_mes = s[s.index.month == fecha.month]
            pred[fecha] = mismo_mes.iloc[-1] if len(mismo_mes) > 0 else s.iloc[-1]
    return pred, None


def holt_winters(s, s_test):
    fit = ExponentialSmoothing(s, trend="add", seasonal="mul", seasonal_periods=12,
                               damped_trend=True).fit(optimized=True)
    pred = fit.forecast(len(s_test))
    pred.index = s_test.index
    return pred, None


def sarima(s, s_test, d):
    usa_log = necesita_log(s)
    s_trabajo = np.log(s) if usa_log else s
    fit = SARIMAX(s_trabajo, order=(0, d, 1), seasonal_order=(0, 1, 1, 12),
                  enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
    pronostico = fit.get_prediction(start=s_test.index[0], end=s_test.index[-1])
    media, ic = pronostico.predicted_mean, pronostico.conf_int(alpha=0.05)
    ic.columns = ["Inferior", "Superior"]
    if usa_log:
        media, ic = np.exp(media), np.exp(ic)
    return media, ic


def main(carpeta):
    train, test = cargar_series(carpeta)
    filas_pron, filas_met, filas_serie = [], [], []

    for serie in SERIES:
        s = train[serie].dropna().asfreq("MS")
        s_test = test[serie].dropna()
        filas_serie.append(pd.DataFrame({"Serie": serie, "Fecha": s.index, "Real": s.values,
                                         "Periodo": "Entrenamiento"}))
        filas_serie.append(pd.DataFrame({"Serie": serie, "Fecha": s_test.index, "Real": s_test.values,
                                         "Periodo": "Prueba"}))
        modelos = {"Seasonal Naïve": lambda: seasonal_naive(s, s_test),
                   "Holt-Winters": lambda: holt_winters(s, s_test),
                   "SARIMA": lambda: sarima(s, s_test, D_AUTO[serie])}
        for modelo, ajustar in modelos.items():
            pred, ic = ajustar()
            pred = pred.reindex(s_test.index)
            err = s_test - pred
            mae, rmse = err.abs().mean(), np.sqrt((err ** 2).mean())
            filas_met.append({"Serie": serie, "Modelo": modelo, "MAE": mae, "RMSE": rmse})
            bloque = pd.DataFrame({"Serie": serie, "Modelo": modelo, "Fecha": s_test.index,
                                   "Real": s_test.values, "Pronostico": pred.values})
            if ic is not None:
                bloque[["Inferior", "Superior"]] = ic.reindex(s_test.index).values
            filas_pron.append(bloque)
            print(f"  {serie:<25} {modelo:<15} MAE={mae:>12,.2f}  RMSE={rmse:>12,.2f}")

    pronosticos = pd.concat(filas_pron, ignore_index=True)
    metricas = pd.DataFrame(filas_met)
    series = pd.concat(filas_serie, ignore_index=True)
    for d in (pronosticos, series):
        d["Fecha"] = pd.to_datetime(d["Fecha"]).dt.strftime("%Y-%m-%d")
    pronosticos.round(2).to_csv(SALIDA / "pronosticos.csv", index=False)
    metricas.round(2).to_csv(SALIDA / "metricas_modelos.csv", index=False)
    series.round(2).to_csv(SALIDA / "series_modelos.csv", index=False)

    print("\nComprobación contra el Lab 1:")
    ok = True
    for (serie, modelo), (mae_ref, rmse_ref) in LAB1.items():
        fila = metricas[(metricas["Serie"] == serie) & (metricas["Modelo"] == modelo)].iloc[0]
        coincide = (abs(fila["MAE"] / mae_ref - 1) < TOLERANCIA
                    and abs(fila["RMSE"] / rmse_ref - 1) < TOLERANCIA)
        ok &= coincide
        print(f"  {serie:<25} {modelo:<15} MAE {fila['MAE']:>12,.2f} (Lab 1 {mae_ref:>12,.2f})  "
              f"RMSE {fila['RMSE']:>12,.2f} (Lab 1 {rmse_ref:>12,.2f})  {'OK' if coincide else 'NO COINCIDE'}")
    if not ok:
        sys.exit("Las métricas no coinciden con el Lab 1; revisar antes de usar los CSV.")
    print(f"\nArchivos guardados en {SALIDA}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
