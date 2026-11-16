# Balance de registros originales y hechos del DW

Los **4.287.473 registros normalizados** y los **4.287.333 hechos** tienen granos
distintos. El primero representa cada observación publicada; el segundo una clave
**territorio canónico × fecha** con acumulados de casos y fallecidos coherentes.
La normalización conserva todos los registros originales.

| Tratamiento | Claves | Observaciones de origen | Hechos resultantes | Diferencia |
|---|---:|---:|---:|---:|
| Clave simple | 4.287.315 | 4.287.315 | 4.287.315 | 0 |
| Consolidación coherente | 18 | 36 | 18 | 18 |
| Cuarentena por conflicto | 61 | 122 | 0 | 122 |
| **Total** | **4.287.394** | **4.287.473** | **4.287.333** | **140** |

**4.287.473 − 122 − 18 = 4.287.333.** No hay otras filas excluidas por calidad,
negativos, falta de población o falta de coordenadas. Esos problemas se conservan
y se marcan. La agregación nacional produce otra tabla, `fact_pais`; no explica
la diferencia de 140 filas de `fact_covid`.

## Qué se consolida y qué se excluye del hecho

La correspondencia territorial explícita puede reunir dos nombres/representaciones
de un territorio en la misma fecha. Una clave con dos observaciones iguales en
**casos y fallecidos, incluidos sus nulos**, genera un hecho con `n_fuentes=2`.
No se exige que los 21 campos originales sean idénticos: otros campos permanecen
en `unificada` y en su procedencia. Tampoco se suman los dos acumulados.

Si casos o fallecidos discrepan, o uno es NULL y el otro no, se pone la clave
completa en cuarentena: ninguna versión se acepta en `fact_covid`.
`grupos_observados.versiones` es un indicador 1/2 de coherencia/conflicto, no el
número de valores distintos. Sus mínimos sirven de diagnóstico; nunca eligen
un conteo supuestamente verdadero entre versiones contradictorias.

Ejemplos comprobados sobre los registros de origen:

- `01-23-2020.csv`, registros 10 y 14: Hubei, `U:15613`, 444 casos y 17 muertes
  en ambos. Se representan con un hecho y dos vínculos de origen.
- `02-28-2020.csv`, registros 99 y 144: North Ireland y United Kingdom / Northern
  Ireland corresponden a `U:82602`, pero informan 1 y 0 casos. Ambos se conservan
  normalizados; la clave queda en cuarentena y no se selecciona ninguno.

`fila_origen` cuenta registros de datos desde 1 después de la cabecera, no líneas
físicas de texto. Las claves múltiples contienen **158 observaciones** en total:
36 coherentes más 122 contradictorias. El verificador las coteja una por una con
los CSV, incluidos casos, muertes y hashes, no solo con una tabla derivada.

## Cómo encontrar exactamente todas las observaciones

Cada carga produce en `data/quality/hito2/<carga>/`:

- `balance_filas.csv`: las tres categorías y su balance.
- `balance_detalle.csv`: las **158 observaciones**, con ID, fecha, archivo,
  registro, SHA-256, nombres originales, conteos y decisión.
- `cuarentena.csv`: las 61 claves conflictivas.

La misma auditoría se reproduce con:

```powershell
& .\.venv-hito1\Scripts\python.exe tests/verificar_cierre.py
```

Escribe su evidencia en `data/quality/cierre_hito2/`. La
[verificación resumida](verificacion_cierre_hito2.json) registra la carga,
el balance y la comparación de contenido completo Parquet/DW. El detalle se
conserva localmente; no es necesario subir copias de registros crudos a GitHub.

En SQL, `v_linaje` conecta observaciones con `grupos_observados`; `aceptada` explica
la decisión. Se verifican unicidad de observación, cobertura del mapa y que
`sum(n_fuentes)` reproduzca la tabla normalizada. Las comprobaciones adicionales
exigen exactamente 61 claves/122 observaciones conflictivas y 18 consolidaciones
para esta instantánea histórica. Si cambian las entradas, no se oculta el cambio:
la carga debe revisarse antes de actualizar esos valores esperados.
