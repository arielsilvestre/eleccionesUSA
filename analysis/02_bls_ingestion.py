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
os.makedirs(OUT_DIR, exist_ok=True)

BLS_API_URL  = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
BLS_API_KEY  = os.getenv('BLS_API_KEY')

# Rango temporal: desde el ciclo previo (2022) hasta el año en curso (2026).
# Cubre el contexto económico relevante para las midterms.  (D-07)
# Nota: type str es intencional — BLS API espera strings ISO para años.
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
    'U' = not seasonally adjusted (unadjusted), 'ST' = state area type. Medida 03 = unemployment rate.
    """
    if state_po not in STATE_FIPS:
        raise KeyError(f'No FIPS mapping for state: {state_po!r}')
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
            if point['value'] == '-':
                # BLS usa '-' para datos aún no publicados; se omite la fila.
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


def fetch_laus(swing_states: dict) -> pd.DataFrame:
    """
    Pide LAUS para todos los estados swing (house U senate).
    Guarda JSON crudo en data/bls/laus_swing_states_raw.json.
    Devuelve DataFrame parseado.
    """
    all_states      = sorted(swing_states['house'] | swing_states['senate'])
    series_ids      = [laus_series_id(s) for s in all_states]
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


if __name__ == '__main__':
    swing = get_swing_states()

    print('\n=== LAUS — Desempleo estatal ===')
    laus_df = fetch_laus(swing)
    print(laus_df.tail(5).to_string(index=False))
