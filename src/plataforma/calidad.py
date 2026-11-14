"""Reglas medibles por carga e índice descriptivo, no certificación epidemiológica."""
import pandas as pd
from .almacen import tabla_df


def ejecutar(con):
    con.execute("""CREATE TABLE candidatos_rezago AS WITH w AS (SELECT *,
      sum(CASE WHEN casos_nuevos=0 THEN 1 ELSE 0 END) OVER (PARTITION BY pais_id ORDER BY fecha ROWS BETWEEN 6 PRECEDING AND 1 PRECEDING) ceros_previos,
      lag(fecha,6) OVER(PARTITION BY pais_id ORDER BY fecha) fecha_6 FROM fact_pais)
      SELECT pais_id,fecha,casos_nuevos,ceros_previos FROM w WHERE ceros_previos=6
      AND date_diff('day',fecha_6,fecha)=6 AND casos_nuevos>=100""")
    con.execute("""CREATE TABLE brechas_territorio AS WITH fechas AS (SELECT DISTINCT territorio_id,fecha_reporte fecha FROM observacion_mapa),
      w AS(SELECT *,lag(fecha) OVER(PARTITION BY territorio_id ORDER BY fecha) anterior FROM fechas)
      SELECT *,date_diff('day',anterior,fecha)-1 dias_sin_fila FROM w WHERE date_diff('day',anterior,fecha)>1""")
    con.execute("""CREATE TABLE calidad_pais AS WITH raw AS (
      SELECT d.pais_id,count(*) filas,
      sum((u.confirmados IS NULL)::INT+(u.fallecidos IS NULL)::INT) faltantes,
      sum((coalesce(u.confirmados<0,false) OR coalesce(u.fallecidos<0,false)
        OR coalesce(abs(u.latitud)>90,false) OR coalesce(abs(u.longitud)>180,false))::INT) invalidas,
      sum(coalesce(u.fallecidos>u.confirmados,false)::INT) inconsistentes,
      sum((try_cast(u.ultima_actualizacion AS DATE) BETWEEN u.fecha_reporte-7 AND u.fecha_reporte+1)::INT) actualizadas,
      count(DISTINCT u.fecha_reporte) dias_con_fila,
      date_diff('day',min(u.fecha_reporte),max(u.fecha_reporte))+1 dias_esperados
      FROM unificada u JOIN observacion_mapa o USING(archivo_origen,fila_origen,fecha_reporte)
      JOIN dim_territorio d USING(territorio_id) GROUP BY d.pais_id),
      dup AS(SELECT d.pais_id,sum(g.n_fuentes-1) repetidas FROM grupos_observados g JOIN dim_territorio d USING(territorio_id) GROUP BY d.pais_id),
      neg AS(SELECT pais_id,count(*) dias_utiles,sum((coalesce(casos_nuevos<0,false) OR coalesce(fallecidos_nuevos<0,false))::INT) retrocesos FROM fact_pais GROUP BY pais_id),
      ref AS(SELECT pais_id,count(diferencia_casos)+count(diferencia_muertes) comparaciones,
        sum(coalesce(diferencia_casos<>0,false)::INT+coalesce(diferencia_muertes<>0,false)::INT) discrepancias FROM reconciliacion GROUP BY pais_id)
      SELECT r.*,d.pais,d.iso3,coalesce(dup.repetidas,0) repetidas,n.retrocesos,
      r.dias_esperados-r.dias_con_fila dias_sin_reporte,
      1-r.faltantes/(2.0*r.filas) completitud,
      1-coalesce(dup.repetidas,0)/r.filas unicidad,
      1-r.invalidas/r.filas validez,
      ((1-r.inconsistentes/r.filas)+(1-coalesce(n.retrocesos,0)/nullif(n.dias_utiles,0)))/2 consistencia,
      1-ref.discrepancias/nullif(ref.comparaciones,0) exactitud_proxy,
      (r.dias_con_fila/r.dias_esperados+coalesce(r.actualizadas,0)/r.filas)/2 oportunidad,
      ref.comparaciones,ref.discrepancias
      FROM raw r JOIN dim_pais d ON d.territorio_id=r.pais_id LEFT JOIN dup ON dup.pais_id=r.pais_id
      LEFT JOIN neg n ON n.pais_id=r.pais_id LEFT JOIN ref ON ref.pais_id=r.pais_id""")
    con.execute("ALTER TABLE calidad_pais ADD COLUMN indice_calidad DOUBLE")
    con.execute("""UPDATE calidad_pais SET indice_calidad=100*(completitud+unicidad+validez+consistencia+oportunidad+coalesce(exactitud_proxy,0)) /
      (5+(exactitud_proxy IS NOT NULL)::INT)""")
    reglas = []

    def regla(codigo, dimension, descripcion, sql, umbral, operador=">=", limitacion=""):
        valor = con.execute(sql).fetchone()[0]
        if valor is None:
            estado = "NO_EVALUABLE"
        else:
            estado = "OK" if (valor >= umbral if operador == ">=" else valor <= umbral) else "ALERTA"
        reglas.append({"regla": codigo, "dimension": dimension, "descripcion": descripcion,
                       "valor": valor, "operador": operador, "umbral": umbral, "estado": estado, "limitacion": limitacion})

    regla("C01", "completitud", "Reportes diarios presentes", "SELECT count(DISTINCT archivo_origen) FROM unificada", 1143)
    regla("C02", "completitud", "Fracción de conteos casos/muertes informados", "SELECT 1-(sum((confirmados IS NULL)::INT+(fallecidos IS NULL)::INT)/(2.0*count(*))) FROM unificada", .999)
    regla("U01", "unicidad", "Repeticiones adicionales de clave territorial canónica", "SELECT sum(n_fuentes-1) FROM grupos_observados", 0, "<=")
    regla("V01", "validez", "Acumulados negativos en origen", "SELECT count(*) FROM unificada WHERE confirmados<0 OR fallecidos<0", 0, "<=", "Se preservan ajustes, nunca se recortan a cero.")
    regla("V02", "validez", "Coordenadas numéricas fuera de rango", "SELECT count(*) FROM unificada WHERE abs(latitud)>90 OR abs(longitud)>180", 0, "<=")
    regla("V03", "validez", "Territorios observados sin población positiva", "SELECT count(*) FROM dim_territorio d WHERE coalesce(poblacion,0)<=0 AND EXISTS(SELECT 1 FROM fact_covid f WHERE f.territorio_id=d.territorio_id)", 0, "<=")
    regla("V04", "validez", "Territorios observados sin coordenadas", "SELECT count(*) FROM dim_territorio d WHERE (latitud IS NULL OR longitud IS NULL) AND EXISTS(SELECT 1 FROM fact_covid f WHERE f.territorio_id=d.territorio_id)", 0, "<=")
    regla("V05", "validez", "Territorios observados sin ISO3 oficial declarado", "SELECT count(*) FROM dim_territorio d WHERE NOT coalesce(iso3_oficial_formato,false) AND EXISTS(SELECT 1 FROM fact_covid f WHERE f.territorio_id=d.territorio_id)", 0, "<=", "XKS es código estadístico, no ISO oficial; se documenta su cruce explícito.")
    regla("S01", "consistencia", "Filas con fallecidos mayores que confirmados", "SELECT count(*) FROM unificada WHERE fallecidos>confirmados", 0, "<=", "Incluye Unknown/Unassigned: no se corrigen automáticamente.")
    regla("S02", "consistencia", "Días-país con retroceso de casos o muertes", "SELECT count(*) FROM fact_pais WHERE casos_nuevos<0 OR fallecidos_nuevos<0", 0, "<=")
    regla("E01", "exactitud", "Concordancia con series históricas revisadas", "SELECT 1-sum((coalesce(diferencia_casos<>0,false)::INT+coalesce(diferencia_muertes<>0,false)::INT)::DOUBLE)/(count(diferencia_casos)+count(diferencia_muertes)) FROM reconciliacion", .99, limitacion="Proxy de acuerdo, no verdad epidemiológica ni fuentes independientes.")
    regla("O01", "oportunidad", "Días-país sin fila entre primera y última aparición", "SELECT sum(dias_sin_reporte) FROM calidad_pais", 0, "<=", "No presupone que un territorio debía existir antes de su primera aparición.")
    regla("O02", "oportunidad", "Fracción de fechas de actualización entre reporte-7 y reporte+1", "SELECT avg((try_cast(ultima_actualizacion AS DATE) BETWEEN fecha_reporte-7 AND fecha_reporte+1)::INT) FROM unificada", .95, limitacion="Last_Update no demuestra fecha de publicación o frecuencia epidemiológica.")
    regla("O03", "oportunidad", "Picos tras seis días sin incremento, al menos 100 casos", "SELECT count(*) FROM candidatos_rezago", 0, "<=", "Candidatos a rezago, no atribución causal confirmada.")
    tabla_df(con, "reglas_calidad", pd.DataFrame(reglas))
    return pd.DataFrame(reglas)
