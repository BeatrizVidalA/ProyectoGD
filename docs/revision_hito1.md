# Revisión del Hito 1 · Explorar

**Proyecto:** Sala de Crisis COVID-19 · GD 2026-2 (IN1232C)
**Revisado:** 7-nov-2026 (actualizado tras revisar el PPT y el PDF)
**Estado:** ✅ Los 4 entregables del Hito 1 están cumplidos; 3 acciones administrativas siguen pendientes.

---

## Qué pedía el Hito 1, según el enunciado y según el PPT

**PDF (sección 6):** Mié 28-oct — «Repositorio creado, roles asignados, notebook
`00_exploracion` (punto de partida) y P7 propuesta».

**PPT (lámina «Calendario de hitos» y «Primeros pasos»):** Mar **10-nov** —
«Notebook `00_exploracion` (punto de partida) y P7 propuesta, en el repositorio». Además,
el **Mié 4-nov** (Lanzamiento) pedía: repositorio y roles asignados.

Las fechas del PPT son las ajustadas respecto del PDF; si EVA difiere, manda EVA.

## 1 · Checklist

| Requisito | Evidencia | Estado |
|---|---|---|
| Repositorio creado | `git` con 2 commits (más uno nuevo con los docs); `.gitignore` excluye `data/raw/` | ✅ |
| Roles asignados | Tabla de roles en `README.md` y `contribuciones.md` | ⚠️ Placeholders; faltan nombres reales |
| Notebook `00_exploracion` | `notebooks/00_exploracion.ipynb`, 23 celdas, **0 errores**; alternativa `.py` para VS Code | ✅ |
| P7 propuesta | `docs/P7_propuesta.md` | ✅ |

## 2 · Checklist de los 6 puntos del notebook

| # | Punto | Evidencia |
|---|---|---|
| 1 | Cargar `01-22-2020.csv`, filas/columnas y tipos | 76 × 6; `Confirmed/Deaths/Recovered` float por nulos |
| 2 | Nulos por columna y significado | 12 nulos en `Province/State` (filas país); 48,7% en `Deaths`/`Recovered` (aún no se reportaban) |
| 3 | `snake_case` + `AAAA-MM-DD` | 24 columnas renombradas; 7 formatos de fecha; `1/23/20 17:00 → 2020-01-23`; 0 fechas sin parsear |
| 4 | Unir enero–junio 2020 | **350.945 filas × 16 columnas**; etapas 1: 4.242 · 2: 5.555 · 3: 217.486 · 4: 123.662; 4 cambios de esquema detectados |
| 5 | Top 10 al 30-jun + Chile | US **2.653.658**; Chile **7.º con 279.393**; gráficos PNG embebidos/guardados en `data/figs/` |
| 6 | Perfilado automático + 3 observaciones | `fg-data-profiling` (respaldo ydata); reporte en `data/profile/`; **11,28%** celdas nulas; 3 duplicados de llave completa; 1 fila exactamente duplicada |

## 3 · Hallazgos (importantes para el Hito 2)

1. **El enunciado y el PPT dicen «dos cambios de esquema»; en enero–junio hay tres:**
   el **29-may-2020** empieza la **etapa 4** (`Incidence_Rate`, `Case-Fatality_Ratio`) con
   123.662 filas dentro de la ventana. El notebook la detecta igualmente y la marca.
2. **Chile cambia de granularidad el 20-may-2020**: 42 días con filas regionales,
   17 territorios distintos (16 regiones + `Unknown`).
3. **La llave del grano es `fecha_reporte × region_pais × provincia_estado × admin2`.**
   Sin `admin2`, 291.074 filas parecen duplicadas (condados EE.UU.); con la llave
   completa quedan **3 duplicados** y **1 fila idéntica**.
4. **`ultima_actualizacion` no es la fecha del reporte:** trae horas y zona horaria;
   el grano temporal correcto es `fecha_reporte` (nombre del archivo).
5. **Cobertura no homogénea:** `latitud/longitud` desde 1-mar; `fips/admin2/activos/
   clave_combinada` desde 22-mar; `tasa_incidentes/tasa_letalidad` desde 29-may.

## 4 · Cómo se verificó la reproducibilidad

```powershell
python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=900 notebooks/00_exploracion.ipynb
python notebooks/00_exploracion.py
```

- Ejecución completa con caché vacía: descarga de los **161** reportes
  (22-ene → 30-jun-2020).
- 0 errores; 2 gráficos PNG; 8 tablas HTML.
- Los crudos **no** se suben al repo.

## 5 · Acciones pendientes (administrativas)

- [ ] Completar **nombres reales** en `README.md` (roles) y `contribuciones.md`.
- [ ] Crear el repo en GitHub y **compartirlo con el docente y con Nicolás** (regla del PPT).
- [ ] Confirmar en EVA la fecha definitiva del Hito 1 (PPT: Mar 10-nov).

## 6 · Riesgos y notas para el Hito 2

- Hito 2 (Mar 17-nov) exige descarga automática de los **1.143** reportes: el notebook
  baja solo ene–jun 2020 hoy; falta el pipeline completo con reintentos y verificación.
- `ydata-profiling` está deprecado: dejamos `fg-data-profiling` como línea principal y
  `ydata_profiling` de respaldo; `setuptools<81` por `pkg_resources`.
- Los **3 duplicados** y las **revisiones negativas** de acumulados se tratan en la capa
  limpia con una tabla de auditoría (no se borran en silencio).
