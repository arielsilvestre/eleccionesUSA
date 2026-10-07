"""
Tarea 6.4 — Mapa interactivo Senate 2026

Genera output/senate_map_2026.html: choropleth plotly de 50 estados con:
  - Paleta de 8 categorías (D-18)
  - Tooltip completo por estado (D-19)
  - 33 Class 2 vivos + 17 Class 1/3 en gris-azulado (D-20)
"""

import os
import pandas as pd
import plotly.graph_objects as go

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR  = os.path.join(BASE_DIR, 'output')

# ─────────────────────────────────────────────────────────────────────────────
# Paleta de colores (D-18)
# ─────────────────────────────────────────────────────────────────────────────

PALETA = {
    'Sólido D':    '#0D47A1',
    'Leve D':      '#1976D2',
    'Favorable D': '#2196F3',
    'Disputado':   '#FFD600',
    'Favorable R': '#FF8F00',
    'Leve R':      '#E53935',
    'Sólido R':    '#B71C1C',
    'No vota 2026': '#90A4AE',
}

# Orden de la leyenda (D → R → gris)
ORDEN_CATEGORIAS = [
    'Sólido D', 'Leve D', 'Favorable D',
    'Disputado',
    'Favorable R', 'Leve R', 'Sólido R',
    'No vota 2026',
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de formato
# ─────────────────────────────────────────────────────────────────────────────

def fmt_partido(codigo) -> str:
    if pd.isna(codigo):
        return '—'
    return 'Demócrata' if str(codigo) == 'D' else 'Republicano'


def fmt_margen(margen, ganador) -> str:
    """Convierte margen (R-D) a texto legible con partido ganador."""
    if pd.isna(margen) or pd.isna(ganador):
        return 'Sin oposición D/R'
    m = abs(float(margen))
    return f'{ganador} +{m:.1f}pp'


def fmt_desempleo(tasa, var) -> str:
    if pd.isna(tasa):
        return '—'
    var_str = ''
    if not pd.isna(var):
        signo = '+' if float(var) >= 0 else ''
        var_str = f' ({signo}{float(var):.1f}pp interanual)'
    return f'{float(tasa):.1f}%{var_str}'


def fmt_bool(valor) -> str:
    if pd.isna(valor):
        return '—'
    return 'Sí' if valor else 'No'


def construir_tooltip(row) -> str:
    """Genera el texto HTML del tooltip para un estado."""
    sp    = row['state_po']
    nombre = row['estado']
    cat   = row['categoria_mapa']

    lineas = [f'<b>{nombre} ({sp})</b>']

    if not row['vota_2026']:
        # Non-Class 2: tooltip simplificado
        lineas.append('No vota en 2026 · Class 1/3')
        if not pd.isna(row['ganador_mas_reciente']):
            anio = int(row['anio_mas_reciente']) if not pd.isna(row['anio_mas_reciente']) else '—'
            lineas.append(f"Último resultado ({anio}): {fmt_margen(row['margen_mas_reciente'], row['ganador_mas_reciente'])}")
        return '<br>'.join(lineas)

    # Class 2
    lineas.append(f'Vota en 2026 · Class 2')
    lineas.append(f"Resultado 2020: {fmt_margen(row['margen_2020'], row['ganador_2020'])}")

    if not pd.isna(row['tendencia_historica']):
        lineas.append(f"Tendencia histórica: {row['tendencia_historica']}")

    if row['es_swing']:
        lineas.append('—')
        if not pd.isna(row['score_total']):
            lineas.append(f"Score total: {row['score_total']:.1f} → <b>{row['riesgo_oficialismo']}</b>")
        if not pd.isna(row['es_bellwether']):
            bell_str = f"Bellwether: {fmt_bool(row['es_bellwether'])}"
            if not pd.isna(row['coincidencia_bellwether']):
                bell_str += f" ({row['coincidencia_bellwether']} ciclos Class 2)"
            lineas.append(bell_str)
        if not pd.isna(row['desempleo_ultimo']):
            lineas.append(f"Desempleo ago-2026: {fmt_desempleo(row['desempleo_ultimo'], row['desempleo_var_anual'])}")

    return '<br>'.join(lineas)


# ─────────────────────────────────────────────────────────────────────────────
# Construcción del mapa
# ─────────────────────────────────────────────────────────────────────────────

def build_map(df: pd.DataFrame) -> go.Figure:
    df = df.copy()
    df['tooltip'] = df.apply(construir_tooltip, axis=1)

    fig = go.Figure()

    for cat in ORDEN_CATEGORIAS:
        subset = df[df['categoria_mapa'] == cat]
        if subset.empty:
            continue

        color = PALETA[cat]
        # Para categorías sin datos en este ciclo: mostrar igual en leyenda
        show_legend = True

        fig.add_trace(go.Choropleth(
            locations=subset['state_po'],
            z=[1] * len(subset),          # valor constante; el color viene de marker
            locationmode='USA-states',
            showscale=False,
            colorscale=[[0, color], [1, color]],
            marker_line_color='white',
            marker_line_width=1.5,
            name=cat,
            hovertext=subset['tooltip'],
            hovertemplate='%{hovertext}<extra></extra>',
            showlegend=show_legend,
            legendgroup=cat,
        ))

    fig.update_layout(
        title={
            'text': 'Senado de EE.UU. 2026 — Condiciones de fondo por estado',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18},
        },
        geo=dict(
            scope='usa',
            projection_type='albers usa',
            showlakes=False,
            bgcolor='#f8f9fa',
        ),
        legend=dict(
            title='<b>Categoría</b>',
            orientation='v',
            x=1.0,
            y=0.5,
            yanchor='middle',
            bgcolor='rgba(255,255,255,0.85)',
            bordercolor='#cccccc',
            borderwidth=1,
        ),
        paper_bgcolor='#f8f9fa',
        plot_bgcolor='#f8f9fa',
        margin=dict(l=0, r=180, t=60, b=20),
        hoverlabel=dict(
            bgcolor='white',
            bordercolor='#cccccc',
            font_size=13,
            font_family='Arial',
        ),
        annotations=[
            dict(
                text=(
                    'Fuente: MIT Election Lab (Harvard Dataverse) · BLS LAUS · '
                    'Análisis propio. Sin datos de encuestas. '
                    'Gris: no tienen elección Senate en 2026.'
                ),
                x=0.5, y=-0.02,
                xref='paper', yref='paper',
                showarrow=False,
                font=dict(size=10, color='#666'),
                xanchor='center',
            )
        ],
    )

    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    df = pd.read_csv(os.path.join(OUT_DIR, 'senate_map_data.csv'))

    fig = build_map(df)

    out_path = os.path.join(OUT_DIR, 'senate_map_2026.html')
    fig.write_html(
        out_path,
        include_plotlyjs='cdn',   # referencia CDN para mantener el HTML liviano
        full_html=True,
    )

    print(f'Mapa guardado: {out_path}')
    print(f'Estados en el mapa: {len(df)}')
    print()
    print('Categorías incluidas:')
    for cat in ORDEN_CATEGORIAS:
        n = (df['categoria_mapa'] == cat).sum()
        if n:
            print(f'  {cat}: {n}')
