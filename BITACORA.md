# Bitácora — Análisis Midterms 2026

Registro cronológico de sesiones y avances del proyecto. Se actualiza al
inicio de cada sesión y después de cada hito relevante.

---

## Sesión 1 — 19/09/2026

### Setup del proyecto
- Creado `CLAUDE.md` a partir de `base.txt` como documento rector del proyecto.
- Creado `ROADMAP.md` con 6 fases y backlog de ideas futuras.
- Creado `.gitignore` incluyendo `.env` para proteger credenciales.
- Creada estructura de carpetas: `/data/mit-election-lab/`, `/data/bls/`,
  `/data/fec/`, `/data/house-gov/`, `/analysis/`, `/output/`.

### Fuentes de datos
- Incorporadas FEC y House.gov como tablas de referencia/verdad (además de
  MIT Election Lab y BLS que ya estaban definidas).
- Movidos archivos BLS (`news-release-table*.xlsx`) de `/data/mit-election-lab/`
  a `/data/bls/` donde corresponden.

### BLS API
- Generada API key gratuita y guardada en `.env` como `BLS_API_KEY`.
- Verificada conexión exitosa: HTTP 200, serie LNS14000000 (desempleo nacional),
  último dato disponible 4.4% (diciembre 2025).

### MIT Election Lab — Fase 2 completada
- Leídos codebooks de House y Senate para entender estructura de los datos.
- Escrito script `analysis/01_mit_swing_classification.py` que:
  - Carga y filtra CSVs House (`.tab`) y Senate (`.csv`) para ciclos 2016–2024.
  - Maneja fusion tickets (NY, CT, NJ, SC) asignando partido por máximos votos.
  - Evita doble conteo en estados que reportan por modo de votación (TOTAL vs. parciales).
  - Calcula margen two-party por distrito (House) y por estado (Senate).
  - Clasifica distritos/estados swing: margen promedio < 10pp o al menos un flip.
  - Aplica filtro D-02: excluye distritos con flip aparente por redistricting
    (margen más reciente > 20pp).
- Generados outputs:
  - `output/house_swing_2026.csv` — **74 distritos swing House**
  - `output/senate_swing_2026.csv` — **11 estados swing Senate (Class 2)**

### Decisiones registradas
- Creado `DECISIONES.md` con 6 decisiones metodológicas (D-01 a D-06).
- Agregadas al `CLAUDE.md` reglas de trabajo: no asumir sin consultar,
  registrar toda decisión en `DECISIONES.md`.

### Estado al cierre de sesión
- Fase 1 completada (salvo 1.6 — connection string Railway pendiente).
- Fase 2 completada (salvo 2.5 — cruce con FEC/House.gov pendiente).

### Puntos a relevar en la próxima sesión
1. **Fase 3 — BLS:** arrancar ingesta de datos económicos.
   - Serie LAUS: desempleo por estado.
   - Serie CPI: inflación nacional y por estado donde esté disponible.
   - Filtrar resultados a los 11 estados swing Senate + estados de los
     74 distritos swing House identificados en esta sesión.
2. **Railway:** pedir connection string para configurar PostgreSQL (tarea 1.6).
   Necesario antes de arrancar Fase 4.
3. **Decisión abierta D-02:** ya resuelta e implementada — sin pendientes.
4. **Tarea 2.5:** cruce de resultados MIT contra FEC y House.gov.
   Puede hacerse en paralelo o después de Fase 3, a definir.

---

## Sesión 2 — 01/10/2026

### Fase 3 — BLS completada
- Escrito script `analysis/02_bls_ingestion.py` que:
  - Carga estados swing de los outputs de Fase 2 (28 estados: unión House + Senate).
  - Mapea estados a FIPS codes y construye series IDs LAUS.
  - Llama a BLS API v2 en batch (28 series en una sola request).
  - Descarga LAUS (desempleo mensual por estado, 2022–2026).
    - Filtra períodos M13 (promedio anual) y valores '-' (datos no publicados).
    - Dato ausente detectado: octubre 2025 (suspensión de apropiaciones).
  - Descarga CPI nacional (CUSR0000SA0, 2022–2026).
  - Parsea respuestas y guarda JSON crudos y CSVs en `/data/bls/`.
  - Genera `output/bls_swing_context.csv` con último dato de desempleo
    (agosto 2026) por estado swing + cambio YoY. 28 estados, 0 nulls.
- Registradas decisiones D-07 (rango temporal BLS: 2022–2026) y
  D-08 (serie CPI: CUSR0000SA0, SA).
- Fases 3.1–3.4 marcadas como completadas en ROADMAP.

### Outputs generados en esta sesión
- `data/bls/laus_swing_states_raw.json` — respuesta cruda LAUS (28 estados)
- `data/bls/laus_swing_states.csv` — 1,540 filas, tasa desempleo 2022–2026
- `data/bls/cpi_national_raw.json` — respuesta cruda CPI
- `data/bls/cpi_national.csv` — 55 filas, CPI 2022–2026
- `output/bls_swing_context.csv` — 28 estados, último dato + YoY

### Estado al cierre de sesión
- Fase 3 completada.
- Pendientes: 1.3 (cobertura 2024 MIT), 1.6 (Railway connection string),
  1.7 (FEC), 1.8 (House.gov), 2.5 (cruce FEC/House.gov).

### Próxima sesión
1. **Fase 4 — PostgreSQL (Railway):** requiere connection string (tarea 1.6).
   Obtener string y configurar antes de arrancar.
2. Tarea 2.5 (cruce MIT vs FEC/House.gov) puede hacerse antes de Fase 4.

---

## Sesión 4 — 05/10/2026

### Tarea 1.3 — Cobertura 2024 en CSVs MIT

- Senate CSV (`1976-2024-senate-state.csv`): **incluye 2024** (33 estados Class 1,
  campo `stage = 'GEN'` en mayúsculas a diferencia de años anteriores).
- House CSV (`1976-2024-house.tab`): **no disponible localmente**; el archivo
  fue descargado en una sesión previa y ya no está en disco. El output
  `output/house_swing_2026.csv` (74 distritos) fue generado en Sesión 1 y sigue
  disponible.

### Tareas 5.4, 5.5, 5.6 — Dataset completo 50 estados para el mapa

- Escrito script `analysis/analisis_05_senate_map_data.py`.
- **Hallazgo D-22:** AZ no es Class 2 — su elección 2020 fue especial (Class 3,
  la banca de John McCain). CLASS2 = 33 estados (no 34).
- **Hallazgo:** el campo `stage` en datos 2024 es `'GEN'` (mayúsculas); el
  filtro original `== 'gen'` lo descartaba. Corregido con `.str.lower()`.
- **Decisión D-23:** safe states clasificados por margen más reciente (no
  promedio histórico) para evitar distorsión en estados con realineamiento
  político (WV, AR, SD, LA).
- Generados outputs:
  - `output/senate_class2_all.csv` — 33 estados Class 2 (11 swing + 22 safe)
  - `output/senate_non_class2.csv` — 17 estados sin Class 2 en 2026
  - `output/senate_map_data.csv` — 50 estados unificados para el mapa

### Distribución de categorías en el mapa

| Categoría      | N | Color     |
|----------------|---|-----------|
| No vota 2026   | 17 | #90A4AE  |
| Sólido R       | 15 | #B71C1C  |
| Sólido D       |  7 | #0D47A1  |
| Disputado      |  5 | #FFD600  |
| Favorable R    |  4 | #FF8F00  |
| Favorable D    |  2 | #2196F3  |

### Tareas 5.1 / 6.1 — House swing + contexto económico

- Escrito script `analysis/analisis_06_house_analysis.py`.
- Scoring House: 60% score_historico + 40% score_economico (sin bellwether — D-24).
- Desempleo nacional de referencia: 4.4% (último dato BLS disponible).
- Output: `output/house_analysis_2026.csv` — 74 distritos swing con score y riesgo.

### Tarea 6.4 — Mapa interactivo Senate HTML

- Escrito script `analysis/analisis_07_senate_map.py`.
- Choropleth plotly 50 estados con paleta D-18, tooltip completo D-19 y grises D-20.
- Output: `output/senate_map_2026.html`.

### Presentación

- Generado `output/presentacion_2026.html` — presentación Reveal.js con análisis completo
  de condiciones de fondo para las midterms 2026.

### Estado al cierre

- Completadas: 1.3, 5.1, 5.4, 5.5, 5.6, 6.1, 6.4.
- Pendiente para el TP:
  - **6.3** Síntesis escrita con limitaciones explícitas

### Próxima sesión

1. **6.3** — Redactar síntesis final con limitaciones (sin polling, análisis de
   condiciones de fondo únicamente).

---

## Sesión 3 — 05/10/2026

### Decisiones estratégicas

- Incorporado análisis **bellwether** como tercer eje de la matriz de scoring
  (D-09 a D-16), inspirado en el concepto de estado "anunciador" de resultado.
- Enfoque elegido: indicador de control de mayoría (Opción A) — no tracking de
  swing de margen. Solo aplicado a Senate.
- **Railway/PostgreSQL postergado** (D-14): CSVs locales son suficientes para el TP.
- **FEC y House.gov postergados** (D-15): no son necesarios para el análisis primario.
- **Entregable final redefinido** (D-16): CSVs de análisis + PPT separado.

### Diseño y documentación

- Brainstorming y diseño completo de la matriz de scoring Senate.
- Escrito spec en `docs/superpowers/specs/2026-10-05-scoring-senate-design.md`.
- Plan de implementación en `docs/superpowers/plans/2026-10-05-scoring-senate.md`.
- Registradas decisiones D-09 a D-16 en `DECISIONES.md`.
- Corregido error en D-12 (años Class 2 correctos: 1990, 1996, 2002, 2008, 2014, 2020).

### Scripts creados

- `analysis/analisis_03_bellwether.py` — tarea 2.6: coincidencia bellwether
  Class 2 por estado (1990–2020). Tests: 15/15.
- `analysis/analisis_04_scoring.py` — tarea 5.3: scores 0-100 y tabla maestra
  Senate. Tests: 30/30.

### Outputs generados

- `output/senate_bellwether.csv` — 11 estados: 5 bellwether (CO 5/6, NM/MN/NH/NC 4/6)
- `output/senate_analysis_2026.csv` — tabla maestra final:
  - Favorable D: MI (73.0), CO (67.1)
  - Disputado: TX (59.5), NC (56.5), MT (43.7), MN (43.0), GA (42.7)
  - Favorable R: NM (38.7), NH (38.4), IA (20.2), ME (17.8)

### Decisiones adicionales de la sesión

- **Mapa interactivo** incorporado como entregable visual (D-17): HTML plotly
  choropleth de 50 estados.
- **Paleta de colores** definida (D-18): 8 categorías, azul oscuro → rojo oscuro
  + gris-azulado para estados sin Class 2 en 2026.
- **Tooltip completo** para todos los estados (D-19): adecuado para contexto
  académico.
- **Cobertura del mapa** (D-20): 34 Class 2 vivos + 16 Class 1/3 muted.
- **Terminología** (D-21): "fundamentals" reemplazado por "condiciones de fondo"
  en todo el proyecto.

### Análisis interpretativo completado

- Lectura completa de `senate_analysis_2026.csv`: mayores riesgos R en TX y NC,
  oportunidades R en NH. MI y CO seguros para D. Síntesis registrada en sesión.

### Estado al cierre de sesión

- Completadas: 2.6, 5.2, 5.3, 6.2.
- Pendientes para el TP:
  - **1.3** Verificar cobertura 2024 en MIT CSVs
  - **5.1** Tabla House swing + BLS
  - **5.4** Dataset Class 2 completo (~34 estados)
  - **5.5** Dataset Class 1/3 (~16 estados)
  - **5.6** Dataset unificado 50 estados
  - **6.1** CSV final House
  - **6.3** Síntesis escrita
  - **6.4** Mapa interactivo HTML
- Postergados: 1.6 (Railway), 1.7, 1.8, 2.5 (FEC/House.gov).

### Próxima sesión

1. **1.3** — verificar cobertura 2024 en MIT (bloquea 5.4 y 5.5).
2. **5.4 + 5.5** — generar datasets Class 2 completo y Class 1/3.
3. **5.6** — unificar en dataset 50 estados.
4. **6.4** — generar mapa HTML una vez datos listos.
5. **5.1 + 6.1** — tabla House si hay tiempo.

---
