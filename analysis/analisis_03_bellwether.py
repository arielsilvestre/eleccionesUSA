"""
Bellwether Senate — Tarea 2.6
Calcula coincidencia histórica entre el ganador del escaño Senate Class 2
de cada estado swing y el partido que controló el Senado tras cada elección.

Ciclos Class 2 analizados: 1990, 1996, 2002, 2008, 2014, 2020
Control del Senado por año (D-12):
  1990: D (56D-44R tras midterms)
  1996: R (55R-45D tras elecciones presidenciales)
  2002: R (51R-48D-1I tras midterms)
  2008: D (59D-41R tras elecciones presidenciales)
  2014: R (54R-46D tras midterms)
  2020: D (50D-50R + VP Harris tras runoffs GA enero 2021)
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIT_DIR  = os.path.join(BASE_DIR, 'data', 'mit-election-lab')
OUT_DIR  = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

ANIOS_CLASS2 = [1990, 1996, 2002, 2008, 2014, 2020]

CONTROL_SENADO = {
    1990: 'D',
    1996: 'R',
    2002: 'R',
    2008: 'D',
    2014: 'R',
    2020: 'D',
}


# ─────────────────────────────────────────────────────────────────────────────
# Funciones puras (testeables)
# ─────────────────────────────────────────────────────────────────────────────

def calcular_coincidencia_estado(ganadores_por_anio: dict, control_senado: dict) -> int:
    """
    Recibe {año: partido_ganador} y {año: partido_control_senado}.
    Devuelve el número de años en que el ganador coincide con el controlador.
    Solo cuenta años presentes en ambos dicts. Ignora ganadores que no sean D o R.
    """
    coincidencias = 0
    for anio, ganador in ganadores_por_anio.items():
        control = control_senado.get(anio)
        if control and ganador in ('D', 'R'):
            if ganador == control:
                coincidencias += 1
    return coincidencias


def calcular_score_bellwether(coincidencias: int, total: int) -> int:
    """
    Score 0-100 según proporción de coincidencias.
    Sin datos devuelve 50 (neutro, no suma ni resta señal).
    """
    if total == 0:
        return 50
    if coincidencias == total:            # 6/6
        return 100
    if coincidencias >= total * 5 / 6:   # 5/6
        return 80
    if coincidencias >= total * 4 / 6:   # 4/6 (umbral mínimo — D-11)
        return 60
    return 50  # < 4/6: neutro


def es_bellwether(coincidencias: int, total: int) -> bool:
    """Verdadero si coincidencia >= 4/6 del total (D-11)."""
    if total == 0:
        return False
    return coincidencias / total >= 4 / 6


def formatear_coincidencia(coincidencias: int, total: int) -> str:
    """Devuelve cadena legible, p.ej. '5 de 6'."""
    return f'{coincidencias} de {total}'


# ─────────────────────────────────────────────────────────────────────────────
# Carga y procesamiento de datos
# ─────────────────────────────────────────────────────────────────────────────

def cargar_ganadores_class2(ruta_csv: str, estados: list, anios: list) -> pd.DataFrame:
    """
    Carga MIT Senate CSV, filtra a estados swing y años Class 2.
    Devuelve DataFrame con columnas: year, state_po, ganador ('D' o 'R').
    Usa special==False para excluir elecciones especiales (ej. GA 2020 Class 3).
    """
    df = pd.read_csv(ruta_csv, low_memory=False)
    df = df[
        (df['stage']   == 'gen') &
        (df['special'] == False) &
        (df['year'].isin(anios)) &
        (df['state_po'].isin(estados)) &
        (df['writein'] == False)
    ].copy()

    cand = (
        df.groupby(['year', 'state_po', 'party_simplified'], as_index=False)
        ['candidatevotes'].sum()
    )

    dr = (
        cand[cand['party_simplified'].isin(['DEMOCRAT', 'REPUBLICAN'])]
        .assign(partido=lambda x: x['party_simplified'].map(
            {'DEMOCRAT': 'D', 'REPUBLICAN': 'R'}
        ))
        .pivot_table(
            index=['year', 'state_po'],
            columns='partido',
            values='candidatevotes',
            aggfunc='sum',
        )
        .reset_index()
    )
    dr.columns.name = None

    if 'D' not in dr.columns:
        dr['D'] = 0.0
    if 'R' not in dr.columns:
        dr['R'] = 0.0

    dr = dr.rename(columns={'D': 'votos_d', 'R': 'votos_r'})
    dr['votos_d'] = dr['votos_d'].fillna(0)
    dr['votos_r'] = dr['votos_r'].fillna(0)
    dr['ganador'] = dr.apply(
        lambda r: 'R' if r['votos_r'] > r['votos_d'] else 'D', axis=1
    )
    return dr[['year', 'state_po', 'ganador', 'votos_d', 'votos_r']]


def calcular_bellwether_por_estado(
    ganadores_df: pd.DataFrame,
    control_senado: dict,
) -> pd.DataFrame:
    """
    Recibe DataFrame year/state_po/ganador.
    Devuelve DataFrame con una fila por estado con métricas bellwether.
    """
    filas = []
    for estado, grupo in ganadores_df.groupby('state_po'):
        ganadores_dict = dict(zip(grupo['year'], grupo['ganador']))
        total = len([a for a in ganadores_dict if a in control_senado])
        coincidencias = calcular_coincidencia_estado(ganadores_dict, control_senado)
        filas.append({
            'state_po': estado,
            'es_bellwether': es_bellwether(coincidencias, total),
            'coincidencia_bellwether': formatear_coincidencia(coincidencias, total),
            'score_bellwether': calcular_score_bellwether(coincidencias, total),
            'detalle_anios': ', '.join(
                f"{a}:{g}({'ok' if control_senado.get(a) == g else 'no'})"
                for a, g in sorted(ganadores_dict.items())
            ),
        })
    return pd.DataFrame(filas)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    senate_swing = pd.read_csv(os.path.join(OUT_DIR, 'senate_swing_2026.csv'))
    estados_swing = senate_swing['state_po'].tolist()

    ruta_mit = os.path.join(MIT_DIR, '1976-2024-senate-state.csv')
    ganadores = cargar_ganadores_class2(ruta_mit, estados_swing, ANIOS_CLASS2)

    resultado = calcular_bellwether_por_estado(ganadores, CONTROL_SENADO)
    resultado = resultado.sort_values('score_bellwether', ascending=False)

    print(f'\n=== BELLWETHER SENATE — {len(resultado)} estados ===')
    print(resultado[['state_po', 'es_bellwether', 'coincidencia_bellwether',
                      'score_bellwether', 'detalle_anios']].to_string(index=False))

    salida = os.path.join(OUT_DIR, 'senate_bellwether.csv')
    resultado.to_csv(salida, index=False)
    print(f'\n-> Guardado: {salida}')
