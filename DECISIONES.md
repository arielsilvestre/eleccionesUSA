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
análisis de fundamentals.

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
LAUS es aceptable para el análisis de fundamentals a nivel anual/trimestral.

**Alternativa descartada:** CUUR0000SA0 (not seasonally adjusted) — descartada
por introducir ruido estacional irrelevante para la predicción electoral.
