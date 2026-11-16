# Sala de Crisis COVID-19: Análisis y gestión de datos epidemiológicos

Proyecto del curso de Gestión de Datos. Construye una plataforma histórica de datos de COVID-19 para Chile y el mundo con Python, Pandas, PyArrow y DuckDB: unifica los reportes de Johns Hopkins University (JHU CSSE), los guarda en Parquet y los carga en un Data Warehouse con modelo en estrella, reglas de calidad y consultas OLAP. La exploración inicial usa Matplotlib y data-profiling.

El periodo cubierto va del 22 de enero de 2020 al 9 de marzo de 2023: 1.143 reportes diarios que cambian de formato cinco veces a lo largo de la serie. Los datos se leen del repositorio de [JHU](https://github.com/CSSEGISandData/COVID-19) y se complementan con la vacunación de OWID y la población de 65 años o más del Banco Mundial. Los recuperados dejan de publicarse en 2021: en esas fechas quedan vacíos en vez de cero.

## Requisitos

- Python 3.12
- El repositorio de JHU clonado en una carpeta `COVID-19` junto a este proyecto, o conexión a internet para descargar los CSV
- Cerca de 1 GB libre por cada carga del Hito 2

## Instalación

Desde la raíz del repositorio:

```bash
python -m venv .venv-hito1
```

Activar el entorno:

```bash
# macOS / Linux
source .venv-hito1/bin/activate

# Windows (cmd)
.\.venv-hito1\Scripts\activate

# Windows (PowerShell)
.\.venv-hito1\Scripts\Activate.ps1
```

Instalar las dependencias fijadas:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-hito2-lock.txt
```

Clonar los datos de JHU junto al proyecto, que es la ruta que usan ambos hitos por defecto:

```bash
git clone https://github.com/CSSEGISandData/COVID-19.git ../COVID-19
```

El `requirements.txt` de la raíz lista el stack previsto para todo el semestre. Para los Hitos 1 y 2 se usa `requirements-hito2-lock.txt`.

## Construir el Hito 2

Con el entorno activado, desde la raíz del repositorio:

```bash
python src/ejecutar_hito2.py construir --sin-red
```

Tarda unos minutos. Escribe los Parquet en `data/clean/hito2/<carga>/` y el DW en `data/dw/hito2/<carga>/covid.duckdb`, y solo si pasan todas las comprobaciones registra la carga en `data/hito2_actual.json`. Si el clon de JHU está en otra carpeta, agregar `--original RUTA`. Para descargar los archivos que falten en vez de usar el clon, cambiar `--sin-red` por `--solo-cache`.

Para validar la carga y ejecutar las pruebas:

```bash
python src/ejecutar_hito2.py validar
python -m unittest discover -s tests -v
python tests/verificar_cierre.py
```

Las consultas OLAP se lanzan con `python src/ejecutar_hito2.py consultar --consulta roll_up` (también `drill_down`, `slice` y `dice`). La documentación técnica, el diccionario de datos y los resultados están en [docs/](docs/).

## Cuadernos

El Hito 1 explora los reportes de enero a junio de 2020. Ejecutarlo con el intérprete del entorno virtual:

1. `notebooks/00_exploracion.ipynb`: lectura, estandarización, unificación, gráficos y perfilado.
2. `notebooks/00_exploracion.py`: el mismo análisis desde consola, con `python notebooks/00_exploracion.py`.

Los gráficos quedan en `data/figs/` y el perfilado en `data/profile/perfilado_exploracion.html`. Sin el clon de JHU, definir antes `COVID_HITO1_DESCARGAR=1` para que descargue los CSV.

## Estructura

- `notebooks/`: exploración del Hito 1.
- `src/ejecutar_hito2.py`: comandos `construir`, `validar`, `consultar` y `traza`.
- `src/plataforma/`: ingesta, normalización de esquemas, calidad, fuentes externas y Data Warehouse.
- `tests/`: pruebas automatizadas y verificación de la carga.
- `data/`: Parquet, DW, gráficos y reportes de calidad. Se generan localmente y no se suben al repositorio.
- `docs/`: diccionario de datos, arquitectura, calidad y revisiones de cada hito.
- `dashboard/`: reservado para el tablero del Hito 3; todavía no contiene una aplicación.
- `requirements-hito2-lock.txt`: versiones exactas para los Hitos 1 y 2.

## Problemas frecuentes

**PowerShell bloquea la activación.** Ejecutar una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y volver a activar el entorno.

**`ModuleNotFoundError` de `duckdb`, `pyarrow` o `pandas`.** El `pip` no es el del entorno virtual. Con el entorno activado: `python -m pip install -r requirements-hito2-lock.txt`.

**`No hay carga validada`.** Falta construir el Hito 2. Ejecutar `python src/ejecutar_hito2.py construir --sin-red` antes de `validar`, `consultar` o las pruebas.

**La construcción se detiene porque falta un CSV.** El clon de JHU no está en `../COVID-19`. Indicar la ruta con `--original RUTA` o usar `--solo-cache` para descargarlo.
