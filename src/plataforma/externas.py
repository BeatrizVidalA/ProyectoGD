"""Series JHU y dos fuentes externas, siempre con cardinalidad explícita."""
import json
from pathlib import Path
import pandas as pd
from .ingesta import SERIES
from .territorios import canonizar


def serie_us_por_lotes(archivo, destino):
    """Series anchas de 1143 fechas sin millones de strings en Pandas."""
    import csv
    import pyarrow as pa
    import pyarrow.csv as pc
    import pyarrow.parquet as pq
    with open(archivo, encoding="utf-8-sig", newline="") as f:
        columnas = next(csv.reader(f))
    fechas = [c for c in columnas if "/" in c and c[0].isdigit()]
    if len(fechas) != 1143 or fechas[0] != "1/22/20" or fechas[-1] != "3/9/23":
        raise ValueError(f"Cobertura inesperada: {archivo}")
    codigos = [c for c in ["UID", "iso2", "iso3", "code3", "FIPS", "Admin2", "Province_State", "Country_Region", "Combined_Key"] if c in columnas]
    tipos = {c: pa.string() for c in codigos}
    tipos.update({c: pa.int64() for c in fechas})
    nombres = {c: "fecha_" + pd.to_datetime(c, format="%m/%d/%y").strftime("%Y_%m_%d") for c in fechas}
    nombres.update({"UID": "uid", "FIPS": "fips", "Admin2": "admin2", "Province_State": "provincia_estado",
                    "Country_Region": "region_pais", "Lat": "latitud", "Long_": "longitud",
                    "Combined_Key": "clave_combinada", "Population": "poblacion"})
    lector = pc.open_csv(archivo, convert_options=pc.ConvertOptions(column_types=tipos, null_values=[""], strings_can_be_null=True))
    schema = pa.schema([pa.field(nombres.get(f.name, f.name), f.type) for f in lector.schema])
    filas = 0
    with pq.ParquetWriter(destino, schema, compression="zstd") as escritor:
        for batch in lector:
            filas += batch.num_rows
            escritor.write_batch(pa.RecordBatch.from_arrays(batch.columns, schema=schema))
    if filas != 3342:
        raise ValueError(f"Cantidad inesperada de condados de serie US: {filas}")


def series(entradas, limpio, pais_ids):
    resultados, linaje = [], []
    for nombre in SERIES:
        archivo = entradas.obtener(nombre, "serie")
        if "_US" in nombre:
            serie_us_por_lotes(archivo, limpio / nombre.replace(".csv", ".parquet"))
            continue
        d = pd.read_csv(archivo, dtype="string", keep_default_na=False).replace("", pd.NA)
        fechas = [c for c in d if "/" in c and c[0].isdigit()]
        if len(fechas) != 1143 or fechas[0] != "1/22/20" or fechas[-1] != "3/9/23":
            raise ValueError(f"Cobertura temporal inesperada: {nombre}")
        renombrar = {c: "fecha_" + pd.to_datetime(c, format="%m/%d/%y").strftime("%Y_%m_%d") for c in fechas}
        renombrar.update({"Province/State": "provincia_estado", "Country/Region": "region_pais", "Lat": "latitud", "Long": "longitud",
                         "UID": "uid", "iso2": "iso2", "iso3": "iso3", "code3": "code3", "FIPS": "fips", "Admin2": "admin2",
                         "Province_State": "provincia_estado", "Country_Region": "region_pais", "Long_": "longitud", "Combined_Key": "clave_combinada", "Population": "poblacion"})
        # Series anchas auxiliares preservadas en Parquet, incluidos los condados de EE.UU.
        d.rename(columns=renombrar).to_parquet(limpio / nombre.replace(".csv", ".parquet"), index=False)
        metrica = "confirmados" if "confirmed" in nombre else "fallecidos" if "deaths" in nombre else "recuperados"
        ids = d["Country/Region"].map(lambda x: pais_ids.get(canonizar(x, "", "")[0]))
        if ids.isna().any():
            raise ValueError(f"País de serie sin dimensión: {d.loc[ids.isna(), 'Country/Region'].unique()}")
        valores = d[fechas].apply(pd.to_numeric, errors="raise")
        valores["pais_id"] = ids
        agrupado = valores.groupby("pais_id").sum(min_count=1).reset_index()
        largo = agrupado.melt(id_vars="pais_id", var_name="fecha", value_name=metrica)
        largo["fecha"] = pd.to_datetime(largo.fecha, format="%m/%d/%y").dt.date
        resultados.append(largo.set_index(["pais_id", "fecha"]))
        linaje.extend({"pais_id": pid, "metrica": metrica, "archivo_origen": nombre, "fila_origen": i + 1,
                       "sha256_origen": entradas.manifiesto[-1]["sha256"]} for i, pid in enumerate(ids))
    nacional = pd.concat(resultados, axis=1).reset_index()
    assert not nacional.duplicated(["pais_id", "fecha"]).any()
    return nacional, pd.DataFrame(linaje)


def integrar(entradas, limpio, dim_paises, incluir_bm=True):
    validos = dim_paises.dropna(subset=["iso3"])
    if validos.iso3.duplicated().any():
        raise ValueError("ISO3 no único en la dimensión país")
    por_iso = validos.set_index("iso3").territorio_id.to_dict()
    path = entradas.obtener("owid_vaccinations.csv", "externa")
    d = pd.read_csv(path, dtype={"iso_code": "string"})
    necesarias = ["location", "iso_code", "date", "people_vaccinated", "people_fully_vaccinated", "people_vaccinated_per_hundred", "people_fully_vaccinated_per_hundred"]
    if not set(necesarias) <= set(d):
        raise ValueError("OWID sin columnas obligatorias")
    d["fila_origen"] = range(1, len(d) + 1)
    d = d[necesarias + ["fila_origen"]].copy()
    d["fecha"] = pd.to_datetime(d.pop("date"), format="%Y-%m-%d", errors="raise").dt.date
    d["iso3_fuente"] = d.pop("iso_code")
    # Kosovo: códigos estadísticos diferentes; equivalencia explícita, no ISO oficial.
    d["iso3"] = d.iso3_fuente.replace({"OWID_KOS": "XKS"})
    if d.duplicated(["iso3", "fecha"]).any():
        raise ValueError("OWID repite código y fecha")
    for c in necesarias[3:]:
        d[c] = pd.to_numeric(d[c], errors="raise")
    d["pais_id"] = d.iso3.map(por_iso)
    d["archivo_origen"] = path.name
    d["sha256_origen"] = entradas.manifiesto[-1]["sha256"]
    d.to_parquet(limpio / "owid_vacunacion_todas.parquet", index=False)
    dentro = d.fecha.between(pd.Timestamp("2020-01-22").date(), pd.Timestamp("2023-03-09").date())
    vac = d.loc[dentro & d.pais_id.notna()].copy()
    assert not vac.duplicated(["pais_id", "fecha"]).any()
    cobertura = [{"fuente": "OWID", "codigo_fuente": r.iso3_fuente, "iso3": r.iso3,
                  "coincide": pd.notna(r.pais_id), "motivo": "coincide" if pd.notna(r.pais_id) else "agregado/no país JHU o sin correspondencia"}
                 for r in d[["iso3_fuente", "iso3", "pais_id"]].drop_duplicates().itertuples()]
    bm = pd.DataFrame({c: pd.Series(dtype=t) for c, t in {
        "pais_id": "string", "anio": "Int64", "indicador": "string", "valor": "float64",
        "iso3_fuente": "string", "fila_origen": "Int64", "archivo_origen": "string", "sha256_origen": "string"}.items()})
    if incluir_bm:
        path = entradas.obtener("worldbank_65plus.json", "externa")
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, list) or len(payload) != 2 or int(payload[0]["pages"]) != 1:
            raise ValueError("Respuesta Banco Mundial incompleta o paginada")
        registros = []
        for i, r in enumerate(payload[1], 1):
            iso = r["countryiso3code"]
            canon = "XKS" if iso == "XKX" else iso
            registros.append({"pais_id": por_iso.get(canon), "iso3_fuente": iso, "iso3": canon,
                "anio": int(r["date"]), "indicador": r["indicator"]["id"], "valor": r["value"],
                "fila_origen": i, "archivo_origen": path.name, "sha256_origen": entradas.manifiesto[-1]["sha256"]})
        todos = pd.DataFrame(registros)
        todos.to_parquet(limpio / "banco_mundial_todos.parquet", index=False)
        cobertura += [{"fuente": "Banco Mundial", "codigo_fuente": r.iso3_fuente, "iso3": r.iso3,
                       "coincide": pd.notna(r.pais_id), "motivo": "coincide" if pd.notna(r.pais_id) else "agregado o sin correspondencia JHU"}
                      for r in todos[["iso3_fuente", "iso3", "pais_id"]].drop_duplicates().itertuples()]
        bm = todos.loc[todos.pais_id.notna()].copy()
        if bm.duplicated(["pais_id", "anio", "indicador"]).any():
            raise ValueError("Banco Mundial no es único por país/año/indicador")
    return vac, bm, pd.DataFrame(cobertura)


def detalle_cruces(con, limpio):
    """Distingue ausencia de código, de fechas y de valores del indicador."""
    d = con.execute("""SELECT q.pais_id,q.pais,q.iso3,coalesce(v.filas,0) filas_owid,
      coalesce(v.con_porcentaje,0) fechas_owid_con_porcentaje,coalesce(b.con_valor,0) anios_bm_con_valor
      FROM calidad_pais q LEFT JOIN (SELECT pais_id,count(*) filas,
      count(people_vaccinated_per_hundred) con_porcentaje FROM fact_vacunacion GROUP BY pais_id) v USING(pais_id)
      LEFT JOIN (SELECT pais_id,count(valor) con_valor FROM fact_indicador_anual GROUP BY pais_id) b USING(pais_id)
      ORDER BY q.pais""").fetchdf()
    owid = set(pd.read_parquet(limpio / "owid_vacunacion_todas.parquet", columns=["pais_id"]).pais_id.dropna())
    archivo_bm = limpio / "banco_mundial_todos.parquet"
    bm = set(pd.read_parquet(archivo_bm, columns=["pais_id"]).pais_id.dropna()) if archivo_bm.exists() else set()
    d["owid"] = d.filas_owid.gt(0)
    d["banco_mundial"] = d.anios_bm_con_valor.gt(0)
    d["motivo_owid"] = ["cruce por país/fecha" if r.filas_owid else
        "entidad sin ISO3 JHU" if pd.isna(r.iso3) else
        "código no presente en la fuente" if r.pais_id not in owid else
        "sin fechas en la ventana JHU" for r in d.itertuples()]
    d["motivo_banco_mundial"] = ["cruce país/año con valor" if r.anios_bm_con_valor else
        "fuente no solicitada" if not archivo_bm.exists() else
        "entidad sin ISO3 JHU" if pd.isna(r.iso3) else
        "código no presente en la fuente" if r.pais_id not in bm else
        "sin valores 2020–2022 para el indicador" for r in d.itertuples()]
    return d
