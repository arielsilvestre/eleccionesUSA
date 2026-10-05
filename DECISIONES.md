# Decisiones metodológicas — Análisis Midterms 2026

Registro de decisiones tomadas durante el proyecto, con contexto y alternativas
descartadas. Sirve de memoria ante futuras sesiones o revisiones.

---

## D-01 — Umbral de swing: < 10 pp o al menos un flip

**Fecha:** inicio Fase 2
**Aplica a:** House y Senate
**Decisión:** un distrito/estado se clasifica como swing si cumple al menos
una de estas condiciones en los ciclos analizados:
- Margen promedio en valor absoluto < 10 puntos porcentuales, O
- Al menos un cambio de partido ganador (flip) entre ciclos.

**Alternativas consideradas:**
- Solo margen < 10pp (más restrictivo, descarta distritos que flippearon con
  margen mayor).
- Margen < 5pp (captura solo los toss-up puros, deja afuera competitivos).

**Pendiente de confirmar con el usuario:** si se quiere agregar un filtro
adicional para excluir distritos donde el único motivo de inclusión es un flip
provocado por redistricting (ver D-02).

---

## D-02 — Distritos con flip por redistricting: excluir por margen 2024 > 20pp

**Fecha:** Fase 2
**Aplica a:** House
**Decisión:** se agrega un filtro adicional al criterio de swing: se excluyen
los distritos donde el margen en valor absoluto en 2024 supera los 20 puntos
porcentuales, aunque hayan tenido un flip en ciclos anteriores.

**Implementación:** en `classify_swing_house()`, después de calcular el swing,
cruzar con el margen del ciclo más reciente disponible por distrito y descartar
los que superen el umbral. Se usa el ciclo más reciente (no necesariamente 2024)
porque algunos distritos renombrados post-redistricting no tienen entrada 2024.

**Ejemplos que quedan fuera con este filtro:**
- CA-13: margen 2024 = -0.1pp (queda dentro — era genuinamente competitivo)
- CA-20: margen 2024 = +34.5pp (queda fuera — no competitivo)
- GA-06: margen 2024 = -49.4pp (queda fuera — no competitivo)

**Por qué esta opción:**
El objetivo del análisis es predecir 2026. El predictor más relevante para
una elección futura es el resultado más reciente disponible — en este caso,
2024. Un distrito que se ganó o perdió por más de 20pp el año anterior no
es competitivo en ningún marco metodológico estándar, sin importar lo que
haya pasado en ciclos anteriores.

Los flips detectados en esos distritos no reflejan un cambio de preferencia
del electorado sino un cambio de geografía por redistricting (los mapas se
redibujaron en 2021). Incluirlos contamina la lista con falsos positivos y
distorsiona cualquier análisis posterior (BLS, síntesis final).

La alternativa de marcar con flag (Opción B) fue descartada porque agrega
complejidad sin beneficio analítico real: si un distrito no es competitivo,
no aporta información útil al output final.

**Umbral elegido:** 20pp. Es suficientemente amplio para no descartar distritos
que tuvieron una elección competitiva en 2024 pero con cierto margen, y
suficientemente estricto para eliminar los casos claramente no competitivos.

---

## D-03 — Senate: Class 2 derivada de datos, no hardcodeada

**Fecha:** Fase 2
**Aplica a:** Senate
**Decisión:** la lista de estados con escaños Class 2 (up en 2026) se deriva
automáticamente del dataset: son los estados que tuvieron una carrera Senate
no-especial en el año 2020. No se hardcodeó la lista.

**Resultado:** 34 estados identificados como Class 2; de esos, 11 califican
como swing según el umbral D-01.

**Limitación:** si un estado tuvo una carrera especial en 2020 (no de la
Class 2 regular), podría quedar incluido erróneamente. Verificar contra lista
oficial si se requiere precisión total.

---

## D-04 — Modo de votación: priorizar TOTAL, agregar si no existe

**Fecha:** Fase 2
**Aplica a:** House y Senate
**Decisión:** para evitar doble conteo en estados que reportan tanto el total
como el desglose por modo (correo, presencial, etc.), se priorizan las filas
con `mode == 'TOTAL'`. Solo cuando un distrito no tiene fila TOTAL se agregan
los modos parciales.

**Alternativa descartada:** filtrar solo TOTAL (perdería cobertura en estados
que solo reportan por modo parcial).

---

## D-05 — Fusion tickets: partido principal = máximos votos

**Fecha:** Fase 2
**Aplica a:** House (estados CT, NJ, NY, SC principalmente)
**Decisión:** cuando un candidato aparece en múltiples líneas de partido
(fusion ticket), se le asigna el partido bajo el cual recibió más votos como
partido principal. El total de votos del candidato suma todas las líneas.

**Alternativa descartada:** contar cada línea de partido por separado (infla
artificialmente el total D o R).

---

## D-06 — Ciclos de referencia para swing House: 2020, 2022, 2024

**Fecha:** Fase 2
**Aplica a:** House
**Decisión:** se usan los últimos 3 ciclos (2020, 2022, 2024) para calcular
el margen promedio y detectar flips. El dato de 2016 y 2018 está disponible
pero se excluye del cálculo de swing para no mezclar geografías pre y
post redistricting 2021.

**Nota:** los datos 2016–2024 sí se cargarán completos a PostgreSQL para
consultas históricas.

---

## D-07 — Rango temporal BLS: 2022–2026

**Fecha:** Fase 3
**Aplica a:** LAUS y CPI
**Decisión:** se solicitan datos desde 2022 hasta 2026 inclusive.

**Justificación:** 2022 es el ciclo midterm inmediatamente anterior,
lo que permite calcular cambio interanual (YoY) desde el año previo
y tener contexto del ciclo electoral pasado. El endpoint BLS v2 permite
hasta 20 años por request; 4 años es conservador y suficiente para el
análisis de condiciones de fondo.

**Alternativas consideradas:**
- 2020–2026: incluiría el año pre-pandemia de recuperación, pero agrega
  ruido por la distorsión del COVID. Se puede ampliar si el análisis lo
  requiere.
- Solo 2024–2026: insuficiente para calcular YoY en 2024.

---

## D-08 — Serie CPI: CUSR0000SA0 (seasonally adjusted)

**Fecha:** Fase 3
**Aplica a:** CPI nacional
**Decisión:** se usa la serie CUSR0000SA0 (CPI-U, todos los ítems,
ajustado estacionalmente).

**Justificación:** los modelos de voto económico (Erikson & Wlezien,
Fair, Abramowitz) usan series ajustadas estacionalmente porque los
votantes responden a la tendencia estructural de la economía. El ajuste
estacional elimina el ruido cíclico (energía cara en invierno, alimentos
en verano) que no refleja condiciones económicas percibidas por el electorado.

**Nota:** LAUS (desempleo estatal) usa la serie no ajustada estacionalmente
(LAUST, prefijo U), ya que no hay disponibilidad de series LAUS SA para
todos los estados en el rango requerido. Esta asimetría SA/NSA entre CPI y
LAUS es aceptable para el análisis de condiciones de fondo a nivel anual/trimestral.

**Alternativa descartada:** CUUR0000SA0 (not seasonally adjusted) — descartada
por introducir ruido estacional irrelevante para la predicción electoral.

---

## D-09 — Enfoque bellwether: indicador de control de mayoría (Opción A)

**Fecha:** Sesión 3 — 05/10/2026
**Aplica a:** Senate
**Decisión:** el análisis bellwether se implementa como indicador de control
de mayoría (Opción A): un estado es bellwether si históricamente el partido
que gana ese escaño Senate termina controlando el Senado.

**Alternativa descartada — Opción B (tracking de swing):** medir si el margen
del estado se mueve en sincronía con el swing nacional. Descartada porque no
responde directamente la pregunta de análisis (¿quién controla el Senado?),
solo informa sobre la magnitud del movimiento.

**Por qué Opción A:** la pregunta central del TP es control de mayoría por
cámara, no voto popular ni swing de margen. El bellwether de control es la
señal más directamente alineada con ese objetivo.

---

## D-10 — Bellwether aplicado solo a Senate (no a House)

**Fecha:** Sesión 3 — 05/10/2026
**Aplica a:** Senate
**Decisión:** el análisis bellwether se implementa únicamente para los
11 estados swing Senate. No se aplica a los 74 distritos House.

**Justificación:** la pregunta principal del análisis es el control del Senado.
El análisis House ya tiene su propia dimensión de competitividad histórica.
Extender bellwether a House agrega complejidad sin beneficio proporcional
para el entregable del TP.

**Posible extensión futura:** se puede incorporar bellwether House si el
análisis se amplía en etapas posteriores.

---

## D-11 — Umbral bellwether: ≥ 4 de 6 midterms

**Fecha:** Sesión 3 — 05/10/2026
**Aplica a:** Senate
**Decisión:** un estado se clasifica como bellwether si el partido ganador
de su escaño Senate coincidió con el partido que controló el Senado en al
menos 4 de los últimos 6 midterms.

**Escala de score por coincidencia:**
- 6 de 6 → score bellwether = 100
- 5 de 6 → score bellwether = 80
- 4 de 6 → score bellwether = 60 (umbral mínimo para es_bellwether = Verdadero)
- < 4 de 6 → score bellwether = 50 (neutro, no suma ni resta señal)

**Alternativas consideradas:**
- Umbral ≥ 5 de 6: más exigente, puede dejar pocos o ningún estado.
- Umbral ≥ 3 de 6: demasiado permisivo (coincidencia aleatoria).

---

## D-12 — Rango temporal bellwether: ciclos electorales Class 2 (1990–2020)

**Fecha:** Sesión 3 — 05/10/2026 (corregido en implementación)
**Aplica a:** Senate
**Decisión:** el cálculo de coincidencia bellwether usa los 6 ciclos electorales
más recientes donde los escaños Class 2 estuvieron en juego: 1990, 1996, 2002,
2008, 2014, 2020. Incluye tanto años midterm (1990, 2002, 2014) como años
presidenciales (1996, 2008, 2020), porque Class 2 solo vota cada 6 años —
no hay 6 midterms disponibles en un rango razonable.

**Error corregido:** la versión original de D-12 listaba "2002, 2006, 2010,
2014, 2018, 2022" como si los escaños Class 2 votaran en cada midterm. Incorrecto.

---

## D-13 — Pesos del score final: 50% histórico / 30% económico / 20% bellwether

**Fecha:** Sesión 3 — 05/10/2026
**Aplica a:** score_total en senate_analysis_2026.csv
**Decisión:** la ponderación de los tres ejes es:
- score_historico × 0.50
- score_economico × 0.30
- score_bellwether × 0.20

**Justificación:** el histórico electoral es el predictor más robusto en
modelos de condiciones de fondo (base empírica amplia). El contexto económico es
el segundo predictor clásico en la literatura de voto económico. El bellwether
es una señal complementaria, no un eje primario — de ahí su peso menor.

**Nota:** estos pesos no surgen de calibración empírica sino de criterio
metodológico. Se declaran explícitamente en el entregable como decisión de
diseño, no como resultado estadístico.

---

## D-14 — Railway/PostgreSQL postergado: CSVs locales suficientes para el TP

**Fecha:** Sesión 3 — 05/10/2026
**Aplica a:** Fase 4 del ROADMAP
**Decisión:** la carga a PostgreSQL en Railway (tareas 4.1–4.6) queda
postergada. Para el TP, los CSVs locales son suficientes como formato
de trabajo y entrega.

**Justificación:** el entregable del TP es un conjunto de tablas analíticas,
no un sistema de producción con base de datos. Railway agrega valor para
una "fase de producción" futura (dashboard, consultas en tiempo real) pero
no es necesario para llegar al análisis final.

**Condición para reactivar:** si el usuario decide construir un dashboard
o herramienta visual sobre los datos, Railway vuelve a ser prioritario.

---

## D-15 — FEC y House.gov postergados: no son necesarios para el análisis primario

**Fecha:** Sesión 3 — 05/10/2026
**Aplica a:** tareas 1.7, 1.8, 2.5
**Decisión:** las descargas de FEC y House.gov (tablas de referencia) y el
cruce de validación MIT vs. FEC/House.gov (tarea 2.5) quedan postergados
para el TP.

**Justificación:** son tareas de validación, no de análisis primario. Los
datos MIT Election Lab son suficientemente confiables para el análisis de
condiciones de fondo. Para un TP que no requiere publicación ni auditoría externa,
la validación cruzada es un plus, no un requisito.

---

## D-16 — Entregable final: CSVs de análisis + PPT separado

**Fecha:** Sesión 3 — 05/10/2026
**Aplica a:** Fase 6 del ROADMAP
**Decisión:** el entregable del TP consta de:
1. CSVs de análisis limpios y documentados (salidas de Fases 2–5).
2. Una presentación PPT separada que explique metodología, decisiones,
   ponderaciones y conclusiones.

**Lo que NO es el entregable:** un dashboard, un notebook ejecutable,
un informe HTML/PDF generado automáticamente, ni una base de datos
en producción. Esos formatos quedan para fases futuras.

**Contenido sugerido para el PPT:**
- ¿Qué quisimos medir y qué dejamos afuera?
- ¿Cómo llegamos a los 11 estados swing y los 74 distritos House?
- ¿Qué dicen los datos económicos sobre esos estados?
- ¿Qué es el bellwether y qué estados lo cumplen?
- ¿Cómo se pondera todo y cuál es la proyección de control Senate?
