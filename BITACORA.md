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
