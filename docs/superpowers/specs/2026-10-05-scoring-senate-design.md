# Diseño — Matriz de scoring Senate 2026

Fecha: 2026-10-05
Proyecto: Análisis Midterms 2026

---

## Objetivo

Producir una tabla maestra (`output/senate_analysis_2026.csv`) que combine tres ejes
de análisis para cada uno de los 11 estados swing Senate (Class 2) e indique el
nivel de riesgo para el oficialismo (Partido Republicano) en cada escaño.

---

## Arquitectura

### Entradas (ya existentes)
- `output/senate_swing_2026.csv` — 11 estados swing, márgenes 2016–2024 (MIT)
- `output/bls_swing_context.csv` — último dato desempleo + variación anual (BLS)
- `data/mit-election-lab/` — CSVs crudos para calcular bellwether

### Scripts nuevos
```
analysis/03_bellwether.py       → tarea 2.6: calcula es_bellwether + coincidencia
analysis/04_scoring.py          → tarea 5.1: combina los 3 ejes → score + etiqueta
analysis/05_senate_final.py     → tarea 5.2: une todo en tabla maestra final
```

### Salida
```
output/senate_analysis_2026.csv — tabla maestra, una fila por estado swing Senate
```

---

## Schema de la tabla final

| Columna | Tipo | Descripción |
|---|---|---|
| `estado` | str | Nombre del estado |
| `tendencia_historica` | str | Sólido R / Leve R / Disputado / Leve D / Sólido D |
| `tipo_competitividad` | str | Competitivo / Flip ocasional / Flip reciente |
| `es_bellwether` | bool | Verdadero si coincide en ≥4 de 6 midterms |
| `coincidencia_bellwether` | str | ej. "5 de 6" |
| `desempleo_ultimo` | float | Tasa de desempleo más reciente (ago 2026) |
| `desempleo_var_anual` | float | Variación respecto al mismo mes del año anterior |
| `score_historico` | int | 0–100, peso 50% |
| `score_economico` | int | 0–100, peso 30% |
| `score_bellwether` | int | 0–100, peso 20% |
| `score_total` | float | Score ponderado final |
| `riesgo_oficialismo` | str | Favorable R / Disputado / Favorable D |

---

## Metodología de scoring

### Score histórico (peso 50%)

Basado en el margen promedio two-party de los ciclos 2016–2024 disponibles en MIT.
Escala invertida: menor margen → mayor competitividad → score más alto.

| Margen promedio | Score |
|---|---|
| 0–2pp | 90–100 |
| 2–5pp | 70–89 |
| 5–10pp | 40–69 |
| >10pp | 0–39 |

Derivación de `tendencia_historica`:
- Margen promedio >10pp a favor de R → Sólido R
- 5–10pp a favor de R → Leve R
- <5pp cualquier dirección → Disputado
- 5–10pp a favor de D → Leve D
- >10pp a favor de D → Sólido D

Derivación de `tipo_competitividad`:
- Margen promedio <5pp en todos los ciclos → Competitivo
- Al menos un flip en el período → Flip ocasional
- Flip en el ciclo más reciente (2022 o 2024) → Flip reciente

### Score económico (peso 30%)

Combina dos señales BLS sobre el estado:

1. **Nivel relativo de desempleo:** posición del estado respecto al promedio de los
   28 estados swing. Mayor desempleo relativo → peor para el oficialismo → score más alto.
   - Normalizado 0–100 con min-max sobre el conjunto de estados swing.

2. **Variación anual (YoY):** si el desempleo sube respecto al año anterior → peor
   para el oficialismo → suma al score.
   - Variación positiva normalizada: +0 a +20 puntos sobre el score base.

Score económico = promedio ponderado (60% nivel + 40% variación).

### Score bellwether (peso 20%)

Basado en cuántos de los últimos 6 midterms (2002–2022) el ganador del escaño
Senate del estado coincidió con el partido que terminó controlando el Senado.

| Coincidencia | Score |
|---|---|
| 6 de 6 | 100 |
| 5 de 6 | 80 |
| 4 de 6 | 60 |
| <4 de 6 | 50 (neutro) |

`es_bellwether` = Verdadero si coincidencia ≥ 4 de 6.

### Score total y etiqueta final

```
score_total = (score_historico * 0.50) + (score_economico * 0.30) + (score_bellwether * 0.20)
```

| Score total | riesgo_oficialismo |
|---|---|
| 0–39 | Favorable R |
| 40–60 | Disputado |
| 61–100 | Favorable D |

---

## Limitaciones explícitas

- Sin polling: el análisis se basa exclusivamente en condiciones de fondo
  (histórico electoral + economía). No refleja intención de voto actual.
- Cobertura temporal: MIT Election Lab cubre hasta 2022; si 2024 no está disponible,
  el margen más reciente usado es 2022.
- Redistricting: afecta House, no Senate — no es limitación para este análisis.
- CPI nacional: no disponible a nivel estatal en BLS para todos los estados;
  el score económico usa solo desempleo (LAUS).

---

## Decisiones pendientes de documentar en DECISIONES.md

- D-09: Pesos del score (50/30/20) — definidos por criterio metodológico, no calibración empírica.
- D-10: Umbral bellwether ≥4 de 6 midterms.
- D-11: Rango temporal bellwether: 2002–2022 (6 ciclos Class 2).
