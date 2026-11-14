# Revisión del Hito 1 · Exploración guiada

**Fecha:** 11-nov-2026. **Alcance:** solo enero–junio de 2020.
**Estado técnico:** seis tareas implementadas, ejecutadas y validadas. Notebook y
archivo .py finalizan correctamente con datos locales. El cierre administrativo
(roles nominales, publicación y EVA) sigue pendiente de evidencia del equipo.

## Base académica y trabajo conservado

El PDF, sección 3, pide seis tareas exploratorias y P7 propuesta. La presentación
reprograma Hito 1 al 10-nov; EVA no se consultó. Se conservan los análisis iniciales,
la propuesta P7, todos los CSV y todas sus filas. No se restauraron versiones Git.

Antes de editar había modificaciones locales en el notebook y su alternativa .py.
La copia local tenía 22 celdas sin ejecución ni salidas. El commit 4ba7f5d conserva
23 celdas y 14 celdas de código ejecutadas sin errores; esto demuestra una ejecución
histórica, pero no valida automáticamente la versión corregida.

## Tabla de las seis tareas

| Tarea | Implementación y evidencia | Validación actual |
|---|---|---|
| 1. Primer CSV | Primeras filas, dimensiones, tipos e interpretación | Datos comprobados: 76 × 6 |
| 2. Nulos | Conteos, interpretación y cobertura estructural separada | Conteos comprobados; no se imputan ceros |
| 3. Estandarización | Nombres, fecha ISO, fecha de reporte, timestamp original y FIPS texto | Conversiones de los 161 archivos verificadas; controles de error aprobados |
| 4. Unificación | Inventario, esquemas, SHA-256, archivo/fila y conflictos conservados | 161 archivos; 350.945 × 19; sin pérdida de filas |
| 5. Ranking y Chile | Ranking y dos gráficos con ejes y unidades; Chile sin superponer niveles | Cumplida; dos PNG revisados visualmente y embebidos en el notebook |
| 6. Perfilado | Perfilado automático obligatorio y tres observaciones concretas | Cumplida; HTML regenerado y contrastado con los resultados |

El notebook se genera de las celdas marcadas con # %% del .py. Sus celdas de código
deben coincidir exactamente. No se usa una segunda implementación de las funciones.

## Resultados comprobados en memoria

| Esquema | Archivos | Filas |
|---|---:|---:|
| 1 | 39 | 4.242 |
| 2 | 21 | 5.555 |
| 3 | 68 | 217.486 |
| 4 | 33 | 123.662 |
| Total | 161 | 350.945 |

En enero–junio hay cuatro esquemas y tres transiciones (1-mar, 22-mar y 29-may),
no cuatro cambios. La clasificación distingue también el esquema 5, sin cargar
su período. Hay 14 campos JHU normalizados, fecha de reporte, etapa y tres campos
adicionales: ultima_actualizacion_original, archivo_origen y fila_origen.
Fila de origen significa registro de datos después de la cabecera, no línea física.

- Primer CSV: provincia 12 nulos; confirmados 10; fallecidos y recuperados 37 cada
  uno (48,68%); país y actualización sin nulos.
- Conversiones de fecha y número inválidas: 0; actualizaciones vacías: 0.
- 245.916 filas tienen fecha de actualización distinta de fecha de reporte.
- FIPS conserva texto. Se comprobó un identificador con cero inicial (01001).
- Tres repeticiones adicionales de la llave fecha–país–provincia–Admin2; una fila
  idéntica adicional. La igualdad exacta excluye archivo/fila para no ocultarlas.
- Conflictos: Hubei 23-ene; New Zealand 26-feb; District of Columbia 22-mar.
  El último tiene 102 casos y fallecidos contradictorios (0 y 2). No se elimina nada.
- 1.357 filas con fallecidos mayores que confirmados; cero acumulados negativos
  de confirmados o fallecidos en esta ventana. Se describen, no se corrigen.

### Nulidad y conservación de texto

Las 16 columnas comparables tienen 633.181 celdas nulas (11,2763574%). La versión
anterior informaba 633.184: Pandas interpretaba automáticamente tres textos None
como NA (provincia de Lebanon 21-feb, Iraq 23-feb y Austria 25-feb). Ahora se conservan
esos textos. El redondeo a dos decimales sigue siendo 11,28%.
En las 19 columnas actuales la nulidad es 9,4958799%; el denominador cambió.
La tabla de cobertura comprueba: nulos unificados = ausencia estructural + vacíos
presentes en el CSV. No se debe confundir porcentaje menor con mejora de calidad.

### Ranking y Chile

| Posición | País o entidad JHU | Confirmados al 30-jun |
|---|---|---:|
| 1 | US | 2.653.658 |
| 2 | Brazil | 1.412.669 |
| 3 | Russia | 646.929 |
| 4 | India | 585.493 |
| 5 | United Kingdom | 314.157 |
| 6 | Peru | 285.213 |
| 7 | Chile | 279.393 |
| 8 | Spain | 249.271 |
| 9 | Italy | 240.578 |
| 10 | Iran | 227.662 |

Se suman acumulados solo dentro de una fecha y según las agrupaciones JHU.
Denmark, France, Netherlands y New Zealand tienen territorio principal y dependencias
separadas: una fila sin provincia no equivale al total agregado de sus dependencias.
Estas filas se muestran antes del ranking. No se hace armonización ISO ni se afirma
que los conteos absolutos comparen riesgo entre países.

Chile: primera fila el 3-mar; nacional hasta 19-may; 16 regiones más Unknown desde
20-may, durante 42 días de esta ventana. Se verificó que nunca coexistan la fila
nacional y sus regiones. Al 30-jun hay 279.393 casos y 5.688 fallecidos.
El gráfico validado separa casos y fallecidos en dos paneles, sin multiplicar
muertes por diez. Los períodos sin datos se mantienen como huecos.

## Ejecución integral y reproducibilidad

Se creó el entorno local .venv-hito1 con autorización del usuario, sin modificar el
Python global. La carpeta está excluida de Git. La instalación terminó correctamente
y pip check informó que no hay requisitos incompatibles.

| Componente | Versión validada |
|---|---|
| Python | 3.12.14, Windows x64 |
| Pandas | 2.3.3 |
| NumPy | 2.5.4 |
| Matplotlib | 3.11.2 |
| nbconvert / nbclient | 7.17.2 / 0.11.0 |
| nbformat / ipykernel | 5.11.1 / 7.4.0 |
| fg-data-profiling | 4.20.0; import data_profiling |

requirements-hito1.txt contiene las dependencias directas; requirements-hito1-lock.txt
registra las versiones exactas y transitivas del entorno validado. El requirements.txt
original del stack futuro se conserva sin cambios.

### Procedimiento y evidencia

1. Se compararon los 161 CSV locales con los originales: igualdad tabular completa.
2. Se probaron rechazo de fecha inválida, número inválido y cabecera desconocida,
   preservación de FIPS con cero inicial y conservación del texto de actualización.
3. Se verificó la detección de raíz desde proyecto, notebooks y carpeta contenedora.
4. Se ejecutó el notebook completo mediante nbconvert con el kernel hito1 del entorno
   local: 21 celdas totales, 10 celdas de código, contadores 1 a 10 y cero errores.
5. Se estableció YDATA_PROFILING_NO_ANALYTICS=1 para deshabilitar la telemetría
   del perfilador. La versión final se volvió a ejecutar
   completa después de este cambio.
6. Se ejecutó también notebooks/00_exploracion.py: salida 0 y todas las comprobaciones
   aprobadas. Los dos PNG son idénticos por SHA-256 a los producidos por el notebook.
7. Se revisaron visualmente ambos PNG: títulos, ejes, leyendas y unidades legibles;
   Chile tiene paneles separados y una marca del cambio territorial del 20-may.
8. Se comprobó el HTML automático: 350.945 observaciones, 19 variables (9 texto,
   10 numéricas), 633.181 celdas faltantes y ninguna variable no soportada.
9. Los PNG del notebook están embebidos y coinciden con los archivos guardados.
   Las celdas de código coinciden con la fuente .py.
10. Se verificó integridad SHA-256 de 2.434 archivos del clon original, excluyendo
    .git, y 161 CSV de caché: ninguno fue modificado, eliminado o agregado.

Ambas ejecuciones finales usaron exclusivamente la caché local, con descarga de
datasets deshabilitada. Los resultados anteriores se regeneraron con el código
corregido; no se copiaron salidas históricas ni se inventaron resultados.
Jupyter emitió avisos de infraestructura de Windows/ZMQ; no hubo errores de celda.

**Reproducible localmente con caché:** sí, en el entorno validado y siguiendo README.
No se probaron Colab, descarga desde caché vacía ni otros sistemas operativos.
La copia del repositorio original solo se consulta; no recibe salidas ni cachés.

## Pendientes administrativos y límites

Faltan nombres reales, atribución individual, evidencia de publicación y acceso
GitHub para docente/ayudante y confirmación EVA. La P7 existente es admisible y
no se modificó. No se hicieron commits, push, merge ni cambios de rama.

No se implementaron ingesta de tres años, Parquet, DW, integración externa, reglas
de seis dimensiones, índice de calidad, nuevos diarios, pronóstico, alertas o tablero.
La resolución de duplicados y reconciliación entre series y reportes quedan para
Hito 2. Los controles exploratorios no acreditan R1–R8 completos.
