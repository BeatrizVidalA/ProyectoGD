"""Prueba HTTP optativa: cinco esquemas y UID sin usar el clon como entrada.

No se ejecuta en unittest; requiere red. Guarda evidencia en data/quality.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from plataforma.ingesta import Entradas
from plataforma.normalizacion import normalizar


def main():
    carpeta = ROOT / "data/quality" / ("descarga_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    carpeta.mkdir(parents=True, exist_ok=False)
    entradas = Entradas(carpeta, ROOT / "sin_clon", solo_cache=True)
    evidencia = []
    original = ROOT.parent / "COVID-19/csse_covid_19_data"
    for etapa, nombre in enumerate(["01-22-2020.csv", "03-01-2020.csv", "03-22-2020.csv", "05-29-2020.csv", "11-09-2020.csv"], 1):
        p = entradas.obtener(nombre, "diario")
        df, _ = normalizar(p, entradas.manifiesto[-1]["sha256"])
        if int(df.etapa.iloc[0]) != etapa:
            raise AssertionError(nombre)
        local = original / "csse_covid_19_daily_reports" / nombre
        if local.exists():
            pd.testing.assert_frame_equal(pd.read_csv(p, dtype="string", keep_default_na=False),
                                          pd.read_csv(local, dtype="string", keep_default_na=False))
        evidencia.append({"archivo": nombre, "etapa": etapa, "filas": len(df), "origen": "HTTP_sin_clon"})
    p = entradas.obtener("UID_ISO_FIPS_LookUp_Table.csv", "uid")
    uid = pd.read_csv(p, dtype="string", keep_default_na=False)
    if len(uid) != 4321 or uid.UID.duplicated().any():
        raise AssertionError("UID inesperada")
    evidencia.append({"archivo": p.name, "filas": len(uid), "origen": "HTTP_sin_clon"})
    entradas.guardar(carpeta / "manifiesto.json")
    (carpeta / "resultados.json").write_text(json.dumps(evidencia, indent=2), encoding="utf-8")
    print(json.dumps({"pruebas": evidencia, "evidencia": str(carpeta)}, indent=2))


if __name__ == "__main__":
    main()
