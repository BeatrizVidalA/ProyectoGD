# Extra — Restricciones (OxCGRT) y olas de casos (4-nov-2026)

Segunda fuente externa integrada al DW (además de vacunación OWID): el panel país-día de Oxford (tabla `restricciones`). Mide la respuesta de política «de jure» (stringency index, 0–100) — no el cumplimiento real — y **no** sostiene causalidad: las restricciones suelen responder a los casos (endogeneidad).

## Cobertura del cruce por ISO3

- 202,760 filas país-día; 185 países; 2020-01-01 a 2022-12-31 (cierra 68 días antes que JHU).
- **182/218 países del DW cruzan (83.5 %)** (Kosovo homologado RKS→XKS). Sin cruce OxCGRT→DW: BMU, TKM, VIR.
- Del lado JHU quedan 36 países sin panel de OxCGRT (microestados, territorios y algunos países sin datos de política): ARM, ATA, ATG, BLM, COK, COM, CUW, CYM, FSM, GGY, GIB, GLP, …

## Chile — restricciones y las cinco olas

| Ola (pico MA7 JHU) | Casos MA7 | Stringency ese día |
|---|---|---|
| 2020-06-17 | 10,310 | 81 |
| 2021-04-14 | 7,321 | 82 |
| 2022-02-13 | 35,656 | 29 |
| 2022-06-17 | 10,548 | 27 |
| 2022-11-10 | 7,052 | 14 |

- Índice máximo de Chile: **90.3 el 2020-07-03**; 482 días ≥ 70 (de 1,034 con dato).
- La relajación sostenida (media móvil 7 días ≤ 30) empieza el **2022-01-12**.
- Primera ola: el índice venía en 81 el día del pico de casos y en 90 cuatro semanas después; en ese mes los casos MA7 cayeron **-75 %**.
- Ómicron: el pico del 2022-02-13 llegó con un índice de 29 y ~87 % de población con vacunación completa (OWID): la ola más grande del país ocurrió con menos de la mitad del rigor de 2020.

## Comparación: Chile, Perú, EE.UU. y Brasil

| País | Máx. (fecha) | Media 2020 | Media 2021 | Media 2022 | Días ≥ 70 | Relajación ≤ 30 |
|---|---|---|---|---|---|---|
| Chile | 90.3 (2020-07-03) | 78.5 | 64.6 | 24.3 | 482 | 2022-01-12 |
| Perú | 96.3 (2020-05-01) | 81.9 | 63.2 | 30.2 | 341 | 2022-07-05 |
| EE.UU. | 75.5 (2020-11-16) | 60.6 | 56.4 | 31.7 | 165 | 2022-04-05 |
| Brasil | 81.0 (2020-05-05) | 67.2 | 59.7 | 28.4 | 213 | 2022-04-21 |

El máximo más alto es **Perú** (96.3) y el más bajo EE.UU. (75.5). La relajación sostenida ≤ 30 llega primero en Chile (2022-01-12) y último en Perú (2022-07-05). En los cuatro países las restricciones fueron la herramienta central de 2020 y se aflojaron de forma sostenida durante 2021–2022, mientras las olas de ómicron eran las mayores de la serie: política relajada y olas récord conviven — la vacunación y la vigilancia pasan a ser las herramientas críticas (ver P7 y R2).

## Lectura y límites

- Asociación descriptiva, **no causal**: el índice sube porque hay casos y baja porque la situación lo permite; ambas series se mueven juntas por diseño.
- «De jure»: codifica lo anunciado, no su cumplimiento; la comparación entre países puede reflejar estilos de reporte.
- Cobertura 2020-01-01 a 2022-12-31 y metodología variable en el tiempo (diferenciación por vacunación): exigen leer las cifras como contexto, no como experimento.
