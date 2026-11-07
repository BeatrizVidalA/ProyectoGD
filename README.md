# Sala de Crisis · COVID-19 — Proyecto Semestral GD 2026-2 (IN1232C)

Plataforma de datos sobre el registro histórico de COVID-19 de Johns Hopkins
([CSSEGISandData/COVID-19](https://github.com/CSSEGISandData/COVID-19), 22-ene-2020 · 9-mar-2023),
con análisis de Chile y el mundo, pronóstico de 14 días, alerta temprana y tablero
interactivo para el Comité Asesor de Preparación Pandémica.

## Equipo y roles

| Rol | Responsabilidad principal | Integrante |
|---|---|---|
| Ingeniería de datos | R1 ingesta, capas crudo/limpio/analítico, DW (R3) | *(completar nombre)* |
| Calidad y gobierno | R2 diccionario, reglas ejecutables, índice de calidad | *(completar nombre)* |
| Análisis y minería | R4 análisis histórico, R5 segmentación y pronóstico | *(completar nombre)* |
| Tablero y comunicación | R7 tablero, R8 informe al Comité, R6 ética | *(completar nombre)* |

> Todos revisamos el trabajo de todos: en el Comité el panel pregunta a cualquier integrante.

## Estructura del repositorio

```
notebooks/           Análisis (.ipynb + .py para VS Code) en orden de ejecución
src/                 Código reutilizable (ingesta, calidad, DW, modelos…)
data/raw/            Datos crudos descargados (NO se suben al repo)
data/clean/          Capa limpia (Parquet)
data/dw/             Data Warehouse (DuckDB)
data/figs/           Gráficos PNG generados por `00_exploracion.py` (no se suben)
docs/                P7 propuesta, diccionario de datos, informes PDF
dashboard/           Tablero (Streamlit / .pbix) y capturas
contribuciones.md    Quién hizo qué y declaración de uso de IA generativa
```

## Cómo reproducir desde cero

Requisitos: Python 3.11 o 3.12.

1. Clonar el repositorio:
   ```
   git clone <url-del-repo> && cd <repo>
   ```
2. Crear y activar un entorno virtual:
   ```
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS / Linux
   ```
3. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```
4. Ejecutar los notebooks en orden numérico:
   ```
   jupyter nbconvert --to notebook --execute --inplace notebooks/00_exploracion.ipynb
   jupyter lab
   ```
   El primer notebook **descarga automáticamente** los reportes diarios que necesita
   (enero–junio 2020) a `data/raw/`; no hay que bajarlos a mano. En
   [Colab](https://colab.research.google.com) el mismo notebook funciona sin cambios
   (las rutas se resuelven solas).
   Alternativa sin Jupyter: `python notebooks/00_exploracion.py` (genera dos gráficos en
   `data/figs/` y el perfilado en `data/profile/`).

## Fuentes de datos

| Fuente | Contenido | Uso |
|---|---|---|
| JHU CSSEGISandData/COVID-19 | 1.143 reportes diarios, series temporales, tabla UID | Datos principales |
| Banco Mundial (API) | Población 65+, PIB per cápita, camas hospitalarias | P7 (propuesta) |
| OWID vaccinations | Vacunación diaria por país | P3 |

Descarga por URL «raw» de GitHub, **sin clonar** el repositorio (pesa por su historial).

## Estado del proyecto

| Hito | Fecha (calendario PPT ajustado) | Estado |
|---|---|---|
| Lanzamiento | Mié 4 nov | ✅ Repositorio y roles (nombres por completar) |
| Hito 1 · Explorar | Mar 10 nov | ✅ Notebook `00_exploracion` ejecutado (350.945 filas, 0 errores) + P7 propuesta |
| Test 3 | Mié 11 nov | — |
| Hito 2 · Plataforma | Mar 17 nov | ⏳ Pendiente (ingesta 1.143 reportes, Parquet, calidad, DW) |
| Hito 3 + ensayo | Mié 18 nov | ⏳ Pendiente |
| Sesión del Comité | Mar 24 nov | ⏳ Pendiente |
| Entrega final (EVA) | Mié 25 nov, 23:59 | ⏳ Pendiente |

> Las fechas están ajustadas según el PPT respecto del PDF del enunciado; en caso de
> diferencia, manda EVA.
