# Roadmap — Proyecto Semestral GD 2026-2 (Sala de Crisis)

> Fechas tomadas de la presentación PPT (**calendario ajustado**); el PDF del enunciado
> muestra hitos anteriores. Si EVA difiere, **manda EVA**. Hito 3 y ensayo caen juntos
> el 18-nov según el PPT.

Fuente de datos principal: [CSSEGISandData/COVID-19](https://github.com/CSSEGISandData/COVID-19)
(Johns Hopkins, archivado). Descargar los CSV con un script «raw» de GitHub; **no clonar
el repositorio completo ni subir los CSV crudos**.

## Cronograma

| Fecha | Objetivo y entregable |
|---|---|
| **Mié 4 nov** | Lanzamiento: enunciado, repositorio y roles. |
| **Mar 10 nov · Hito 1 · Explorar** | Notebook `00_exploracion` (punto de partida) y P7 propuesta en el repositorio. |
| **Mié 11 nov** | Test 3 (DW, BI y arquitecturas en la nube). No hay hito esa semana. |
| **Mar 17 nov · Hito 2 · Plataforma** | Ingesta de los 1.143 reportes unificada, capa Parquet, reglas de calidad y modelo estrella cargado. |
| **Mié 18 nov · Hito 3 · Análisis y ensayo** | P1–P6 avanzadas, pronóstico con backtesting, tablero v1 y ensayo con Nicolás. |
| **Mar 24 nov · Sesión del Comité** | 15 minutos por equipo con desafío en vivo. |
| **Mié 25 nov, 23:59 · Entrega final** | repositorio y `.zip` en EVA: código, capa limpia y DW, informes, tablero y `contribuciones.md`. **No incluir los CSV crudos.** |

## Prioridades técnicas

1. **Canalización ejecutable de un comando** — descarga → limpieza → DW → análisis → tablero.
2. **Capas**: cruda (CSV tal cual) → limpia (Parquet) → analítica (DW de R3). Comparar
   tamaño en disco y tiempo de lectura CSV vs Parquet.
3. **Revisiones negativas**: registrar acumulados que retroceden (84 países) en una tabla de
   auditoría en vez de borrarlos; casos diarios con `diff()`, media móvil solo sobre diarios.
4. **Cambio de granularidad de Chile**: país hasta el 19-may-2020; regiones + Unknown desde
   el **20-may-2020**.
5. **Fuentes externas**: OWID vacunación para P3; **Banco Mundial** (`SP.POP.65UP.TO.ZS`)
   para P7; OxCGRT como respaldo de P7. Cruce por ISO3; reportar tasa de cruce.
6. **Desafío en vivo**: `pronosticar(territorio, fecha_corte, horizonte=14)` y
   `alerta(territorio, fecha)` reciben la fecha de corte; el tablero filtra por territorio
   y fecha sin tocar el código; backtesting con 3 fechas de corte (MAE y MAPE).

## ¿Qué pedía exactamente el Hito 1?

| Entregable | Estado |
|---|---|
| Repositorio creado | ✅ |
| Roles asignados | ⚠️ Placeholders; faltan nombres reales |
| Notebook `00_exploracion.ipynb` | ✅ Ejecutado, 0 errores (350.945 filas) |
| P7 propuesta | ✅ En `docs/P7_propuesta.md` |

También existe `notebooks/00_exploracion.py` (mismo análisis, pensado para VS Code).

## Estructura entregada

```
notebooks/00_exploracion.ipynb   análisis ejecutado (columnas en español)
notebooks/00_exploracion.py      mismo análisis en .py para VS Code
README.md                         cómo reproducir todo desde cero (pasos numerados)
ROADMAP.md                        este archivo
docs/P7_propuesta.md              propuesta de P7
docs/revision_hito1.md            revisión del Hito 1
requirements.txt  contribuciones.md  .gitignore
```

## Pendiente antes del Hito 2 (17-nov)

- [ ] Nombres reales en README y contribuciones.
- [ ] Crear repo GitHub y compartirlo con docente y Nicolás (regla del PPT).
- [ ] Confirmar las fechas en EVA.
- [ ] Script de descarga de los **1.143** reportes (hoy el notebook baja solo ene–jun 2020 con caché).
- [ ] Verificación de integridad (conteo de archivos/filas) para el pipeline.
