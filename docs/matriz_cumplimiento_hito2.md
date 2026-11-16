# Matriz detallada de cumplimiento del Hito 2

Contraste del enunciado 2026-2, sección 3, páginas 4–6 y rúbrica A páginas 8–9,
con PPT, diapositivas 13–15 y calendario ajustado de la 23. Estado de ejecución y
carga seleccionada: [revisión de cierre](revision_hito2.md). «Validado localmente»
se refiere al conjunto disponible y las pruebas indicadas; no certifica una nota.

| Requisito | Implementación y evidencia | Estado / trabajo posterior |
|---|---|---|
| R1: obtención reproducible de 1.143 diarios | `ingesta.Entradas`, calendario de `normalizacion.escribir_diarios`, CLI `construir`; inventario/manifiesto | Implementado; recorrido local completo. HTTP probado con muestras, no con caché totalmente vacío |
| R1: series y UID | Cinco series Parquet, 4.321 UID; series US por lotes y validación de 1.143 fechas | Procesado en carga completa |
| R1: cinco esquemas, snake_case y fechas ISO | Cabeceras exactas en `ESQUEMAS`, normalización tipada, prueba de rechazo desconocido | Cinco etapas y conteos por etapa verificados |
| R1: capa cruda | Originales de solo lectura más caché y manifiesto URL/ruta/hash | Verificados 1.151 hashes; crudos fuera de Git |
| R1: Parquet y DW | Parquet por año, DuckDB por carga, publicación de versión | Comparación de todos los campos/filas por huella ordenada, más conteos y sumas |
| R1: CSV/Parquet | `validacion.benchmark`, misma tabla tipada de 10.000 filas, cinco lecturas alternadas | Bytes y tiempos medidos; caché caliente y muestra, sin generalizar velocidad |
| R1: motor frente a NoSQL | DuckDB frente a MongoDB en `arquitectura_hito2.md` | Justificación documentada para ventanas, joins, grano e integridad |
| R1: reproducción | README: entorno, Hito 1, Hito 2, validación y consultas | Comandos ejecutados en este equipo; no se probó otro equipo o Colab |
| R1 excelente: equivalente nube y costo, o ejecución nube | `arquitectura_nube.md`, Fargate + S3 + publicación versionada; tarifas oficiales y supuestos | Alternativa documental preparada; no desplegada ni facturada |
| R2: diccionario completo | 21 campos, significado/tipo/dominio/origen/fecha desde, `diccionario_datos.md` | Documentado y contrastado con esquema normalizado |
| R2: seis dimensiones, umbrales y estados | `calidad.ejecutar`, `reglas_calidad` y resumen | 14 reglas: 4 OK y 10 alertas de origen |
| R2: retrocesos, brechas, rezagos e inconsistencias | Reglas, `brechas_territorio`, `candidatos_rezago`, reconciliación | Cuantificados; candidatos a rezago no prueban causalidad |
| R2: índice país y decisiones | `calidad_pais`; seis componentes, cobertura y tratamiento por problema | Índice 0–100 comprobado; concordancia JHU es proxy de exactitud |
| R2: duplicados y diferencia origen/hecho | `auditoria.balance_filas`, `detalle_balance`, 158 registros cotejados | 122 observaciones conflictivas excluidas del hecho y 18 consolidadas; todas preservadas normalizadas |
| R2 excelente: linaje | `v_linaje`, `v_linaje_rollup`, manifiesto, linaje series y externas, CLI `traza` | Archivo/registro/hash disponibles; derivaciones futuras del tablero deben propagar esa procedencia |
| R3: estrella, grano territorio × día | `fact_covid`, `dim_fecha`, `dim_territorio` | Claves únicas y relaciones comprobadas; PK de hechos lógica, validada por SQL |
| R3: acumulados y nuevos diarios | Ventanas de fecha previa, deltas firmados y brechas NULL | Primer diario y deltas consecutivos comprobados; no se recortan negativos |
| R3: jerarquías y población | Padres/país, UID y puente de nombres históricos | Integridad de padres/país comprobada; 178 identidades históricas sin UID y población faltante señalada |
| R3: Chile y agregación | Nacional hasta 19-may-2020; regiones + Unknown desde 20-may; sin doble suma | Pruebas sobre cambio real, conteos regionales y totales a junio/último día |
| R3: una externa por ISO3 y motivos | OWID por país/fecha, `paises_cruce.csv` y `tasas_cruce.csv` | 190/202, 94,06 %; equivalencia Kosovo documentada |
| R3: OLAP en DW | Cuatro consultas de `almacen.OLAP` y CLI | Roll-up, drill-down, slice y dice ejecutados, sin consultar CSV |
| R3 excelente: segunda externa o historia territorial | Banco Mundial anual y puente histórico | 194/202, 96,04 %; dos fuentes sin multiplicación de hechos y cambio Chile probado |
| R6: argumento Ley 19.628 y Ley 21.719 | Fuentes BCN versionadas, distinción agregado/personal e identificación indirecta | Documentado con vigencia; criterio técnico de supresión, no obligación legal inventada |
| R6: identificar celdas pequeñas y aplicar regla | `v_control_divulgacion`, `v_publica_territorio`, `v_publica_segura`, `v_publica_pais` | Backend comprobado, incluidas fronteras y nulos; aplicación visual pendiente Hito 3 |
| R6: advertencias | Letalidad/testeo, revisiones, denominadores y cautela causal | Documentadas; deben mostrarse en la interfaz futura |
| R6 excelente: condados US y pérdida | 317 UID pequeños, 316 observados, 321.444 filas; medición de celdas/filas | Backend aplicado y medido; cierre conservador tiene pérdida alta |

## Límites que no se ocultan

La descarga completa por HTTP desde cero no se ejecutó; el recorrido de los datos
disponibles sí. La propuesta nube satisface la alternativa de diseño/costo sin
afirmar despliegue. Las alertas históricas permanecen; no son fallos de ejecución
que se «corrijan» inventando datos. R6 del entregable final requiere aplicar la
supresión en el tablero: ese componente visual sigue pendiente y no se califica
como completado aquí. Consultar la revisión para las incidencias de ejecución y
sus códigos de salida, además de las pruebas numéricas.
