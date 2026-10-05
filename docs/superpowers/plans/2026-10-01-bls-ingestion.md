# Fase 3 — BLS Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ingestar datos de desempleo estatal (LAUS) e inflación nacional (CPI) desde la API de BLS, filtrados a los estados swing identificados en Fase 2, y guardarlos en `/data/bls/` y `/output/`.

**Architecture:** Un único script `analysis/02_bls_ingestion.py` que carga los outputs de Fase 2, construye los series IDs de BLS, llama a la API v2 en batch, parsea las respuestas a DataFrames y los exporta a CSV. Los JSON crudos también se guardan para auditoría. Finalmente genera `output/bls_swing_context.csv` con el dato de desempleo más reciente por estado anotado con los flags de swing.

**Tech Stack:** Python 3, pandas, requests, python-dotenv. API key en `.env` como `BLS_API_KEY`.

---

## Archivos que se crean o modifican

| Acción  | Ruta                                        | Responsabilidad                                  |
|---------|---------------------------------------------|--------------------------------------------------|
| Crear   | `analysis/02_bls_ingestion.py`              | Script principal — todo el flujo de Fase 3       |
| Crear   | `data/bls/laus_swing_states_raw.json`       | Respuesta cruda de la API para LAUS              |
| Crear   | `data/bls/cpi_national_raw.json`            | Respuesta cruda de la API para CPI               |
| Crear   | `data/bls/laus_swing_states.csv`            | LAUS parseado a tabla (state, year, period, val) |
| Crear   | `data/bls/cpi_national.csv`                 | CPI parseado a tabla (year, period, value)       |
| Crear   | `output/bls_swing_context.csv`              | Último dato de desempleo × lista swing           |
| Modificar | `DECISIONES.md`                           | Agregar D-07 (rango de fechas BLS)               |
| Modificar | `ROADMAP.md`                              | Marcar 3.1–3.4 completados                       |
| Modificar | `BITACORA.md`                             | Registrar sesión                                 |

---

## Task 1: Scaffold y helpers de FIPS/series

**Archivos:**
- Crear: `analysis/02_bls_ingestion.py`

- [ ] **Step 1: Crear el script con imports, constantes y FIPS mapping**

```python
"""
BLS Ingestion — Fase 3
Descarga datos de la API BLS:
  - LAUS: tasa de desempleo mensual por estado (estados swing de Fase 2)
  - CPI: índice de precios al consumidor nacional (CUSR0000SA0)
Guarda JSON crudos en /data/bls/ y CSVs parseados en /data/bls/ y /output/.
"""

import json
import os

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLS_DIR  = os.path.join(BASE_DIR, 'data', 'bls')
OUT_DIR  = os.path.join(BASE_DIR, 'output')
os.makedirs(BLS_DIR, exist_ok=True)

BLS_API_URL  = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
BLS_API_KEY  = os.getenv('BLS_API_KEY')

# Rango temporal: desde el ciclo previo (2022) hasta el año en curso (2026).
# Cubre el contexto económico relevante para las midterms.  (D-07)
BLS_START_YEAR = '2022'
BLS_END_YEAR   = '2026'

# FIPS a nivel estatal (2 dígitos, con cero inicial)
STATE_FIPS = {
    'AK': '02', 'AL': '01', 'AZ': '04', 'CA': '06', 'CO': '08',
    'CT': '09', 'FL': '12', 'GA': '13', 'IA': '19', 'IL': '17',
    'ME': '23', 'MI': '26', 'MN': '27', 'MT': '30', 'NC': '37',
    'NE': '31', 'NH': '33', 'NJ': '34', 'NM': '35', 'NV': '32',
    'NY': '36', 'OH': '39', 'OR': '41', 'PA': '42', 'TX': '48',
    'VA': '51', 'WA': '53', 'WI': '55',
}

# Series IDs fijos
CPI_SERIES_ID = 'CUSR0000SA0'   # CPI-U, todos los ítems, ajustado estacionalmente


def laus_series_id(state_po: str) -> str:
    """
    Devuelve el series ID de BLS LAUS para la tasa de desempleo estatal.
    Formato: LAUST + FIPS(2 dígitos) + 0000000000003
    'U' = not seasonally adjusted, medida 03 = unemployment rate.
    """
    fips = STATE_FIPS[state_po]
    return f'LAUST{fips}0000000000003'


def get_swing_states() -> dict:
    """
    Lee los CSVs de Fase 2 y devuelve:
      {'house': set(state_po), 'senate': set(state_po)}
    Solo incluye estados para los que existe FIPS en STATE_FIPS.
    """
    house_csv  = os.path.join(OUT_DIR, 'house_swing_2026.csv')
    senate_csv = os.path.join(OUT_DIR, 'senate_swing_2026.csv')

    house_states  = set(pd.read_csv(house_csv)['state_po'].unique())
    senate_states = set(pd.read_csv(senate_csv)['state_po'].unique())

    # Filtrar a los que tienen FIPS definido (cobertura total esperada)
    missing_h = house_states - set(STATE_FIPS)
    missing_s = senate_states - set(STATE_FIPS)
    if missing_h:
        print(f'  AVISO: estados House sin FIPS: {missing_h}')
    if missing_s:
        print(f'  AVISO: estados Senate sin FIPS: {missing_s}')

    return {
        'house' : house_states & set(STATE_FIPS),
        'senate': senate_states & set(STATE_FIPS),
    }
```

- [ ] **Step 2: Verificar que el mapping funciona**

Agregar al final del archivo (bajo el bloque `if __name__ == '__main__'` que crearemos en Task 4):

```python
# Prueba rápida de helpers (ejecutar directamente para verificar)
if __name__ == '__main__':
    print('--- Verificación helpers ---')
    print(f'NC series ID : {laus_series_id("NC")}')   # esperado: LAUST370000000000003
    print(f'MI series ID : {laus_series_id("MI")}')   # esperado: LAUST260000000000003
    swing = get_swing_states()
    all_swing = swing['house'] | swing['senate']
    print(f'Estados House  swing : {len(swing["house"])}')   # esperado: ~22-28
    print(f'Estados Senate swing : {len(swing["senate"])}')  # esperado: 11
    print(f'Union swing states   : {sorted(all_swing)}')
```

- [ ] **Step 3: Ejecutar y verificar**

```
cd "C:\Users\asilvestre\OneDrive - PSF\Documentos\GitHub\eleccionesUSA"
python analysis/02_bls_ingestion.py
```

Salida esperada:
```
--- Verificación helpers ---
NC series ID : LAUST370000000000003
MI series ID : LAUST260000000000003
Estados House  swing : <número entre 20 y 28>
Estados Senate swing : 11
Union swing states   : ['AK', 'AL', 'AZ', ...]
```

- [ ] **Step 4: Commit**

```bash
git add analysis/02_bls_ingestion.py
git commit -m "feat(bls): scaffold script fase 3, FIPS mapping y helpers"
```

---

## Task 2: Cliente BLS API

**Archivos:**
- Modificar: `analysis/02_bls_ingestion.py`

- [ ] **Step 1: Agregar función `call_bls_api` antes del bloque `__main__`**

```python
def call_bls_api(series_ids: list, start_year: str, end_year: str) -> dict:
    """
    Llama a la BLS API v2. Devuelve el dict completo de la respuesta JSON.
    Lanza RuntimeError si la API no responde con REQUEST_SUCCEEDED.
    Límites con key: 500 consultas/día, 50 series por request, 20 años.
    """
    if not BLS_API_KEY:
        raise RuntimeError('BLS_API_KEY no encontrada en .env')

    payload = {
        'seriesid'       : series_ids,
        'startyear'      : start_year,
        'endyear'        : end_year,
        'registrationkey': BLS_API_KEY,
    }
    response = requests.post(BLS_API_URL, json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()
    status = data.get('status')
    if status != 'REQUEST_SUCCEEDED':
        messages = data.get('message', [])
        raise RuntimeError(f'BLS API status={status!r}. Mensajes: {messages}')

    return data
```

- [ ] **Step 2: Actualizar el bloque `__main__` para probar la función con una sola serie**

Reemplazar el bloque `if __name__ == '__main__':` por:

```python
if __name__ == '__main__':
    print('--- Verificación helpers ---')
    print(f'NC series ID : {laus_series_id("NC")}')
    print(f'MI series ID : {laus_series_id("MI")}')
    swing = get_swing_states()
    all_swing = swing['house'] | swing['senate']
    print(f'Estados House  swing : {len(swing["house"])}')
    print(f'Estados Senate swing : {len(swing["senate"])}')
    print(f'Union swing states   : {sorted(all_swing)}')

    print('\n--- Verificación API (prueba con 1 serie) ---')
    test_raw = call_bls_api(['LNS14000000'], '2025', '2026')
    test_data = test_raw['Results']['series'][0]['data']
    print(f'Serie LNS14000000 — primer dato: {test_data[0]}')
    print('API OK')
```

- [ ] **Step 3: Ejecutar y verificar**

```
python analysis/02_bls_ingestion.py
```

Salida esperada (el valor variará):
```
--- Verificación API (prueba con 1 serie) ---
Serie LNS14000000 — primer dato: {'year': '2026', 'period': 'M08', 'periodName': 'August', 'value': '4.4', ...}
API OK
```

Si aparece `RuntimeError: BLS API status=...`, revisar que `.env` tenga `BLS_API_KEY=<valor>` y que el archivo `.env` esté en el directorio raíz del proyecto.

- [ ] **Step 4: Commit**

```bash
git add analysis/02_bls_ingestion.py
git commit -m "feat(bls): add call_bls_api client function"
```

---

## Task 3: Fetch y guardado de LAUS

**Archivos:**
- Modificar: `analysis/02_bls_ingestion.py`
- Crear (generado): `data/bls/laus_swing_states_raw.json`
- Crear (generado): `data/bls/laus_swing_states.csv`

- [ ] **Step 1: Agregar función `parse_laus_response`**

```python
def parse_laus_response(raw: dict, series_to_state: dict) -> pd.DataFrame:
    """
    Convierte la respuesta cruda de la API LAUS a un DataFrame limpio.
    Filtra los períodos M13 (promedio anual) — queremos datos mensuales.
    Columnas: state_po, series_id, year, period, period_name, unemployment_rate
    """
    rows = []
    for series in raw['Results']['series']:
        sid   = series['seriesID']
        state = series_to_state.get(sid, 'UNKNOWN')
        for point in series['data']:
            if point['period'] == 'M13':   # anual — se descarta
                continue
            rows.append({
                'state_po'         : state,
                'series_id'        : sid,
                'year'             : int(point['year']),
                'period'           : point['period'],        # e.g. 'M01'
                'period_name'      : point['periodName'],    # e.g. 'January'
                'unemployment_rate': float(point['value']),
            })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(['state_po', 'year', 'period']).reset_index(drop=True)
    return df
```

- [ ] **Step 2: Agregar función `fetch_laus`**

```python
def fetch_laus(swing_states: dict) -> pd.DataFrame:
    """
    Pide LAUS para todos los estados swing (house U senate).
    Guarda JSON crudo en data/bls/laus_swing_states_raw.json.
    Devuelve DataFrame parseado.
    """
    all_states     = sorted(swing_states['house'] | swing_states['senate'])
    series_ids     = [laus_series_id(s) for s in all_states]
    series_to_state = {laus_series_id(s): s for s in all_states}

    print(f'  Fetching LAUS para {len(all_states)} estados: {all_states}')
    raw = call_bls_api(series_ids, BLS_START_YEAR, BLS_END_YEAR)

    # Guardar crudo
    raw_path = os.path.join(BLS_DIR, 'laus_swing_states_raw.json')
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(raw, f, indent=2)
    print(f'  JSON crudo guardado: {raw_path}')

    df = parse_laus_response(raw, series_to_state)

    # Verificación básica
    returned_states = set(df['state_po'].unique())
    missing = set(all_states) - returned_states
    if missing:
        print(f'  AVISO: estados sin datos en respuesta LAUS: {missing}')

    csv_path = os.path.join(BLS_DIR, 'laus_swing_states.csv')
    df.to_csv(csv_path, index=False)
    print(f'  CSV guardado: {csv_path} ({len(df)} filas, {df["state_po"].nunique()} estados)')
    return df
```

- [ ] **Step 3: Actualizar `__main__` para llamar `fetch_laus`**

Reemplazar el bloque `if __name__ == '__main__':` por:

```python
if __name__ == '__main__':
    swing = get_swing_states()

    print('\n=== LAUS — Desempleo estatal ===')
    laus_df = fetch_laus(swing)
    print(laus_df.tail(5).to_string(index=False))
```

- [ ] **Step 4: Ejecutar y verificar**

```
python analysis/02_bls_ingestion.py
```

Salida esperada:
```
=== LAUS — Desempleo estatal ===
  Fetching LAUS para 28 estados: ['AK', 'AL', 'AZ', ...]
  JSON crudo guardado: ...\data\bls\laus_swing_states_raw.json
  CSV guardado: ...\data\bls\laus_swing_states.csv (NNN filas, 28 estados)
 state_po  series_id  year period  period_name  unemployment_rate
       WI  LAUST550000000000003  2026    M07         July              3.2
  ...
```

Verificar manualmente:
- El CSV existe en `data/bls/laus_swing_states.csv`
- Tiene columnas: `state_po, series_id, year, period, period_name, unemployment_rate`
- No hay filas con `period == 'M13'`
- `unemployment_rate` está entre 1.0 y 20.0 (rango razonable)

- [ ] **Step 5: Commit**

```bash
git add analysis/02_bls_ingestion.py data/bls/laus_swing_states_raw.json data/bls/laus_swing_states.csv
git commit -m "feat(bls): fetch y guardado LAUS estados swing (3.1, 3.3, 3.4)"
```

---

## Task 4: Fetch y guardado de CPI nacional

**Archivos:**
- Modificar: `analysis/02_bls_ingestion.py`
- Crear (generado): `data/bls/cpi_national_raw.json`
- Crear (generado): `data/bls/cpi_national.csv`

- [ ] **Step 1: Agregar función `fetch_cpi`**

```python
def fetch_cpi() -> pd.DataFrame:
    """
    Pide la serie CPI-U nacional (CUSR0000SA0, SA) para el rango de fechas.
    Guarda JSON crudo en data/bls/cpi_national_raw.json.
    Devuelve DataFrame con columnas: series_id, year, period, period_name, cpi_value.
    """
    print(f'  Fetching CPI nacional ({CPI_SERIES_ID})')
    raw = call_bls_api([CPI_SERIES_ID], BLS_START_YEAR, BLS_END_YEAR)

    raw_path = os.path.join(BLS_DIR, 'cpi_national_raw.json')
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(raw, f, indent=2)
    print(f'  JSON crudo guardado: {raw_path}')

    rows = []
    for point in raw['Results']['series'][0]['data']:
        if point['period'] == 'M13':
            continue
        rows.append({
            'series_id'  : CPI_SERIES_ID,
            'year'       : int(point['year']),
            'period'     : point['period'],
            'period_name': point['periodName'],
            'cpi_value'  : float(point['value']),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(['year', 'period']).reset_index(drop=True)

    csv_path = os.path.join(BLS_DIR, 'cpi_national.csv')
    df.to_csv(csv_path, index=False)
    print(f'  CSV guardado: {csv_path} ({len(df)} filas)')
    return df
```

- [ ] **Step 2: Actualizar `__main__` para llamar también `fetch_cpi`**

```python
if __name__ == '__main__':
    swing = get_swing_states()

    print('\n=== LAUS — Desempleo estatal ===')
    laus_df = fetch_laus(swing)
    print(laus_df.tail(5).to_string(index=False))

    print('\n=== CPI — Inflación nacional ===')
    cpi_df = fetch_cpi()
    print(cpi_df.tail(5).to_string(index=False))
```

- [ ] **Step 3: Ejecutar y verificar**

```
python analysis/02_bls_ingestion.py
```

Salida esperada:
```
=== CPI — Inflación nacional ===
  Fetching CPI nacional (CUSR0000SA0)
  JSON crudo guardado: ...\data\bls\cpi_national_raw.json
  CSV guardado: ...\data\bls\cpi_national.csv (NN filas)
   series_id  year period  period_name  cpi_value
CUSR0000SA0  2026    M07         July      315.2
  ...
```

Verificar:
- `cpi_value` está en rango 290–330 (valores típicos de CPI-U en 2022–2026)
- Sin filas `M13`

- [ ] **Step 4: Commit**

```bash
git add analysis/02_bls_ingestion.py data/bls/cpi_national_raw.json data/bls/cpi_national.csv
git commit -m "feat(bls): fetch y guardado CPI nacional (3.2, 3.4)"
```

---

## Task 5: Construir `bls_swing_context.csv`

**Archivos:**
- Modificar: `analysis/02_bls_ingestion.py`
- Crear (generado): `output/bls_swing_context.csv`

Este output une el último dato de desempleo por estado con los flags de swing. Es el insumo para el análisis de Fase 5.

- [ ] **Step 1: Agregar función `build_swing_context`**

```python
def build_swing_context(laus_df: pd.DataFrame, swing_states: dict) -> pd.DataFrame:
    """
    Para cada estado swing, extrae:
      - tasa de desempleo más reciente disponible
      - cambio YoY (mismo período del año anterior), si existe
      - flags swing_house / swing_senate
    Exporta a output/bls_swing_context.csv.
    """
    all_states = sorted(swing_states['house'] | swing_states['senate'])

    # Mes más reciente por estado
    latest = (
        laus_df
        .sort_values(['state_po', 'year', 'period'], ascending=[True, False, False])
        .groupby('state_po', as_index=False)
        .first()
        [['state_po', 'year', 'period', 'period_name', 'unemployment_rate']]
        .rename(columns={
            'year'             : 'latest_year',
            'period'           : 'latest_period',
            'period_name'      : 'latest_period_name',
            'unemployment_rate': 'unemployment_rate_latest',
        })
    )

    # Mismo período del año anterior para calcular YoY
    prev_year_lookup = laus_df.copy()
    prev_year_lookup['year_next'] = prev_year_lookup['year'] + 1
    yoy = latest.merge(
        prev_year_lookup[['state_po', 'year_next', 'period', 'unemployment_rate']]
        .rename(columns={
            'year_next'        : 'latest_year',
            'unemployment_rate': 'unemployment_rate_prev_year',
        }),
        on=['state_po', 'latest_year', 'latest_period'],
        how='left',
    )
    yoy['unemployment_yoy_change'] = (
        yoy['unemployment_rate_latest'] - yoy['unemployment_rate_prev_year']
    ).round(2)

    # Flags swing
    yoy['swing_house']  = yoy['state_po'].isin(swing_states['house'])
    yoy['swing_senate'] = yoy['state_po'].isin(swing_states['senate'])

    # Ordenar por tasa más reciente
    result = yoy.sort_values('unemployment_rate_latest', ascending=False).reset_index(drop=True)

    cols = [
        'state_po',
        'swing_house', 'swing_senate',
        'latest_year', 'latest_period', 'latest_period_name',
        'unemployment_rate_latest', 'unemployment_rate_prev_year',
        'unemployment_yoy_change',
    ]
    result = result[cols]

    csv_path = os.path.join(OUT_DIR, 'bls_swing_context.csv')
    result.to_csv(csv_path, index=False)
    print(f'  CSV guardado: {csv_path} ({len(result)} estados)')
    return result
```

- [ ] **Step 2: Actualizar `__main__` para incluir el paso final**

```python
if __name__ == '__main__':
    swing = get_swing_states()

    print('\n=== LAUS — Desempleo estatal ===')
    laus_df = fetch_laus(swing)
    print(laus_df.tail(5).to_string(index=False))

    print('\n=== CPI — Inflación nacional ===')
    cpi_df = fetch_cpi()
    print(cpi_df.tail(5).to_string(index=False))

    print('\n=== Contexto BLS swing states ===')
    context_df = build_swing_context(laus_df, swing)
    print(context_df.to_string(index=False))
    print(f'\nPeriodo cubierto LAUS: {laus_df["year"].min()}–{laus_df["year"].max()}')
    print(f'Periodo cubierto CPI : {cpi_df["year"].min()}–{cpi_df["year"].max()}')
```

- [ ] **Step 3: Ejecutar y verificar output final**

```
python analysis/02_bls_ingestion.py
```

Salida esperada para la sección final:
```
=== Contexto BLS swing states ===
state_po  swing_house  swing_senate  latest_year  ...  unemployment_rate_latest  unemployment_yoy_change
      NV         True         False         2026  ...                       5.2                     0.3
      CA         True         False         2026  ...                       5.0                    -0.1
     ...
```

Verificar:
- El CSV `output/bls_swing_context.csv` tiene una fila por estado swing
- Todos los 11 estados Senate swing están presentes (`swing_senate == True`)
- No hay filas con `unemployment_rate_latest` nulo
- El campo `unemployment_yoy_change` puede ser nulo para 2022 (no hay año previo en el rango)

- [ ] **Step 4: Commit**

```bash
git add analysis/02_bls_ingestion.py output/bls_swing_context.csv
git commit -m "feat(bls): build bls_swing_context.csv con ultimo dato desempleo x estado swing"
```

---

## Task 6: Documentar decisiones y actualizar tracking

**Archivos:**
- Modificar: `DECISIONES.md`
- Modificar: `ROADMAP.md`
- Modificar: `BITACORA.md`

- [ ] **Step 1: Agregar D-07 en `DECISIONES.md`**

Abrir `DECISIONES.md` y agregar al final:

```markdown
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
```

- [ ] **Step 2: Actualizar `ROADMAP.md` — marcar 3.1–3.4 completados**

Cambiar:
```
- [ ] **3.1** Script: llamar API BLS, serie LAUS (desempleo por estado)
- [ ] **3.2** Script: llamar API BLS, serie CPI (inflación nacional y por estado disponible)
- [ ] **3.3** Filtrar respuestas a los estados swing identificados en Fase 2
- [ ] **3.4** Guardar respuestas en `/data/bls/` como JSON y/o CSV
```
Por:
```
- [x] **3.1** Script: llamar API BLS, serie LAUS (desempleo por estado)
- [x] **3.2** Script: llamar API BLS, serie CPI (inflación nacional y por estado disponible)
- [x] **3.3** Filtrar respuestas a los estados swing identificados en Fase 2
- [x] **3.4** Guardar respuestas en `/data/bls/` como JSON y/o CSV
```

- [ ] **Step 3: Agregar entrada en `BITACORA.md`**

```markdown
## Sesión 2 — 01/10/2026

### Fase 3 — BLS completada
- Escrito script `analysis/02_bls_ingestion.py` que:
  - Carga estados swing de los outputs de Fase 2.
  - Mapea estados a FIPS codes y construye series IDs LAUS.
  - Llama a BLS API v2 en batch (hasta 50 series/request).
  - Descarga LAUS (desempleo mensual por estado, 2022–2026).
  - Descarga CPI nacional (CUSR0000SA0, 2022–2026).
  - Parsea respuestas, filtra períodos anuales (M13).
  - Guarda JSON crudos y CSVs en `/data/bls/`.
  - Genera `output/bls_swing_context.csv` con último dato de desempleo
    por estado swing + cambio YoY.
- Registrada decisión D-07 (rango temporal BLS: 2022–2026).
- Fases 3.1–3.4 marcadas como completadas en ROADMAP.

### Estado al cierre de sesión
- Fase 3 completada.
- Pendientes: 1.3, 1.6 (Railway), 1.7, 1.8, 2.5 (cruce FEC/House.gov).

### Próxima sesión
1. **Fase 4 — PostgreSQL (Railway):** requiere connection string (tarea 1.6).
   Obtener string y configurar antes de arrancar.
2. Tarea 2.5 (cruce MIT vs FEC/House.gov) se puede hacer antes de Fase 4.
```

- [ ] **Step 4: Commit final**

```bash
git add DECISIONES.md ROADMAP.md BITACORA.md
git commit -m "docs: registrar Fase 3 completada, D-07, bitacora sesion 2"
```

---

## Self-review

**Cobertura del spec (ROADMAP 3.1–3.4):**
- 3.1 LAUS por estado → Task 3 (`fetch_laus`) ✓
- 3.2 CPI nacional → Task 4 (`fetch_cpi`) ✓
- 3.3 Filtrar a swing states → `get_swing_states()` + `build_swing_context()` ✓
- 3.4 Guardar en `/data/bls/` como JSON y CSV → Tasks 3, 4, 5 ✓

**Decisiones pendientes de confirmar antes de ejecutar:**
- El rango 2022–2026 es una propuesta (D-07). Confirmar con el usuario antes de ejecutar si hay preferencia distinta.
- La serie CPI elegida es `CUSR0000SA0` (CPI-U, seasonally adjusted). Si se prefiere not-seasonally-adjusted usar `CUUR0000SA0`.

**Sin placeholders:** todo el código está completo. ✓

**Consistencia de tipos:** `state_po` es string en todos los DataFrames. `year` se convierte a int. `unemployment_rate` y `cpi_value` a float. ✓
