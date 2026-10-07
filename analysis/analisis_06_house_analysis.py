"""
Tarea 5.1 / 6.1 — Tabla House swing + contexto económico BLS

Genera:
  output/house_analysis_2026.csv  — 74 distritos swing con scoring y contexto BLS

Metodología:
  - Sin bellwether (no hay ciclo electoral equivalente por distrito).
  - Score = 60% score_historico + 40% score_economico (ambas fórmulas igual que Senate).
  - score_historico: 100 - avg_abs_margin * 6  (capped 0–100)
  - score_economico: derivado de desempleo vs media nacional y cambio YoY
  - riesgo_oficialismo: Favorable R (0–39) / Disputado (40–60) / Favorable D (61–100)
  - Positivo = leans R, Negativo = leans D (convención heredada del script Senate)
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR  = os.path.join(BASE_DIR, 'output')

# Desempleo nacional de referencia (último dato disponible BLS — agosto 2026)
# Usado para normalizar el score económico por estado swing
DESEMPLEO_NACIONAL = 4.4  # porcentaje


# ─────────────────────────────────────────────────────────────────────────────
# Funciones de scoring (igual que analisis_04_scoring.py)
# ─────────────────────────────────────────────────────────────────────────────

def calcular_score_historico(avg_abs_margin: float) -> int:
    """Competitividad histórica. Menor margen = estado más competitivo = score más alto."""
    return max(0, min(100, round(100 - avg_abs_margin * 6)))


def derivar_tendencia_historica(avg_margin: float) -> str:
    """avg_margin positivo = R ganó en promedio."""
    if avg_margin > 10:    return 'Sólido R'
    elif avg_margin > 5:   return 'Leve R'
    elif avg_margin >= -5: return 'Disputado'
    elif avg_margin >= -10: return 'Leve D'
    else:                  return 'Sólido D'


def derivar_tipo_competitividad(n_flips: int, min_abs_margin: float) -> str:
    if n_flips >= 2:
        return 'Flip reciente'
    elif n_flips == 1:
        return 'Flip ocasional'
    else:
        return 'Competitivo'


def calcular_score_economico(
    desempleo: float,
    desempleo_nacional: float,
    desempleo_yoy: float,
) -> int:
    """
    Mismo modelo que Senate (D-11):
      - Desempleo alto vs nacional → presión sobre oficialismo (score sube para D)
      - Subida YoY del desempleo → presión adicional
    Score va de 0 (muy favorable R) a 100 (muy favorable D).
    """
    if pd.isna(desempleo) or pd.isna(desempleo_yoy):
        return 50  # neutro si faltan datos

    # Diferencia con la media nacional: >0 = más desempleo que el promedio
    diff_nacional = desempleo - desempleo_nacional

    score = 50
    # Componente nivel
    if diff_nacional > 2:    score += 30
    elif diff_nacional > 1:  score += 20
    elif diff_nacional > 0:  score += 10
    elif diff_nacional < -2: score -= 30
    elif diff_nacional < -1: score -= 20
    elif diff_nacional < 0:  score -= 10

    # Componente tendencia YoY
    if desempleo_yoy > 1:    score += 20
    elif desempleo_yoy > 0:  score += 10
    elif desempleo_yoy < -1: score -= 20
    elif desempleo_yoy < 0:  score -= 10

    return max(0, min(100, score))


def calcular_score_total(score_historico: int, score_economico: int) -> float:
    """60% histórico + 40% económico (sin bellwether para House)."""
    return round(score_historico * 0.60 + score_economico * 0.40, 1)


def derivar_riesgo_oficialismo(score_total: float) -> str:
    if score_total <= 39:  return 'Favorable R'
    elif score_total <= 60: return 'Disputado'
    else:                   return 'Favorable D'


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Cargar inputs
    house  = pd.read_csv(os.path.join(OUT_DIR, 'house_swing_2026.csv'))
    bls    = pd.read_csv(os.path.join(OUT_DIR, 'bls_swing_context.csv'))

    # Conservar sólo columnas BLS necesarias y renombrar para claridad
    bls_cols = bls[['state_po', 'unemployment_rate_latest', 'unemployment_yoy_change']].copy()
    bls_cols = bls_cols.rename(columns={
        'unemployment_rate_latest':  'desempleo_ultimo',
        'unemployment_yoy_change':   'desempleo_var_anual',
    })

    # Join por estado (left join para conservar todos los distritos)
    df = house.merge(bls_cols, on='state_po', how='left')

    # Derivar campos analíticos
    df['tendencia_historica']  = df['avg_margin'].apply(derivar_tendencia_historica)
    df['tipo_competitividad']  = df.apply(
        lambda r: derivar_tipo_competitividad(r['n_flips'], r['min_abs_margin']), axis=1
    )
    df['score_historico']  = df['avg_abs_margin'].apply(calcular_score_historico)
    df['score_economico']  = df.apply(
        lambda r: calcular_score_economico(
            r['desempleo_ultimo'], DESEMPLEO_NACIONAL, r['desempleo_var_anual']
        ), axis=1
    )
    df['score_total']          = df.apply(
        lambda r: calcular_score_total(r['score_historico'], r['score_economico']), axis=1
    )
    df['riesgo_oficialismo']   = df['score_total'].apply(derivar_riesgo_oficialismo)

    # Ordenar por score_total descendente (más favorable a D primero)
    df = df.sort_values('score_total', ascending=False).reset_index(drop=True)

    # Seleccionar y reordenar columnas del output
    output_cols = [
        'district_id', 'state_po', 'district',
        'last_winner', 'tendencia_historica', 'tipo_competitividad',
        'avg_abs_margin', 'avg_margin', 'margin_2024', 'min_abs_margin',
        'n_flips', 'n_cycles',
        'desempleo_ultimo', 'desempleo_var_anual',
        'score_historico', 'score_economico', 'score_total',
        'riesgo_oficialismo',
        'cycles', 'margins_by_cycle',
    ]
    df = df[output_cols]

    # Guardar
    out_path = os.path.join(OUT_DIR, 'house_analysis_2026.csv')
    df.to_csv(out_path, index=False)

    print(f'Guardado: {out_path}  ({len(df)} distritos)')
    print(f'\nEstados con datos BLS: {df["desempleo_ultimo"].notna().sum()} / {len(df)}')

    # Resumen por riesgo
    print('\n=== Distribución riesgo_oficialismo ===')
    print(df.groupby('riesgo_oficialismo').size().sort_values(ascending=False).to_string())

    # Top 15 Favorable D (mayor presión sobre oficialismo)
    print('\n=== Top 15 Favorable D (score_total más alto) ===')
    top_d = df[df['riesgo_oficialismo'] == 'Favorable D'].head(15)
    print(top_d[['district_id', 'last_winner', 'tendencia_historica',
                 'score_total', 'desempleo_ultimo', 'desempleo_var_anual']].to_string(index=False))

    # Top 15 Favorable R
    print('\n=== Top 15 Favorable R (score_total más bajo) ===')
    top_r = df[df['riesgo_oficialismo'] == 'Favorable R'].head(15)
    print(top_r[['district_id', 'last_winner', 'tendencia_historica',
                 'score_total', 'desempleo_ultimo', 'desempleo_var_anual']].to_string(index=False))

    print(f'\nDesempleo nacional de referencia usado: {DESEMPLEO_NACIONAL}%')
