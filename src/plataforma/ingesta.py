"""Entradas inmutables, caché y manifiesto de procedencia."""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

JHU = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/"
EXTERNAS = {
    "owid_vaccinations.csv": "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.csv",
    "worldbank_65plus.json": "https://api.worldbank.org/v2/country/all/indicator/SP.POP.65UP.TO.ZS?date=2020:2022&format=json&per_page=20000",
}
SERIES = [f"time_series_covid19_{m}_{g}.csv" for g, ms in
          [("global", ["confirmed", "deaths", "recovered"]), ("US", ["confirmed", "deaths"])] for m in ms]


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def descargar(url, destino):
    """No reemplaza entradas existentes. HTTP 404 no se interpreta como día omitible."""
    destino = Path(destino)
    if destino.exists():
        if destino.stat().st_size == 0:
            raise ValueError(f"Entrada vacía: {destino}")
        return destino
    for intento in range(3):
        try:
            with urlopen(Request(url, headers={"User-Agent": "SalaCrisis-Academic/1.0"}), timeout=90) as r:
                datos = r.read()
            if not datos or datos.lstrip().startswith((b"<!DOCTYPE", b"<html")):
                raise ValueError(f"Respuesta no válida: {url}")
            destino.parent.mkdir(parents=True, exist_ok=True)
            with destino.open("xb") as f:
                f.write(datos)
            return destino
        except HTTPError as e:
            if e.code == 404 or intento == 2:
                raise
        except (URLError, TimeoutError):
            if intento == 2:
                raise
        time.sleep(2 ** intento)
    raise RuntimeError(url)


class Entradas:
    def __init__(self, proyecto, original, sin_red=False, solo_cache=False):
        self.proyecto = Path(proyecto)
        self.original = None if solo_cache else Path(original)
        self.sin_red = sin_red
        self.manifiesto = []

    def obtener(self, nombre, tipo):
        if tipo == "diario":
            relativo, cache = "csse_covid_19_daily_reports/" + nombre, "daily_reports/" + nombre
        elif tipo == "serie":
            relativo, cache = "csse_covid_19_time_series/" + nombre, "time_series/" + nombre
        elif tipo == "uid":
            relativo, cache = nombre, nombre
        else:
            relativo, cache = None, "external/" + nombre
        url = EXTERNAS[nombre] if relativo is None else JHU + relativo
        candidatos = [(self.proyecto / "data/raw" / cache, "cache")]
        if self.original and relativo:
            candidatos.append((self.original / "csse_covid_19_data" / relativo, "clon_referenciado"))
        for archivo, origen in candidatos:
            if archivo.is_file():
                break
        else:
            if self.sin_red:
                raise FileNotFoundError(f"Falta {nombre}; modo sin red. No se omitirá esta entrada.")
            archivo = descargar(url, candidatos[0][0])
            origen = "descarga"
        if archivo.stat().st_size == 0:
            raise ValueError(f"Entrada vacía: {archivo}")
        # Rutas relativas al proyecto; la ubicación externa es explícita, no una copia oculta.
        import os
        self.manifiesto.append({"archivo": nombre, "tipo": tipo, "ruta": os.path.relpath(archivo, self.proyecto),
                                 "origen": origen, "url": url, "bytes": archivo.stat().st_size,
                                 "sha256": sha256(archivo), "verificado_utc": datetime.now(timezone.utc).isoformat()})
        return archivo

    def guardar(self, destino):
        Path(destino).write_text(json.dumps(self.manifiesto, ensure_ascii=False, indent=2), encoding="utf-8")
