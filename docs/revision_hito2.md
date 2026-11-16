# Revisión técnica del Hito 2

Proyecto Sala de crisis COVID-19. Cierre de revisión: 16-nov-2026.
Rama comprobada: `Beatriz`. Carga publicada localmente:
`20261116T170938Z_a1af38`, identificada por `data/hito2_actual.json`.

## 1. Estado inicial y alcance

Existían la exploración del Hito 1 y módulos propios del Hito 2 para ingesta,
normalización, calidad, DW y externas. Su existencia no demostraba una carga
completa exitosa. La revisión encontró problemas de memoria, agregación jerárquica,
tratamiento de nulos en divulgación y evidencia de reproducción insuficiente.
Se conservaron las implementaciones útiles y se corrigieron sus fallos.
Se revisaron el enunciado, el PPT, documentación, pruebas y proyecto de referencia.
No se implementaron Hito 3, dashboard ni pronósticos.

## 2. Proyecto de referencia y reutilización

Se inspeccionaron seis notebooks, cuatro archivos del dashboard, README,
dependencias y PDF de la referencia, siempre en modo de lectura.
Su separación de módulos, instrucciones y problemas frecuentes sirve de guía
de presentación. La comparación detallada está en
[comparacion_referencia.md](comparacion_referencia.md).

No se adoptaron sus transformaciones: eliminar identificadores y coordenadas,
usar Last_Update como fecha del reporte, rellenar ausencias con cero, recortar
correcciones negativas o sumar acumulados durante un semestre altera el significado
histórico. Tampoco se tomó como benchmark una medición de operaciones diferidas
sin materializarlas. No se copiaron código, cifras, resultados ni dependencias.
No se encontró archivo de licencia; la adaptación se limita a organización del
README y contenido redactado para este proyecto.

## 3. Archivos intervenidos

| Archivo o conjunto | Cambio |
|---|---|
| `src/plataforma/almacen.py` | Hechos, consolidación, jerarquías, linaje acotado y supresión nula segura |
| `src/plataforma/externas.py` | Series por lotes Arrow, externa opcional tipada y motivos de cruce |
| `src/plataforma/pipeline.py` | Memoria acotada, manifiesto, finalización reanudable y publicación atómica |
| `src/plataforma/validacion.py` | 50 comprobaciones, incluyendo balance, jerarquías y divulgación |
| `src/plataforma/auditoria.py` | Balance exhaustivo de filas y detalle de todas las claves múltiples |
| `src/plataforma/__main__.py` | CLI, reanudación y consultas con memoria acotada |
| `tests/test_hito2.py` | Nueve pruebas; se añadió matriz de fronteras de población y conteos |
| `tests/verificar_cierre.py` | Verificación completa de hashes, Parquet/DW, registros múltiples, OLAP y condados |
| `tests/verificar_descarga.py` | Prueba HTTP optativa con evidencia separada |
| `README.md` | Reproducción, arquitectura, resultados, límites y preguntas frecuentes |
| `docs/` | Comparación concreta, arquitectura nube/costo, balance, calidad, ética y evidencias de cierre |
| `ROADMAP.md` | Sustitución de pendientes Hito 2 desactualizados por estado real |
| `.gitignore`, `requirements-hito2-lock.txt`, `contribuciones.md` | Exclusión de artefactos, entorno fijado y asistencia declarada |

El código y notebook del Hito 1 se conservaron; se regeneraron sus salidas al
comprobar regresión. Los datasets y resultados grandes quedan locales e ignorados.
Este inventario describe el trabajo de revisión, no atribuye toda diferencia
preexistente de Git a esta sesión.

En esta continuación se añadieron `src/plataforma/auditoria.py`,
`tests/verificar_cierre.py`, `docs/arquitectura_nube.md`,
`docs/balance_filas_hito2.md`, `docs/matriz_cumplimiento_hito2.md` y los extractos
de tarifas/verificación. Se actualizaron README, ROADMAP, contribuciones,
arquitectura, protección, comparación, revisión y resúmenes; en código,
`almacen.py`, `pipeline.py`, `validacion.py`, `__main__.py` y `test_hito2.py`.
Los cambios anteriores de ingesta/normalización y externas se conservaron.
Se actualizó únicamente PyArrow de 24.0.0 a 25.0.1 en `.venv-hito1`, con
autorización para el ajuste local. DuckDB permanece en 1.5.6 y el Python global
no se modificó; se conservaron las versiones previas en la evidencia local.

## 4. Errores corregidos y decisiones

- Se evitó construir índices masivos y contar estructuras distintas sobre millones
  de filas; la unicidad e integridad lógica se verifican explícitamente por SQL.
- Se sustituyeron agregaciones correlacionadas por joins de igualdad y selección
  de niveles. Un subtotal y sus condados no se suman dos veces.
- Las series estadounidenses se convierten por lotes Arrow; no se materializan
  millones de strings en Pandas.
- Las discrepancias de una misma clave quedan en cuarentena. Los mínimos/máximos
  de diagnóstico no seleccionan arbitrariamente una versión para el hecho.
- La supresión distingue un diario NULL de una celda pequeña y cuenta las métricas
  no nulas correctamente. El linaje solicitado materializa solo su ámbito.
- La ausencia de Banco Mundial conserva un esquema tipado y no rompe OWID.
- La conexión configura un hilo y 128 MB desde su apertura. El checkpoint se
  consume y el puntero solo se publica **después de cerrar DuckDB**; un fallo
  nativo de cierre no debe seleccionar una carga nueva.
- En el cierre se reemplazó el autojoin de millones de hechos al medir pérdida
  por una unión con los pocos países afectados. Conserva la política de supresión
  y reduce el trabajo y memoria; no se modifican los conteos históricos.
- Se puede retomar la fase final con `construir --sin-red --retomar ID`:
  verifica hashes, conteos y sumas Parquet/DW, repite controles y solo después
  publica el puntero. Un directorio parcial no equivale a una carga validada.

## 5. Ejecución y resultados reproducidos

La carga seleccionada ejecutó el recorrido completo desde la ingesta local,
sin `--retomar`, y terminó con **código de salida 0**. El resumen registra
174,47 segundos hasta finalizar las comprobaciones. Se procesaron todos los
datos disponibles; no se volvió a descargar toda la historia por HTTP.

| Objeto | Registros |
|---|---:|
| Reportes diarios | 1.143 |
| Tabla normalizada | 4.287.473 |
| Grupos territoriales observados | 4.287.394 |
| `fact_covid` | 4.287.333 |
| `dim_territorio` | 4.499 |
| `dim_fecha` | 1.143 |
| `fact_pais` | 220.580 |
| `fact_serie_pais` | 229.743 |
| `fact_vacunacion` | 133.346 |
| `fact_indicador_anual` | 582 |
| Reconciliaciones | 220.578 |

Hay 1.151 entradas con procedencia: diarios, cinco series, UID y dos externas.
Los cinco esquemas aportan respectivamente 39, 21, 68, 164 y 851 archivos.
La tabla normalizada conserva todas las filas. Hay 79 repeticiones adicionales
de clave canónica: 61 claves contradictorias ponen 122 filas en cuarentena y
18 repeticiones con conteos iguales se consolidan. Balance del hecho:
4.287.473 − 122 − 18 = 4.287.333. Se conservan los vínculos a los originales.
De los territorios, 4.321 tienen UID y 178 son identidades históricas sin UID.

### Pruebas y regresión

- **9/9 pruebas automatizadas aprobadas**, incluyendo fronteras de divulgación.
- **50/50 comprobaciones de integración aprobadas** sobre la carga completa:
  esquema, conteos, claves, relaciones, deltas, jerarquías y joins externos.
  [Detalle exportado](pruebas_hito2.csv).
- Se ejecutaron roll-up, drill-down, slice, dice y traza. El drill-down final de
  Chile reúne 17 regiones, incluyendo Unknown: 5.192.286 casos y 64.273 muertes.
- Se probaron seis descargas HTTP reales: una por esquema y UID; coincidieron
  tabularmente con los originales. No se descargaron nuevamente los 1.143 CSV.
- Hito 1: ejecución secuencial exitosa del `.py`, 161 archivos, 350.945 filas,
  19 columnas, gráficos y perfilado. El notebook conserva 10 celdas ejecutadas
  sin errores. Una ejecución simultánea agotó memoria; se repitió por separado
  con éxito. El README prescribe ejecución secuencial con poca RAM.

### Calidad y reconciliación

Las 14 reglas cubren seis dimensiones: **4 OK y 10 ALERTA**. Son hallazgos de los
datos, separados de las pruebas de funcionamiento. Se detectaron 6 acumulados
negativos, 10.777 filas con fallecidos mayores que casos, 536 días-país con
retrocesos, 175 días-país sin fila entre extremos observados y 1.589 candidatos
a rezago. No se inventan observaciones ni se recortan negativos.
La completitud de conteos es 99,9946 %. Faltan población positiva para 273
territorios y coordenadas para 270. No hay coordenadas numéricas fuera de rango.

La concordancia con las series revisadas es 98,6391 %; hay 4.069 diferencias de
casos y 1.932 de muertes. Es un proxy de acuerdo entre productos JHU, no exactitud
epidemiológica independiente. El índice país pondera por igual seis componentes;
si no hay comparador de exactitud promedia los cinco disponibles y lo informa.
Ver [reglas y limitaciones](calidad_hito2.md).

### Fuentes externas y rendimiento

OWID cruza **190/202 (94,06 %)** países/entidades observados y Banco Mundial
**194/202 (96,04 %)**, sin multiplicar hechos. El denominador incluye entidades
históricas y especiales. OWID cubre 2-dic-2020 a 9-mar-2023 en la ventana usada;
el indicador de población de 65+ tiene 582 registros, 194 países y años 2020–2022.
Las ausencias tienen motivos en `paises_cruce.csv`. Kosovo usa equivalencias
explícitas XKS/OWID_KOS/XKX; no son tres códigos ISO oficiales equivalentes.

Benchmark de la misma tabla tipada: 10.000 filas, 21 columnas, 2.000 por esquema.
CSV: 2.411.174 bytes; Parquet ZSTD: 278.682 bytes. Cinco lecturas alternadas tras
calentamiento dieron medianas de 0,006358 s y 0,004314 s, respectivamente, sin afirmar superioridad general. Los diarios completos
ocupan 591.001.942 bytes originales y 265.432.895 bytes Parquet normalizados;
estos últimos añaden campos de procedencia, por lo que no son esquemas idénticos.
[Resumen y versiones](resultados_hito2.json).

## 6. Matriz de cumplimiento

La [matriz detallada por requisito](matriz_cumplimiento_hito2.md) contrasta cada
punto del enunciado con módulos, evidencia y límites; esta tabla es su resumen.

| Requisito | Estado comprobado | Evidencia y límite |
|---|---|---|
| R1: ingesta, cinco esquemas, series, UID, capas y benchmark | Implementado y validado localmente | 1.143 diarios; Parquet/DW concordantes; equivalente AWS y presupuesto documentados; descarga HTTP completa desde cero no repetida |
| R2: seis dimensiones, índice, anomalías, reconciliación y trazabilidad | Implementado y validado localmente | 14 reglas; cuarentena y linaje; exactitud es proxy y persisten alertas de origen |
| R3: estrella, diarios, jerarquías, Chile, externas y OLAP | Implementado y validado localmente | 50 comprobaciones, dos externas y cuatro consultas; 178 identidades históricas sin UID y cobertura incompleta |
| R6: protección y ética | Backend y documentación validados; visualización pendiente | Leyes contrastadas, fronteras probadas, pérdida medida en condados; aplicación visual y permisos corresponden al futuro dashboard |

Esto describe evidencia técnica, no garantiza una calificación ni sustituye la
revisión del profesor. La arquitectura y justificación DuckDB frente a NoSQL están
en [arquitectura_hito2.md](arquitectura_hito2.md); los campos en
[diccionario_datos.md](diccionario_datos.md).

## 7. Protección y nivel excelente pendiente

Se evaluaron 4.287.333 filas. La supresión primaria afecta 165.064; hay 1.606.713
celdas entre 1 y 4 y 317 condados UID con población menor a 5.000. El cierre
conservador de `v_publica_segura` oculta 3.850.612 filas (aproximadamente 89,8 %)
y 15.391.755 celdas no nulas: su pérdida de utilidad es elevada.
La vista primaria es diagnóstica; las vistas no implementan permisos ni hacen
publicables automáticamente las tablas internas. Ver
[proteccion_etica_hito2.md](proteccion_etica_hito2.md).

Para aspirar a excelencia: revisar alertas y equivalencias históricas con evidencia,
mejorar supresión secundaria sin reconstrucción y con menor pérdida, validar en
otro equipo, revisar la propuesta de nube si se decide desplegar y preparar el ZIP
académico con Parquet y DW seleccionados. Dos fuentes externas ya están integradas;
su mera presencia no prueba excelente calidad ni responde P7.

## 8. README, restricciones y siguiente etapa

El README sigue la organización práctica del ejemplo: requisitos, instalación,
pasos numerados, módulos y problemas frecuentes. Añade arquitectura real, tres
capas, consultas, pruebas, resultados, matriz enlazada, limitaciones y estado por
hito. Todos sus resultados se refieren a esta carga; no presenta el dashboard
ni Hito 3 como terminados. Los nombres del equipo quedan sujetos a documentación
en `contribuciones.md`.

Se trabajó en el proyecto oficial y rama Beatriz. No se hicieron commits, push,
merge ni cambios de rama; se conservaron el código del proyecto, datos y entregables anteriores. El clon JHU y la
referencia se usaron únicamente como entradas de lectura.

Quedan para Hito 3: respuestas P1–P7 con evidencia, segmentación, pronóstico y
backtesting, evaluación de alertas, dashboard con protección integrada, ensayo
e informes finales. EVA y la calificación final no se verificaron.

## 9. Evidencia adicional de cierre solicitada el 16-nov

La [comparación directa de README](comparacion_referencia.md) registra el orden
real de las seis secciones del ejemplo, líneas iniciales, formato visual y
correspondencia con nuestro README. También identifica notebooks por celda y
módulos por línea. No se atribuyen tablas ni diagramas al ejemplo: son añadidos
propios para los requisitos de 2026-2.

El [balance completo](balance_filas_hito2.md) separa 4.287.315 claves simples,
18 claves coherentes con 36 observaciones y 61 claves conflictivas con 122
observaciones. Se cotejaron las 158 observaciones múltiples directamente con los
CSV. El archivo local `balance_detalle.csv` identifica todas las fechas, archivos,
registros y hashes; no queda una exclusión de filas sin categoría.

La [verificación completa](verificacion_cierre_hito2.json) compara la huella
SHA-256 del contenido de las 4.287.473 filas y 21 campos, ordenados por archivo y
registro y serializados en lotes Arrow del mismo tamaño. Es una comprobación
criptográfica completa de Parquet/DW, además de los conteos y sumas de integración.
Verifica también que las 1.151 fuentes mantienen sus hashes.

El [presupuesto AWS](arquitectura_nube.md) usa tarifas oficiales consultadas y
supuestos explícitos: 10 horas/mes de tarea 2 vCPU/8 GB, 10 GB-mes S3, solicitudes
e IPv4; subtotal 1,463248 USD y reserva de 2 USD, presupuesto redondeado 3,47 USD/mes.
No representa una factura ni recursos desplegados. Cubre la alternativa documental
de R1 excelente sin afirmar una ejecución en nube.

La [evaluación de divulgación](proteccion_etica_hito2.md) distingue 317 condados
pequeños en UID y 316 con hechos observados: 321.444 filas, 142.759 con supresión
primaria y 163.532 celdas 1–4. El cierre conservador oculta las 321.444 filas de
ese subconjunto. La identidad UID sin observaciones se nombra explícitamente;
no se inventan datos para completar la tabla maestra.

### Qué queda cerrado y qué requiere trabajo posterior

- **Plataforma del Hito 2:** ingesta local completa, cinco esquemas, capas,
  calidad, balance, estrella, dos externas, OLAP y controles backend de protección.
- **Extensiones documentadas:** arquitectura equivalente en nube y costo;
  trazabilidad y cambios de granularidad; pérdida de divulgación en condados.
- **Validación no realizada:** descarga HTTP de toda la historia desde caché vacío,
  ejecución en otro equipo/Colab, despliegue en nube y acceso compartido en EVA.
- **Hito 3:** integración visual de supresión y advertencias, pruebas de filtros
  y exportaciones del dashboard, P1–P7, minería, predicción y alerta. Por eso no
  se declara cumplido el R6 completo del entregable final ni se asigna nota.

El README representa la implementación hasta Hito 2 y separa esos pendientes.
Los resúmenes numéricos son archivos compartibles; los datos crudos, detalles de
ejecución y binarios de las cargas siguen locales según `.gitignore`.

## 10. Incidencia nativa encontrada y validación posterior

Las primeras reconstrucciones completas con PyArrow 24.0.0 y DuckDB 1.5.6
alcanzaban las 50 comprobaciones, pero terminaban al cerrar la conexión con
**−1073740791 / 0xC0000409**. También se reprodujo fuera del aislamiento del
ejecutor, por lo que no se atribuye el fallo a ese aislamiento.

Se corrigió la secuencia de publicación para cerrar primero la conexión, se
utilizaron buffers Arrow al registrar tablas y se redujeron autojoins innecesarios.
Esos ajustes por sí solos no eliminaron la incidencia. Tras el ajuste local
autorizado a **PyArrow 25.0.1**, manteniendo DuckDB 1.5.6, la reconstrucción completa
`20261116T170938Z_a1af38` terminó con **código 0**, sin reanudación ni salidas forzadas.
La verificación independiente posterior también terminó con código 0.

La [nota oficial de Arrow 25.0.1](https://arrow.apache.org/blog/2026/08/10/25.0.1-release/)
documenta correcciones nativas de mimalloc. Es un antecedente compatible con el
síntoma, no una identificación forense de la causa exacta de este caso.
No se ocultan los intentos fallidos ni se deduce éxito solo de un JSON impreso.

Las evidencias quedan en `data/quality/cierre_hito2/`: registros `pipeline_*.log`,
`pruebas_pyarrow25.log`, `verificacion_pyarrow25.log`, regresión del Hito 1 y
comandos CLI. El archivo `requirements_antes_ajuste.txt` conserva el entorno previo;
`requirements-hito2-lock.txt` fija el entorno final reproducido. No hizo falta
instalar DuckDB 2 ni modificar los DW anteriores.

### Comprobación final del entorno actualizado

La [comprobación de entrega](comprobacion_cierre_hito2.json) registra código 0
para pipeline, verificación independiente, regresión Hito 1, cuatro OLAP y traza.
Las nueve pruebas automatizadas y 50 comprobaciones de integración pasaron;
`pip check` no detectó dependencias incompatibles. Se comprobaron nuevamente
**2.460 archivos protegidos**, incluidos JHU, referencia y los dos fuentes del
Hito 1: ninguna diferencia de SHA-256 ni archivo ausente.

No quedaron enlaces locales rotos en README/documentación. Los cinco enlaces
externos del README respondieron HTTP 200. Se revisó visualmente una vista HTML
renderizada del README, incluidos acentos, comandos y tablas; no se publicó en
GitHub durante la revisión. Los dos diagramas utilizan sintaxis Mermaid compatible
con GitHub. Los intentos fallidos se conservan localmente y la entrega debe usar
solo la carga seleccionada por `data/hito2_actual.json`.
