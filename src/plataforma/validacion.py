"""Invariantes obligatorias; fallan antes de publicar el puntero de una carga."""
import statistics
import time
import pandas as pd


def validar(con):
    checks = []

    def comprobar(nombre, sql, esperado=0):
        obtenido = con.execute(sql).fetchone()[0]
        if obtenido != esperado:
            raise AssertionError(f"{nombre}: {obtenido!r} != {esperado!r}")
        checks.append({"prueba": nombre, "resultado": obtenido, "esperado": esperado, "estado": "OK"})

    comprobar("1143 reportes", "SELECT count(DISTINCT archivo_origen) FROM unificada", 1143)
    comprobar("filas conservadas", "SELECT count(*) FROM unificada", 4287473)
    comprobar("cinco esquemas", "SELECT count(DISTINCT etapa) FROM unificada", 5)
    for etapa, filas in {1: 4242, 2: 5555, 3: 217486, 4: 643463, 5: 3416727}.items():
        comprobar(f"filas esquema {etapa}", f"SELECT count(*) FROM unificada WHERE etapa={etapa}", filas)
    comprobar("un mapeo por observación", "SELECT (SELECT count(*) FROM unificada)-(SELECT count(*) FROM observacion_mapa)")
    comprobar("grupos conservan linaje", "SELECT (SELECT count(*) FROM unificada)-(SELECT sum(n_fuentes) FROM grupos_observados)")
    comprobar("cuarentena explícita", "SELECT (SELECT count(*) FROM grupos_observados WHERE versiones=1)-(SELECT count(*) FROM fact_covid)")
    for tabla, claves in {"observacion_mapa": "observacion_id", "fact_covid": "territorio_id,fecha",
                          "fact_pais": "pais_id,fecha", "fact_serie_pais": "pais_id,fecha",
                          "fact_vacunacion": "pais_id,fecha", "fact_indicador_anual": "pais_id,anio,indicador"}.items():
        comprobar(f"clave única {tabla}", f"SELECT count(*) FROM (SELECT {claves} FROM {tabla} GROUP BY {claves} HAVING count(*)>1)")
    comprobar("FK territorio", "SELECT count(*) FROM fact_covid f ANTI JOIN dim_territorio d USING(territorio_id)")
    comprobar("FK fecha", "SELECT count(*) FROM fact_covid f ANTI JOIN dim_fecha d USING(fecha)")
    comprobar("primer acumulado no es diario", "SELECT count(*) FROM fact_covid WHERE fecha_anterior IS NULL AND (casos_nuevos IS NOT NULL OR fallecidos_nuevos IS NOT NULL)")
    comprobar("diarios coherentes", """SELECT count(*) FROM fact_covid WHERE dias_desde_anterior=1 AND
      (casos_nuevos IS DISTINCT FROM confirmados-confirmados_anteriores OR fallecidos_nuevos IS DISTINCT FROM fallecidos-fallecidos_anteriores)""")
    comprobar("brechas no son un solo día", "SELECT count(*) FROM fact_covid WHERE dias_desde_anterior>1 AND (casos_nuevos IS NOT NULL OR fallecidos_nuevos IS NOT NULL)")
    comprobar("join OWID no multiplica", "SELECT (SELECT count(*) FROM v_pais_vacunacion)-(SELECT count(*) FROM fact_pais)")
    comprobar("join BM no multiplica", "SELECT (SELECT count(*) FROM v_pais_indicador)-(SELECT count(*) FROM fact_pais)")
    comprobar("Chile 30jun casos", "SELECT confirmados FROM fact_pais WHERE pais_id='U:152' AND fecha=DATE '2020-06-30'", 279393)
    comprobar("Chile 30jun muertes", "SELECT fallecidos FROM fact_pais WHERE pais_id='U:152' AND fecha=DATE '2020-06-30'", 5688)
    comprobar("Chile último día casos", "SELECT confirmados FROM fact_pais WHERE pais_id='U:152' AND fecha=DATE '2023-03-09'", 5192286)
    comprobar("Chile último día muertes", "SELECT fallecidos FROM fact_pais WHERE pais_id='U:152' AND fecha=DATE '2023-03-09'", 64273)
    comprobar("Chile regiones solo desde 20may", "SELECT count(*) FROM fact_covid f JOIN dim_territorio d USING(territorio_id) WHERE d.pais='Chile' AND d.nivel='region' AND fecha<DATE '2020-05-20'")
    comprobar("primeros diarios regionales nulos", "SELECT count(*) FROM fact_covid f JOIN dim_territorio d USING(territorio_id) WHERE d.pais='Chile' AND d.nivel='region' AND fecha=DATE '2020-05-20' AND casos_nuevos IS NOT NULL")
    comprobar("Chile 17 territorios por fecha regional", "SELECT count(*) FROM (SELECT fecha,count(*) n FROM fact_covid f JOIN dim_territorio d USING(territorio_id) WHERE d.pais='Chile' AND fecha>=DATE '2020-05-20' GROUP BY fecha HAVING count(*)<>17)")
    comprobar("Chile no mezcla nacional y regiones", "SELECT count(*) FROM fact_covid f JOIN dim_territorio d USING(territorio_id) WHERE d.pais='Chile' AND d.nivel='pais' AND fecha>=DATE '2020-05-20'")
    comprobar("índice entre 0 y 100", "SELECT count(*) FROM calidad_pais WHERE indice_calidad NOT BETWEEN 0 AND 100 OR indice_calidad IS NULL")
    comprobar("seis dimensiones", "SELECT count(DISTINCT dimension) FROM reglas_calidad", 6)
    comprobar("vacunación Chile con valores", "SELECT count(*)>0 FROM fact_vacunacion WHERE pais_id='U:152' AND people_vaccinated IS NOT NULL", True)
    comprobar("supresión no expone métricas", "SELECT count(*) FROM v_publica_segura WHERE suprimir AND (confirmados IS NOT NULL OR fallecidos IS NOT NULL OR casos_nuevos IS NOT NULL OR fallecidos_nuevos IS NOT NULL)")
    comprobar("balance origen hecho", """SELECT (SELECT count(*) FROM unificada)
      -(SELECT count(*) FROM fact_covid)
      -(SELECT coalesce(sum(CASE WHEN versiones>1 THEN n_fuentes ELSE n_fuentes-1 END),0)
        FROM grupos_observados)""")
    comprobar("122 observaciones en cuarentena", "SELECT sum(n_fuentes) FROM grupos_observados WHERE versiones>1", 122)
    comprobar("61 claves en cuarentena", "SELECT count(*) FROM grupos_observados WHERE versiones>1", 61)
    comprobar("18 observaciones consolidadas", "SELECT sum(n_fuentes-1) FROM grupos_observados WHERE versiones=1", 18)
    comprobar("FK padre territorial", "SELECT count(*) FROM dim_territorio d ANTI JOIN dim_territorio p ON d.padre_id=p.territorio_id WHERE d.padre_id IS NOT NULL")
    comprobar("FK país territorial", "SELECT count(*) FROM dim_territorio d ANTI JOIN dim_pais p ON d.pais_id=p.territorio_id")
    comprobar("padres pertenecen al mismo país", "SELECT count(*) FROM dim_territorio d JOIN dim_territorio p ON d.padre_id=p.territorio_id WHERE d.pais_id<>p.pais_id")
    for tabla in ['fact_pais','fact_serie_pais','fact_vacunacion','fact_indicador_anual']:
        comprobar(f"FK país {tabla}", f"SELECT count(*) FROM {tabla} f ANTI JOIN dim_pais d ON f.pais_id=d.territorio_id")
    comprobar("supresión primaria no expone métricas", "SELECT count(*) FROM v_publica_territorio WHERE suprimir AND (confirmados IS NOT NULL OR fallecidos IS NOT NULL OR casos_nuevos IS NOT NULL OR fallecidos_nuevos IS NOT NULL)")
    comprobar("supresión país no expone totales", "SELECT count(*) FROM v_publica_pais WHERE suprimir AND (confirmados IS NOT NULL OR fallecidos IS NOT NULL)")
    comprobar("sin indicador de supresión nulo", "SELECT count(*) FROM v_control_divulgacion WHERE suprimir IS NULL")
    return pd.DataFrame(checks)


def benchmark(limpio, destino, inventario):
    import pyarrow as pa
    import pyarrow.csv as csv
    import pyarrow.parquet as pq
    muestras = []
    abiertos = {}
    por_anio = {}
    for anio, grupo in inventario.groupby(inventario.fecha.str[:4]):
        por_anio[str(anio)] = {nombre: i for i, nombre in enumerate(grupo.sort_values("fecha").archivo)}
    for i in range(1, 6):
        partes, acumulado = [], 0
        for r in inventario.loc[inventario.etapa.eq(i)].sort_values("fecha").itertuples():
            anio = r.fecha[:4]
            if anio not in abiertos:
                abiertos[anio] = pq.ParquetFile(limpio / f"diarios_{anio}.parquet")
            tabla = abiertos[anio].read_row_group(por_anio[anio][r.archivo])
            if tabla.num_rows != r.filas or set(tabla.column("archivo_origen").to_pylist()) != {r.archivo}:
                raise ValueError("Orden o contenido de row groups no coincide con el inventario")
            partes.append(tabla)
            acumulado += tabla.num_rows
            if acumulado >= 2000:
                break
        muestras.append(pa.concat_tables(partes).slice(0, 2000))
    muestra = pa.concat_tables(muestras)
    cp, pp = destino / "muestra_equivalente.csv", destino / "muestra_equivalente.parquet"
    csv.write_csv(muestra, cp)
    pq.write_table(muestra, pp, compression="zstd")
    opciones = csv.ConvertOptions(column_types={f.name: f.type for f in muestra.schema}, null_values=[""],
                                  strings_can_be_null=True, quoted_strings_can_be_null=True)
    a, b = csv.read_csv(cp, convert_options=opciones), pq.read_table(pp)
    assert a.equals(b, check_metadata=False), "Benchmark requiere contenidos y tipos idénticos"
    tiempos = {"csv": [], "parquet": []}
    for repeticion in range(5):
        for formato in (["csv", "parquet"] if repeticion % 2 == 0 else ["parquet", "csv"]):
            inicio = time.perf_counter()
            tabla = csv.read_csv(cp, convert_options=opciones) if formato == "csv" else pq.read_table(pp)
            assert tabla.num_rows == 10000
            tiempos[formato].append(time.perf_counter() - inicio)
    return {"filas": 10000, "columnas": muestra.num_columns, "csv_bytes": cp.stat().st_size,
            "parquet_bytes": pp.stat().st_size, "csv_mediana_seg": statistics.median(tiempos["csv"]),
            "parquet_mediana_seg": statistics.median(tiempos["parquet"]), "lecturas_seg": tiempos,
            "metodo": "Misma tabla tipada, 2000 filas por esquema, ZSTD, cinco lecturas alternadas tras calentamiento; no caché fría."}
