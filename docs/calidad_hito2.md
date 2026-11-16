# Calidad y gobierno — Hito 2

## Cifras de retrocesos y producto de origen

La serie global revisada presenta descensos de confirmados en **84 países y
171 días-país**. No es el mismo producto que los CSV diarios publicados en cada
fecha. En los totales nacionales derivados de esos reportes se observan descensos
de casos en **159 países / 350 días-país** y de muertes en **111 / 272**;
la unión es **166 países y 536 días-país**. No se suman 350 y 272 como si fueran
días distintos: ambas métricas pueden retroceder el mismo día.

La diferencia entre productos incluye revisiones retrospectivas, cobertura e
identidades/granularidad históricas. Se conservan ambos productos separados;
no se fuerzan los reportes a reproducir la cifra 84 de las series revisadas.
Estas cifras describen los datos, no un descenso demostrado de contagios reales.

Las reglas de `src/plataforma/calidad.py` corren automáticamente en cada carga.
`reglas_calidad.csv` registra dimensión, descripción, valor, operador, umbral, estado
y limitación. OK satisface el umbral, ALERTA lo incumple y NO_EVALUABLE requiere
información adicional. Alertas de los datos originales no se ocultan ni equivalen
a errores técnicos del pipeline. Los errores técnicos abortan la publicación.

## Reglas y decisiones

| Dimensión | Qué se mide | Umbral |
|---|---|---|
| Completitud | Reportes y conteos casos/muertes informados | 1.143 y fracción ≥0,999 |
| Unicidad | Repeticiones adicionales de clave canónica | 0 |
| Validez | Acumulados negativos, coordenadas fuera de rango, población/ISO/coordenadas faltantes | 0 casos para cada regla |
| Consistencia | Muertes mayores que casos y retrocesos país/día | 0 |
| Exactitud | Acuerdo de acumulados con historia revisada de series | ≥0,99 de comparaciones conocidas |
| Oportunidad | Huecos entre primera/última aparición, actualización próxima al reporte, candidatos a rezago | 0 huecos, ≥0,95 actualizados y 0 candidatos |

Los umbrales son criterios académicos explícitos, no estándares clínicos. Un pico
de al menos 100 nuevos casos tras seis días de incrementos cero y calendario
consecutivo es un **candidato** a rezago: no confirma su causa. Una frecuencia semanal
legítima también lo activa. No se redistribuyen sus casos a días inventados.

`cobertura_columnas.csv` separa vacíos publicados y columnas aún inexistentes.
`brechas_territorio` mide días sin fila entre observaciones de una misma identidad;
no supone existencia anterior a su primera observación. El índice nacional usa
presencia de reportes país, sin confundir retiro de una unidad histórica con falta
de un archivo global. El cese de recuperados no se imputa ni se usa como cero fiable.

Los conflictos se conservan en crudo y se excluyen del hecho utilizable. Repeticiones
con casos/muertes iguales se consolidan solo en el hecho y conservan varios orígenes.
No se corrigen automáticamente negativos, muertes superiores a casos o desacuerdos
con series. Metadatos no disponibles excluyen tasas/mapas, no los acumulados crudos.

## Índice por país

Seis componentes entre 0 y 1, con el mismo peso:

- C = 1 − celdas faltantes casos/muertes / (2 × filas originales).
- U = 1 − repeticiones adicionales canónicas / filas originales.
- V = 1 − filas con acumulado negativo o coordenada numérica fuera de rango / filas.
- S = promedio de (1 − filas con muertes > casos / filas) y
  (1 − días nacionales con retroceso de casos o muertes / días nacionales utilizables).
- E = 1 − discrepancias casos/muertes / comparaciones conocidas con series.
- O = promedio de cobertura de días entre primera/última aparición y fracción de
  actualizaciones entre fecha_reporte −7 y fecha_reporte +1.

Índice = 100 × promedio de los componentes disponibles. Si E no es evaluable, se
promedian cinco componentes; se informa el número de comparaciones para evitar
interpretar ausencia de referencia como calidad perfecta. Los denominadores y
componentes se conservan en `calidad_pais`, junto con conteos y días sin reporte.

Es un índice **descriptivo y relativo a estas reglas**: no mide subregistro, calidad
del sistema de salud, exceso de mortalidad o verdad epidemiológica. E es un proxy
de concordancia: ambas representaciones provienen de JHU y no son independientes.
Last_Update tampoco prueba el tiempo real de publicación. Repetir cifras viejas
puede parecer completo y no ser oportuno; los candidatos a rezago complementan,
pero no resuelven, esa limitación.

El volumen de filas por país cambia con su granularidad: los pesos por fila influyen
en C/U/V/S. Por ello se muestran también conteos, componentes y decisiones, no solo
un ranking. Ningún país se excluye de todos los análisis por un umbral del índice.
