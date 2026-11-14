"""Estrella territorio × día y vistas auditables de agregación."""
from pathlib import Path
import pandas as pd
from .territorios import construir


def sql_texto(valor):
    return "'" + str(valor).replace("'", "''") + "'"


def tabla_df(con, nombre, df):
    con.register("entrada_pandas", df)
    con.execute(f"CREATE TABLE {nombre} AS SELECT * FROM entrada_pandas")
    con.unregister("entrada_pandas")


def construir_estrella(con, parquet, uid):
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
    con.execute("CREATE UNIQUE INDEX obs_id ON observacion_mapa(observacion_id)")
    con.execute("""CREATE TABLE grupos_observados AS SELECT o.territorio_id,u.fecha_reporte fecha,
      count(*) n_fuentes, count(DISTINCT struct_pack(c:=u.confirmados,d:=u.fallecidos)) versiones,
      min(u.confirmados) confirmados,min(u.fallecidos) fallecidos
      FROM unificada u JOIN observacion_mapa o USING(archivo_origen,fila_origen,fecha_reporte)
      GROUP BY o.territorio_id,u.fecha_reporte""")
    # Una clave con casos/muertes contradictorios se conserva en crudo y se pone en cuarentena.
    con.execute("""CREATE TABLE fact_covid (
      territorio_id VARCHAR REFERENCES dim_territorio(territorio_id), fecha DATE REFERENCES dim_fecha(fecha),
      confirmados DOUBLE, fallecidos DOUBLE, casos_nuevos DOUBLE, fallecidos_nuevos DOUBLE,
      fecha_anterior DATE, confirmados_anteriores DOUBLE, fallecidos_anteriores DOUBLE,
      dias_desde_anterior INTEGER, delta_confirmados DOUBLE, delta_fallecidos DOUBLE,
      n_fuentes BIGINT, PRIMARY KEY(territorio_id,fecha))""")
    con.execute("""INSERT INTO fact_covid WITH anteriores AS (
      SELECT *,lag(fecha) OVER w fecha_anterior,lag(confirmados) OVER w confirmados_anteriores,
      lag(fallecidos) OVER w fallecidos_anteriores FROM grupos_observados WHERE versiones=1
      WINDOW w AS (PARTITION BY territorio_id ORDER BY fecha))
      SELECT territorio_id,fecha,confirmados,fallecidos,
      CASE WHEN date_diff('day',fecha_anterior,fecha)=1 THEN confirmados-confirmados_anteriores END,
      CASE WHEN date_diff('day',fecha_anterior,fecha)=1 THEN fallecidos-fallecidos_anteriores END,
      fecha_anterior,confirmados_anteriores,fallecidos_anteriores,date_diff('day',fecha_anterior,fecha)::INTEGER,
      confirmados-confirmados_anteriores,fallecidos-fallecidos_anteriores,n_fuentes FROM anteriores""")
    con.execute("""CREATE VIEW v_linaje AS SELECT o.*,u.sha256_origen,u.etapa,u.region_pais,u.provincia_estado,u.admin2,
      u.confirmados,u.fallecidos,g.versiones,g.n_fuentes,g.versiones=1 aceptada
      FROM observacion_mapa o JOIN unificada u USING(archivo_origen,fila_origen,fecha_reporte)
      JOIN grupos_observados g ON g.territorio_id=o.territorio_id AND g.fecha=o.fecha_reporte""")
    con.execute("""CREATE TABLE bridge_nombres_historicos AS SELECT m.*,r.desde,r.hasta,r.filas FROM mapa_territorial m
      JOIN (SELECT firma_id,min(fecha_reporte) desde,max(fecha_reporte) hasta,count(*) filas
      FROM observacion_mapa GROUP BY firma_id) r USING(firma_id)""")
    # Preferir el subtotal observado cuando coexiste con descendientes del mismo dominio.
    # Las dependencias con ISO propio son dominios disjuntos en la convención de JHU.
    con.execute("""CREATE VIEW v_rollup_territorial AS SELECT f.*,d.pais_id,d.nivel,d.poblacion,
      NOT EXISTS(SELECT 1 FROM fact_covid padre WHERE padre.fecha=f.fecha AND
        (padre.territorio_id=d.padre_id AND NOT coalesce(d.es_dependencia,false)
         OR padre.territorio_id=d.pais_id AND f.territorio_id<>d.pais_id AND NOT coalesce(d.es_dependencia,false))) incluido
      FROM fact_covid f JOIN dim_territorio d USING(territorio_id)""")
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
    con.execute("CREATE UNIQUE INDEX pais_fecha ON fact_pais(pais_id,fecha)")
    con.execute("""CREATE VIEW dim_pais AS SELECT * FROM dim_territorio WHERE nivel='pais'""")
    return dim


def cargar_externas(con, serie, linaje, vac, bm, cruces):
    for nombre, df in [("fact_serie_pais", serie), ("linaje_series", linaje), ("fact_vacunacion", vac),
                       ("fact_indicador_anual", bm), ("cruces_externos", cruces)]:
        tabla_df(con, nombre, df)
    con.execute("CREATE UNIQUE INDEX serie_pk ON fact_serie_pais(pais_id,fecha)")
    con.execute("CREATE UNIQUE INDEX vacuna_pk ON fact_vacunacion(pais_id,fecha)")
    con.execute("CREATE UNIQUE INDEX bm_pk ON fact_indicador_anual(pais_id,anio,indicador)")
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
      coalesce(d.poblacion<5000,true) AND (f.confirmados BETWEEN 1 AND 4 OR f.fallecidos BETWEEN 1 AND 4
        OR f.casos_nuevos BETWEEN 1 AND 4 OR f.fallecidos_nuevos BETWEEN 1 AND 4) suprimir,
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


OLAP = {
    "roll_up": "SELECT d.pais,year(f.fecha) anio,sum(f.casos_nuevos) casos_netos_reportados FROM fact_pais f JOIN dim_pais d ON d.territorio_id=f.pais_id WHERE d.pais='Chile' GROUP BY d.pais,year(f.fecha) ORDER BY anio",
    "drill_down": "SELECT d.provincia,f.confirmados,f.fallecidos FROM fact_covid f JOIN dim_territorio d USING(territorio_id) WHERE d.pais='Chile' AND d.nivel='region' AND f.fecha=DATE '2023-03-09' ORDER BY d.provincia",
    "slice": "SELECT d.pais,f.confirmados,f.fallecidos FROM fact_pais f JOIN dim_pais d ON d.territorio_id=f.pais_id WHERE f.fecha=DATE '2020-06-30' ORDER BY f.confirmados DESC NULLS LAST LIMIT 10",
    "dice": "SELECT d.pais,min(f.fecha) desde,max(f.fecha) hasta,sum(f.casos_nuevos) casos_netos FROM fact_pais f JOIN dim_pais d ON d.territorio_id=f.pais_id WHERE d.pais IN ('Chile','Argentina','Peru') AND f.fecha BETWEEN DATE '2021-12-01' AND DATE '2021-12-31' GROUP BY d.pais ORDER BY d.pais",
}
