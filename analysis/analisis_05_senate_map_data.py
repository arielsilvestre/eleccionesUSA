"""
Tareas 5.4, 5.5, 5.6 — Dataset completo 50 estados para el mapa Senate 2026

Genera:
  output/senate_class2_all.csv   — 34 estados Class 2 con clasificación completa
  output/senate_non_class2.csv   — 16 estados sin Class 2 en 2026
  output/senate_map_data.csv     — 50 estados unificados para el mapa

Metodología:
  - Swing states (11): usan datos de senate_analysis_2026.csv (scoring completo).
  - Safe Class 2 states (23): tendencia calculada desde ciclos Class 2 (2002-2020).
  - Non-Class 2 states (16): partido del ganador más reciente (2022 ó 2024).
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIT_DIR  = os.path.join(BASE_DIR, 'data', 'mit-election-lab')
OUT_DIR  = os.path.join(BASE_DIR, 'output')

# Años en que Class 2 compitió (cada 6 años)
CLASS2_YEARS = {2002, 2008, 2014, 2020}

# 33 estados con senador Class 2 en juego en 2026
# (elecciones regulares no-especiales de 2020; AZ fue especial → excluida)
CLASS2_STATES = [
    'AK', 'AL', 'AR', 'CO', 'DE', 'GA', 'IA', 'ID', 'IL',
    'KS', 'KY', 'LA', 'MA', 'ME', 'MI', 'MN', 'MS', 'MT', 'NC',
    'NE', 'NH', 'NJ', 'NM', 'OK', 'OR', 'RI', 'SC', 'SD', 'TN',
    'TX', 'VA', 'WV', 'WY',
]

# 17 estados sin Class 2 en 2026 (sus dos senadores son Class 1 y Class 3)
# AZ incluida: su elección de 2020 fue especial (Class 3), no regular Class 2
NON_CLASS2_STATES = [
    'AZ', 'CA', 'CT', 'FL', 'HI', 'IN', 'MD', 'MO', 'ND',
    'NV', 'NY', 'OH', 'PA', 'UT', 'VT', 'WA', 'WI',
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de datos
# ─────────────────────────────────────────────────────────────────────────────

def keep_best_mode(df, group_cols, mode_col, preferred):
    """Conserva sólo el modo preferido (p.ej. 'total') si existe, si no todos.

    Usa merge en lugar de groupby+apply para evitar que pandas descarte las
    columnas de agrupamiento en versiones recientes.
    """
    preferred_lower = preferred.lower()
    preferred_rows = df[df[mode_col].str.lower() == preferred_lower]
    groups_with_preferred = preferred_rows[group_cols].drop_duplicates()

    # Grupos que tienen el modo preferido → conservar sólo esas filas
    has_pref = df.merge(groups_with_preferred, on=group_cols, how='inner')
    has_pref = has_pref[has_pref[mode_col].str.lower() == preferred_lower]

    # Grupos sin modo preferido → conservar todas sus filas
    no_pref = df.merge(groups_with_preferred, on=group_cols, how='left', indicator=True)
    no_pref = no_pref[no_pref['_merge'] == 'left_only'].drop(columns=['_merge'])

    return pd.concat([has_pref, no_pref], ignore_index=True)


def load_senate_raw():
    """Carga CSV MIT Senate y devuelve el dataframe crudo."""
    return pd.read_csv(
        os.path.join(MIT_DIR, '1976-2024-senate-state.csv'),
        low_memory=False,
    )


def prepare_senate(df_raw, year_min=2002):
    """Aplica filtros estándar y best-mode.

    Nota: el campo 'stage' usa 'gen' en datos hasta 2022 y 'GEN' en 2024,
    por lo que se hace la comparación en minúsculas.
    """
    df = df_raw[
        (df_raw['stage'].str.lower() == 'gen') &
        (df_raw['special'] == False) &
        (df_raw['year']    >= year_min) &
        (df_raw['writein'] == False)
    ].copy()
    return keep_best_mode(df, ['year', 'state_po'], 'mode', 'total')


def compute_margins(df):
    """Calcula margen two-party (R - D) por año/estado. Positivo = gana R."""
    cand = (
        df.groupby(['year', 'state_po', 'candidate', 'party_simplified'], as_index=False)
        ['candidatevotes'].sum()
    )
    total_votes = df.groupby(['year', 'state_po'], as_index=False)['totalvotes'].max()

    dr = (
        cand[cand['party_simplified'].isin(['DEMOCRAT', 'REPUBLICAN'])]
        .assign(p=lambda x: x['party_simplified'].map({'DEMOCRAT': 'D', 'REPUBLICAN': 'R'}))
        .groupby(['year', 'state_po', 'p'], as_index=False)['candidatevotes'].sum()
        .pivot_table(index=['year', 'state_po'], columns='p',
                     values='candidatevotes', aggfunc='sum')
        .reset_index()
    )
    dr.columns.name = None
    dr = dr.rename(columns={'D': 'dem_votes', 'R': 'rep_votes'})
    dr = dr.merge(total_votes, on=['year', 'state_po'])

    dr['dem_votes'] = dr.get('dem_votes', pd.Series(dtype=float)).fillna(0)
    dr['rep_votes'] = dr.get('rep_votes', pd.Series(dtype=float)).fillna(0)
    dr['uncontested'] = (dr['dem_votes'] == 0) | (dr['rep_votes'] == 0)

    contested = ~dr['uncontested']
    dr['two_party_total'] = dr['dem_votes'] + dr['rep_votes']
    dr.loc[contested, 'margin'] = (
        (dr.loc[contested, 'rep_votes'] - dr.loc[contested, 'dem_votes'])
        / dr.loc[contested, 'two_party_total'] * 100
    )
    dr['winner'] = dr['margin'].apply(
        lambda x: 'R' if pd.notna(x) and x > 0 else ('D' if pd.notna(x) else None)
    )
    return dr


def build_state_name_map(df_raw):
    """state_po → nombre en title case (ej. 'MI' → 'Michigan')."""
    return (
        df_raw[['state_po', 'state']]
        .drop_duplicates()
        .set_index('state_po')['state']
        .str.title()
        .to_dict()
    )


# ─────────────────────────────────────────────────────────────────────────────
# Clasificación
# ─────────────────────────────────────────────────────────────────────────────

def derivar_tendencia(avg_margin: float) -> str:
    """Clasifica la tendencia histórica según margen promedio (positivo = R)."""
    if avg_margin > 10:    return 'Sólido R'
    elif avg_margin > 5:   return 'Leve R'
    elif avg_margin >= -5: return 'Disputado'
    elif avg_margin >= -10: return 'Leve D'
    else:                  return 'Sólido D'


def tendencia_a_categoria(tendencia: str) -> str:
    """Tendencia → categoría de mapa (para safe states)."""
    return tendencia  # son exactamente iguales en este caso


def riesgo_a_categoria(riesgo: str) -> str:
    """riesgo_oficialismo → categoría de mapa (para swing states)."""
    mapping = {
        'Favorable D': 'Favorable D',
        'Favorable R': 'Favorable R',
        'Disputado':   'Disputado',
    }
    return mapping.get(riesgo, 'Disputado')


# ─────────────────────────────────────────────────────────────────────────────
# Tarea 5.4 — Class 2 completo (34 estados)
# ─────────────────────────────────────────────────────────────────────────────

def build_class2_all(margins, swing_analysis, state_name_map):
    swing_states = set(swing_analysis['estado'])

    # Datos Class 2: sólo ciclos históricos de Class 2 en general (sin especiales)
    c2 = margins[
        margins['state_po'].isin(CLASS2_STATES) &
        margins['year'].isin(CLASS2_YEARS) &
        ~margins['uncontested']
    ].copy()

    def resumir(g):
        g = g.sort_values('year')
        row_2020 = g[g['year'] == 2020]
        # Margen más reciente: 2020 si existe, si no el último ciclo disponible
        margen_reciente = round(row_2020['margin'].values[0], 1) if len(row_2020) else round(g.iloc[-1]['margin'], 1)
        return pd.Series({
            'avg_margen':       round(g['margin'].mean(), 1),
            'avg_abs_margen':   round(g['margin'].abs().mean(), 1),
            'margen_2020':      round(row_2020['margin'].values[0], 1) if len(row_2020) else None,
            'ganador_2020':     row_2020['winner'].values[0] if len(row_2020) else None,
            'margen_reciente':  margen_reciente,  # para clasificar safe states
            'n_ciclos':         len(g),
        })

    summary = (
        c2.groupby('state_po')
        .apply(resumir, include_groups=False)
        .reset_index()
    )

    rows = []
    for _, row in summary.iterrows():
        sp = row['state_po']
        nombre = state_name_map.get(sp, sp)

        if sp in swing_states:
            sa = swing_analysis[swing_analysis['estado'] == sp].iloc[0]
            rows.append({
                'state_po':              sp,
                'estado':                nombre,
                'vota_2026':             True,
                'clase':                 'Class 2',
                'es_swing':              True,
                'tendencia_historica':   sa['tendencia_historica'],
                'tipo_competitividad':   sa['tipo_competitividad'],
                'ganador_2020':          row['ganador_2020'],
                'margen_2020':           row['margen_2020'],
                'avg_margen':            row['avg_margen'],
                'n_ciclos':              int(row['n_ciclos']),
                'es_bellwether':         sa['es_bellwether'],
                'coincidencia_bellwether': sa['coincidencia_bellwether'],
                'desempleo_ultimo':      sa['desempleo_ultimo'],
                'desempleo_var_anual':   sa['desempleo_var_anual'],
                'score_historico':       sa['score_historico'],
                'score_economico':       sa['score_economico'],
                'score_bellwether':      sa['score_bellwether'],
                'score_total':           sa['score_total'],
                'riesgo_oficialismo':    sa['riesgo_oficialismo'],
                'categoria_mapa':        riesgo_a_categoria(sa['riesgo_oficialismo']),
            })
        else:
            # Para safe states, clasificar por el margen más reciente (no el promedio
            # histórico) para reflejar la alineación política actual y no los
            # realineamientos de estados como WV, AR, SD, LA.
            tendencia = derivar_tendencia(row['margen_reciente'])
            rows.append({
                'state_po':              sp,
                'estado':                nombre,
                'vota_2026':             True,
                'clase':                 'Class 2',
                'es_swing':              False,
                'tendencia_historica':   tendencia,
                'tipo_competitividad':   'No competitivo',
                'ganador_2020':          row['ganador_2020'],
                'margen_2020':           row['margen_2020'],
                'avg_margen':            row['avg_margen'],
                'n_ciclos':              int(row['n_ciclos']),
                'es_bellwether':         None,
                'coincidencia_bellwether': None,
                'desempleo_ultimo':      None,
                'desempleo_var_anual':   None,
                'score_historico':       None,
                'score_economico':       None,
                'score_bellwether':      None,
                'score_total':           None,
                'riesgo_oficialismo':    None,
                'categoria_mapa':        tendencia_a_categoria(tendencia),
            })

    return pd.DataFrame(rows).sort_values('state_po').reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Tarea 5.5 — Non-Class 2 (16 estados)
# ─────────────────────────────────────────────────────────────────────────────

def build_non_class2(margins, state_name_map):
    recent = margins[
        margins['state_po'].isin(NON_CLASS2_STATES) &
        ~margins['uncontested']
    ].copy()

    def get_reciente(g):
        g = g.sort_values('year', ascending=False)
        last = g.iloc[0]
        return pd.Series({
            'anio_mas_reciente':    int(last['year']),
            'ganador_mas_reciente': last['winner'],
            'margen_mas_reciente':  round(last['margin'], 1),
        })

    summary = (
        recent.groupby('state_po')
        .apply(get_reciente, include_groups=False)
        .reset_index()
    )

    rows = []
    for _, row in summary.iterrows():
        sp = row['state_po']
        rows.append({
            'state_po':             sp,
            'estado':               state_name_map.get(sp, sp),
            'vota_2026':            False,
            'clase':                'Class 1/3',
            'anio_mas_reciente':    row['anio_mas_reciente'],
            'ganador_mas_reciente': row['ganador_mas_reciente'],
            'margen_mas_reciente':  row['margen_mas_reciente'],
            'categoria_mapa':       'No vota 2026',
        })

    return pd.DataFrame(rows).sort_values('state_po').reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Tarea 5.6 — Unificado 50 estados
# ─────────────────────────────────────────────────────────────────────────────

def build_map_data(class2_all, non_class2):
    """Combina Class 2 y Non-Class 2 en un dataset unificado de 50 estados."""
    cols_comunes = [
        'state_po', 'estado', 'vota_2026', 'clase', 'categoria_mapa',
        'tendencia_historica', 'ganador_2020', 'margen_2020',
        'es_swing', 'score_total', 'riesgo_oficialismo',
        'desempleo_ultimo', 'desempleo_var_anual',
        'es_bellwether', 'coincidencia_bellwether',
        'anio_mas_reciente', 'ganador_mas_reciente', 'margen_mas_reciente',
    ]

    # Agregar columnas faltantes a class2_all
    c2 = class2_all.copy()
    c2['anio_mas_reciente']    = 2020
    c2['ganador_mas_reciente'] = c2['ganador_2020']
    c2['margen_mas_reciente']  = c2['margen_2020']

    # Agregar columnas faltantes a non_class2
    nc2 = non_class2.copy()
    for col in ['tendencia_historica', 'ganador_2020', 'margen_2020',
                'es_swing', 'score_total', 'riesgo_oficialismo',
                'desempleo_ultimo', 'desempleo_var_anual',
                'es_bellwether', 'coincidencia_bellwether']:
        nc2[col] = None

    combined = pd.concat(
        [c2[cols_comunes], nc2[cols_comunes]],
        ignore_index=True,
    )
    return combined.sort_values('state_po').reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('Cargando datos MIT Senate...')
    df_raw  = load_senate_raw()
    df      = prepare_senate(df_raw)
    margins = compute_margins(df)
    state_name_map = build_state_name_map(df_raw)

    swing_analysis = pd.read_csv(os.path.join(OUT_DIR, 'senate_analysis_2026.csv'))

    # ── 5.4 — Class 2 completo ──────────────────────────────────────────────
    class2_all = build_class2_all(margins, swing_analysis, state_name_map)
    out_c2 = os.path.join(OUT_DIR, 'senate_class2_all.csv')
    class2_all.to_csv(out_c2, index=False)
    print(f'\n5.4 guardado: {out_c2}  ({len(class2_all)} estados)')

    swing_count = class2_all['es_swing'].sum()
    safe_count  = (~class2_all['es_swing']).sum()
    print(f'   Swing: {swing_count}  |  Safe: {safe_count}')
    print('\n   Safe states por tendencia:')
    safe = class2_all[~class2_all['es_swing']][
        ['state_po', 'tendencia_historica', 'ganador_2020', 'margen_2020', 'avg_margen']
    ]
    print(safe.to_string(index=False))

    # ── 5.5 — Non-Class 2 ───────────────────────────────────────────────────
    non_class2 = build_non_class2(margins, state_name_map)
    out_nc2 = os.path.join(OUT_DIR, 'senate_non_class2.csv')
    non_class2.to_csv(out_nc2, index=False)
    print(f'\n5.5 guardado: {out_nc2}  ({len(non_class2)} estados)')
    print(non_class2[['state_po', 'ganador_mas_reciente', 'anio_mas_reciente']].to_string(index=False))

    # ── 5.6 — Mapa unificado ────────────────────────────────────────────────
    map_data = build_map_data(class2_all, non_class2)
    out_map = os.path.join(OUT_DIR, 'senate_map_data.csv')
    map_data.to_csv(out_map, index=False)
    print(f'\n5.6 guardado: {out_map}  ({len(map_data)} estados)')

    print('\n=== Distribución de categorías en el mapa ===')
    print(map_data.groupby('categoria_mapa').size().sort_values(ascending=False).to_string())

    # Verificar que tenemos los 50 estados
    all_states = set(CLASS2_STATES) | set(NON_CLASS2_STATES)
    map_states = set(map_data['state_po'])
    missing = all_states - map_states
    extra   = map_states - all_states
    if missing:
        print(f'\nATENCION — estados faltantes en el mapa: {missing}')
    if extra:
        print(f'ATENCION — estados extra en el mapa: {extra}')
    if not missing and not extra:
        print(f'\nVerificacion OK: los 50 estados presentes.')
