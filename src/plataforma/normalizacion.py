"""Cinco esquemas sin imputación ni eliminación de registros."""
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import pandas as pd

MAPA = {
    "Province/State": "provincia_estado", "Province_State": "provincia_estado",
    "Country/Region": "region_pais", "Country_Region": "region_pais",
    "Last Update": "ultima_actualizacion", "Last_Update": "ultima_actualizacion",
    "Latitude": "latitud", "Lat": "latitud", "Longitude": "longitud", "Long_": "longitud",
    "FIPS": "fips", "Admin2": "admin2", "Confirmed": "confirmados", "Deaths": "fallecidos",
    "Recovered": "recuperados", "Active": "activos", "Combined_Key": "clave_combinada",
    "Incidence_Rate": "tasa_incidentes", "Incident_Rate": "tasa_incidentes",
    "Case-Fatality_Ratio": "tasa_letalidad", "Case_Fatality_Ratio": "tasa_letalidad",
}
E1 = {"Province/State", "Country/Region", "Last Update", "Confirmed", "Deaths", "Recovered"}
E3 = {"FIPS", "Admin2", "Province_State", "Country_Region", "Last_Update", "Lat", "Long_", "Confirmed", "Deaths", "Recovered", "Active", "Combined_Key"}
ESQUEMAS = {1: E1, 2: E1 | {"Latitude", "Longitude"}, 3: E3,
            4: E3 | {"Incidence_Rate", "Case-Fatality_Ratio"}, 5: E3 | {"Incident_Rate", "Case_Fatality_Ratio"}}
NUMERICAS = ["confirmados", "fallecidos", "recuperados", "activos", "latitud", "longitud", "tasa_incidentes", "tasa_letalidad"]
TEXTOS = ["provincia_estado", "region_pais", "ultima_actualizacion", "fips", "admin2", "clave_combinada",
          "ultima_actualizacion_original", "actualizacion_hora", "archivo_origen", "sha256_origen"]
FORMATOS = ["%m/%d/%y %H:%M", "%m/%d/%Y %H:%M", "%m/%d/%y %H:%M:%S", "%m/%d/%Y %H:%M:%S",
            "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"]


def clasificar(columnas):
    for etapa, esperadas in ESQUEMAS.items():
        if set(columnas) == esperadas:
            return etapa
    raise ValueError(f"Cabecera no reconocida: {list(columnas)}")


def normalizar(path, huella):
    crudo = pd.read_csv(path, dtype="string", keep_default_na=False).replace("", pd.NA)
    etapa = clasificar(crudo.columns)
    if crudo.empty:
        raise ValueError(f"Archivo vacío: {path}")
    df = crudo.rename(columns=MAPA).copy()
    presentes = set(df.columns)
    df["ultima_actualizacion_original"] = df.ultima_actualizacion.copy()
    # Parsear valores distintos evita repetir el mismo trabajo miles de veces por archivo.
    interpretadas = {}
    for valor in df.ultima_actualizacion.dropna().unique():
        for formato in FORMATOS:
            try:
                interpretadas[valor] = datetime.strptime(valor.strip(), formato)
                break
            except ValueError:
                pass
        else:
            raise ValueError(f"Fecha inválida en {path}: {valor!r}")
    df["actualizacion_hora"] = df.ultima_actualizacion.map(lambda x: interpretadas[x].isoformat() if pd.notna(x) else None)
    df["ultima_actualizacion"] = df.ultima_actualizacion.map(lambda x: interpretadas[x].date().isoformat() if pd.notna(x) else None)
    cobertura = []
    for campo in sorted(set(MAPA.values())):
        cobertura.append({"campo": campo, "etapa": etapa, "filas": len(df),
                          "estructurales": len(df) if campo not in presentes else 0,
                          "vacios_origen": int(df[campo].isna().sum()) if campo in presentes else 0})
    for campo in NUMERICAS:
        if campo not in df:
            df[campo] = float("nan")
        else:
            # Cualquier texto inválido detiene la carga con contexto, no se vuelve NA silenciosamente.
            try:
                df[campo] = pd.to_numeric(df[campo], errors="raise").astype("float64")
            except (ValueError, TypeError) as e:
                raise ValueError(f"Número inválido {path}/{campo}") from e
    for campo in TEXTOS:
        if campo not in df:
            df[campo] = None
        df[campo] = df[campo].astype("string")
    df["fecha_reporte"] = datetime.strptime(Path(path).name, "%m-%d-%Y.csv").date()
    df["etapa"] = etapa
    df["archivo_origen"] = Path(path).name
    df["fila_origen"] = range(1, len(df) + 1)
    df["sha256_origen"] = huella
    return df, cobertura


def escribir_diarios(entradas, destino, progreso=print):
    import pyarrow as pa
    import pyarrow.parquet as pq
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    schema = pa.schema([(c, pa.string()) for c in TEXTOS] + [(c, pa.float64()) for c in NUMERICAS]
                       + [("fecha_reporte", pa.date32()), ("etapa", pa.int16()), ("fila_origen", pa.int32())])
    resumen, cobertura = [], []
    escritor, anio = None, None
    try:
        for i, fecha in enumerate(pd.date_range("2020-01-22", "2023-03-09")):
            nombre = fecha.strftime("%m-%d-%Y.csv")
            archivo = entradas.obtener(nombre, "diario")
            df, cov = normalizar(archivo, entradas.manifiesto[-1]["sha256"])
            if fecha.year != anio:
                if escritor:
                    escritor.close()
                anio = fecha.year
                escritor = pq.ParquetWriter(destino / f"diarios_{anio}.parquet", schema, compression="zstd")
            escritor.write_table(pa.Table.from_pandas(df[schema.names], schema=schema, preserve_index=False))
            resumen.append({"archivo": nombre, "fecha": fecha.date().isoformat(), "etapa": int(df.etapa.iloc[0]), "filas": len(df)})
            cobertura.extend(cov)
            if (i + 1) % 100 == 0:
                progreso(f"  reportes procesados: {i + 1}/1143", flush=True)
    finally:
        if escritor:
            escritor.close()
    return pd.DataFrame(resumen), pd.DataFrame(cobertura).groupby(["campo", "etapa"], as_index=False).sum()
