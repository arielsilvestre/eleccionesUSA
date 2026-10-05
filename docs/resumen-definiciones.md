# Resumen de definiciones metodológicas — Midterms 2026

_Última actualización: 2026-10-01_

---

## Objetivo central

**¿Retiene el Partido Republicano la mayoría en House y/o Senate en noviembre de 2026?**

La variable de resultado es **control de mayoría por cámara**, no net seat change ni voto popular agregado.

---

## Qué cuenta como "swing" (D-01 + D-02 + D-06)

Un distrito (House) o estado (Senate) entra en el universo de análisis si cumple **al menos una** de las dos condiciones:

- Margen promedio en valor absoluto **< 10 pp** en los ciclos de referencia, **O**
- Al menos **un flip** (cambio de partido ganador) entre ciclos.

### Filtro adicional para House — anti-redistricting (D-02)

Aunque un distrito califique por el criterio anterior, se **excluye** si su margen en 2024 superó los **20 pp** en valor absoluto. Esos flips reflejan el redibujado de mapas de 2021, no competitividad electoral real.

> Ejemplos: CA-13 (margen 2024 = −0.1 pp → queda) · CA-20 (+34.5 pp → sale) · GA-06 (−49.4 pp → sale)

### Ciclos de referencia para House (D-06)

Solo se usan **2020, 2022 y 2024**. Los ciclos 2016 y 2018 se cargan a la base de datos para consultas históricas, pero no entran en el cálculo de swing para no mezclar geografías pre/post redistricting 2021.

### Senate — Class 2 (D-03)

Los estados en juego en 2026 corresponden a los escaños **Class 2**, derivados de los datos: estados con carrera Senate no-especial en 2020.
Resultado: **34 estados** identificados → **11 clasificados como swing**.

---

## Métricas del análisis

| Eje | Fuente | Qué mide |
|---|---|---|
| Historial electoral | MIT Election Lab (Harvard Dataverse) | Competitividad estructural por distrito/estado |
| Contexto económico | BLS API (LAUS + CPI) | Desempleo e inflación, nacional y por estado swing |
| Validación | FEC + House.gov Election Statistics | Cruce y verificación de resultados MIT |

El análisis se basa en **condiciones de fondo** (historial + economía). **No se usan encuestas**, Cook Political Report, Sabato's Crystal Ball ni generic ballot polls. Esta limitación se declara explícitamente en el output final.

---

## Decisiones técnicas de procesamiento

### D-04 — Modo de votación
Para estados que reportan votos por modo (presencial, correo, etc.), se prioriza la fila `mode == 'TOTAL'`. Solo cuando un distrito no tiene fila TOTAL se agregan los modos parciales, para evitar doble conteo.

### D-05 — Fusion tickets
En estados con fusion tickets (CT, NJ, NY, SC principalmente), cuando un candidato aparece bajo múltiples partidos:
- **Partido asignado:** el que le aportó más votos.
- **Total de votos:** suma de todas las líneas del candidato.

---

## Pendientes / preguntas abiertas

| ID | Pregunta | Estado |
|---|---|---|
| D-01 | ¿Se quiere un filtro adicional para excluir distritos donde el único motivo de inclusión es un flip por redistricting (más allá de D-02)? | Pendiente confirmación |
| Síntesis | ¿Cómo se combinan el eje histórico y el eje económico en la conclusión final? | Sin definir — Fase 4 |
