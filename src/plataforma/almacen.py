"""Estrella territorio × día y vistas auditables de agregación."""
from pathlib import Path
import pandas as pd
from .territorios import construir


def sql_texto(valor):
    return "'" + str(valor).replace("'", "''") + "'"


def tabla_df(con, nombre, df):
    import pyarrow as pa
    # Mantener buffers Arrow nativos durante toda la consulta. Evita depender
    # de objetos Python celda por celda al liberar resultados en Windows.
    entrada = pa.Table.from_pandas(df, preserve_index=False)
    con.register("entrada_arrow", entrada)
    try:
        con.execute(f"CREATE TABLE {nombre} AS SELECT * FROM entrada_arrow")
    finally:
        con.unregister("entrada_arrow")


def construir_estrella(con, parquet, uid):
    print("  DW: tabla unificada y correspondencias", flush=True)
    con.execute(f"CREATE TABLE unificada AS SELECT * FROM read_parquet({sql_texto(Path(parquet).as_posix() + '/diarios_*.parquet')})")
    firmas = con.execute("""SELECT DISTINCT region_pais, provincia_estado, admin2, fips FROM unificada
                             ORDER BY region_pais, provincia_estado, admin2, fips""").fetchdf()
    firmas["firma_id"] = range(1, len(firmas) + 1)
    dim, mapa = construir(uid, firmas)
    tabla_df(con, "dim_territorio", dim)
    con.execute("ALTER TABLE dim_territorio ADD PRIMARY KEY (territorio_id)")
    tabla_df(con, "mapa_territorial", mapa)
    con.execute("CREATE UNIQUE INDEX mapa_id ON mapa_territorial(firma_id)")
    con.execute("""CREATE TABLE dim_fecha AS SELECT CAST(d AS DATE) fecha, year(d)::SMALLINT anio,
      month(d)::TINYINT mes, day(d)::TINYINT dia, week(d)::TINYINT semana_iso,
      quarter(d)::TINYINT trimestre FROM generate_series(DATE '2020-01-22', DATE '2023-03-09', INTERVAL 1 DAY) t(d)""")
    con.execute("ALTER TABLE dim_fecha ADD PRIMARY KEY(fecha)")
    con.execute("""CREATE TABLE observacion_mapa AS SELECT u.archivo_origen || ':' || u.fila_origen observacion_id,
      u.archivo_origen,u.fila_origen,u.fecha_reporte,m.firma_id,m.territorio_id
      FROM unificada u JOIN mapa_territorial m ON u.region_pais IS NOT DISTINCT FROM m.region_pais
      AND u.provincia_estado IS NOT DISTINCT FROM m.provincia_estado AND u.admin2 IS NOT DISTINCT FROM m.admin2
      AND u.fips IS NOT DISTINCT FROM m.fips""")
    con.execute("""CREATE TABLE grupos_observados AS SELECT o.territorio_id,u.fecha_reporte fecha,
      count(*) n_fuentes,
      CASE WHEN min(u.confirmados) IS DISTINCT FROM max(u.confirmados)
          OR min(u.fallecidos) IS DISTINCT FROM max(u.fallecidos)
          OR (count(u.confirmados)>0 AND count(u.confirmados)<count(*))
          OR (count(u.fallecidos)>0 AND count(u.fallecidos)<count(*))
        THEN 2 ELSE 1 END versiones,
      min(u.confirmados) confirmados,min(u.fallecidos) fallecidos
      FROM unificada u JOIN observacion_mapa o USING(archivo_origen,fila_origen,fecha_reporte)
      GROUP BY o.territorio_id,u.fecha_reporte""")
    # Una clave con casos/muertes contradictorios se conserva en crudo y se pone en cuarentena.
    print("  DW: hechos únicos y diarios firmados", flush=True)
    # En un DW de carga cerrada, índices ART sobre millones de claves consumen RAM
    # adicional fuera del buffer. Las claves de hechos son lógicas y se validan por SQL
    # antes de publicar. Las dimensiones pequeñas conservan su PK física.
    con.execute("""CREATE TABLE fact_covid AS WITH anteriores AS (
      SELECT *,lag(fecha) OVER w fecha_anterior,lag(confirmados) OVER w confirmados_anteriores,
      lag(fallecidos) OVER w fallecidos_anteriores FROM grupos_observados WHERE versiones=1
      WINDOW w AS (PARTITION BY territorio_id ORDER BY fecha))
      SELECT territorio_id,fecha,confirmados,fallecidos,
      CASE WHEN date_diff('day',fecha_anterior,fecha)=1 THEN confirmados-confirmados_anteriores END casos_nuevos,
      CASE WHEN date_diff('day',fecha_anterior,fecha)=1 THEN fallecidos-fallecidos_anteriores END fallecidos_nuevos,
      fecha_anterior,confirmados_anteriores,fallecidos_anteriores,date_diff('day',fecha_anterior,fecha)::INTEGER dias_desde_anterior,
      confirmados-confirmados_anteriores delta_confirmados,fallecidos-fallecidos_anteriores delta_fallecidos,n_fuentes FROM anteriores""")
    con.execute("""CREATE VIEW v_linaje AS SELECT o.*,u.sha256_origen,u.etapa,u.region_pais,u.provincia_estado,u.admin2,
      u.confirmados,u.fallecidos,g.versiones,g.n_fuentes,g.versiones=1 aceptada
      FROM observacion_mapa o JOIN unificada u USING(archivo_origen,fila_origen,fecha_reporte)
      JOIN grupos_observados g ON g.territorio_id=o.territorio_id AND g.fecha=o.fecha_reporte""")
    con.execute("""CREATE TABLE bridge_nombres_historicos AS SELECT m.*,r.desde,r.hasta,r.filas FROM mapa_territorial m
      JOIN (SELECT firma_id,min(fecha_reporte) desde,max(fecha_reporte) hasta,count(*) filas
      FROM observacion_mapa GROUP BY firma_id) r USING(firma_id)""")
    # Preferir el subtotal observado cuando coexiste con descendientes del mismo dominio.
    # Las dependencias con ISO propio son dominios disjuntos en la convención de JHU.
    print("  DW: jerarquías sin subconsultas correlacionadas", flush=True)
    con.execute("""CREATE VIEW v_rollup_territorial AS SELECT f.*,d.pais_id,d.nivel,d.poblacion,
      NOT ((padre.territorio_id IS NOT NULL AND NOT
             (d.nivel='region' AND coalesce(d.es_dependencia,false)))
           OR (pais.territorio_id IS NOT NULL AND f.territorio_id<>d.pais_id
               AND NOT coalesce(d.es_dependencia,false))) incluido
      FROM fact_covid f JOIN dim_territorio d USING(territorio_id)
      LEFT JOIN fact_covid padre ON padre.territorio_id=d.padre_id AND padre.fecha=f.fecha
      LEFT JOIN fact_covid pais ON pais.territorio_id=d.pais_id AND pais.fecha=f.fecha""")
    con.execute("""CREATE TABLE agregado_pais AS WITH suma AS (
      SELECT pais_id,fecha,count(*) territorios,count(confirmados) con_casos,count(fallecidos) con_muertes,
      sum(confirmados) casos,sum(fallecidos) muertes FROM v_rollup_territorial WHERE incluido GROUP BY pais_id,fecha),
      conflictos AS (SELECT d.pais_id,g.fecha,count(*) claves_conflictivas FROM grupos_observados g
      JOIN dim_territorio d USING(territorio_id) WHERE versiones>1 GROUP BY d.pais_id,g.fecha)
      SELECT s.pais_id,s.fecha,s.territorios,coalesce(c.claves_conflictivas,0) claves_conflictivas,
      CASE WHEN s.con_casos=s.territorios AND coalesce(c.claves_conflictivas,0)=0 THEN s.casos END confirmados,
      CASE WHEN s.con_muertes=s.territorios AND coalesce(c.claves_conflictivas,0)=0 THEN s.muertes END fallecidos
      FROM suma s LEFT JOIN conflictos c USING(pais_id,fecha)""")
    con.execute("""CREATE TABLE fact_pais AS WITH a AS (SELECT *,lag(fecha) OVER w fecha_anterior,
      lag(confirmados) OVER w confirmados_anteriores,lag(fallecidos) OVER w fallecidos_anteriores
      FROM agregado_pais WINDOW w AS(PARTITION BY pais_id ORDER BY fecha))
      SELECT *,CASE WHEN date_diff('day',fecha_anterior,fecha)=1 THEN confirmados-confirmados_anteriores END casos_nuevos,
      CASE WHEN date_diff('day',fecha_anterior,fecha)=1 THEN fallecidos-fallecidos_anteriores END fallecidos_nuevos
      FROM a""")
    con.execute("""CREATE VIEW dim_pais AS SELECT * FROM dim_territorio WHERE nivel='pais'""")
    con.execute("""CREATE VIEW v_linaje_rollup AS SELECT l.*,r.incluido incluido_total_pais
      FROM v_linaje l LEFT JOIN v_rollup_territorial r
      ON l.territorio_id=r.territorio_id AND l.fecha_reporte=r.fecha""")
    return dim


def cargar_externas(con, serie, linaje, vac, bm, cruces):
    for nombre, df in [("fact_serie_pais", serie), ("linaje_series", linaje), ("fact_vacunacion", vac),
                       ("fact_indicador_anual", bm), ("cruces_externos", cruces)]:
        tabla_df(con, nombre, df)
    con.execute("""CREATE VIEW v_pais_vacunacion AS SELECT f.*,d.pais,d.iso3,v.people_vaccinated,
      v.people_fully_vaccinated,v.people_vaccinated_per_hundred,v.people_fully_vaccinated_per_hundred,
      v.archivo_origen archivo_vacunacion,v.fila_origen fila_vacunacion
      FROM fact_pais f JOIN dim_pais d ON d.territorio_id=f.pais_id
      LEFT JOIN fact_vacunacion v ON v.pais_id=f.pais_id AND v.fecha=f.fecha""")
    con.execute("""CREATE VIEW v_pais_indicador AS SELECT f.*,b.valor porcentaje_65plus,b.fila_origen fila_bm
      FROM fact_pais f LEFT JOIN fact_indicador_anual b ON f.pais_id=b.pais_id AND year(f.fecha)=b.anio
      AND b.indicador='SP.POP.65UP.TO.ZS'""")
    con.execute("""CREATE TABLE reconciliacion AS SELECT f.pais_id,f.fecha,f.confirmados reporte_casos,s.confirmados serie_casos,
      f.fallecidos reporte_muertes,s.fallecidos serie_muertes,
      f.confirmados-s.confirmados diferencia_casos,f.fallecidos-s.fallecidos diferencia_muertes
      FROM fact_pais f JOIN fact_serie_pais s USING(pais_id,fecha)""")


def divulgacion(con):
    con.execute("""CREATE VIEW v_control_divulgacion AS SELECT f.territorio_id,f.fecha,
      d.pais_id,d.poblacion,d.nivel,
      coalesce(d.poblacion<5000,true) AND coalesce((f.confirmados BETWEEN 1 AND 4 OR f.fallecidos BETWEEN 1 AND 4
        OR f.casos_nuevos BETWEEN 1 AND 4 OR f.fallecidos_nuevos BETWEEN 1 AND 4),false) suprimir,
      f.confirmados,f.fallecidos,f.casos_nuevos,f.fallecidos_nuevos
      FROM fact_covid f JOIN dim_territorio d USING(territorio_id)""")
    # Si alguna celda es sensible se ocultan todas las métricas de esa fila, incluidas tasas futuras.
    con.execute("""CREATE VIEW v_publica_territorio AS SELECT territorio_id,fecha,pais_id,nivel,poblacion,suprimir,
      CASE WHEN NOT suprimir THEN confirmados END confirmados,
      CASE WHEN NOT suprimir THEN fallecidos END fallecidos,
      CASE WHEN NOT suprimir THEN casos_nuevos END casos_nuevos,
      CASE WHEN NOT suprimir THEN fallecidos_nuevos END fallecidos_nuevos
      FROM v_control_divulgacion""")
    # Cierre conservador: si hay una supresión en un país, no publicar sus totales ni su historia
    # en esta vista. Evita derivar celdas ocultas con acumulados vecinos o totales publicados aquí.
    con.execute("""CREATE VIEW v_publica_pais AS SELECT f.pais_id,f.fecha,
      CASE WHEN NOT p.suprimir THEN f.confirmados END confirmados,
      CASE WHEN NOT p.suprimir THEN f.fallecidos END fallecidos,p.suprimir
      FROM fact_pais f JOIN (SELECT pais_id,bool_or(suprimir) suprimir FROM v_control_divulgacion GROUP BY pais_id) p USING(pais_id)""")
    # La vista territorial también oculta toda la historia/métricas de países afectados para no
    # ofrecer diferencias temporales o sumas complementarias en la interfaz pública prevista.
    con.execute("""CREATE VIEW v_publica_segura AS SELECT f.territorio_id,f.fecha,d.pais_id,p.suprimir,
      CASE WHEN NOT p.suprimir THEN f.confirmados END confirmados,
      CASE WHEN NOT p.suprimir THEN f.fallecidos END fallecidos,
      CASE WHEN NOT p.suprimir THEN f.casos_nuevos END casos_nuevos,
      CASE WHEN NOT p.suprimir THEN f.fallecidos_nuevos END fallecidos_nuevos
      FROM fact_covid f JOIN dim_territorio d USING(territorio_id)
      JOIN (SELECT pais_id,bool_or(suprimir) suprimir FROM v_control_divulgacion GROUP BY pais_id) p USING(pais_id)""")


def metricas_divulgacion(con):
    """Pérdida de celdas, no suma de personas sobre acumulados repetidos."""
    r = con.execute("""SELECT count(*) filas_evaluadas,
      count(*) FILTER(WHERE suprimir) filas_supresion_primaria,
      sum(coalesce((confirmados BETWEEN 1 AND 4)::INT,0)+coalesce((fallecidos BETWEEN 1 AND 4)::INT,0)+
          coalesce((casos_nuevos BETWEEN 1 AND 4)::INT,0)+coalesce((fallecidos_nuevos BETWEEN 1 AND 4)::INT,0)) celdas_1a4
      FROM v_control_divulgacion""").fetchdf().to_dict("records")[0]
    r["filas_cierre_conservador"] = con.execute("SELECT count(*) FROM v_publica_segura WHERE suprimir").fetchone()[0]
    r["condados_uid_menores_5000"] = con.execute("SELECT count(*) FROM dim_territorio WHERE pais='US' AND nivel='condado' AND poblacion<5000").fetchone()[0]
    # Unir por los pocos países, no fact_covid contra una expansión de sí misma
    # de más de cuatro millones de claves. La decisión es idéntica a la vista.
    r["celdas_no_nulas_ocultas"] = con.execute("""WITH paises AS (
      SELECT pais_id,bool_or(suprimir) suprimir FROM v_control_divulgacion GROUP BY pais_id)
      SELECT sum((f.confirmados IS NOT NULL)::INT+(f.fallecidos IS NOT NULL)::INT+
      (f.casos_nuevos IS NOT NULL)::INT+(f.fallecidos_nuevos IS NOT NULL)::INT)
      FROM v_control_divulgacion f JOIN paises p USING(pais_id) WHERE p.suprimir""").fetchone()[0]
    return r


def trazar(con, territorio, fecha):
    """Materializa solo dos días y el mapa solicitado, sin expandir todo el linaje."""
    return con.execute("""WITH mapa AS MATERIALIZED (
      SELECT m.*,d.pais_id,d.padre_id,d.nivel,d.es_dependencia FROM mapa_territorial m
      JOIN dim_territorio d USING(territorio_id) WHERE d.territorio_id=? OR d.pais_id=?),
      obs AS MATERIALIZED (SELECT * FROM unificada
        WHERE fecha_reporte BETWEEN CAST(? AS DATE)-1 AND CAST(? AS DATE)),
      hechos AS MATERIALIZED (SELECT territorio_id,fecha FROM fact_covid
        WHERE fecha BETWEEN CAST(? AS DATE)-1 AND CAST(? AS DATE)),
      grupos AS MATERIALIZED (SELECT * FROM grupos_observados
        WHERE fecha BETWEEN CAST(? AS DATE)-1 AND CAST(? AS DATE))
      SELECT u.archivo_origen,u.fila_origen,u.fecha_reporte,d.territorio_id,d.pais_id,
      u.region_pais,u.provincia_estado,u.admin2,u.confirmados,u.fallecidos,u.sha256_origen,
      g.versiones,g.n_fuentes,g.versiones=1 aceptada,
      CASE WHEN f.territorio_id IS NOT NULL THEN
        NOT ((padre.territorio_id IS NOT NULL AND NOT (d.nivel='region' AND coalesce(d.es_dependencia,false)))
             OR (pais.territorio_id IS NOT NULL AND f.territorio_id<>d.pais_id AND NOT coalesce(d.es_dependencia,false)))
      END incluido_total_pais
      FROM obs u JOIN mapa d ON u.region_pais IS NOT DISTINCT FROM d.region_pais
      AND u.provincia_estado IS NOT DISTINCT FROM d.provincia_estado AND u.admin2 IS NOT DISTINCT FROM d.admin2
      AND u.fips IS NOT DISTINCT FROM d.fips
      LEFT JOIN grupos g ON g.territorio_id=d.territorio_id AND g.fecha=u.fecha_reporte
      LEFT JOIN hechos f ON f.territorio_id=d.territorio_id AND f.fecha=u.fecha_reporte
      LEFT JOIN hechos padre ON padre.territorio_id=d.padre_id AND padre.fecha=u.fecha_reporte
      LEFT JOIN hechos pais ON pais.territorio_id=d.pais_id AND pais.fecha=u.fecha_reporte
      ORDER BY u.fecha_reporte,u.archivo_origen,u.fila_origen""",
      [territorio, territorio, fecha, fecha, fecha, fecha, fecha, fecha]).fetchdf()


OLAP = {
    "roll_up": "SELECT d.pais,year(f.fecha) anio,sum(f.casos_nuevos) casos_netos_reportados FROM fact_pais f JOIN dim_pais d ON d.territorio_id=f.pais_id WHERE d.pais='Chile' GROUP BY d.pais,year(f.fecha) ORDER BY anio",
    "drill_down": "SELECT d.provincia,f.confirmados,f.fallecidos FROM fact_covid f JOIN dim_territorio d USING(territorio_id) WHERE d.pais='Chile' AND d.nivel='region' AND f.fecha=DATE '2023-03-09' ORDER BY d.provincia",
    "slice": "SELECT d.pais,f.confirmados,f.fallecidos FROM fact_pais f JOIN dim_pais d ON d.territorio_id=f.pais_id WHERE f.fecha=DATE '2020-06-30' ORDER BY f.confirmados DESC NULLS LAST LIMIT 10",
    "dice": "SELECT d.pais,min(f.fecha) desde,max(f.fecha) hasta,sum(f.casos_nuevos) casos_netos FROM fact_pais f JOIN dim_pais d ON d.territorio_id=f.pais_id WHERE d.pais IN ('Chile','Argentina','Peru') AND f.fecha BETWEEN DATE '2021-12-01' AND DATE '2021-12-31' GROUP BY d.pais ORDER BY d.pais",
}
