# Protección y ética — fundamentos de plataforma

## Argumento jurídico acotado, contrastado al 16-nov-2026

La Ley 19.628 distingue información sobre personas identificadas o identificables
de datos estadísticos que no permiten asociar un titular. Incluye salud entre datos
sensibles cuando son personales. Un total territorial no es automáticamente un dato
personal: la identificabilidad depende del contexto.
[BCN, Ley 19.628, versión al 21-oct-2026 y artículo 2](https://www.bcn.cl/leychile/navegar?idNorma=141599&idVersion=2026-10-21).

La Ley 21.719 amplía la consideración de identificación indirecta y define
anonimización. Sus modificaciones principales entran en vigencia el **1-dic-2026**;
no se presentan como ya vigentes el día de esta validación.
[BCN, texto y vigencia](https://www.bcn.cl/leychile/Navegar/imprimir?idNorma=1209272),
[definiciones y transitorios](https://www.bcn.cl/leychile/navegar?idNorma=1209272).

**Inferencia aplicada:** conteos pequeños, lugares reducidos y conocimiento externo
podrían facilitar identificación. Por eso se implementa una precaución técnica;
no se afirma que todos los registros JHU sean datos personales ni que exista una
obligación legal específica de suprimir exactamente 1–4. Es un criterio del proyecto.

### Aplicación de ambas leyes al conjunto

| Norma / disposición | Lectura relevante | Aplicación y límite |
|---|---|---|
| Ley 19.628, art. 2 letras e, f y g | Distingue dato estadístico, dato personal y dato sensible de salud | JHU publica conteos territoriales, sin fichas de personas; que sean agregados no basta si el contexto permite identificar a alguien |
| Ley 19.628, arts. 4 y 10 | Condiciones de tratamiento y protección especial de datos sensibles | Ser accesible públicamente no constituye una autorización general para vincular información de salud a personas |
| Ley 21.719, art. primero, modificación del art. 2 | Considera identificación directa/indirecta y define anonimización irreversible | Quitar nombres o publicar una suma no demuestra anonimización; una localidad pequeña más información externa puede permitir inferencias |
| Ley 21.719, art. primero transitorio | Difiere la vigencia de las modificaciones principales | El 16-nov-2026 sigue aplicándose el régimen anterior; el nuevo entra el 1-dic-2026. No se confunde publicación con vigencia |

Ejemplo ilustrativo de riesgo, no un hecho demostrado en JHU: una celda de un caso
en una comunidad pequeña, combinada con noticias que identifican al único paciente,
podría asociar la cifra a una persona. El riesgo depende del contexto y del conocimiento
auxiliar. No se incorporaron nombres, RUT, domicilios individuales ni microdatos.

Se consultó el [texto oficial de Ley 21.719](https://www.bcn.cl/leychile/navegar?idNorma=1209272)
y su [artículo transitorio y vigencia](https://www.bcn.cl/leychile/Navegar/imprimir?idNorma=1209272).
Las conclusiones sobre este dataset son inferencias técnicas del proyecto, no una
certificación jurídica ni una promesa de anonimato universal.

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

## Evidencia de cierre sobre todos los hechos

La carga evaluada contiene 4.287.333 hechos. Las métricas reproducidas son:

| Ámbito / indicador | Resultado |
|---|---:|
| Filas con supresión primaria, todos los territorios | 165.064 |
| Celdas 1–4 en cuatro métricas, antes de aplicar población | 1.606.713 |
| Filas ocultas por el cierre conservador | 3.850.612 |
| Celdas no nulas ocultas por ese cierre | 15.391.755 |
| Condados UID de EE.UU. con población menor a 5.000 | 317 |
| De esos condados, con hechos observados | 316 |
| Filas observadas de esos 316 condados | 321.444 |
| Filas con supresión primaria de esos condados | 142.759 |
| Celdas 1–4 en esos condados | 163.532 |
| Filas de esos condados ocultas por cierre conservador | 321.444 |

El condado UID `U:84002282`, **Yakutat plus Hoonah-Angoon, Alaska**, población
2.727, no tiene hechos con esa identidad. Se mantiene en la dimensión; no se
inventan observaciones para alcanzar 317. Por eso el denominador de territorios
observados es 316 y el de la tabla maestra es 317. La población es la referencia
UID disponible, no una población diaria estimada para cada fecha histórica.

La pérdida es de celdas y filas, no de personas distintas. El cierre conservador
afecta también otros territorios del mismo país: aproximadamente 89,8 % de todos
los hechos quedan ocultos. Esta precaución tiene un costo de utilidad alto y no
debe presentarse como la política óptima del futuro tablero.

`tests/test_hito2.py` comprueba fronteras de población 4.999/5.000/desconocida y
conteos NULL, −1, 0, 1, 4 y 5. Las comprobaciones de integración verifican que ni
las vistas primaria/segura ni los totales país expongan las métricas marcadas.
`tests/verificar_cierre.py` mide nuevamente los afectados en la carga completa.
La evidencia compartible está en [verificacion_cierre_hito2.json](verificacion_cierre_hito2.json).

**Componente preparado para Hito 3:** consumir las vistas públicas y su campo
`suprimir`, mostrar «Suprimido por protección» en lugar de 0 y evitar calcular
tasas, diferencias, tooltips o exportaciones desde las tablas internas. Los avisos
de calidad y letalidad deben acompañar esas vistas. Esta integración visual,
incluidas pruebas de filtros/exportaciones y permisos, **no está implementada**.
