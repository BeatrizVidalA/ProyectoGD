# Protección y ética — fundamentos de plataforma

## Argumento jurídico acotado, verificado al 11-nov-2026

La Ley 19.628 distingue información sobre personas identificadas o identificables
de datos estadísticos que no permiten asociar un titular. Incluye salud entre datos
sensibles cuando son personales. Un total territorial no es automáticamente un dato
personal: la identificabilidad depende del contexto.
[BCN, Ley 19.628 y artículo 2](https://www.bcn.cl/leychile/N?f=2023-05-09&i=141599).

La Ley 21.719 amplía la consideración de identificación indirecta y define
anonimización. Sus modificaciones principales entran en vigencia el **1-dic-2026**;
no se presentan como ya vigentes el día de esta validación.
[BCN, texto y vigencia](https://www.bcn.cl/leychile/Navegar/imprimir?idNorma=1209272),
[definiciones y transitorios](https://www.bcn.cl/leychile/navegar?idNorma=1209272).

**Inferencia aplicada:** conteos pequeños, lugares reducidos y conocimiento externo
podrían facilitar identificación. Por eso se implementa una precaución técnica;
no se afirma que todos los registros JHU sean datos personales ni que exista una
obligación legal específica de suprimir exactamente 1–4. Es un criterio del proyecto.

## Regla ejecutable y medición

En `v_control_divulgacion` se identifica población menor que 5.000 (o desconocida,
por precaución) y algún conteo entre 1 y 4 en casos, muertes o sus nuevos diarios.
`v_publica_territorio` oculta todas las métricas de esa fila, no solo la celda pequeña.
Es una vista diagnóstica de supresión primaria, no una garantía contra reconstrucción.

La vista recomendada para un futuro acceso público es `v_publica_segura`, con cierre
conservador: si un país contiene alguna fila marcada, oculta todas las métricas
territoriales de ese país durante la historia. `v_publica_pais` oculta también sus
totales. Así estas vistas no publican diferencias temporales ni complementos del
mismo país para recuperar una celda. La pérdida de utilidad puede ser muy grande.
No se utiliza esta política para alterar la base analítica interna.

`divulgacion.json` mide filas evaluadas, supresión primaria, celdas pequeñas,
filas afectadas por cierre conservador, celdas no nulas ocultas y condados UID de
EE.UU. menores de 5.000. Se mide pérdida de celdas, **no** suma de acumulados como
si fueran personas distintas. Los metadatos faltantes permanecen visibles como
limitación de evaluación, no población ficticia.

Esta supresión es deliberadamente conservadora y no es una política óptima para
el tablero. Hito 3 debe evaluar utilidad y diseñar supresión complementaria más
selectiva antes de cambiarla. No hay dashboard ni control de permisos desplegado;
un usuario con acceso al DW completo puede consultar la base interna. Tampoco se
garantiza anonimato frente a todas las fuentes públicas externas ya existentes.

## Advertencias para análisis y futura interfaz

La letalidad aparente depende de detección de casos, cobertura, rezagos y definiciones;
no equivale automáticamente a riesgo individual. Los registros tienen revisiones,
frecuencias y granularidades distintas. Las comparaciones internacionales requieren
denominadores y coberturas compatibles. Una asociación con vacunación, edad o
restricciones no demuestra causalidad. La plataforma no emite decisiones clínicas.
