# Propuesta de P7 — Pregunta propia del equipo

## Cómo elegimos la pregunta

P7 debe relacionar los **casos** con una **fuente externa** registrada en el enunciado
(OWID, OxCGRT o Banco Mundial), cruzando por código ISO3, y distinguir
**correlación de causalidad**.

- Nuestro P3 usará **OWID (vacunación)**: es la vía natural para letalidad aparente
  antes/después de vacunar.
- Para P7 elegimos una fuente que la preparación y la discusión del Comité explotan bien:
  la **demografía** de los países.

## P7 (propuesta principal)

> **¿Los países con una mayor proporción de población de 65 años o más registraron una
> mortalidad por COVID-19 más alta por 100.000 habitantes?**

- **Fuente externa:** Banco Mundial, indicador `SP.POP.65UP.TO.ZS` (API
  `api.worldbank.org/v2`), vía código ISO3.
- **Llave de cruce:** ISO3 de la tabla UID ↔ código de país del Banco Mundial.
  Informaremos cuántos territorios cruzan y cuáles quedan fuera y por qué
  (microterritorios sin código del Banco Mundial, p. ej. Diamond Princess, MS Zaandam).
- **Qué se espera ver:** scatter de mortalidad acumulada por 100.000 (a fines de 2022)
  vs. % de 65+, agrupando por región del mundo; correlación con y sin controles básicos
  (PIB per cápita, que integra camas hospitalarias si el tiempo lo permite).
- **Advertencia metodológica:** correlación **no** implica causalidad: la proporción de
  65+ confunde con nivel de desarrollo, testeo y calidad del registro civil. Un país con
  buen testeo detecta más fallecidos; eso también explica la asociación. Comparables no
  son necesariamente comparados.

## Variante de respaldo (si el cruce con el Banco Mundial complica)

> **¿Los países que impusieron restricciones más severas (Oxford COVID-19 Government
> Response Tracker, índice `StringencyIndex`) tuvieron menor incidencia 14 días después?**
> Fuente: `github.com/OxCGRT/covid-policy-dataset`, llave `CountryCode` = ISO3.
> Diseño: correlación rezagada por semana; misma advertencia de causalidad.

## Decisión esperada

P7 principal con el **Banco Mundial**; P3 con **OWID**; así integramos **dos fuentes
externas** (nivel excelente de R3) sin duplicar el mismo cruce.
