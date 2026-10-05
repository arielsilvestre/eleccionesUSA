# Proyecto: Análisis de Midterms 2026 (EE.UU.)

## Reglas de trabajo (leer antes de cada sesión)

1. **No asumir — consultar siempre.** Antes de asumir cualquier cosa
   (criterio, umbral, comportamiento esperado, decisión de diseño), detenerme
   y escribir explícitamente: _"Voy a asumir que X — ¿confirmas?"_. No avanzar
   hasta recibir confirmación. Esto aplica a cualquier decisión no documentada
   en este archivo o en `DECISIONES.md`.

2. **Registrar decisiones.** Toda decisión metodológica relevante que surja
   durante el trabajo debe quedar documentada en `DECISIONES.md`, con contexto
   y alternativas consideradas. Si una decisión queda pendiente de confirmación,
   marcarla como tal en ese archivo.

## Objetivo
Evaluar si el oficialismo (Partido Republicano / administración Trump) retiene
la mayoría en House y Senate en las elecciones de medio término del
3 de noviembre de 2026, con foco en los distritos/estados swing que definen
ese control.

## Decisiones de scope (ya cerradas — no reabrir sin confirmación explícita)

- **Cámaras:** ambas — House (435 bancas) y Senate (escaños en juego este ciclo).
- **Definición de "ganar":** retención de mayoría por cámara. No es net seat
  change ni voto popular agregado.
- **Alcance geográfico:** distritos/estados swing, no promedio nacional.
- **Datasets autorizados:**
  1. MIT Election Lab — https://electionlab.mit.edu/data
  2. BLS (Bureau of Labor Statistics) — https://www.bls.gov/developers/
  3. FEC (Federal Election Commission) — tabla de referencia/verdad
     https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/
  4. Election Statistics 1920–present (House.gov) — tabla de referencia/verdad
     https://history.house.gov/Institution/Election-Statistics/Election-Statistics/
- **Datasets fuera de scope:** Census ACS 1-year. No usarlo salvo pedido
  explícito del usuario; mencionarlo solo como limitación o extensión futura.
- **Sin polling:** no usar encuestas, Cook Political Report, Sabato's Crystal
  Ball ni generic ballot polls. El análisis es de *condiciones de fondo*
  (historial electoral + economía), no de intención de voto directa. Declarar
  esta limitación en el output final.

## Uso de cada dataset

- **MIT Election Lab:** determina qué distritos House y qué escaños Senate son
  swing este ciclo, usando margen histórico 2016–2024. Fuente: CSVs
  descargables desde Harvard Dataverse (no tiene API).
- **BLS:** indicador económico (empleo/inflación) vía API REST, requiere key
  gratuita. Aplicar a nivel nacional y, donde esté disponible, por estado —
  específicamente sobre los distritos/estados swing identificados por MIT,
  no como promedio nacional genérico.
- **FEC (tabla de referencia):** resultados electorales oficiales certificados.
  Usar para validar y cruzar contra los datos del MIT Election Lab. No es
  fuente de análisis primaria.
- **House.gov Election Statistics (tabla de referencia):** serie histórica
  1920–presente de resultados House. Usar para validar cobertura histórica y
  como respaldo cuando MIT no cubra un ciclo específico.

## Entregable esperado

1. Lista de distritos House y escaños Senate en juego, clasificados por
   competitividad según histórico MIT.
2. Contexto económico (BLS) nacional y por estado clave.
3. Síntesis: qué dice cada eje sobre las chances del oficialismo, con
   limitaciones explícitas (sin polling, no es predicción de intención de voto).

## Stack técnico

- **Lenguaje:** Python 3 + pandas
- **Almacenamiento:** PostgreSQL en Railway (objetivo principal); CSV como
  formato intermedio durante la ingesta y para outputs puntuales.
- **Flujo general:** descarga/ingesta → CSV local → carga a PostgreSQL →
  análisis y consultas desde la base.

## Fuentes de datos — acceso

### MIT Election Lab (Harvard Dataverse)
CSVs descargables manualmente desde Harvard Dataverse. Datasets relevantes:
- **House:** `doi:10.7910/DVN/IG0UN2` — U.S. House Elections 1976–2022
- **Senate:** `doi:10.7910/DVN/PEJ5QU` — U.S. Senate Elections 1976–2022
- Nota: 2024 puede no estar en estos datasets aún; verificar disponibilidad
  en https://electionlab.mit.edu/data al momento de la descarga.

### BLS API
- Endpoint base: `https://api.bls.gov/publicAPI/v2/timeseries/data/`
- Requiere API key gratuita: https://www.bls.gov/developers/
- API key generada y guardada en `.env` como `BLS_API_KEY`.
- Series de interés: desempleo estatal (LAUS) e inflación (CPI).

### FEC — Tabla de referencia
- URL: https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/
- Descarga manual (CSV/XLS por ciclo electoral).
- Rol: validación y cruce contra datos MIT Election Lab.

### House.gov Election Statistics — Tabla de referencia
- URL: https://history.house.gov/Institution/Election-Statistics/Election-Statistics/
- Serie histórica 1920–presente, descarga manual por año.
- Rol: respaldo histórico y validación de cobertura cuando MIT no cubra un ciclo.

## Estructura de carpetas

```
/data/mit-election-lab/   → CSVs crudos descargados de Harvard Dataverse
/data/bls/                → respuestas de la API guardadas (JSON/CSV)
/data/fec/                → CSVs/XLS descargados de FEC (tabla de referencia)
/data/house-gov/          → archivos de Election Statistics House.gov (tabla de referencia)
/analysis/                → scripts Python de procesamiento
/output/                  → CSVs finales / queries de resultado
```

## Pendiente / prerequisitos

1. Generar API key de BLS en https://www.bls.gov/developers/ (registro gratuito).
2. Descargar CSVs de MIT Election Lab desde Harvard Dataverse (links arriba).
3. Configurar conexión a PostgreSQL en Railway (connection string).
