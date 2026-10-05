"""
Scoring Senate 2026 — Tarea 5.3
Combina score histórico (MIT), económico (BLS) y bellwether
para producir la tabla maestra senate_analysis_2026.csv.

Pesos: 50% histórico + 30% económico + 20% bellwether (D-13)
Etiquetas: 0-39 Favorable R / 40-60 Disputado / 61-100 Favorable D
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR  = os.path.join(BASE_DIR, 'output')


# ─────────────────────────────────────────────────────────────────────────────
# Funciones puras (testeables)
# ─────────────────────────────────────────────────────────────────────────────

def calcular_score_historico(avg_abs_margin: float) -> int:
    """
    Score 0-100 basado en margen promedio absoluto.
    Fórmula: max(0, min(100, round(100 - margen * 6)))
    0pp=100, 5pp=70, 10pp=40, 17pp=0
    """
    return max(0, min(100, round(100 - avg_abs_margin * 6)))


def derivar_tendencia_historica(avg_margin: float) -> str:
    """
    Clasifica el estado según margen promedio signado (R positivo, D negativo).
    > 10pp   → 'Sólido R'
    5–10pp   → 'Leve R'
    -5–5pp   → 'Disputado'
    -10–-5pp → 'Leve D'
    < -10pp  → 'Sólido D'
    """
    if avg_margin > 10:
        return 'Sólido R'
    elif avg_margin > 5:
        return 'Leve R'
    elif avg_margin >= -5:
        return 'Disputado'
    elif avg_margin >= -10:
        return 'Leve D'
    else:
        return 'Sólido D'


def derivar_tipo_competitividad(margins_by_year_str: str, years_raced_str: str) -> str:
    """
    Clasifica el estado según patrón de flips en el histórico disponible.
    'Flip reciente'  — flip en el ciclo más reciente
    'Flip ocasional' — flip en ciclos anteriores, pero no el más reciente
    'Competitivo'    — sin flips detectados
    Margen positivo = R gana; negativo = D gana.
    """
    margenes  = [float(m) for m in margins_by_year_str.split(',')]
    ganadores = ['R' if m > 0 else 'D' for m in margenes]

    if len(ganadores) < 2:
        return 'Competitivo'

    indices_flip = [i for i in range(1, len(ganadores)) if ganadores[i] != ganadores[i - 1]]

    if not indices_flip:
        return 'Competitivo'

    ultimo_idx = len(ganadores) - 1
    if ultimo_idx in indices_flip:
        return 'Flip reciente'
    return 'Flip ocasional'


def calcular_score_economico(
    tasa: float, var: float,
    tasa_min: float, tasa_max: float,
    var_min: float, var_max: float,
) -> int:
    """
    Score 0-100 combinando nivel de desempleo y variación anual.
    Mayor tasa relativa al grupo = peor para oficialismo = mayor score.
    Mayor aumento YoY relativo = peor para oficialismo = mayor score.
    Pesos: 60% nivel + 40% variación.
    Cuando todos los estados tienen el mismo valor, retorna 50 (neutro).
    """
    if tasa_max == tasa_min:
        nivel_norm = 50.0
    else:
        nivel_norm = (tasa - tasa_min) / (tasa_max - tasa_min) * 100

    if var_max == var_min:
        var_norm = 50.0
    else:
        var_norm = (var - var_min) / (var_max - var_min) * 100

    return round(nivel_norm * 0.6 + var_norm * 0.4)


def calcular_score_total(
    score_historico: int,
    score_economico: int,
    score_bellwether: int,
) -> float:
    """Pondera los tres scores con pesos 50/30/20 (D-13)."""
    return round(score_historico * 0.50 + score_economico * 0.30 + score_bellwether * 0.20, 1)


def derivar_riesgo_oficialismo(score_total: float) -> str:
    """
    Etiqueta final derivada del score total.
    0–39   → 'Favorable R'
    40–60  → 'Disputado'
    61–100 → 'Favorable D'
    """
    if score_total <= 39:
        return 'Favorable R'
    elif score_total <= 60:
        return 'Disputado'
    else:
        return 'Favorable D'


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    swing = pd.read_csv(os.path.join(OUT_DIR, 'senate_swing_2026.csv'))
    bls   = pd.read_csv(os.path.join(OUT_DIR, 'bls_swing_context.csv'))
    bellw = pd.read_csv(os.path.join(OUT_DIR, 'senate_bellwether.csv'))

    # Filtrar BLS a estados swing Senate
    bls_senate = bls[bls['swing_senate'] == True].copy()

    # Parámetros de normalización económica (sobre los 11 estados swing Senate)
    tasa_min = bls_senate['unemployment_rate_latest'].min()
    tasa_max = bls_senate['unemployment_rate_latest'].max()
    var_min  = bls_senate['unemployment_yoy_change'].min()
    var_max  = bls_senate['unemployment_yoy_change'].max()

    # Score e indicadores históricos
    swing['score_historico']    = swing['avg_abs_margin'].apply(calcular_score_historico)
    swing['tendencia_historica'] = swing['avg_margin'].apply(derivar_tendencia_historica)
    swing['tipo_competitividad'] = swing.apply(
        lambda r: derivar_tipo_competitividad(r['margins_by_year'], r['years_raced']),
        axis=1,
    )

    # Score económico
    bls_senate = bls_senate.copy()
    bls_senate['score_economico'] = bls_senate.apply(
        lambda r: calcular_score_economico(
            r['unemployment_rate_latest'], r['unemployment_yoy_change'],
            tasa_min, tasa_max, var_min, var_max,
        ),
        axis=1,
    )

    # Unir los tres ejes
    tabla = (
        swing[['state_po', 'tendencia_historica', 'tipo_competitividad', 'score_historico']]
        .merge(
            bls_senate[['state_po', 'unemployment_rate_latest', 'unemployment_yoy_change',
                         'score_economico']],
            on='state_po', how='left',
        )
        .merge(
            bellw[['state_po', 'es_bellwether', 'coincidencia_bellwether', 'score_bellwether']],
            on='state_po', how='left',
        )
    )

    tabla['score_total'] = tabla.apply(
        lambda r: calcular_score_total(
            r['score_historico'], r['score_economico'], r['score_bellwether']
        ),
        axis=1,
    )
    tabla['riesgo_oficialismo'] = tabla['score_total'].apply(derivar_riesgo_oficialismo)

    # Renombrar columnas al esquema final
    tabla = tabla.rename(columns={
        'state_po': 'estado',
        'unemployment_rate_latest': 'desempleo_ultimo',
        'unemployment_yoy_change':  'desempleo_var_anual',
    })

    tabla = tabla.sort_values('score_total', ascending=False)

    columnas_finales = [
        'estado', 'tendencia_historica', 'tipo_competitividad',
        'es_bellwether', 'coincidencia_bellwether',
        'desempleo_ultimo', 'desempleo_var_anual',
        'score_historico', 'score_economico', 'score_bellwether', 'score_total',
        'riesgo_oficialismo',
    ]
    tabla = tabla[columnas_finales]

    print(f'\n=== SCORING SENATE 2026 — {len(tabla)} estados ===')
    print(tabla.to_string(index=False))

    salida = os.path.join(OUT_DIR, 'senate_analysis_2026.csv')
    tabla.to_csv(salida, index=False)
    print(f'\n-> Guardado: {salida}')
