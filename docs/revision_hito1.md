# Revisión del Hito 1 · Explorar

**Proyecto:** Sala de Crisis COVID-19 · GD 2026-2 (IN1232C)
**Revisado:** 6-nov-2026 · **Estado:** ✅ Cumple los cuatro requisitos del hito; quedan 3 acciones administrativas.

---

## 1 · Checklist contra el enunciado

El enunciado (sección 6) pide para el Hito 1: **repositorio creado, roles asignados,
notebook `00_exploracion` (punto de partida) y P7 propuesta**.

| Requisito | Evidencia | Estado |
|---|---|---|
| Repositorio creado | `git init`; 10 archivos versionados; `.gitignore` excluye `data/raw/` | ✅ |
| Roles asignados | Tabla de roles en `README.md` y `contribuciones.md` | ⚠️ Faltan nombres reales |
| `00_exploracion.ipynb` | `notebooks/00_exploracion.ipynb`, **14 celdas ejecutadas, 0 errores**, 2 gráficos y 8 tablas con salida | ✅ |
| P7 propuesta | `docs/P7_propuesta.md` (población 65+ del Banco Mundial vs. mortalidad, ISO3) | ✅ |

## 2 · Checklist del notebook (los 6 puntos exigidos)

| # | Punto del enunciado | Cómo se resolvió | Evidencia de la ejecución |
|---|---|---|---|
| 1 | Cargar `01-22-2020.csv`, primeras filas, filas/columnas y tipos | Descarga por URL raw con caché; `head()`, `shape`, `dtypes` | **76 filas × 6 columnas**; `Confirmed/Deaths/Recovered` float por nulos |
| 2 | Nulos por columna + explicación | Tabla `isna().sum()` con interpretación por columna | 12 nulos en `Province/State` (filas país); **48,7%** en `Deaths`/`Recovered` (aún no se reportaban) |
| 3 | `snake_case` + fecha `AAAA-MM-DD` | Mapa único de 24 columnas; 7 formatos de fecha explícitos | `1/23/20 17:00` → `2020-01-23`; 0 fechas sin parsear en 350.945 filas |
| 4 | Unir enero–junio 2020 (cambios de esquema) | Detección de etapa por columnas + `concat`; fecha desde el nombre del archivo | **350.945 filas × 16 columnas**; etapas 1: 4.242 · 2: 5.555 · 3: 217.486 · 4: 123.662 |
| 5 | Top 10 países al 30-jun y evolución de Chile | `groupby` por país en la fecha de corte; línea de Chile | US **2.653.658**; Chile **7.º con 279.393**; gráficos embebidos |
| 6 | Perfilado automático + 3 observaciones | `fg-data-profiling` (respaldo `ydata-profiling`), reporte HTML | Reporte en `data/profile/`; **11,28% celdas nulas**, 3 duplicados de llave completa, 1 fila exactamente duplicada |

## 3 · Hallazgos de la revisión (importantes para el Hito 2)

1. **El enunciado dice «los dos primeros cambios de esquema», pero en enero–junio hay
   tres.** El 29-may-2020 empieza la **etapa 4** (`Incidence_Rate`, `Case-Fatality_Ratio`),
   con 123.662 filas dentro de la ventana. El notebook la detecta y la marca; hay que
   corregir esa frase en el informe técnico.
2. **Chile cambia de granularidad el 20-may-2020** (no a «fines de mayo»): 42 días con
   filas regionales, 17 territorios distintos (16 regiones + `Unknown`). Desde el 20-may
   el total país se obtiene sumando; antes viene en una sola fila.
3. **La llave del grano es `fecha_reporte × country_region × province_state × admin2`.**
   Sin `admin2`, 291.074 filas parecen duplicadas (son condados de EE.UU.); con la llave
   completa quedan **3 duplicados** y **1 fila exactamente duplicada**, que deben revisarse
   en la capa limpia (no borrarse en silencio).
4. **`last_update` no es la fecha del reporte:** contiene horas y desfases de zona
   horaria. El grano temporal correcto es `fecha_reporte` (nombre del archivo).
5. **Cobertura de columnas no homogénea:** `lat/lon` desde 1-mar; `fips/admin2/active/
   combined_key` desde 22-mar; `incident_rate/case_fatality_ratio` desde 29-may. No son
   nulos aleatorios: son columnas que aún no existían.

## 4 · Cómo se verificó la reproducibilidad

```powershell
python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=900 notebooks/00_exploracion.ipynb
```

- Ejecución desde cero con caché vacía: descarga 161 reportes (22-ene a 30-jun-2020).
- Resultado: **0 errores**, 2 gráficos PNG, 8 tablas HTML, 23 celdas totales.
- Los datos crudos quedan en `data/raw/` (ignorado por git); el notebook se puede
  reejecutar sin volver a descargar.

## 5 · Acciones pendientes (administrativas, no técnicas)

- [ ] Completar los **nombres reales** en `README.md` (tabla de roles) y `contribuciones.md`.
- [ ] Crear el repositorio en GitHub, subirlo y compartirlo con docente/ayudante
  (verificar que `data/raw/` no se suba: ya está en `.gitignore`).
- [ ] Confirmar en EVA la **fecha definitiva** del Hito 1 (la presentación ajustó el
  calendario; el PDF decía 28-oct).

## 6 · Riesgos y notas para el Hito 2

- El notebook descarga 161 archivos por red; en el Hito 2 el pipeline debe bajar los
  **1.143** con reintentos y verificación de integridad.
- `ydata-profiling` está deprecado: dejamos `fg-data-profiling` como principal y el
  import anterior como respaldo; fijamos `setuptools<81` por `pkg_resources`.
- Las **3 filas duplicadas** y las **revisiones negativas** de acumulados se tratan en
  la capa limpia con una tabla de auditoría (decisión ya tomada en el roadmap).
