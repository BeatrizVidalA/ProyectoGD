# Roadmap — Proyecto Semestral GD 2026-2 (Sala de Crisis)

> Calendario basado en las **fechas ajustadas de la presentación (PPTX)**. El PDF del enunciado
> muestra algunos hitos anteriores; **confirmar el calendario definitivo en EVA** antes de
> comprometerse a estas fechas.

Fuente de datos principal: [CSSEGISandData/COVID-19](https://github.com/CSSEGISandData/COVID-19)
(Johns Hopkins, archivado). Descargar los CSV con un script; **no clonar el repositorio completo
ni subir los CSV crudos**.

## Cronograma

| Fecha | Objetivo y entregable |
|---|---|
| **6–10 nov · Hito 1** | Crear la estructura del repositorio y el README reproducible; asignar roles; preparar `00_exploracion.ipynb` con enero–junio de 2020; proponer P7 y su fuente externa. |
| **11–17 nov · Hito 2: plataforma** | Automatizar la descarga de los 1.143 reportes diarios, unificar los cinco esquemas y generar Parquet. Implementar reglas de calidad, documentar anomalías y cargar el modelo estrella en DuckDB. Integrar al menos una fuente externa por ISO3 y medir los cruces. |
| **17–18 nov · Hito 3: análisis y tablero inicial** | Responder P1–P7; calcular casos diarios sin ocultar revisiones negativas; implementar pronóstico de 14 días con dos modelos, tres fechas de backtesting y regla de alerta. Entregar una primera versión del tablero con filtros por territorio/fecha y mapas. |
| **19–21 nov · Completar y documentar** | Cerrar las reglas de privacidad y advertencias; pulir tablero, resultados y recomendaciones. Preparar diccionario de datos, informe técnico de hasta 15 páginas e informe al Comité de hasta 2 páginas. |
| **22–23 nov · Ensayo** | Simular territorios y fechas de corte al azar; comprobar que `pronosticar()` y `alerta()` no usan datos posteriores al corte (fugas). Practicar la defensa para que todos puedan explicar el proyecto. |
| **24 nov · Comité** | Presentación de 15 minutos: 7 de relato, 4 de desafío en vivo, 4 de preguntas. |
| **25 nov, 23:59 · Entrega** | Subir el repositorio reproducible y el ZIP a EVA: código, capa limpia y DW, informes, tablero y `contribuciones.md`. **No incluir los CSV crudos.** |

## Prioridades técnicas

1. **Canalización ejecutable de principio a fin** — un solo comando debe reproducir descarga → limpieza → DW → análisis → tablero.
2. **Capas de datos**: cruda → limpia → analítica, cada una versionada y documentada.
3. **Revisiones negativas**: registrar los acumulados que retroceden en una tabla de auditoría en vez de borrarlos; los casos diarios deben exponerlos, no ocultarlos.
4. **Cambio de granularidad de Chile**: tratar explícitamente el paso de nivel país a nivel regiones (los reportes de JHU cambian de esquema).
5. **Fuentes externas**:
   - OWID → vacunación para responder P3 (vía ISO3).
   - Banco Mundial → indicador para P7, si queda tiempo.

## Próximos pasos inmediatos

- [x] Inicializar el repositorio git (el directorio aún no es un repo).
- [x] Crear estructura de carpetas: `data/{raw,clean,dw}`, `notebooks/`, `src/`, `docs/`, `dashboard/`.
- [x] `00_exploracion.ipynb` sobre enero–junio de 2020 (los cinco esquemas).
- [x] Proponer la pregunta P7 y justificar la fuente externa.
- [ ] Script de descarga de los **1.143** reportes (hoy el notebook 00 descarga solo ene–jun 2020, con caché).
- [ ] Verificación de integridad de la descarga (conteo de filas/archivos) para el Hito 2.

## Hito 1 · completado (6-nov-2026)

- `notebooks/00_exploracion.ipynb` ejecutado de punta a punta: 350.945 filas, 0 errores.
- `docs/revision_hito1.md`: revisión contra el enunciado y hallazgos.
- `docs/P7_propuesta.md`: P7 con Banco Mundial (65+) y respaldo OxCGRT.
- Pendiente administrativo: completar nombres de roles y subir el repo a GitHub.
