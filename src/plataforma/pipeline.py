"""Orquestación local; cada ejecución conserva su propia versión de salida."""
import importlib.metadata
import json
import os
import platform
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import pandas as pd
from .ingesta import Entradas, sha256
from .normalizacion import escribir_diarios
from .almacen import construir_estrella, cargar_externas, divulgacion, metricas_divulgacion, tabla_df, OLAP
from .externas import series, integrar, detalle_cruces
from .calidad import ejecutar as calidad
from .validacion import validar, benchmark
from .auditoria import balance_filas, detalle_balance


def json_guardar(path, objeto):
    Path(path).write_text(json.dumps(objeto, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def ejecutar(proyecto, args):
    import duckdb
    import pyarrow as pa
    pa.set_cpu_count(2)
    inicio = time.perf_counter()
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:6]
    limpio = proyecto / "data/clean/hito2" / run
    analitico = proyecto / "data/dw/hito2" / run
    reportes = proyecto / "data/quality/hito2" / run
    for p in [limpio, analitico, reportes]:
        p.mkdir(parents=True, exist_ok=False)
    entradas = Entradas(proyecto, args.original or proyecto.parent / "COVID-19", args.sin_red, args.solo_cache)
    print(f"Carga {run}: ingesta y normalización", flush=True)
    inventario, cobertura = escribir_diarios(entradas, limpio)
    inventario.to_csv(reportes / "inventario_diarios.csv", index=False)
    cobertura.to_csv(reportes / "cobertura_columnas.csv", index=False)
    path = entradas.obtener("UID_ISO_FIPS_LookUp_Table.csv", "uid")
    uid = pd.read_csv(path, dtype="string", keep_default_na=False)
    uid["fila_uid"] = range(1, len(uid) + 1)
    if uid.UID.duplicated().any():
        raise ValueError("UID territorial duplicado")
    uid.to_parquet(limpio / "uid_original.parquet", index=False)
    entradas.guardar(reportes / "manifiesto_fuentes.json")
    dbpath = analitico / "covid.duckdb"
    # Configurar desde la apertura: no crear el pool por defecto para reducirlo
    # después con SET, especialmente al construir/cerrar el DW en Windows.
    with duckdb.connect(str(dbpath), config={"threads": 1, "memory_limit": "128MB"}) as con:
        con.execute("SET threads=1")
        con.execute("SET memory_limit='128MB'")
        con.execute("SET preserve_insertion_order=false")
        con.execute("SET temp_directory=" + "'" + (analitico / "temporal").as_posix().replace("'", "''") + "'")
        print("Construyendo dimensión histórica y estrella", flush=True)
        dim = construir_estrella(con, limpio, uid)
        tabla_df(con, "uid_original", uid)
        dim.to_parquet(limpio / "dim_territorio.parquet", index=False)
        paises = dim.loc[dim.nivel.eq("pais")].copy()
        print("Procesando cinco series e integrando OWID/Banco Mundial", flush=True)
        serie, linaje = series(entradas, limpio, paises.set_index("pais").territorio_id.to_dict())
        vac, bm, cruces = integrar(entradas, limpio, paises, not args.sin_banco_mundial)
        for nombre, tabla in [("serie_pais", serie), ("linaje_series", linaje), ("vacunacion", vac), ("indicador_anual", bm), ("cruces", cruces)]:
            tabla.to_parquet(limpio / (nombre + ".parquet"), index=False)
        cargar_externas(con, serie, linaje, vac, bm, cruces)
        entradas.guardar(reportes / "manifiesto_fuentes.json")
        print("Evaluando calidad, divulgación e invariantes", flush=True)
        reglas = calidad(con)
        divulgacion(con)
        puntero = completar(con, proyecto, run, limpio, analitico, reportes, entradas, inicio)
    publicar(proyecto, puntero)


def completar(con, proyecto, run, limpio, analitico, reportes, entradas, inicio, reanudado=False):
    dbpath = analitico / "covid.duckdb"
    reglas = con.execute("SELECT * FROM reglas_calidad").fetchdf()
    checks = validar(con)
    checks.to_csv(reportes / "pruebas_integracion.csv", index=False)
    balance_filas(con).to_csv(reportes / "balance_filas.csv", index=False)
    detalle_balance(con).to_csv(reportes / "balance_detalle.csv", index=False)
    reglas.to_csv(reportes / "reglas_calidad.csv", index=False)
    for tabla in ["calidad_pais", "candidatos_rezago", "brechas_territorio", "cruces_externos"]:
        con.execute(f"SELECT * FROM {tabla}").fetchdf().to_csv(reportes / f"{tabla}.csv", index=False)
    for nombre, consulta in OLAP.items():
        con.execute(consulta).fetchdf().to_csv(reportes / f"olap_{nombre}.csv", index=False)
    inventario = pd.read_csv(reportes / "inventario_diarios.csv")
    print("Benchmark de 10000 filas, con selección desde el inventario", flush=True)
    comparacion = benchmark(limpio, reportes, inventario)
    comparacion["diarios_csv_bytes"] = sum(r["bytes"] for r in entradas.manifiesto if r["tipo"] == "diario")
    comparacion["diarios_parquet_bytes"] = sum(p.stat().st_size for p in limpio.glob("diarios_*.parquet"))
    json_guardar(reportes / "benchmark.json", comparacion)
    counts = {}
    for tabla in ["unificada", "dim_territorio", "dim_fecha", "grupos_observados", "fact_covid", "fact_pais", "fact_serie_pais", "fact_vacunacion", "fact_indicador_anual", "reconciliacion"]:
        counts[tabla] = con.execute(f"SELECT count(*) FROM {tabla}").fetchone()[0]
    resumen_cruces = con.execute("""SELECT 'OWID' fuente,count(*) paises_jhu,
      count(*) FILTER(WHERE EXISTS(SELECT 1 FROM fact_vacunacion v WHERE v.pais_id=q.pais_id)) coinciden
      FROM calidad_pais q UNION ALL SELECT 'Banco Mundial',count(*),
      count(*) FILTER(WHERE EXISTS(SELECT 1 FROM fact_indicador_anual b WHERE b.pais_id=q.pais_id AND b.valor IS NOT NULL)) FROM calidad_pais q""").fetchdf()
    resumen_cruces["tasa"] = resumen_cruces.coinciden / resumen_cruces.paises_jhu
    resumen_cruces.to_csv(reportes / "tasas_cruce.csv", index=False)
    detalle_cruces(con, limpio).to_csv(reportes / "paises_cruce.csv", index=False)
    privacidad = metricas_divulgacion(con)
    json_guardar(reportes / "divulgacion.json", privacidad)
    con.execute("SELECT * FROM grupos_observados WHERE versiones>1").fetchdf().to_csv(reportes / "cuarentena.csv", index=False)
    con.execute("SELECT * FROM dim_territorio WHERE metodo='historico_sin_uid'").fetchdf().to_csv(reportes / "territorios_historicos.csv", index=False)
    con.execute("""SELECT 'confirmados' metrica,count(*) diferencias FROM reconciliacion WHERE diferencia_casos<>0
      UNION ALL SELECT 'fallecidos',count(*) FROM reconciliacion WHERE diferencia_muertes<>0""").fetchdf().to_csv(reportes / "reconciliacion_resumen.csv", index=False)
    con.execute("CHECKPOINT").fetchall()
    print("Verificando que las entradas sigan intactas", flush=True)
    for r in entradas.manifiesto:
        if sha256(proyecto / r["ruta"]) != r["sha256"]:
            raise ValueError(f"Entrada cambió durante la ejecución: {r['archivo']}")
    entradas.guardar(reportes / "manifiesto_fuentes.json")
    versiones = {p: importlib.metadata.version(p) for p in ["pandas", "pyarrow", "duckdb"]}
    resumen = {"run": run, "segundos": time.perf_counter() - inicio, "tablas": counts,
           "pruebas_ok": len(checks), "reglas": reglas.to_dict("records"), "cruces": resumen_cruces.to_dict("records"),
           "benchmark": comparacion, "divulgacion": privacidad, "python": platform.python_version(), "versiones": versiones,
           "reanudado": reanudado, "alcance_tiempo": "fase final" if reanudado else "carga completa",
               "fuentes": len(entradas.manifiesto), "estado": "VALIDADO_LOCAL", "descarga_completa_desde_cero_probada": False}
    json_guardar(reportes / "resumen.json", resumen)
    puntero = {"run": run, "dw": str(dbpath.relative_to(proyecto)).replace(os.sep, "/"),
           "parquet": str(limpio.relative_to(proyecto)).replace(os.sep, "/"),
           "reportes": str(reportes.relative_to(proyecto)).replace(os.sep, "/")}
    return puntero


def publicar(proyecto, puntero):
    # Publicar después de cerrar la conexión, además de aprobar comprobaciones.
    # Un fallo de cierre no debe anunciar una nueva versión seleccionada.
    run = puntero["run"]
    puntero_temporal = proyecto / f"data/hito2_actual_{run}.tmp"
    json_guardar(puntero_temporal, puntero)
    os.replace(puntero_temporal, proyecto / "data/hito2_actual.json")
    print(json.dumps(puntero, ensure_ascii=False, indent=2), flush=True)


def retomar(proyecto, run):
    import re
    import duckdb
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z_[a-f0-9]{6}", run):
        raise ValueError("Identificador de carga inválido")
    inicio = time.perf_counter()
    limpio = proyecto / "data/clean/hito2" / run
    analitico = proyecto / "data/dw/hito2" / run
    reportes = proyecto / "data/quality/hito2" / run
    entradas = Entradas(proyecto, proyecto.parent / "COVID-19", sin_red=True)
    entradas.manifiesto = json.loads((reportes / "manifiesto_fuentes.json").read_text(encoding="utf-8"))
    for r in entradas.manifiesto:
        if sha256(proyecto / r["ruta"]) != r["sha256"]:
            raise ValueError(f"Entrada cambió: {r['archivo']}")
    with duckdb.connect(str(analitico / "covid.duckdb"), config={"memory_limit": "128MB", "threads": 1}) as con:
        con.execute("SET threads=1")
        con.execute("SET memory_limit='128MB'")
        con.execute("SET preserve_insertion_order=false")
        con.execute("SET temp_directory=" + "'" + (analitico / "temporal").as_posix().replace("'", "''") + "'")
        from .almacen import sql_texto
        q = "SELECT count(*),sum(confirmados),sum(fallecidos) FROM "
        esperado = con.execute(q + "unificada").fetchone()
        real = con.execute(q + "read_parquet(" + sql_texto(limpio.as_posix() + "/diarios_*.parquet") + ")").fetchone()
        if real != esperado:
            raise ValueError("Parquet y DW no coinciden; no se publica la carga")
        puntero = completar(con, proyecto, run, limpio, analitico, reportes, entradas, inicio, reanudado=True)
    publicar(proyecto, puntero)
