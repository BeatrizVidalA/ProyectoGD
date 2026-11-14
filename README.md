# Sala de Crisis · COVID-19 — Proyecto Semestral GD 2026-2 (IN1232C)

El objetivo final es una plataforma histórica de COVID-19 con análisis, pronóstico,
alerta y tablero para el Comité. **El trabajo actual se limita al Hito 1:** exploración
del 22-ene al 30-jun-2020. Parquet, DW, integración externa, minería y tablero
son trabajo futuro; no están implementados.

## Equipo y roles

| Rol | Responsabilidad principal | Integrante |
|---|---|---|
| Ingeniería de datos | R1 ingesta, capas crudo/limpio/analítico, DW (R3) | *(completar nombre)* |
| Calidad y gobierno | R2 diccionario, reglas ejecutables, índice de calidad | *(completar nombre)* |
| Análisis y minería | R4 análisis histórico, R5 segmentación y pronóstico | *(completar nombre)* |
| Tablero y comunicación | R7 tablero, R8 informe al Comité, R6 ética | *(completar nombre)* |

> Todos revisamos el trabajo de todos: en el Comité el panel pregunta a cualquier integrante.

## Estado y archivos del Hito 1

- `notebooks/00_exploracion.ipynb`: seis tareas cumplidas, ejecutadas en orden y con salidas guardadas.
- `notebooks/00_exploracion.py`: las mismas celdas y explicaciones en formato `# %%`.
- `data/raw/daily_reports/`: caché de 161 CSV; no se modifica al reutilizarla.
- `data/figs/`: dos gráficos PNG regenerables.
- `data/profile/perfilado_exploracion.html`: perfilado automático regenerable.
- `docs/revision_hito1.md`: resultados, comprobaciones y límites.
- `docs/P7_propuesta.md`: propuesta académica; todavía no hay integración externa.

La tabla exploratoria conserva 350.945 filas y ahora tiene **19 columnas**: las 16
anteriores más `ultima_actualizacion_original`, `archivo_origen` y `fila_origen`.
No se eliminan duplicados ni se imputan conteos. `src/` solo contiene `.gitkeep`;
`dashboard/` contiene una descripción. `data/clean/` está vacía y no se genera en este hito.

## Cómo ejecutar la exploración

1. Abrir una terminal en `proyecto gestion/`. El repositorio disponible es local;
   no se ha verificado su publicación ni un enlace GitHub del equipo.
2. Usar Python 3.12. El entorno local `.venv-hito1` ya fue creado y validado con autorización.
   Para preparar otro entorno Windows con las mismas versiones, usar `requirements-hito1-lock.txt`.
   `requirements-hito1.txt` enumera las dependencias directas del hito con rangos de versión.
   El `requirements.txt` original se conserva como stack previsto para el proyecto
   completo. La instalación necesita autorización en una sesión asistida. Si se
   prepara manualmente un entorno nuevo en Windows:

   ```powershell
   python -m venv .venv-hito1
   .\.venv-hito1\Scripts\python.exe -m pip install -r requirements-hito1-lock.txt
   .\.venv-hito1\Scripts\python.exe -m ipykernel install --prefix .venv-hito1 --name hito1 --display-name "Python (Hito 1)"
   ```

3. Ejecutar todas las celdas, en orden, desde Jupyter o VS Code, seleccionando ese
   intérprete. Para ejecución por consola:

   ```powershell
   .\.venv-hito1\Scripts\python.exe notebooks/00_exploracion.py
   ```

   Para ejecutar y guardar las salidas del notebook con un kernel que use ese entorno:

   ```powershell
   $env:JUPYTER_PATH = (Resolve-Path .venv-hito1/share/jupyter).Path
   .\.venv-hito1\Scripts\python.exe -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=hito1 --ExecutePreprocessor.timeout=900 notebooks/00_exploracion.ipynb
   ```

   Este último comando guarda salidas en el notebook. Se debe seleccionar/configurar
   un kernel del mismo entorno: disponer de `python3` con otro intérprete no basta.

4. La ruta se resuelve desde la raíz, `notebooks/` o la carpeta contenedora. Para
   otra ubicación, definir antes `COVID_HITO1_ROOT` con la ruta absoluta del proyecto.
   **Colab no se ha probado**; requiere disponer del proyecto y configurar la ruta
   si no se encuentra automáticamente. No se promete funcionamiento sin preparación.

5. Por defecto no se usa red: primero se valida la caché y, si falta un CSV, se lee
   el clon hermano `../COVID-19/` sin escribir en él. Si no existe ninguna copia,
   la ejecución falla indicando el día; nunca lo omite. Fuera de esta validación,
   la descarga de solo los reportes faltantes de esta ventana se puede habilitar:

   ```powershell
   $env:COVID_HITO1_DESCARGAR = "1"
   ```

   Un caché inválido produce un error y no se sobrescribe automáticamente. Un HTTP
   404 detiene la carga; fallos transitorios tienen tres intentos. No se descarga
   el repositorio completo ni datos posteriores a junio de 2020.

6. Verificar dos PNG y el HTML de perfilado. Estos resultados se regeneran al ejecutar.
   El perfilado es obligatorio: si falta su biblioteca, la ejecución no declara éxito.
   Los crudos, gráficos y perfilado están ignorados por Git; un ZIP manual debe
   revisarse por separado. No se realizaron commits ni publicación desde esta revisión.

## Validación realizada

Notebook completo: 21 celdas, 10 de código ejecutadas consecutivamente, cero errores
y dos imágenes embebidas. La alternativa `.py` también finalizó correctamente y
produjo los mismos PNG (igualdad SHA-256). Perfilado: 350.945 observaciones y 19
variables, sin variables no soportadas. Las versiones exactas y dependencias
transitivas están en `requirements-hito1-lock.txt` (Windows x64, Python 3.12.14).

Ambas ejecuciones usaron los 161 archivos de caché y ninguna descarga de datasets.
La telemetría del perfilador está deshabilitada. Se comprobaron hashes de los
2.434 archivos del clon original, excluyendo `.git`, y de los 161 CSV de caché:
no se modificaron. Esta validación cubre reproducción local con caché; Colab y
una descarga desde caché vacía no se probaron.

## Interpretaciones y límites

Los acumulados se agregan por territorio dentro de una fecha; no se suman entre días.
Chile usa la fila nacional hasta el 19-may y las 16 regiones más Unknown desde el
20-may. Se verifica que no se superpongan niveles. Antes del 3-mar no hay fila de
Chile en estos reportes; el gráfico mantiene el hueco, sin inventar ceros.

La actualización se convierte a AAAA-MM-DD conservando su texto original y se separa
de `fecha_reporte`. FIPS se lee como texto. Las conversiones inválidas detienen la
carga. Las celdas vacías se distinguen de columnas ausentes en esquemas antiguos.
Tres textos literales `None` se conservan: no se confunden silenciosamente con NA.

La P7 propuesta (Banco Mundial y población de 65+) se conserva; OWID para P3 también
es una intención futura. La P7, los gráficos iniciales y el perfilado no completan
R1–R8. Los nombres reales, contribuciones individuales, compartir GitHub y confirmar
EVA siguen requiriendo evidencia del equipo.

## Estado del proyecto

| Hito | Fecha (calendario PPT ajustado) | Estado |
|---|---|---|
| Lanzamiento | Mié 4 nov | Git local creado; roles nominales pendientes |
| Hito 1 · Explorar | Mar 10 nov | Seis tareas ejecutadas y verificadas; pendientes administrativos del equipo |
| Test 3 | Mié 11 nov | — |
| Hito 2 · Plataforma | Mar 17 nov | ⏳ Pendiente (ingesta 1.143 reportes, Parquet, calidad, DW) |
| Hito 3 + ensayo | Mié 18 nov | ⏳ Pendiente |
| Sesión del Comité | Mar 24 nov | ⏳ Pendiente |
| Entrega final (EVA) | Mié 25 nov, 23:59 | ⏳ Pendiente |

> Las fechas están ajustadas según el PPT respecto del PDF del enunciado; en caso de
> diferencia, manda EVA.
