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
from .almacen import construir_estrella, cargar_externas, divulgacion, tabla_df, OLAP
from .externas import series, integrar
from .calidad import ejecutar as calidad
from .validacion import validar, benchmark


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
    dbpath = analitico / "covid.duckdb"
    with duckdb.connect(str(dbpath)) as con:
        con.execute("SET threads=2")
        con.execute("SET memory_limit='768MB'")
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
        print("Evaluando calidad, divulgación e invariantes", flush=True)
        reglas = calidad(con)
        divulgacion(con)
        checks = validar(con)
        checks.to_csv(reportes / "pruebas_integracion.csv", index=False)
        reglas.to_csv(reportes / "reglas_calidad.csv", index=False)
        for tabla in ["calidad_pais", "candidatos_rezago", "brechas_territorio", "cruces_externos"]:
            con.execute(f"SELECT * FROM {tabla}").fetchdf().to_csv(reportes / f"{tabla}.csv", index=False)
        for nombre, consulta in OLAP.items():
            con.execute(consulta).fetchdf().to_csv(reportes / f"olap_{nombre}.csv", index=False)
        comparacion = benchmark(con, reportes)
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
        con.execute("""SELECT q.pais,q.iso3,
          EXISTS(SELECT 1 FROM fact_vacunacion v WHERE v.pais_id=q.pais_id) owid,
          EXISTS(SELECT 1 FROM fact_indicador_anual b WHERE b.pais_id=q.pais_id AND b.valor IS NOT NULL) banco_mundial
          FROM calidad_pais q ORDER BY q.pais""").fetchdf().to_csv(reportes / "paises_cruce.csv", index=False)
        privacidad = con.execute("""SELECT count(*) filas_evaluadas,count(*) FILTER(WHERE suprimir) filas_supresion_primaria,
          sum((confirmados BETWEEN 1 AND 4)::INT+(fallecidos BETWEEN 1 AND 4)::INT+
          coalesce((casos_nuevos BETWEEN 1 AND 4)::INT,0)+coalesce((fallecidos_nuevos BETWEEN 1 AND 4)::INT,0)) celdas_1a4
          FROM v_control_divulgacion""").fetchdf().to_dict("records")[0]
        privacidad["filas_cierre_conservador"] = con.execute("SELECT count(*) FROM v_publica_segura WHERE suprimir").fetchone()[0]
        privacidad["condados_uid_menores_5000"] = con.execute("SELECT count(*) FROM dim_territorio WHERE pais='US' AND nivel='condado' AND poblacion<5000").fetchone()[0]
        privacidad["celdas_no_nulas_ocultas"] = con.execute("""SELECT sum((f.confirmados IS NOT NULL)::INT+(f.fallecidos IS NOT NULL)::INT+(f.casos_nuevos IS NOT NULL)::INT+(f.fallecidos_nuevos IS NOT NULL)::INT)
          FROM fact_covid f JOIN v_publica_segura v USING(territorio_id,fecha) WHERE v.suprimir""").fetchone()[0]
        json_guardar(reportes / "divulgacion.json", privacidad)
        con.execute("SELECT * FROM grupos_observados WHERE versiones>1").fetchdf().to_csv(reportes / "cuarentena.csv", index=False)
        con.execute("SELECT * FROM dim_territorio WHERE metodo='historico_sin_uid'").fetchdf().to_csv(reportes / "territorios_historicos.csv", index=False)
        con.execute("""SELECT 'confirmados' metrica,count(*) diferencias FROM reconciliacion WHERE diferencia_casos<>0
          UNION ALL SELECT 'fallecidos',count(*) FROM reconciliacion WHERE diferencia_muertes<>0""").fetchdf().to_csv(reportes / "reconciliacion_resumen.csv", index=False)
        con.execute("CHECKPOINT")
    print("Verificando que las entradas sigan intactas", flush=True)
    for r in entradas.manifiesto:
        assert sha256(proyecto / r["ruta"]) == r["sha256"], f"Entrada cambió durante la ejecución: {r['archivo']}"
    entradas.guardar(reportes / "manifiesto_fuentes.json")
    versiones = {p: importlib.metadata.version(p) for p in ["pandas", "pyarrow", "duckdb"]}
    resumen = {"run": run, "segundos": time.perf_counter() - inicio, "tablas": counts,
               "pruebas_ok": len(checks), "reglas": reglas.to_dict("records"), "cruces": resumen_cruces.to_dict("records"),
               "benchmark": comparacion, "divulgacion": privacidad, "python": platform.python_version(), "versiones": versiones,
               "fuentes": len(entradas.manifiesto), "estado": "VALIDADO_LOCAL", "descarga_completa_desde_cero_probada": False}
    json_guardar(reportes / "resumen.json", resumen)
    puntero = {"run": run, "dw": str(dbpath.relative_to(proyecto)).replace(os.sep, "/"),
               "parquet": str(limpio.relative_to(proyecto)).replace(os.sep, "/"),
               "reportes": str(reportes.relative_to(proyecto)).replace(os.sep, "/")}
    # Solo se actualiza tras todas las comprobaciones. Los intentos anteriores se conservan.
    json_guardar(proyecto / "data/hito2_actual.json", puntero)
    print(json.dumps({**puntero, "filas": counts["unificada"], "pruebas_ok": len(checks)}, ensure_ascii=False, indent=2), flush=True)
