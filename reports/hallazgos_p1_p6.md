# Hallazgos P1–P6 — Sala de crisis COVID-19 (4-nov-2026)

## P1 — Chile vs Sudamérica

| País | Casos/100.000 | Fallecidos/100.000 |
|---|---|---|
| Uruguay | 29,775 | 219.3 |
| Chile | 27,162 | 336.2 |
| Argentina | 22,225 | 288.7 |
| Brasil | 17,445 | 329.0 |
| Perú | 13,610 | 665.8 |
| Colombia | 12,498 | 279.7 |
| Paraguay | 11,334 | 278.7 |
| Bolivia | 10,231 | 191.6 |
| Ecuador | 5,992 | 204.1 |
| Venezuela | 1,942 | 20.6 |

**Olas de Chile (picos MA7 casos/día):**

- 2020-06-17: MA7 = 5,999 casos/día
- 2021-04-14: MA7 = 7,321 casos/día
- 2022-02-13: MA7 = 35,656 casos/día
- 2022-06-17: MA7 = 10,548 casos/día
- 2022-11-10: MA7 = 7,052 casos/día

**Síntesis:** Chile registra 27,162 casos y 336.2 fallecidos por 100.000 — 2.º país de Sudamérica en incidencia acumulada, tras Uruguay (29.775) y por delante de Argentina (22.225); Perú lidera la mortalidad aparente (666/100.000) por la reconciliación de 2021; Chile ocupa el 2.º lugar con 336/100.000. La ola más letal fue la primera: 310 fallecidos/día MA7 el 2020-07-23 (tras el pico de casos del 2020-06-17); la de mayor magnitud fue ómicron (2022-02-13, ~35.700 casos/día MA7, ~150 fallecidos/día MA7).

## P2 — Regiones de Chile (desde junio 2020)

| Región | Casos/100.000 | Fallecidos/100.000 | Posición (fallec./100k) |
|---|---|---|---|
| Magallanes | 40,225 | 467.8 | 1 |
| Metropolitana | 26,604 | 434.8 | 2 |
| Arica y Parinacota | 35,124 | 399.9 | 3 |
| Los Rios | 38,451 | 367.4 | 4 |
| Valparaiso | 27,043 | 356.7 | 5 |
| Tarapaca | 33,948 | 355.8 | 6 |
| Antofagasta | 29,877 | 323.6 | 7 |
| Maule | 33,112 | 321.9 | 8 |
| Los Lagos | 29,234 | 311.1 | 9 |
| Biobio | 32,725 | 310.1 | 10 |
| OHiggins | 24,218 | 309.0 | 11 |
| Araucania | 30,578 | 307.2 | 12 |
| Coquimbo | 27,836 | 287.0 | 13 |
| Nuble | 33,062 | 279.0 | 14 |
| Atacama | 40,460 | 249.5 | 15 |
| Aysen | 35,235 | 215.2 | 16 |

**Biobío** ocupa el puesto **10** de 16 regiones en fallecidos por 100.000 (310.1/100.000) desde junio de 2020 — en línea con su incidencia (32.725 casos/100.000, puesto 8). Magallanes (468/100.000) y Metropolitana (435/100.000) lideran la mortalidad aparente; Metropolitana concentra además el mayor volumen absoluto (9.144 fallecidos en 2021).

## P3 — Letalidad aparente antes y después de la vacunación

**Chile — CFR acumulada hasta enero 2021 (pre-vacunación): 2.54 %; desde junio 2021 (vacunación masiva): 0.92 %.**

La CFR aparente cayó con la vacunación (de ~2–5 % en 2020 a <1 % en 2022), pero parte de la caída es mecánica: creció el testeo (ómicron detectó muchos más casos leves). Por eso la comparación usa fallecidos por 100.000 y no solo la razón muertes/casos. Los días de corrección masiva se excluyen del numerador/denominador mensual (Chile 2022-03-21: +11.447 fallecidos de la revisión del registro; Perú 2021-06-02: artefacto de transición; 2022-05-23: corrección global); ellos sí se conservan en los acumulados publicados. Los picos de CFR de 2021-07/08 reflejan la revisión del registro de fallecidos repartida en semanas (Chile) y la reconciliación de actas (Perú 2021-04→07). El repunte final de Perú es un artefacto de sub-reporte de casos al final del período, no un aumento real de letalidad; ver diccionario §5.

## P4 — Confiabilidad de los datos de cada país

Los 10 países con peor índice de calidad (de R2; ver diccionario §5):

| País | Índice | Retrocesos | Días con gap >7d | Fallecidos>casos | Negativas | CFR>100 |
|---|---|---|---|---|---|---|
| USA | 34.0 | 54746 | 0 | 7125 | 3 | 1347 |
| COL | 64.1 | 234 | 1 | 508 | 4 | 3 |
| PER | 65.8 | 466 | 0 | 13 | 0 | 3 |
| BEL | 69.5 | 18 | 0 | 348 | 0 | 348 |
| PRK | 70.0 | 0 | 0 | 300 | 0 | 299 |
| NLD | 71.4 | 300 | 0 | 64 | 0 | 1 |
| CAN | 78.7 | 51 | 0 | 1039 | 0 | 0 |
| GBR | 79.3 | 26 | 0 | 1377 | 0 | 0 |
| DEU | 88.0 | 454 | 0 | 0 | 0 | 0 |
| MEX | 89.4 | 390 | 1 | 0 | 0 | 0 |

**Decisiones:** (1) los retrocesos se conservan y se marcan (`retroceso_*`), nunca se borran ni se anclan a cero; (2) los días de corrección masiva (2022-05-23) se excluyen de promedios y modelos; (3) `deaths>confirmed` se marca sin corregir (Reino Unido jun-2020; Perú jun-2021); (4) las filas negativas crudas (7) se excluyen de análisis; (5) para tasas y rankings se usan países con población conocida; los `especial` no entran en comparaciones.

## P5 — Grupos de países con pandemias parecidas

El enunciado permite agrupar por forma de la curva o por indicadores. La forma pura (incidencia semanal normalizada por el máximo, k-means) resultó homogénea en todo el mundo (silueta 0,09–0,10: todos los picos convergen en ómicron). Se usaron en cambio **indicadores**: log₁₀ de casos y fallecidos por 100.000, log₁₀ de la CFR aparente, proporción de casos en 2020 y en 2022+, y número de olas (picos MA7 con prominencia ≥10 % del máximo, distancia ≥120 días). k=3 elegido por silueta (0.325); 131 países con ≥100.000 casos.

| Grupo | Países | Casos/100k medio | Fallecidos/100k medio | CFR % | Cuota 2022 | Países (muestra) |
|---|---|---|---|---|---|---|
| 0 | 54 | 15,236 | 231.2 | 1.50 | 37 % | ALB, ARE, ARG, ARM, AZE, BGR |
| 1 | 26 | 1,248 | 19.2 | 1.41 | 22 % | AFG, AGO, BGD, CHN, CMR, DZA |
| 2 | 51 | 39,520 | 164.8 | 0.41 | 68 % | AUS, AUT, BEL, BHR, BRB, BRN |

**Chile queda en el grupo 0** (América Latina + Europa del Este + EE.UU.): pandemias de olas múltiples con CFR aparente alta (~1–2 %), donde el esfuerzo de 2020–2021 quedó eclipsado por ómicron en volumen pero no en mortalidad.

## P6 — ¿Se podía anticipar la ola de ómicron en Chile?

Backtesting en tres cortes (horizonte 14 días; MAE y MAPE):

| Corte | MAE base | MAPE base | MAE Holt | MAPE Holt |
|---|---|---|---|---|
| 2020-09-15 | 267.62 | 18.85 % | 262.57 | 17.2 % |
| 2021-03-15 | 1593.91 | 24.73 % | 1474.94 | 23.68 % |
| 2021-12-01 | 564.21 | 42.29 % | 451.03 | 25.69 % |

**Ómicron no era extrapolable 14 días antes** (corte 2021-12-01: la curva era plana; MAPE 25.69 %). La alerta —no el modelo puntual— sí la detectó: primera señal el **2021-11-11**, **94 días antes** del pico (2022-02-13); segunda señal el 2022-01-04, 40 días antes.

**Alerta temprana en la historia de Chile** (umbral: variación semanal MA7 ≥ +30 % e incidencia ≥ 6/100.000):

- Activaciones: 16; falsas alarmas estrictas: 1 (2020-07-26).

- Ola 2020-06-17: primera alerta 2020-05-06 (42 días de anticipación; 2 activaciones).

- Ola 2021-04-14: primera alerta 2021-01-04 (100 días de anticipación; 3 activaciones).

- Ola 2022-02-13: primera alerta 2021-11-11 (94 días de anticipación; 2 activaciones).

- Ola 2022-06-17: primera alerta 2022-05-09 (39 días de anticipación; 3 activaciones).

- Ola 2022-11-10: primera alerta 2022-09-23 (48 días de anticipación; 3 activaciones).

- Alzas menores sin ola mayor asociada: 2021-10-17, 2023-02-25.
