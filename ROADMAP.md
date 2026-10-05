# Roadmap — Análisis Midterms 2026

Estado: `[ ]` pendiente · `[x]` completado · `[~]` en progreso · `[!]` bloqueado

---

## Fase 1 — Setup y adquisición de datos

- [x] **1.1** Descargar CSV House (MIT Election Lab) desde Harvard Dataverse
      `doi:10.7910/DVN/IG0UN2`
- [x] **1.2** Descargar CSV Senate (MIT Election Lab) desde Harvard Dataverse
      `doi:10.7910/DVN/PEJ5QU`
- [ ] **1.3** Verificar cobertura de datos 2024 en ambos CSVs; documentar si falta
- [x] **1.4** Generar API key gratuita de BLS en https://www.bls.gov/developers/
- [x] **1.5** Guardar API key en archivo `.env` — conexión verificada (HTTP 200, REQUEST_SUCCEEDED)
- [ ] **1.6** Obtener connection string de PostgreSQL desde Railway
- [ ] **1.7** Descargar resultados electorales FEC (tabla de referencia)
      https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/
- [ ] **1.8** Descargar Election Statistics House.gov (tabla de referencia)
      https://history.house.gov/Institution/Election-Statistics/Election-Statistics/

---

## Fase 2 — Ingesta y limpieza (MIT Election Lab)

- [x] **2.1** Script: leer CSVs House y Senate, filtrar ciclos 2016–2024
- [x] **2.2** Script: calcular margen por distrito/estado por ciclo electoral
- [x] **2.3** Script: clasificar distritos/estados como swing según criterio de margen
      (umbral: <10 pp ó al menos un flip + filtro D-02 redistricting — House: 74 distritos / Senate: 11 estados Class 2)
- [x] **2.4** Exportar lista de swings — `output/house_swing_2026.csv` y `output/senate_swing_2026.csv`
- [ ] **2.5** Cruzar resultados MIT contra FEC y House.gov; documentar discrepancias
- [x] **2.6** Script bellwether: calcular coincidencia histórica por estado swing
      Senate (Class 2, ciclos 1990–2020) → `output/senate_bellwether.csv`

---

## Fase 3 — Ingesta BLS

- [x] **3.1** Script: llamar API BLS, serie LAUS (desempleo por estado)
- [x] **3.2** Script: llamar API BLS, serie CPI (inflación nacional y por estado disponible)
- [x] **3.3** Filtrar respuestas a los estados swing identificados en Fase 2
- [x] **3.4** Guardar respuestas en `/data/bls/` como JSON y/o CSV

---

## Fase 4 — Base de datos PostgreSQL (Railway)

- [ ] **4.1** Diseñar schema: tablas `house_results`, `senate_results`, `bls_unemployment`,
      `bls_inflation`, `swing_districts`, `fec_results`, `house_gov_stats`
- [ ] **4.2** Script: crear tablas en Railway vía SQLAlchemy o psycopg2
- [ ] **4.3** Script: cargar CSVs MIT procesados a PostgreSQL
- [ ] **4.4** Script: cargar datos BLS a PostgreSQL
- [ ] **4.5** Script: cargar tablas de referencia FEC y House.gov a PostgreSQL
- [ ] **4.6** Validar integridad: counts, nulls, rangos de fechas

---

## Fase 5 — Análisis

- [ ] **5.1** Tabla House swing + contexto económico BLS por estado
      → `output/house_analysis_2026.csv`
- [x] **5.2** Query: ranking de competitividad Senate (cubierto por `senate_analysis_2026.csv`)
- [x] **5.3** Script scoring: combinar score histórico + económico + bellwether
      → `output/senate_analysis_2026.csv` con tabla maestra Senate
- [ ] **5.4** Dataset completo Class 2 Senate (~34 estados): tendencia histórica + titular
      → `output/senate_class2_all.csv`
- [ ] **5.5** Dataset Class 1 y 3 (~16 estados): partido del titular actual (2022/2024)
      → `output/senate_non_class2.csv`
- [ ] **5.6** Combinar en dataset unificado 50 estados para el mapa
      → `output/senate_map_data.csv`

---

## Fase 6 — Output

- [ ] **6.1** Exportar tabla House swing + contexto económico a CSV final
      (depende de 5.1)
- [x] **6.2** Tabla maestra Senate lista → `output/senate_analysis_2026.csv`
- [ ] **6.3** Redactar síntesis con limitaciones explícitas (sin polling,
      análisis de condiciones de fondo únicamente)
- [ ] **6.4** Generar mapa interactivo HTML (plotly choropleth 50 estados)
      → `output/senate_map_2026.html` (depende de 5.6)

---

## Backlog / ideas futuras (fuera de scope actual)

- [ ] Incorporar datos FEC de financiamiento de campaña (además de resultados) como señal adicional
- [ ] Incorporar Census ACS para perfil demográfico de distritos swing
- [ ] Dashboard visual (Streamlit u otro) sobre los datos de Railway
- [ ] Automatizar actualización BLS con scheduler (resultados mensuales)
