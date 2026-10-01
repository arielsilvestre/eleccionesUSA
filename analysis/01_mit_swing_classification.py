"""
MIT Election Lab — Swing Classification
Fase 2 del roadmap: identifica distritos House y estados Senate competitivos
para las midterms de noviembre 2026.

Criterio swing:
  House  : |margen promedio| < 10pp en ciclos 2020/2022/2024, O al menos un flip.
  Senate : Class 2 (escaños que vuelven a votarse en 2026, última elección 2020).
           |margen 2020| < 10pp, O |margen promedio| (todas las razas del estado
           2016-2024) < 10pp.
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIT_DIR  = os.path.join(BASE_DIR, 'data', 'mit-election-lab')
OUT_DIR  = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

SWING_THRESHOLD  = 10   # puntos porcentuales
RECENT_CYCLES_H  = [2020, 2022, 2024]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def keep_best_mode(df, group_keys, mode_col, total_val):
    """
    Por cada combinación de group_keys, prefiere filas con mode == total_val.
    Si no existen filas TOTAL para ese grupo, conserva todos los modos
    (se sumarán después al agrupar por candidato).
    Evita doble conteo en estados que reportan TOTAL + breakdown por modo.
    """
    has_total = (
        df[df[mode_col] == total_val][group_keys]
        .drop_duplicates()
        .assign(_has_total=True)
    )
    df = df.merge(has_total, on=group_keys, how='left')
    df['_has_total'] = df['_has_total'].fillna(False)
    filtered = df[(df[mode_col] == total_val) | (~df['_has_total'])].drop(columns='_has_total')
    return filtered


# ─────────────────────────────────────────────────────────────────────────────
# HOUSE
# ─────────────────────────────────────────────────────────────────────────────

def load_house():
    df = pd.read_csv(
        os.path.join(MIT_DIR, '1976-2024-house.tab'),
        low_memory=False
    )
    df = df[
        (df['stage']   == 'GEN')  &
        (df['special'] == False)  &
        (df['year']    >= 2016)   &
        (df['writein'] == False)
    ].copy()

    # Evitar doble conteo cuando hay TOTAL + modos parciales
    df = keep_best_mode(df, ['year', 'state_po', 'district'], 'mode', 'TOTAL')
    return df


def compute_house_margins(df):
    # Fusion tickets: un candidato puede aparecer en múltiples partidos.
    # Paso 1 — votos por candidato+partido (ya desduplicados por modo)
    cand_party = (
        df.groupby(['year', 'state_po', 'district', 'candidate', 'party'], as_index=False)
        ['candidatevotes'].sum()
    )

    # Paso 2 — partido principal = el que le dio más votos
    primary = (
        cand_party
        .sort_values('candidatevotes', ascending=False)
        .groupby(['year', 'state_po', 'district', 'candidate'], as_index=False)
        .first()[['year', 'state_po', 'district', 'candidate', 'party']]
    )
    primary['party_simple'] = primary['party'].map(
        {'DEMOCRAT': 'D', 'REPUBLICAN': 'R'}
    ).fillna('OTHER')

    # Paso 3 — votos totales por candidato (sumando todas sus líneas de partido)
    cand_total = (
        cand_party
        .groupby(['year', 'state_po', 'district', 'candidate'], as_index=False)
        ['candidatevotes'].sum()
        .merge(primary[['year', 'state_po', 'district', 'candidate', 'party_simple']],
               on=['year', 'state_po', 'district', 'candidate'])
    )

    # Paso 4 — totalvotes por distrito/año
    totalvotes = (
        df.groupby(['year', 'state_po', 'district'], as_index=False)
        ['totalvotes'].max()
    )

    # Paso 5 — votos D y R por distrito/año
    dr = (
        cand_total[cand_total['party_simple'].isin(['D', 'R'])]
        .groupby(['year', 'state_po', 'district', 'party_simple'], as_index=False)
        ['candidatevotes'].sum()
        .pivot_table(index=['year', 'state_po', 'district'],
                     columns='party_simple', values='candidatevotes', aggfunc='sum')
        .reset_index()
    )
    dr.columns.name = None
    dr = dr.rename(columns={'D': 'dem_votes', 'R': 'rep_votes'})
    dr = dr.merge(totalvotes, on=['year', 'state_po', 'district'])

    dr['dem_votes'] = dr.get('dem_votes', 0).fillna(0)
    dr['rep_votes'] = dr.get('rep_votes', 0).fillna(0)
    dr['uncontested'] = (dr['dem_votes'] == 0) | (dr['rep_votes'] == 0)

    contested = ~dr['uncontested']
    dr['two_party_total'] = dr['dem_votes'] + dr['rep_votes']
    dr.loc[contested, 'margin'] = (
        (dr.loc[contested, 'rep_votes'] - dr.loc[contested, 'dem_votes'])
        / dr.loc[contested, 'two_party_total'] * 100
    )
    dr['winner'] = dr['margin'].apply(
        lambda x: 'R' if pd.notna(x) and x > 0 else ('D' if pd.notna(x) and x < 0 else None)
    )
    return dr


def classify_swing_house(margins, recent=RECENT_CYCLES_H, threshold=SWING_THRESHOLD,
                         redistricting_margin_cap=20):
    recent_df = margins[margins['year'].isin(recent) & ~margins['uncontested']].copy()

    def summarize(g):
        g = g.sort_values('year')
        winners = g['winner'].tolist()
        n_flips = sum(1 for i in range(1, len(winners)) if winners[i] != winners[i - 1])
        return pd.Series({
            'n_cycles'        : len(g),
            'avg_margin'      : round(g['margin'].mean(), 1),
            'avg_abs_margin'  : round(g['margin'].abs().mean(), 1),
            'min_abs_margin'  : round(g['margin'].abs().min(), 1),
            'n_flips'         : n_flips,
            'last_winner'     : winners[-1] if winners else None,
            'cycles'          : ','.join(g['year'].astype(str)),
            'margins_by_cycle': ','.join(g['margin'].round(1).astype(str)),
        })

    summary = recent_df.groupby(['state_po', 'district']).apply(summarize, include_groups=False).reset_index()
    summary['is_swing'] = (summary['avg_abs_margin'] < threshold) | (summary['n_flips'] > 0)

    # D-02: excluir distritos cuyo margen más reciente supera el cap (flip por redistricting)
    # Se usa el ciclo más reciente disponible, no necesariamente 2024
    # (algunos distritos no tienen 2024 por renombramiento post-redistricting)
    most_recent = (
        margins[margins['year'].isin(recent) & ~margins['uncontested']]
        .sort_values('year', ascending=False)
        .groupby(['state_po', 'district'], as_index=False)
        .first()[['state_po', 'district', 'year', 'margin']]
        .rename(columns={'margin': 'margin_most_recent', 'year': 'most_recent_year'})
    )
    summary = summary.merge(most_recent, on=['state_po', 'district'], how='left')
    summary['margin_most_recent_abs'] = summary['margin_most_recent'].abs()
    summary['is_swing'] = summary['is_swing'] & (
        summary['margin_most_recent_abs'] <= redistricting_margin_cap
    )
    # Renombrar para el output (mantener margin_2024 como alias cuando el ciclo es 2024)
    summary['margin_2024'] = summary.apply(
        lambda r: r['margin_most_recent'] if r.get('most_recent_year') == 2024 else None,
        axis=1
    )

    swing = (
        summary[summary['is_swing']]
        .sort_values('avg_abs_margin')
        .copy()
    )
    swing['district_id'] = (
        swing['state_po'] + '-'
        + swing['district'].astype(int).astype(str).str.zfill(2)
    )
    cols = ['district_id', 'state_po', 'district', 'last_winner',
            'avg_abs_margin', 'avg_margin', 'min_abs_margin',
            'margin_2024', 'n_flips', 'n_cycles', 'cycles', 'margins_by_cycle']
    return swing[cols]


# ─────────────────────────────────────────────────────────────────────────────
# SENATE
# ─────────────────────────────────────────────────────────────────────────────

def load_senate():
    df = pd.read_csv(
        os.path.join(MIT_DIR, '1976-2024-senate-state.csv'),
        low_memory=False
    )
    df = df[
        (df['stage']   == 'gen')  &
        (df['special'] == False)  &
        (df['year']    >= 2016)   &
        (df['writein'] == False)
    ].copy()

    df = keep_best_mode(df, ['year', 'state_po'], 'mode', 'total')
    return df


def compute_senate_margins(df):
    cand = (
        df.groupby(['year', 'state_po', 'candidate', 'party_simplified'], as_index=False)
        ['candidatevotes'].sum()
    )
    totalvotes = df.groupby(['year', 'state_po'], as_index=False)['totalvotes'].max()

    dr = (
        cand[cand['party_simplified'].isin(['DEMOCRAT', 'REPUBLICAN'])]
        .assign(party_simple=lambda x: x['party_simplified'].map({'DEMOCRAT': 'D', 'REPUBLICAN': 'R'}))
        .groupby(['year', 'state_po', 'party_simple'], as_index=False)
        ['candidatevotes'].sum()
        .pivot_table(index=['year', 'state_po'],
                     columns='party_simple', values='candidatevotes', aggfunc='sum')
        .reset_index()
    )
    dr.columns.name = None
    dr = dr.rename(columns={'D': 'dem_votes', 'R': 'rep_votes'})
    dr = dr.merge(totalvotes, on=['year', 'state_po'])

    dr['dem_votes'] = dr.get('dem_votes', 0).fillna(0)
    dr['rep_votes'] = dr.get('rep_votes', 0).fillna(0)
    dr['uncontested'] = (dr['dem_votes'] == 0) | (dr['rep_votes'] == 0)

    contested = ~dr['uncontested']
    dr['two_party_total'] = dr['dem_votes'] + dr['rep_votes']
    dr.loc[contested, 'margin'] = (
        (dr.loc[contested, 'rep_votes'] - dr.loc[contested, 'dem_votes'])
        / dr.loc[contested, 'two_party_total'] * 100
    )
    dr['winner'] = dr['margin'].apply(
        lambda x: 'R' if pd.notna(x) and x > 0 else ('D' if pd.notna(x) and x < 0 else None)
    )
    return dr


def classify_swing_senate(margins, threshold=SWING_THRESHOLD):
    # Class 2: estados con carrera no-especial en 2020 -> vuelven a votar en 2026
    class2 = set(margins[margins['year'] == 2020]['state_po'])
    df = margins[margins['state_po'].isin(class2) & ~margins['uncontested']].copy()

    def summarize(g):
        g = g.sort_values('year')
        m2020 = g[g['year'] == 2020]['margin'].values
        return pd.Series({
            'n_races'           : len(g),
            'margin_2020'       : round(m2020[0], 1) if len(m2020) else None,
            'avg_abs_margin'    : round(g['margin'].abs().mean(), 1),
            'avg_margin'        : round(g['margin'].mean(), 1),
            'last_winner'       : g.iloc[-1]['winner'],
            'years_raced'       : ','.join(g['year'].astype(str)),
            'margins_by_year'   : ','.join(g['margin'].round(1).astype(str)),
        })

    summary = df.groupby('state_po').apply(summarize, include_groups=False).reset_index()
    summary['is_swing'] = (
        (summary['margin_2020'].abs() < threshold) |
        (summary['avg_abs_margin'] < threshold)
    )
    swing = summary[summary['is_swing']].sort_values('avg_abs_margin').copy()
    cols = ['state_po', 'last_winner', 'margin_2020', 'avg_abs_margin',
            'avg_margin', 'n_races', 'years_raced', 'margins_by_year']
    return swing[cols]


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # ── House ──
    print('Procesando House...')
    house_raw     = load_house()
    house_margins = compute_house_margins(house_raw)
    house_swing   = classify_swing_house(house_margins)

    print(f'\n=== HOUSE — distritos swing para 2026 ({len(house_swing)} distritos) ===')
    print(house_swing[['district_id', 'last_winner', 'avg_abs_margin',
                        'n_flips', 'margins_by_cycle']].to_string(index=False))

    out_h = os.path.join(OUT_DIR, 'house_swing_2026.csv')
    house_swing.to_csv(out_h, index=False)
    print(f'\n-> Guardado: {out_h}')

    # ── Senate ──
    print('\nProcesando Senate...')
    senate_raw     = load_senate()
    senate_margins = compute_senate_margins(senate_raw)
    senate_swing   = classify_swing_senate(senate_margins)

    print(f'\n=== SENATE — estados swing Class 2 para 2026 ({len(senate_swing)} estados) ===')
    print(senate_swing[['state_po', 'last_winner', 'margin_2020',
                         'avg_abs_margin', 'years_raced']].to_string(index=False))

    out_s = os.path.join(OUT_DIR, 'senate_swing_2026.csv')
    senate_swing.to_csv(out_s, index=False)
    print(f'\n-> Guardado: {out_s}')
