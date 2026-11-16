"""Balance exhaustivo entre observaciones originales y hechos analíticos."""


def balance_filas(con):
    """Cada fila pertenece a una sola categoría; consolidar no elimina su linaje."""
    return con.execute("""SELECT
      CASE WHEN versiones>1 THEN 'cuarentena_conflicto'
           WHEN n_fuentes>1 THEN 'consolidacion_coherente'
           ELSE 'clave_simple' END tratamiento,
      count(*) claves, sum(n_fuentes)::BIGINT filas_origen,
      count(*) FILTER(WHERE versiones=1) hechos_dw,
      (sum(n_fuentes)-count(*) FILTER(WHERE versiones=1))::BIGINT diferencia
      FROM grupos_observados GROUP BY tratamiento ORDER BY tratamiento""").fetchdf()


def detalle_balance(con):
    """Exporta todas las observaciones de claves múltiples, incluso las aceptadas.

    El ordinal es solo una referencia estable para contar consolidaciones; no
    elige una versión de un conflicto ni altera fact_covid.
    """
    return con.execute("""WITH afectadas AS MATERIALIZED (
      SELECT o.*,g.n_fuentes,g.versiones FROM observacion_mapa o
      JOIN (SELECT * FROM grupos_observados WHERE n_fuentes>1) g
      ON g.territorio_id=o.territorio_id AND g.fecha=o.fecha_reporte)
      SELECT a.territorio_id,a.fecha_reporte fecha,a.observacion_id,
        a.archivo_origen,a.fila_origen,u.sha256_origen,u.region_pais,
        u.provincia_estado,u.admin2,u.fips,u.confirmados,u.fallecidos,
        a.n_fuentes,a.versiones,
        CASE WHEN a.versiones>1 THEN 'cuarentena_conflicto'
             ELSE 'consolidacion_coherente' END tratamiento,
        row_number() OVER(PARTITION BY a.territorio_id,a.fecha_reporte
                          ORDER BY a.archivo_origen,a.fila_origen) ordinal_origen
      FROM afectadas a JOIN unificada u USING(archivo_origen,fila_origen)
      ORDER BY a.fecha_reporte,a.territorio_id,a.fila_origen""").fetchdf()
