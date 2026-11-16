"""Verificación de la carga completa publicada; no descarga ni reconstruye datos.

Ejecutar desde la raíz: python tests/verificar_cierre.py
Escribe evidencia en data/quality/cierre_hito2/, sin modificar el DW.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import duckdb
import pandas as pd
from plataforma.auditoria import balance_filas, detalle_balance
from plataforma.almacen import OLAP, sql_texto, trazar, metricas_divulgacion
from plataforma.ingesta import sha256
from plataforma.normalizacion import normalizar
from plataforma.validacion import validar


def huella_tabla(con, origen):
    """SHA-256 de todos los campos y filas ordenadas, mediante lotes Arrow iguales."""
    digest = hashlib.sha256()
    filas = 0
    reader = con.execute(f'SELECT * FROM {origen} ORDER BY archivo_origen,fila_origen').to_arrow_reader(16384)
    try:
        for batch in reader:
            digest.update(batch.serialize().to_pybytes())
            filas += batch.num_rows
    finally:
        reader.close()
    return {'filas': filas, 'sha256_lotes_arrow': digest.hexdigest()}


def ejecutar():
    out = ROOT / 'data/quality/cierre_hito2'
    out.mkdir(parents=True, exist_ok=True)
    puntero = json.loads((ROOT / 'data/hito2_actual.json').read_text(encoding='utf-8'))
    reportes = ROOT / puntero['reportes']
    manifiesto = json.loads((reportes / 'manifiesto_fuentes.json').read_text(encoding='utf-8'))
    for fuente in manifiesto:
        if sha256(ROOT / fuente['ruta']) != fuente['sha256']:
            raise AssertionError(f"Cambió la fuente {fuente['archivo']}")
    print('Manifiesto completo: hashes OK', flush=True)
    with duckdb.connect(str(ROOT / puntero['dw']), read_only=True,
                        config={'memory_limit': '128MB', 'threads': 1}) as con:
        con.execute('SET preserve_insertion_order=false')
        con.execute('SET temp_directory=' + sql_texto((out / 'temporal').as_posix()))
        checks = validar(con)
        checks.to_csv(out / 'pruebas_integracion.csv', index=False)
        print(f'Integración: {len(checks)} OK', flush=True)
        dw = huella_tabla(con, 'unificada')
        print('Huella completa DW calculada', flush=True)
        parquet = huella_tabla(con, 'read_parquet(' + sql_texto((ROOT / puntero['parquet']).as_posix() + '/diarios_*.parquet') + ')')
        if dw != parquet:
            raise AssertionError('Los contenidos completos de Parquet y DW difieren')
        print('Parquet/DW: todos los campos y filas coinciden por SHA-256', flush=True)
        balance = balance_filas(con)
        detalle = detalle_balance(con)
        if int(balance.filas_origen.sum()) != dw['filas'] or int(balance.diferencia.sum()) != 140:
            raise AssertionError('Balance de filas inesperado')
        fuentes = {f['archivo']: f for f in manifiesto if f['tipo'] == 'diario'}
        verificadas = 0
        for archivo, parte in detalle.groupby('archivo_origen'):
            fuente = fuentes[archivo]
            datos, _ = normalizar(ROOT / fuente['ruta'], fuente['sha256'])
            for r in parte.itertuples():
                original = datos.iloc[r.fila_origen-1]
                for campo in ['confirmados', 'fallecidos']:
                    a,b = original[campo],getattr(r,campo)
                    if not ((pd.isna(a) and pd.isna(b)) or a == b):
                        raise AssertionError(f'{archivo}:{r.fila_origen} {campo}')
                if original.sha256_origen != r.sha256_origen:
                    raise AssertionError('Hash de linaje diferente')
                verificadas += 1
        balance.to_csv(out / 'balance_filas.csv', index=False)
        detalle.to_csv(out / 'balance_detalle.csv', index=False)
        olap = {}
        for nombre, sql in OLAP.items():
            df = con.execute(sql).fetchdf()
            if df.empty:
                raise AssertionError(f'OLAP vacío: {nombre}')
            df.to_csv(out / f'olap_{nombre}.csv', index=False)
            olap[nombre] = len(df)
        traza = trazar(con, 'U:152', '2020-05-20')
        if len(traza) != 18 or int(traza.incluido_total_pais.sum()) != 18:
            raise AssertionError('Traza de cambio de granularidad Chile incorrecta')
        traza.to_csv(out / 'traza_chile.csv', index=False)
        print('Balance, CSV originales, cuatro OLAP y traza Chile: OK', flush=True)
        condados = con.execute("""WITH paises AS (
          SELECT pais_id,bool_or(suprimir) suprimir FROM v_control_divulgacion GROUP BY pais_id)
          SELECT count(*) filas_observadas,
          count(DISTINCT c.territorio_id) condados_observados,
          count(*) FILTER(WHERE c.suprimir) filas_supresion_primaria,
          count(*) FILTER(WHERE s.suprimir) filas_cierre_conservador,
          sum((c.confirmados BETWEEN 1 AND 4)::INTEGER)
            +sum((c.fallecidos BETWEEN 1 AND 4)::INTEGER)
            +sum(coalesce((c.casos_nuevos BETWEEN 1 AND 4)::INTEGER,0))
            +sum(coalesce((c.fallecidos_nuevos BETWEEN 1 AND 4)::INTEGER,0)) celdas_1a4
          FROM v_control_divulgacion c JOIN dim_territorio d USING(territorio_id)
          JOIN paises s ON s.pais_id=c.pais_id
          WHERE d.pais='US' AND d.nivel='condado' AND d.poblacion<5000""").fetchdf().to_dict('records')[0]
        retrocesos = con.execute("""SELECT
          count(DISTINCT pais_id) FILTER(WHERE casos_nuevos<0) paises_casos_diarios,
          count(DISTINCT pais_id) FILTER(WHERE fallecidos_nuevos<0) paises_muertes_diarios,
          count(*) FILTER(WHERE casos_nuevos<0) dias_pais_casos,
          count(*) FILTER(WHERE fallecidos_nuevos<0) dias_pais_muertes,
          count(DISTINCT pais_id) FILTER(WHERE casos_nuevos<0 OR fallecidos_nuevos<0) paises_cualquier_retroceso,
          count(*) FILTER(WHERE casos_nuevos<0 OR fallecidos_nuevos<0) dias_pais_cualquier_retroceso
          FROM fact_pais""").fetchdf().to_dict('records')[0]
        retrocesos['serie_revisada_casos'] = con.execute("""WITH a AS (
          SELECT pais_id,confirmados-lag(confirmados) OVER(PARTITION BY pais_id ORDER BY fecha) cambio
          FROM fact_serie_pais) SELECT count(DISTINCT pais_id) paises,count(*) dias_pais
          FROM a WHERE cambio<0""").fetchdf().to_dict('records')[0]
        resultado = {'run':puntero['run'], 'estado':'OK','fuentes_hash_ok':len(manifiesto),
          'pruebas_integracion':len(checks), 'dw_completo':dw,'parquet_completo':parquet,
          'metodo_igualdad':'SHA-256 de lotes Arrow de 16384 filas ordenadas por archivo y registro, todos los campos',
          'balance':balance.to_dict('records'),'observaciones_multiples_cotejadas_con_csv':verificadas,
          'olap_filas':olap,'traza_chile_filas':len(traza),'divulgacion':metricas_divulgacion(con),
          'condados_us_poblacion_menor_5000':condados,'retrocesos':retrocesos}
    (out / 'verificacion_completa.json').write_text(json.dumps(resultado,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
    print(json.dumps(resultado,indent=2,ensure_ascii=False,default=str),flush=True)


if __name__ == '__main__':
    ejecutar()
