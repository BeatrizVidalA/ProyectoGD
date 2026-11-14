# Diccionario de la tabla unificada — Hito 2

Grano de `unificada`: **registro original territorial × fecha de reporte**, antes de
resolver duplicados. Se conservan 4.287.473 registros. En `fact_covid` el grano es
**territorio canónico × día**, único; las versiones contradictorias se separan en
cuarentena. No se debe equiparar ambos conteos.

`fila_origen` cuenta registros de datos, desde 1 después de la cabecera; no líneas
físicas del CSV. `archivo_origen` más `fila_origen` identifica cada observación.
El manifiesto guarda ubicación relativa, URL, bytes y SHA-256 de cada entrada.

| Campo unificado | Tipo Parquet | Significado / dominio | Origen JHU | Existe desde |
|---|---|---|---|---|
| region_pais | string | Nombre original de país o entidad; no necesariamente ISO | Country/Region, Country_Region | 22-ene-2020 |
| provincia_estado | string nullable | Provincia/estado o dependencia; ausencia no implica error | Province/State, Province_State | 22-ene-2020 |
| ultima_actualizacion | string ISO AAAA-MM-DD nullable | Fecha declarada de actualización; diferente del reporte | Last Update, Last_Update | 22-ene-2020 |
| confirmados | float64 nullable | Casos acumulados informados; negativos preservados y marcados | Confirmed | 22-ene-2020 |
| fallecidos | float64 nullable | Fallecidos acumulados; puede superar casos o ser negativo en ajustes | Deaths | 22-ene-2020 |
| recuperados | float64 nullable | Recuperados acumulados; cobertura deja de ser utilizable en 2021 | Recovered | 22-ene-2020 |
| latitud | float64 nullable | Grados; dominio esperado [-90,90] | Latitude, Lat | 1-mar-2020 |
| longitud | float64 nullable | Grados; dominio esperado [-180,180] | Longitude, Long_ | 1-mar-2020 |
| fips | string nullable | Identificador original; no convertir a entero ni inventar ceros | FIPS | 22-mar-2020 |
| admin2 | string nullable | Condado/unidad de segundo nivel, especialmente EE.UU. | Admin2 | 22-mar-2020 |
| activos | float64 nullable | Activos publicados; no se reconstruyen tras cesar recuperados | Active | 22-mar-2020 |
| clave_combinada | string nullable | Etiqueta territorial publicada; no es identificador estable suficiente | Combined_Key | 22-mar-2020 |
| tasa_incidentes | float64 nullable | Tasa publicada por JHU por 100.000; no se suma ni se usa como nuevos diarios | Incidence_Rate, Incident_Rate | 29-may-2020; cambia nombre 9-nov-2020 |
| tasa_letalidad | float64 nullable | Porcentaje publicado de fallecidos/casos; depende de detección y cobertura | Case-Fatality_Ratio, Case_Fatality_Ratio | 29-may-2020; cambia nombre 9-nov-2020 |
| fecha_reporte | date32 | Fecha del nombre MM-DD-AAAA.csv; calendario 22-ene-2020 a 9-mar-2023 | Nombre del archivo | Derivado para toda la historia |
| etapa | int16 | Esquema 1,2,3,4,5; se exige cabecera completa conocida | Cabecera del archivo | Derivado para toda la historia |
| ultima_actualizacion_original | string nullable | Texto íntegro, incluida hora; no se inventa zona horaria | Last Update, Last_Update sin modificar | Preservado para toda la historia |
| actualizacion_hora | string ISO nullable | Momento interpretado sin zona supuesta; error de conversión detiene carga | Campo anterior y formatos explícitos | Derivado para toda la historia |
| archivo_origen | string | Nombre del CSV que contiene la observación | Sistema de archivos / URL | Derivado para toda la historia |
| fila_origen | int32 | Número de registro después de cabecera, desde 1 | Posición dentro de CSV | Derivado para toda la historia |
| sha256_origen | string | Huella de los bytes originales, 64 dígitos hexadecimales | SHA-256 del archivo de entrada | Derivado para toda la historia |

## Dominios y ausencias

Las fechas de inicio indican existencia de la columna, no completitud de todas sus
celdas. `cobertura_columnas.csv` cuantifica vacíos de origen y ausencias estructurales
por campo y etapa. Se mantienen separados. Solo la cadena vacía se convierte en NA;
textos como `None` se conservan. La dimensión interpreta `None` en provincia como
marcador histórico nacional mediante una regla explícita, sin cambiar la observación.

Conteos se almacenan como float64 para representar nulos y ajustes originales sin
coerción silenciosa. Las reglas evalúan su dominio esperado; no recortan negativos.
Un formato numérico o temporal no interpretable detiene la carga con contexto.

## Campos analíticos y dimensiones

`dim_fecha`: fecha, año, mes, día, semana ISO y trimestre. La clave es fecha.

`dim_territorio`: `territorio_id` estable (`U:UID` o hash `H:` de una identidad histórica
no resuelta), `pais_id`, `padre_id`, UID, país, provincia, Admin2, nivel, ISO3 propio y
del país, población, coordenadas, dependencia y método de correspondencia. Los
valores UID provienen de su tabla maestra; no se propaga población nacional a regiones.
`fila_uid` permite volver a la fila de esa tabla. `iso3_oficial_formato` identifica
códigos declarados de tres letras con la excepción XKS; no sustituye un registro
ISO versionado. Kosovo se trata explícitamente como código estadístico.

`bridge_nombres_historicos` registra nombres originales, correspondencia, primera y
última fecha observada. Son intervalos de observación, no vigencias legales inferidas.
No se emparejan automáticamente nombres parecidos ni condados cuyo FIPS cambió de cobertura.

`fact_covid`: acumulados casos/muertes, nuevos diarios firmados, observación anterior,
distancia temporal, deltas desde ella y número de fuentes. Los primeros diarios y los
diarios tras una brecha quedan NULL; el delta de la brecha se conserva aparte.
`fact_pais` deriva totales sin superponer ancestros y descendientes. Una contradicción
o un componente no informado puede volver NULL el total; no se trata como cero.

`fact_serie_pais`: historia revisada de las series globales, separada de los reportes.
`linaje_series` conserva archivo, fila, métrica y hash; la fecha de la celda se obtiene
de la columna original m/d/aa. Series estadounidenses también se conservan en Parquet ancho.

`fact_vacunacion`: país × fecha; personas con al menos una dosis, esquema inicial
completo y porcentajes publicados; ISO3 de fuente, archivo, fila y hash. Sin interpolar.
`fact_indicador_anual`: país × año × indicador; SP.POP.65UP.TO.ZS para 2020–2022,
porcentaje de población de 65 años o más. Se conserva NULL cuando no hay dato.
