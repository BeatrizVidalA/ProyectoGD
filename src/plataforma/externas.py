"""Series JHU y dos fuentes externas, siempre con cardinalidad explícita."""
import json
from pathlib import Path
import pandas as pd
from .ingesta import SERIES
from .territorios import canonizar


def series(entradas, limpio, pais_ids):
    resultados, linaje = [], []
    for nombre in SERIES:
        archivo = entradas.obtener(nombre, "serie")
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
        if "_US" in nombre:
            continue
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
    bm = pd.DataFrame(columns=["pais_id", "anio", "indicador", "valor", "iso3_fuente", "fila_origen", "archivo_origen", "sha256_origen"])
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
