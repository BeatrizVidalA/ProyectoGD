# %% [markdown]
# # 00_exploracion.py - Hito 1 (version .py para abrir en VS Code, columnas en espanol)
# Proyecto: Sala de Crisis COVID-19 - Gestion de Datos IN1232C
# Resuelve el punto de partida del enunciado sobre reportes de enero a junio de 2020:
# 1) cargar 01-22-2020.csv, 2) nulos, 3) snake_case en espanol + fechas AAAA-MM-DD,
# 4) unir ene-jun 2020, 5) top 10 paises + Chile, 6) perfilado + 3 observaciones.
# Para correrlo: desde la carpeta del proyecto, `python notebooks/00_exploracion.py`
# o en VS Code: abrir este archivo y "Run Python File in Terminal".
# %%

import datetime as dt
import io
import time
from pathlib import Path
from urllib.request import urlopen

import matplotlib

matplotlib.use("Agg")  # graficos a PNG, no bloquea la terminal
import matplotlib.pyplot as plt
import pandas as pd

pd.set_option("display.max_columns", 40)

# Rutas (funcionan desde la raiz del repo o desde notebooks/)
PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw" / "daily_reports"
CLEAN = PROJECT / "data" / "clean"
FIGS = PROJECT / "data" / "figs"
PROFILE = PROJECT / "data" / "profile"
for carpeta in (RAW, CLEAN, FIGS, PROFILE):
    carpeta.mkdir(parents=True, exist_ok=True)

URL_BASE = (
    "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/"
    "csse_covid_19_data/csse_covid_19_daily_reports/{nombre}"
)

# Traduccion de los nombres originales de JHU a snake_case en espanol:
#   Province/State  -> provincia_estado      Country/Region -> region_pais
#   Last Update     -> ultima_actualizacion  Confirmed      -> confirmados
#   Deaths          -> fallecidos            Recovered      -> recuperados
#   Active          -> activos               Latitude       -> latitud
#   Longitude       -> longitud              Combined_Key   -> clave_combinada
#   Incidence_Rate  -> tasa_incidentes       Case_Fatality_Ratio -> tasa_letalidad
MAPA_COLUMNAS = {
    "Province/State": "provincia_estado",
    "Country/Region": "region_pais",
    "Last Update": "ultima_actualizacion",
    "FIPS": "fips",
    "Admin2": "admin2",
    "Province_State": "provincia_estado",
    "Country_Region": "region_pais",
    "Last_Update": "ultima_actualizacion",
    "Latitude": "latitud",
    "Longitude": "longitud",
    "Lat": "latitud",
    "Long_": "longitud",
    "Confirmed": "confirmados",
    "Deaths": "fallecidos",
    "Recovered": "recuperados",
    "Active": "activos",
    "Combined_Key": "clave_combinada",
    "Incidence_Rate": "tasa_incidentes",
    "Incident_Rate": "tasa_incidentes",
    "Case-Fatality_Ratio": "tasa_letalidad",
    "Case_Fatality_Ratio": "tasa_letalidad",
}


def descargar(nombre: str) -> bytes:
    """Descarga un CSV de JHU con cache local (idempotente, con reintentos)."""
    destino = RAW / nombre
    if destino.exists() and destino.stat().st_size > 0:
        return destino.read_bytes()
    for intento in range(3):
        try:
            with urlopen(URL_BASE.format(nombre=nombre), timeout=30) as r:
                datos = r.read()
            if len(datos) < 50:
                raise IOError("respuesta demasiado corta")
            destino.write_bytes(datos)
            return datos
        except Exception:
            if intento == 2:
                raise
            time.sleep(2)
    raise IOError(nombre)


def estandarizar(df: pd.DataFrame) -> pd.DataFrame:
    """Nombres a snake_case en espanol y ultima_actualizacion a AAAA-MM-DD."""
    df = df.rename(columns=MAPA_COLUMNAS)
    s = df["ultima_actualizacion"].astype("string").str.strip()
    fecha = pd.Series(pd.NaT, index=s.index)
    for fmt in (
        "%m/%d/%y %H:%M", "%m/%d/%Y %H:%M", "%m/%d/%y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
    ):
        pend = fecha.isna() & s.notna()
        if pend.any():
            fecha[pend] = pd.to_datetime(s[pend], format=fmt, errors="coerce")
    df["ultima_actualizacion"] = fecha.dt.strftime("%Y-%m-%d")
    return df


def etapa_parcial(cols) -> int:
    """Etapa de esquema segun columnas: 1..4 (ene-jun 2020: 1-3 y 4 desde 29-may)."""
    if {"Incidence_Rate", "Incident_Rate", "Case_Fatality_Ratio"} & set(cols):
        return 4
    if "FIPS" in cols:
        return 3
    if "Latitude" in cols:
        return 2
    return 1


# %% [markdown]
# ## 1) Cargar 01-22-2020.csv: primeras filas, filas/columnas y tipos
# Nota: aqui todavia se ven los nombres originales en ingles de JHU.
# %%
pr1 = pd.read_csv(io.BytesIO(descargar("01-22-2020.csv")))
print("Primeras filas (nombres originales de JHU):")
print(pr1.head())
print(f"\nFilas: {len(pr1)} | Columnas: {len(pr1.columns)}")
print("\nTipos de datos:")
print(pr1.dtypes)

# %% [markdown]
# ## 2) Valores nulos por columna y que significan
# %%
nulos = pr1.isna().sum().to_frame("nulos")
nulos["% del total"] = (100 * nulos["nulos"] / len(pr1)).round(1)
interpretacion = {
    "Province/State": "Fila a nivel pais (sin provincia/estado)",
    "Confirmed": "No informado ese dia (distinto de 0 casos)",
    "Deaths": "No informado / aun sin reporte (distinto de 0)",
    "Recovered": "No informado / aun sin reporte (distinto de 0)",
}
nulos["interpretacion"] = [interpretacion.get(c, "-") for c in nulos.index]
print(nulos)

# %% [markdown]
# ## 3) Estandarizacion: snake_case en espanol + fecha AAAA-MM-DD
# %%
pr1_std = estandarizar(pr1)
print(pr1_std[["provincia_estado", "region_pais", "ultima_actualizacion",
               "confirmados", "fallecidos", "recuperados"]].head())

# %% [markdown]
# ## 4) Unir reportes enero-junio 2020 en un solo DataFrame
# (cambios de esquema: 1-mar lat/long, 22-mar FIPS/Admin2, 29-may tasa_incidentes)
# %%
def rango_fechas(d1: dt.date, d2: dt.date):
    d = d1
    while d <= d2:
        yield d
        d += dt.timedelta(days=1)


partes = []
for d in rango_fechas(dt.date(2020, 1, 22), dt.date(2020, 6, 30)):
    nombre = f"{d:%m-%d-%Y}.csv"
    try:
        crudo = pd.read_csv(io.BytesIO(descargar(nombre)), low_memory=False)
    except FileNotFoundError:
        print("sin archivo (JHU lo omitio):", nombre)
        continue
    df_dia = estandarizar(crudo)
    df_dia["fecha_reporte"] = f"{d:%Y-%m-%d}"
    df_dia["etapa"] = etapa_parcial(set(crudo.columns))
    partes.append(df_dia)

df = pd.concat(partes, ignore_index=True)
for c in ["confirmados", "fallecidos", "recuperados", "activos", "latitud",
          "longitud", "tasa_incidentes", "tasa_letalidad"]:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

print(f"DataFrame unificado: {df.shape}")
print("Columnas:", list(df.columns))
print("Filas por etapa:", df["etapa"].value_counts().sort_index().to_dict())

# Que columna existe desde que fecha (insumo del diccionario del Hito 2)
for c in ["latitud", "longitud", "fips", "admin2", "activos", "clave_combinada",
          "tasa_incidentes", "tasa_letalidad"]:
    print(c, "-> desde", df.loc[df[c].notna(), "fecha_reporte"].min())

# %% [markdown]
# ## 5) Top 10 paises al 30-jun-2020 y evolucion de Chile
# %%
top10 = (
    df.loc[df["fecha_reporte"] == "2020-06-30"]
    .groupby("region_pais", as_index=False)["confirmados"].sum()
    .sort_values("confirmados", ascending=False)
    .head(10)
)
print(top10)

ax = top10.iloc[::-1].plot.barh(x="region_pais", y="confirmados", legend=False)
ax.set_title("Casos acumulados al 30-jun-2020 - Top 10 paises")
ax.set_xlabel("casos confirmados acumulados")
plt.tight_layout()
plt.savefig(FIGS / "top10_2020-06-30.png", dpi=150)
plt.close()
print("Grafico guardado:", FIGS / "top10_2020-06-30.png")

chile = (
    df.loc[df["region_pais"] == "Chile"]
    .groupby("fecha_reporte", as_index=False)[["confirmados", "fallecidos"]].sum()
)
chile["fecha_reporte"] = pd.to_datetime(chile["fecha_reporte"])
plt.figure(figsize=(11, 4))
plt.plot(chile["fecha_reporte"], chile["confirmados"], label="casos acumulados")
plt.plot(chile["fecha_reporte"], chile["fallecidos"] * 10, label="fallecidos x10")
plt.title("Chile ene-jun 2020 (fallecidos escalados x10)")
plt.legend()
plt.tight_layout()
plt.savefig(FIGS / "chile_ene_jun2020.png", dpi=150)
plt.close()
print("Grafico guardado:", FIGS / "chile_ene_jun2020.png")

# Cambio de granularidad de Chile: pais -> regiones el 20-may-2020
fila_chile = df.loc[df["region_pais"] == "Chile"]
dias = (
    fila_chile.assign(con_region=fila_chile["provincia_estado"].notna())
    .groupby("fecha_reporte")["con_region"].sum()
)
print("Chile: primera fecha con regiones:", dias[dias > 0].index.min(),
      "| territorios distintos:", fila_chile["provincia_estado"].nunique())

# %% [markdown]
# ## 6) Perfilado automatico + 3 observaciones
# %%
try:
    from data_profiling import ProfileReport
except ImportError:
    from ydata_profiling import ProfileReport

perfil = ProfileReport(df, title="COVID-19 ene-jun 2020", minimal=True, progress_bar=False)
perfil.to_file(PROFILE / "perfilado_exploracion.html")
print("Reporte de perfilado:", PROFILE / "perfilado_exploracion.html")

llave = ["fecha_reporte", "provincia_estado", "region_pais", "admin2"]
print(f"Filas: {len(df):,} | Columnas: {df.shape[1]}")
print(f"Duplicados (llave completa): {int(df.duplicated(subset=llave).sum()):,}")
print(f"Filas duplicadas exactas: {int(df.duplicated().sum()):,}")
print(f"% celdas nulas: {df.isna().mean().mean() * 100:.2f}%")

# Tres observaciones (con cifras de esta ejecucion):
# 1) Cobertura de columnas no homogenea: latitud/longitud desde 01-mar;
#    fips/admin2/activos/clave_combinada desde 22-mar;
#    tasa_incidentes/tasa_letalidad desde 29-may. No son nulos aleatorios:
#    son columnas que aun no existian.
# 2) Gran parte de los nulos es informativa: en 01-22-2020, 48,7% de fallecidos/
#    recuperados nulos porque aun no se reportaban; provincia_estado nulo = fila
#    pais, admin2 nulo = fuera de EE.UU. Imputarlos seria inventar informacion.
# 3) El grano real es territorio x dia; la llave debe incluir admin2. Sin admin2,
#    291.074 filas parecen duplicadas (condados EE.UU.); con admin2 quedan 3
#    duplicados y 1 fila exacta. Ademas, ultima_actualizacion no es la fecha del
#    reporte (trae horas/zona horaria); el grano temporal es fecha_reporte.

print("\nHito 1 listo: 6 puntos resueltos.")
print("Ver: data/profile/perfilado_exploracion.html, data/figs/*.png")
