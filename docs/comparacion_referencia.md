# Comparación técnica con el proyecto de referencia

Revisión inicial del 14-nov y contraste de cierre del 16-nov-2026. Proyecto oficial: ProyectoGD, rama Beatriz. Referencia
consultada en solo lectura: `Gestion/Proyecto_GD`; no se ejecutaron sus notebooks
ni su dashboard, porque contienen descargas, instalaciones y escrituras.

## Qué contiene la referencia

Se inspeccionaron seis notebooks (tres originales y tres optimizados), README,
dependencias, configuración Streamlit y módulos `data.py`, `metrics.py`, `main.py`
y `ui.py`. También se inventariaron CSV, perfilado, PNG y dos Parquet existentes.
El material académico incluido corresponde a 2025-II, no al encargo 2026-2 actual.
Las salidas guardadas de algunos notebooks no certifican una reproducción actual.

| Aspecto | Referencia | Proyecto oficial / decisión |
|---|---|---|
| README | Requisitos → instalación → ejecución → notebooks → estructura → problemas frecuentes | Se adopta esa secuencia y claridad, con contenido propio hasta Hito 2 |
| Organización | Separación datos, métricas e interfaz Streamlit | Se conserva la modularidad propia por ingesta, normalización, territorio, DW, calidad y validación |
| Ventanas | Limpieza de enero 2021 y análisis semestral; algunos textos dicen 2020 mientras el código usa 2021 | Se exige el inventario completo de 1.143 reportes y se comprueba cada esquema |
| Identificadores | Los notebooks de limpieza eliminan FIPS, Admin2, coordenadas y Combined_Key | No se adapta: perjudicaría jerarquía, mapas, unicidad y linaje |
| Tiempo | Se utiliza Last_Update como fecha analítica en varios análisis | No se adapta: se usa fecha del archivo y se conserva actualización por separado |
| Nulos | Hay fillna(0) al convertir casos y fallecidos | No se adapta: no informado y cero tienen significados diferentes |
| Acumulados | Un ranking semestral suma Confirmed entre fechas | No se adapta: cuenta repetidamente los mismos acumulados |
| Diarios | metrics.py recorta diferencias negativas con clip(lower=0) y rellena algunos primeros valores | No se adapta: se conservan correcciones firmadas y primer diario NULL |
| Benchmark Dask | Una medición cronometra read_csv antes de compute | No se adapta: tiempo de construcción diferida y lectura materializada no son comparables |
| Recuperados | El dashboard distingue ausencia de reporte y muestra avisos | Idea comunicacional útil para Hito 3; no se copió su transformación ni se derivan activos aquí |
| Perfilado y Parquet | Artefactos exploratorios existentes | Se conserva nuestro perfilado Hito 1 y se generan capas completas propias; no se copian resultados |
| DW e integración | No se encontraron estrella, seis dimensiones ejecutables ni cruces OWID/BM en los módulos revisados | No sustituye los mínimos R1–R3 del enunciado actual |
| Pruebas | No se encontraron pruebas automatizadas en los archivos inventariados | Se conservan y amplían pruebas propias sobre registros reales y casos límite |
| Visualización | Componentes de tarjetas, filtros y avisos Streamlit/Plotly | Se describen como posible inspiración futura; no se desarrolla el dashboard en esta etapa |

## Reutilización y atribución

La mejora incorporada es **organizacional y documental**: orden de secciones,
comandos desde la raíz, dependencias separadas, explicación de módulos y sección
de problemas frecuentes. Los comandos del README se ajustan a nuestros ejecutores,
entorno y datos; no se copian nombres, cifras o afirmaciones de la referencia.

No se copió código, estilos, gráficos, datos ni dependencias del ejemplo. No se
encontró un archivo LICENSE/COPYING en la copia inspeccionada; por eso tampoco se
asume autorización para redistribuir sus módulos. La referencia se reconoce como
inspiración de presentación, no como evidencia académica de nuestra implementación.

No se añadió Dask, Streamlit, GeoPandas ni mapas: no resuelven un requisito pendiente
de la plataforma que justifique ampliar dependencias en esta etapa.

## Comparación directa de los README

Ubicación comprobada de la referencia:
`C:\Users\beaaa\OneDrive\Documents\Gestion\Proyecto_GD\README.md`.
Se leyó íntegramente. Las líneas siguientes corresponden a esa copia local, no
a una URL de GitHub inventada. La versión consultada queda identificada por SHA-256
en el inventario local `data/quality/cierre_hito2/protegidos_antes.json`.
SHA-256 del README consultado:
`36ba76ed244537139eea4d9b58352afdf95712241182bcb45a801f490545ecd4`.

| Orden | Sección del ejemplo y línea inicial | Adaptación en nuestro README |
|---|---|---|
| 1 | Título y descripción, línea 1 | Sala de crisis COVID-19, objetivo y ventana JHU; alcance hasta Hito 2 |
| 2 | Requisitos, línea 7 | Python, Windows, clon/caché y memoria realmente utilizados |
| 3 | Instalación, línea 12 | Entorno, dependencias fijadas y preparación de PowerShell en tres pasos |
| 4 | Ejecutar el dashboard, línea 49 | Ejecutar el Hito 1 y Ejecutar el Hito 2; no se inventa un dashboard |
| 5 | Notebooks, línea 61 | Notebook propio, alternativa `.py` y pipeline de consola, con su relación explícita |
| 6 | Estructura, línea 71 | Lista de archivos/módulos reales y función de cada uno |
| 7 | Problemas frecuentes, línea 82 | Mismo formato de síntoma en negrita y solución concreta; cierre de la guía |

El ejemplo utiliza un título H1, seis encabezados H2, párrafos breves, listas,
una lista numerada para notebooks y bloques de comandos con lenguaje. **No tiene
tablas, imágenes, badges ni diagramas Mermaid.** Su claridad viene de dar los
comandos desde la raíz, separar dependencias de dashboard/notebooks y explicar
por qué importa la ruta exacta `dashboard/main.py`.

Nuestro README sigue esa secuencia inicial y conserva problemas frecuentes al
final. Utiliza listas de módulos como el ejemplo, bloques PowerShell y pasos
numerados. Entre estructura y problemas frecuentes añade las secciones que exige
el enunciado actual: arquitectura, calidad, DW/externas, resultados, protección y
estado por hito. Las dos tablas de resultados/avance y el diagrama Mermaid son
añadidos propios; no se atribuyen al ejemplo. Se eliminó la apariencia de inventario
técnico al comienzo y se trasladó el detalle de auditoría a documentos enlazados.

## Evidencia concreta en código y notebooks de referencia

Los índices de celda se cuentan desde cero sobre el JSON `.ipynb`; permiten ubicar
el código sin depender de números de línea variables del archivo serializado.

| Archivo y ubicación | Hallazgo revisado | Decisión |
|---|---|---|
| `01_limpieza_datos.ipynb`, celda 9 | `drop` de FIPS, Admin2, Lat, Long_ y Combined_Key | No copiar: perdería identificadores, geografía y jerarquía R1–R3 |
| `01_limpieza_datos_optimizado.ipynb`, celdas 5 y 10 | Cronómetro de `dd.read_csv` antes del posterior `compute()` | No usar como medición equivalente de lectura materializada |
| `02_analisis_exploratorio.ipynb`, celdas 0 y 3 | Texto enero–junio 2020, carga de 2021 | No trasladar fechas ni resultados |
| Mismo notebook, celda 6 | `fillna(0)` para casos y muertes | Conservar nulos originales en nuestro pipeline |
| Mismo notebook, celda 9 | Suma semestral de `Confirmed` para ranking | Usar acumulado de una fecha o diarios sobre un intervalo |
| Mismo notebook, celda 17 | Agrupación por Last_Update para curva de Chile | Usar fecha del archivo; conservar Last_Update por separado |
| `dashboard/metrics.py`, línea 31 | Diferencias con `clip(lower=0)` | No borrar correcciones negativas |
| `dashboard/data.py`, líneas 27–40 | Separación de recuperados sin reporte y caché de una hora | Idea de comunicación/caché para Hito 3; sin copiar implementación |
| `dashboard/main.py`, líneas 136–166 | Cobertura de recuperados y aviso «Sin publicación» | Explicar cobertura al mostrar métricas futuras |
| `dashboard/ui.py`, líneas 284–308 | Ayuda, avisos y separación de interfaz | Organización útil futura; sin estilos ni app copiados |
| `03_visualizaciones.ipynb` y versión optimizada | Gráficos y mapas exploratorios | No sustituyen OLAP, estrella ni las exigencias del tablero futuro |

También se revisaron `requirements.txt`, `requirements-notebooks.txt`,
`.streamlit/config.toml` y el enunciado 2025-II incluido en la referencia. El PDF
2026-2 y PPT propios gobiernan esta entrega. No se ejecutó código del ejemplo;
la comparación es estática y no certifica que su dashboard funcione actualmente.
