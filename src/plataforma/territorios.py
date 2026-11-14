"""Correspondencias explícitas; nunca emparejamiento difuso automático."""
import hashlib
import json
import pandas as pd

ALIAS = {
    "Mainland China": "China", "Republic of Korea": "Korea, South", "South Korea": "Korea, South",
    "Iran (Islamic Republic of)": "Iran", "Republic of Ireland": "Ireland", "Russian Federation": "Russia",
    "Viet Nam": "Vietnam", "Taiwan": "Taiwan*", "Taipei and environs": "Taiwan*",
    "Czech Republic": "Czechia", "Cape Verde": "Cabo Verde", "East Timor": "Timor-Leste",
    "Ivory Coast": "Cote d'Ivoire", "Republic of Moldova": "Moldova", "Republic of the Congo": "Congo (Brazzaville)",
    "Bahamas, The": "Bahamas", "The Bahamas": "Bahamas", "Gambia, The": "Gambia", "The Gambia": "Gambia",
    "Palestine": "West Bank and Gaza", "occupied Palestinian territory": "West Bank and Gaza", "Vatican City": "Holy See",
    "UK": "United Kingdom", "US": "US",
}
DEPENDENCIAS = {
    "Aruba": ("Netherlands", "Aruba"), "Curacao": ("Netherlands", "Curacao"),
    "Cayman Islands": ("United Kingdom", "Cayman Islands"), "Channel Islands": ("United Kingdom", "Channel Islands"),
    "Faroe Islands": ("Denmark", "Faroe Islands"), "Greenland": ("Denmark", "Greenland"),
    "French Guiana": ("France", "French Guiana"), "Guadeloupe": ("France", "Guadeloupe"),
    "Martinique": ("France", "Martinique"), "Mayotte": ("France", "Mayotte"), "Reunion": ("France", "Reunion"),
    "Saint Barthelemy": ("France", "Saint Barthelemy"), "Saint Martin": ("France", "St Martin"), "St. Martin": ("France", "St Martin"),
    "Gibraltar": ("United Kingdom", "Gibraltar"), "Guernsey": ("United Kingdom", "Guernsey"),
    "Jersey": ("United Kingdom", "Jersey"), "North Ireland": ("United Kingdom", "Northern Ireland"),
    "Hong Kong": ("China", "Hong Kong"), "Hong Kong SAR": ("China", "Hong Kong"),
    "Macau": ("China", "Macau"), "Macao SAR": ("China", "Macau"),
    "Puerto Rico": ("US", "Puerto Rico"), "Guam": ("US", "Guam"),
}


def texto(x):
    return str(x).strip() if pd.notna(x) else ""


def clave(valores):
    return "H:" + hashlib.sha256(json.dumps(list(valores), ensure_ascii=False).encode()).hexdigest()[:24]


def canonizar(pais, provincia, admin2):
    pais, provincia, admin2 = map(texto, (pais, provincia, admin2))
    if provincia == "None":
        provincia = ""  # Marcador histórico, preservado en la tabla unificada.
    if pais in DEPENDENCIAS:
        pais, provincia = DEPENDENCIAS[pais]
    pais = ALIAS.get(pais, pais)
    if pais in {"Others", "Cruise Ship"} and "Diamond Princess" in provincia:
        pais, provincia = "Diamond Princess", ""
    return pais, provincia, admin2


def construir(uid, firmas):
    exactos, nacionales, fips = {}, {}, {}
    for r in uid.to_dict("records"):
        key = tuple(texto(r[c]) for c in ["Country_Region", "Province_State", "Admin2"])
        exactos[key] = r
        if not key[1] and not key[2]:
            nacionales[key[0]] = r
        if texto(r["FIPS"]):
            fips.setdefault(texto(r["FIPS"]).removesuffix(".0").zfill(5), []).append(r)
    dimensiones = {}

    def dimension(r):
        tid = "U:" + str(r["UID"])
        if tid in dimensiones:
            return tid
        pais, provincia, admin = [texto(r[c]) for c in ["Country_Region", "Province_State", "Admin2"]]
        n = nacionales[pais]
        pid = "U:" + str(n["UID"])
        parent = exactos.get((pais, provincia, "")) if admin else n if provincia else None
        iso = texto(r["iso3"])
        dimensiones[tid] = {"territorio_id": tid, "pais_id": pid, "padre_id": "U:" + str(parent["UID"]) if parent else None,
            "uid": str(r["UID"]), "pais": pais, "provincia": provincia or None, "admin2": admin or None,
            "nivel": "condado" if admin else "region" if provincia else "pais", "iso3": iso or None,
            "pais_iso3": texto(n["iso3"]) or None, "iso3_oficial_formato": bool(iso and iso != "XKS"),
            "poblacion": pd.to_numeric(r["Population"], errors="coerce"),
            "latitud": pd.to_numeric(r["Lat"], errors="coerce"), "longitud": pd.to_numeric(r["Long_"], errors="coerce"),
            "es_dependencia": bool(provincia and iso and iso != texto(n["iso3"])), "metodo": "uid",
            "fila_uid": int(r["fila_uid"])}
        return tid

    for r in uid.to_dict("records"):
        dimension(r)
    mapeos = []
    for r in firmas.to_dict("records"):
        pais, provincia, admin = canonizar(r["region_pais"], r["provincia_estado"], r["admin2"])
        encontrado = exactos.get((pais, provincia, admin))
        metodo = "uid_exacto_o_alias_explicito"
        f = texto(r["fips"]).removesuffix(".0").zfill(5)
        if encontrado is None and pais == "US" and admin and len(fips.get(f, [])) == 1:
            candidato = fips[f][0]
            # No fusionar nombres diferentes: un FIPS puede cambiar su cobertura histórica.
            if texto(candidato["Admin2"]) == admin and texto(candidato["Province_State"]) == provincia:
                encontrado, metodo = candidato, "uid_fips_confirmado"
        if encontrado:
            tid = dimension(encontrado)
        else:
            pid = "U:" + str(nacionales[pais]["UID"]) if pais in nacionales else clave([pais, "pais"])
            if pid not in dimensiones:
                dimensiones[pid] = {"territorio_id": pid, "pais_id": pid, "pais": pais, "nivel": "pais",
                                      "metodo": "historico_sin_uid", "es_dependencia": False, "iso3_oficial_formato": False}
            tid = clave([pais, provincia, admin]) if provincia or admin else pid
            if tid not in dimensiones:
                dimensiones[tid] = {"territorio_id": tid, "pais_id": pid, "padre_id": pid, "pais": pais,
                    "provincia": provincia or None, "admin2": admin or None, "nivel": "historico",
                    "pais_iso3": dimensiones[pid].get("iso3"), "iso3": dimensiones[pid].get("iso3"),
                    "metodo": "historico_sin_uid", "es_dependencia": False,
                    "iso3_oficial_formato": dimensiones[pid].get("iso3_oficial_formato", False)}
            metodo = "historico_sin_uid"
        mapeos.append({**r, "territorio_id": tid, "metodo_match": metodo})
    dim = pd.DataFrame(dimensiones.values())
    # Columnas incluso cuando todos los valores son NA.
    for c in ["uid", "padre_id", "provincia", "admin2", "iso3", "pais_iso3", "poblacion", "latitud", "longitud", "fila_uid"]:
        if c not in dim:
            dim[c] = None
    return dim, pd.DataFrame(mapeos)
