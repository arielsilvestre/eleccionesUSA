# Plan de implementación — Scoring Senate 2026

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Objetivo:** Construir los scripts de análisis (bellwether + scoring) y producir
`output/senate_analysis_2026.csv`, la tabla maestra con score de riesgo por estado
swing Senate para las midterms 2026.

**Arquitectura:** Tres tareas secuenciales: (1) corrección de D-12 en DECISIONES.md
y actualización de ROADMAP.md, (2) `analysis/03_bellwether.py` que carga MIT data
1990–2020 y calcula coincidencia histórica por estado, (3) `analysis/04_scoring.py`
que combina los tres ejes en scores 0–100 y produce la tabla final.

**Stack técnico:** Python 3, pandas, pytest

---

## AVISO IMPORTANTE — Corrección a D-12

D-12 en DECISIONES.md dice "2002, 2006, 2010, 2014, 2018, 2022" como los 6 midterms.
Eso es incorrecto: esos son años midterm en general, pero los escaños Class 2 votan
cada 6 años. Los 6 ciclos electorales Class 2 más recientes en el rango MIT (1976–2024)
son: **1990, 1996, 2002, 2008, 2014, 2020**. Los años 1996, 2008 y 2020 son
elecciones presidenciales, pero son los únicos ciclos donde estos escaños estuvieron
en juego. La Tarea 1 corrige D-12.

---

## Archivos del plan

| Acción | Archivo |
|---|---|
| Crear | `analysis/03_bellwether.py` |
| Crear | `analysis/04_scoring.py` |
| Crear | `tests/test_03_bellwether.py` |
| Crear | `tests/test_04_scoring.py` |
| Modificar | `DECISIONES.md` — corregir D-12 |
| Modificar | `ROADMAP.md` — agregar tarea 2.6 |
| Generar | `output/senate_bellwether.csv` |
| Generar | `output/senate_analysis_2026.csv` |

---

## Tarea 1 — Corregir D-12 y actualizar ROADMAP

**Archivos:**
- Modificar: `DECISIONES.md`
- Modificar: `ROADMAP.md`

- [ ] **Paso 1.1: Corregir D-12 en DECISIONES.md**

Buscar el bloque `## D-12` y reemplazar la descripción de años.
El texto actual dice "2002, 2006, 2010, 2014, 2018, 2022".
Reemplazar por:

```
## D-12 — Rango temporal bellwether: ciclos electorales Class 2 (1990–2020)

**Fecha:** Sesión 3 — 05/10/2026 (corregido en implementación)
**Aplica a:** Senate
**Decisión:** el cálculo de coincidencia bellwether usa los 6 ciclos electorales
más recientes donde los escaños Class 2 estuvieron en juego: 1990, 1996, 2002,
2008, 2014, 2020. Incluye tanto años midterm (1990, 2002, 2014) como años
presidenciales (1996, 2008, 2020), porque Class 2 solo vota cada 6 años —
no hay 6 midterms disponibles en un rango razonable.

**Error corregido:** la versión original de D-12 listaba "2002, 2006, 2010,
2014, 2018, 2022" como si los escaños Class 2 votaran en cada midterm. Incorrecto.
```

- [ ] **Paso 1.2: Agregar tarea 2.6 al ROADMAP**

En `ROADMAP.md`, debajo de `- [ ] **2.5**`, agregar:

```markdown
- [ ] **2.6** Script bellwether: calcular coincidencia histórica por estado swing
      Senate (Class 2, ciclos 1990–2020) → `output/senate_bellwether.csv`
```

Y debajo de `## Fase 5`, agregar las tareas de scoring:

```markdown
- [ ] **5.3** Script scoring: combinar score histórico + económico + bellwether
      → `output/senate_analysis_2026.csv` con tabla maestra Senate
```

- [ ] **Paso 1.3: Commit**

```bash
git add DECISIONES.md ROADMAP.md
git commit -m "docs: corregir D-12 (años Class 2 correctos) y agregar tareas 2.6 y 5.3"
```

---

## Tarea 2 — Script bellwether (`analysis/03_bellwether.py`)

**Archivos:**
- Crear: `tests/test_03_bellwether.py`
- Crear: `analysis/analisis_03_bellwether.py`
- Generar: `output/senate_bellwether.csv`

### Contexto

El script carga `data/mit-election-lab/1976-2024-senate-state.csv`, filtra a los
11 estados swing Senate y a los años Class 2 (1990, 1996, 2002, 2008, 2014, 2020),
determina el ganador de cada carrera, y compara contra el partido que controló el
Senado tras cada elección.

**Control del Senado por año (hardcodeado):**
```python
CONTROL_SENADO = {
    1990: 'D',  # 56D-44R tras midterms 1990
    1996: 'R',  # 55R-45D tras elecciones 1996
    2002: 'R',  # 51R-48D-1I tras midterms 2002
    2008: 'D',  # 59D-41R tras elecciones 2008
    2014: 'R',  # 54R-46D tras midterms 2014
    2020: 'D',  # 50D-50R + VP Harris tras runoffs GA ene 2021
}
```

- [ ] **Paso 2.1: Escribir tests que fallan**

Crear `tests/test_03_bellwether.py`:

```python
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'analysis'))

from analisis_03_bellwether import (
    calcular_coincidencia_estado,
    calcular_score_bellwether,
    es_bellwether,
    formatear_coincidencia,
)

CONTROL_SENADO = {
    1990: 'D', 1996: 'R', 2002: 'R', 2008: 'D', 2014: 'R', 2020: 'D',
}


class TestCalcularCoincidenciaEstado:
    def test_coincidencia_perfecta(self):
        # Estado ganado por D en años D, R en años R
        ganadores = {1990: 'D', 1996: 'R', 2002: 'R', 2008: 'D', 2014: 'R', 2020: 'D'}
        resultado = calcular_coincidencia_estado(ganadores, CONTROL_SENADO)
        assert resultado == 6

    def test_sin_coincidencia(self):
        # Estado siempre gana el partido contrario al que controla
        ganadores = {1990: 'R', 1996: 'D', 2002: 'D', 2008: 'R', 2014: 'D', 2020: 'R'}
        resultado = calcular_coincidencia_estado(ganadores, CONTROL_SENADO)
        assert resultado == 0

    def test_coincidencia_parcial(self):
        ganadores = {1990: 'D', 1996: 'D', 2002: 'R', 2008: 'D', 2014: 'R', 2020: 'D'}
        # 1990:D=D✓, 1996:D≠R✗, 2002:R=R✓, 2008:D=D✓, 2014:R=R✓, 2020:D=D✓ => 5
        resultado = calcular_coincidencia_estado(ganadores, CONTROL_SENADO)
        assert resultado == 5

    def test_anio_faltante_ignorado(self):
        # Solo 4 años disponibles
        ganadores = {2002: 'R', 2008: 'D', 2014: 'R', 2020: 'D'}
        resultado = calcular_coincidencia_estado(ganadores, CONTROL_SENADO)
        assert resultado == 4


class TestCalcularScoreBellwether:
    def test_6_de_6(self):
        assert calcular_score_bellwether(6, 6) == 100

    def test_5_de_6(self):
        assert calcular_score_bellwether(5, 6) == 80

    def test_4_de_6(self):
        assert calcular_score_bellwether(4, 6) == 60

    def test_3_de_6(self):
        assert calcular_score_bellwether(3, 6) == 50

    def test_sin_datos(self):
        assert calcular_score_bellwether(0, 0) == 50


class TestEsBellwether:
    def test_verdadero_con_4_de_6(self):
        assert es_bellwether(4, 6) is True

    def test_verdadero_con_6_de_6(self):
        assert es_bellwether(6, 6) is True

    def test_falso_con_3_de_6(self):
        assert es_bellwether(3, 6) is False

    def test_falso_sin_datos(self):
        assert es_bellwether(0, 0) is False


class TestFormatearCoincidencia:
    def test_formato_estandar(self):
        assert formatear_coincidencia(5, 6) == '5 de 6'

    def test_formato_cero(self):
        assert formatear_coincidencia(0, 6) == '0 de 6'
```

- [ ] **Paso 2.2: Correr tests para confirmar que fallan**

```bash
cd "C:\Users\asilvestre\OneDrive - PSF\Documentos\GitHub\eleccionesUSA"
python -m pytest tests/test_03_bellwether.py -v
```

Resultado esperado: `ModuleNotFoundError: No module named 'analisis_03_bellwether'`

- [ ] **Paso 2.3: Implementar `analysis/03_bellwether.py`**

```python
"""
Bellwether Senate — Tarea 2.6
Calcula coincidencia histórica entre el ganador del escaño Senate Class 2
de cada estado swing y el partido que controló el Senado tras cada elección.

Ciclos Class 2 analizados: 1990, 1996, 2002, 2008, 2014, 2020
"""

import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIT_DIR  = os.path.join(BASE_DIR, 'data', 'mit-election-lab')
OUT_DIR  = os.path.join(BASE_DIR, 'output')
os.makedirs(OUT_DIR, exist_ok=True)

ANIOS_CLASS2 = [1990, 1996, 2002, 2008, 2014, 2020]

CONTROL_SENADO = {
    1990: 'D',  # 56D-44R tras midterms 1990
    1996: 'R',  # 55R-45D tras elecciones 1996
    2002: 'R',  # 51R-48D-1I tras midterms 2002
    2008: 'D',  # 59D-41R tras elecciones 2008
    2014: 'R',  # 54R-46D tras midterms 2014
    2020: 'D',  # 50D-50R + VP Harris tras runoffs GA ene 2021
}


# ─────────────────────────────────────────────────────────────────────────────
# Funciones puras (testeables)
# ─────────────────────────────────────────────────────────────────────────────

def calcular_coincidencia_estado(ganadores_por_anio: dict, control_senado: dict) -> int:
    """
    Recibe {año: partido_ganador} y {año: partido_control_senado}.
    Devuelve el número de años en que el ganador coincide con el controlador.
    Solo cuenta años presentes en ambos dicts.
    """
    coincidencias = 0
    for anio, ganador in ganadores_por_anio.items():
        control = control_senado.get(anio)
        if control and ganador in ('D', 'R'):
            if ganador == control:
                coincidencias += 1
    return coincidencias


def calcular_score_bellwether(coincidencias: int, total: int) -> int:
    """Score 0-100 según proporción de coincidencias. Sin datos devuelve 50 (neutro)."""
    if total == 0:
        return 50
    if coincidencias == total:          # 6/6
        return 100
    if coincidencias >= total * 5 / 6:  # 5/6
        return 80
    if coincidencias >= total * 4 / 6:  # 4/6
        return 60
    return 50  # < 4/6: neutro


def es_bellwether(coincidencias: int, total: int) -> bool:
    """Verdadero si coincidencia >= 4/6 del total."""
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
    Carga MIT Senate CSV, filtra a estados y años Class 2.
    Devuelve DataFrame con columnas: year, state_po, ganador ('D', 'R', u 'OTRO').
    """
    df = pd.read_csv(ruta_csv, low_memory=False)
    df = df[
        (df['stage']   == 'gen') &
        (df['special'] == False) &
        (df['year'].isin(anios)) &
        (df['state_po'].isin(estados)) &
        (df['writein'] == False)
    ].copy()

    # Agregar votos por año/estado/partido
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
    dr = dr.rename(columns={'D': 'votos_d', 'R': 'votos_r'})
    dr['votos_d'] = dr.get('votos_d', 0).fillna(0)
    dr['votos_r'] = dr.get('votos_r', 0).fillna(0)
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
                f"{a}:{g}({'✓' if control_senado.get(a) == g else '✗'})"
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
```

- [ ] **Paso 2.4: Correr tests para confirmar que pasan**

```bash
python -m pytest tests/test_03_bellwether.py -v
```

Resultado esperado:
```
PASSED tests/test_03_bellwether.py::TestCalcularCoincidenciaEstado::test_coincidencia_perfecta
PASSED tests/test_03_bellwether.py::TestCalcularCoincidenciaEstado::test_sin_coincidencia
PASSED tests/test_03_bellwether.py::TestCalcularCoincidenciaEstado::test_coincidencia_parcial
PASSED tests/test_03_bellwether.py::TestCalcularCoincidenciaEstado::test_anio_faltante_ignorado
PASSED tests/test_03_bellwether.py::TestCalcularScoreBellwether::test_6_de_6
PASSED tests/test_03_bellwether.py::TestCalcularScoreBellwether::test_5_de_6
PASSED tests/test_03_bellwether.py::TestCalcularScoreBellwether::test_4_de_6
PASSED tests/test_03_bellwether.py::TestCalcularScoreBellwether::test_3_de_6
PASSED tests/test_03_bellwether.py::TestCalcularScoreBellwether::test_sin_datos
PASSED tests/test_03_bellwether.py::TestEsBellwether::test_verdadero_con_4_de_6
PASSED tests/test_03_bellwether.py::TestEsBellwether::test_verdadero_con_6_de_6
PASSED tests/test_03_bellwether.py::TestEsBellwether::test_falso_con_3_de_6
PASSED tests/test_03_bellwether.py::TestEsBellwether::test_falso_sin_datos
PASSED tests/test_03_bellwether.py::TestFormatearCoincidencia::test_formato_estandar
PASSED tests/test_03_bellwether.py::TestFormatearCoincidencia::test_formato_cero
15 passed
```

- [ ] **Paso 2.5: Ejecutar el script y verificar output**

```bash
python analysis/03_bellwether.py
```

Verificar que se generó `output/senate_bellwether.csv` con 11 filas (una por estado swing Senate).

- [ ] **Paso 2.6: Commit**

```bash
git add analysis/analisis_03_bellwether.py tests/test_03_bellwether.py output/senate_bellwether.csv
git commit -m "feat(bellwether): tarea 2.6 — coincidencia historica Class 2 por estado swing"
```

---

## Tarea 3 — Script scoring + tabla final (`analysis/04_scoring.py`)

**Archivos:**
- Crear: `tests/test_04_scoring.py`
- Crear: `analysis/analisis_04_scoring.py`
- Generar: `output/senate_analysis_2026.csv`

### Contexto de entradas

El script une tres fuentes:
- `output/senate_swing_2026.csv` — columnas clave: `state_po`, `avg_abs_margin`, `avg_margin`, `margins_by_year`, `years_raced`
- `output/bls_swing_context.csv` — columnas clave: `state_po`, `swing_senate`, `unemployment_rate_latest`, `unemployment_yoy_change`
- `output/senate_bellwether.csv` — columnas clave: `state_po`, `es_bellwether`, `coincidencia_bellwether`, `score_bellwether`

- [ ] **Paso 3.1: Escribir tests que fallan**

Crear `tests/test_04_scoring.py`:

```python
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'analysis'))

from analisis_04_scoring import (
    calcular_score_historico,
    derivar_tendencia_historica,
    derivar_tipo_competitividad,
    calcular_score_economico,
    calcular_score_total,
    derivar_riesgo_oficialismo,
)


class TestCalcularScoreHistorico:
    def test_margen_cero(self):
        assert calcular_score_historico(0.0) == 100

    def test_margen_2pp(self):
        assert calcular_score_historico(2.0) == 88

    def test_margen_5pp(self):
        assert calcular_score_historico(5.0) == 70

    def test_margen_10pp(self):
        assert calcular_score_historico(10.0) == 40

    def test_margen_20pp(self):
        assert calcular_score_historico(20.0) == 0  # clamp en 0

    def test_margen_negativo_imposible_devuelve_100(self):
        # avg_abs_margin nunca es negativo, pero por seguridad
        assert calcular_score_historico(-1.0) == 100


class TestDerivarTendenciaHistorica:
    def test_solido_r(self):
        assert derivar_tendencia_historica(15.0) == 'Sólido R'

    def test_leve_r(self):
        assert derivar_tendencia_historica(7.0) == 'Leve R'

    def test_disputado_positivo(self):
        assert derivar_tendencia_historica(3.0) == 'Disputado'

    def test_disputado_negativo(self):
        assert derivar_tendencia_historica(-3.0) == 'Disputado'

    def test_leve_d(self):
        assert derivar_tendencia_historica(-7.0) == 'Leve D'

    def test_solido_d(self):
        assert derivar_tendencia_historica(-15.0) == 'Sólido D'

    def test_umbral_exacto_5(self):
        # 5.0 exacto es Leve R (> 5 es Leve R, pero == 5 cae en Disputado)
        assert derivar_tendencia_historica(5.0) == 'Disputado'

    def test_umbral_exacto_10(self):
        # 10.0 exacto es Leve R (> 10 es Sólido R)
        assert derivar_tendencia_historica(10.0) == 'Leve R'


class TestDerivarTipoCompetitividad:
    def test_sin_flip(self):
        # Todos ganados por R
        resultado = derivar_tipo_competitividad('5.9,1.8', '2016,2020')
        assert resultado == 'Competitivo'

    def test_flip_reciente(self):
        # 2018: margen 3.0 > 0 → R gana; 2020: margen -2.0 < 0 → D gana
        # Flip en el ciclo más reciente (2020) → 'Flip reciente'
        resultado = derivar_tipo_competitividad('3.0,-2.0', '2018,2020')
        assert resultado == 'Flip reciente'

    def test_flip_ocasional(self):
        # Flip en 2016→2018 pero no en 2018→2020
        resultado = derivar_tipo_competitividad('5.0,-3.0,2.0', '2016,2018,2020')
        assert resultado == 'Flip ocasional'


class TestCalcularScoreEconomico:
    def test_estado_peor_desempleo(self):
        # Estado con tasa máxima y mayor aumento: score = 100
        score = calcular_score_economico(
            tasa=6.0, var=1.0,
            tasa_min=3.0, tasa_max=6.0,
            var_min=-1.0, var_max=1.0,
        )
        assert score == 100

    def test_estado_mejor_desempleo(self):
        # Estado con tasa mínima y mayor caída: score = 0
        score = calcular_score_economico(
            tasa=3.0, var=-1.0,
            tasa_min=3.0, tasa_max=6.0,
            var_min=-1.0, var_max=1.0,
        )
        assert score == 0

    def test_estado_medio(self):
        # Exactamente en la mitad en ambas dimensiones
        score = calcular_score_economico(
            tasa=4.5, var=0.0,
            tasa_min=3.0, tasa_max=6.0,
            var_min=-1.0, var_max=1.0,
        )
        assert score == 50

    def test_sin_variacion_entre_estados(self):
        # Todos los estados tienen la misma tasa: nivel = 50 (neutro)
        score = calcular_score_economico(
            tasa=4.0, var=0.5,
            tasa_min=4.0, tasa_max=4.0,
            var_min=0.0, var_max=1.0,
        )
        assert score == 50  # nivel=50 + var=50 → promedio ponderado


class TestCalcularScoreTotal:
    def test_ponderacion_correcta(self):
        # 50% historico + 30% economico + 20% bellwether
        resultado = calcular_score_total(80, 60, 40)
        esperado = round(80 * 0.5 + 60 * 0.3 + 40 * 0.2, 1)
        assert resultado == esperado

    def test_todos_iguales(self):
        assert calcular_score_total(50, 50, 50) == 50.0


class TestDerivarRiesgoOficialismo:
    def test_favorable_r(self):
        assert derivar_riesgo_oficialismo(20.0) == 'Favorable R'

    def test_limite_favorable_r(self):
        assert derivar_riesgo_oficialismo(39.0) == 'Favorable R'

    def test_disputado_inferior(self):
        assert derivar_riesgo_oficialismo(40.0) == 'Disputado'

    def test_disputado_superior(self):
        assert derivar_riesgo_oficialismo(60.0) == 'Disputado'

    def test_favorable_d(self):
        assert derivar_riesgo_oficialismo(61.0) == 'Favorable D'

    def test_score_maximo(self):
        assert derivar_riesgo_oficialismo(100.0) == 'Favorable D'
```

- [ ] **Paso 3.2: Correr tests para confirmar que fallan**

```bash
python -m pytest tests/test_04_scoring.py -v
```

Resultado esperado: `ModuleNotFoundError: No module named 'analisis_04_scoring'`

- [ ] **Paso 3.3: Implementar `analysis/04_scoring.py`**

```python
"""
Scoring Senate 2026 — Tarea 5.3
Combina score histórico (MIT), económico (BLS) y bellwether
para producir la tabla maestra senate_analysis_2026.csv.

Pesos: 50% histórico + 30% económico + 20% bellwether (D-13)
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
    Escala: 0pp=100, 17pp=0 (lineal, clamp 0-100).
    Formula: max(0, min(100, round(100 - margen * 6)))
    """
    return max(0, min(100, round(100 - avg_abs_margin * 6)))


def derivar_tendencia_historica(avg_margin: float) -> str:
    """
    Clasifica el estado según margen promedio signado (R positivo, D negativo).
    > 10pp  → 'Sólido R'
    5-10pp  → 'Leve R'
    -5–5pp  → 'Disputado'
    -10–-5pp → 'Leve D'
    < -10pp → 'Sólido D'
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
    'Flip ocasional' — flip en ciclos anteriores pero no el más reciente
    'Competitivo'    — sin flips detectados
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
    0–39  → 'Favorable R'
    40–60 → 'Disputado'
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
    # ── Cargar entradas ──
    swing    = pd.read_csv(os.path.join(OUT_DIR, 'senate_swing_2026.csv'))
    bls      = pd.read_csv(os.path.join(OUT_DIR, 'bls_swing_context.csv'))
    bellw    = pd.read_csv(os.path.join(OUT_DIR, 'senate_bellwether.csv'))

    # Filtrar BLS a estados swing Senate
    bls_senate = bls[bls['swing_senate'] == True].copy()

    # Parámetros de normalización económica (sobre los 11 estados swing Senate)
    tasa_min = bls_senate['unemployment_rate_latest'].min()
    tasa_max = bls_senate['unemployment_rate_latest'].max()
    var_min  = bls_senate['unemployment_yoy_change'].min()
    var_max  = bls_senate['unemployment_yoy_change'].max()

    # ── Calcular scores ──
    swing['score_historico'] = swing['avg_abs_margin'].apply(calcular_score_historico)
    swing['tendencia_historica'] = swing['avg_margin'].apply(derivar_tendencia_historica)
    swing['tipo_competitividad'] = swing.apply(
        lambda r: derivar_tipo_competitividad(r['margins_by_year'], r['years_raced']),
        axis=1,
    )

    bls_senate = bls_senate.copy()
    bls_senate['score_economico'] = bls_senate.apply(
        lambda r: calcular_score_economico(
            r['unemployment_rate_latest'], r['unemployment_yoy_change'],
            tasa_min, tasa_max, var_min, var_max,
        ),
        axis=1,
    )

    # ── Unir todo ──
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
        lambda r: calcular_score_total(r['score_historico'], r['score_economico'],
                                       r['score_bellwether']),
        axis=1,
    )
    tabla['riesgo_oficialismo'] = tabla['score_total'].apply(derivar_riesgo_oficialismo)

    # ── Renombrar columnas para output final ──
    tabla = tabla.rename(columns={
        'state_po': 'estado',
        'unemployment_rate_latest': 'desempleo_ultimo',
        'unemployment_yoy_change': 'desempleo_var_anual',
    })

    # ── Ordenar y exportar ──
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
```

- [ ] **Paso 3.4: Correr tests para confirmar que pasan**

```bash
python -m pytest tests/test_04_scoring.py -v
```

Resultado esperado:
```
PASSED tests/test_04_scoring.py::TestCalcularScoreHistorico::test_margen_cero
PASSED tests/test_04_scoring.py::TestCalcularScoreHistorico::test_margen_2pp
PASSED tests/test_04_scoring.py::TestCalcularScoreHistorico::test_margen_5pp
PASSED tests/test_04_scoring.py::TestCalcularScoreHistorico::test_margen_10pp
PASSED tests/test_04_scoring.py::TestCalcularScoreHistorico::test_margen_20pp
PASSED tests/test_04_scoring.py::TestCalcularScoreHistorico::test_margen_negativo_imposible_devuelve_100
PASSED tests/test_04_scoring.py::TestDerivarTendenciaHistorica::test_solido_r
... (todos pasan)
```

- [ ] **Paso 3.5: Ejecutar el script y verificar output**

```bash
python analysis/04_scoring.py
```

Verificar:
- Se imprime tabla con 11 filas, una por estado
- Columna `riesgo_oficialismo` contiene solo valores: 'Favorable R', 'Disputado', 'Favorable D'
- Sin valores nulos en `score_total`
- Archivo `output/senate_analysis_2026.csv` generado

- [ ] **Paso 3.6: Commit**

```bash
git add analysis/analisis_04_scoring.py tests/test_04_scoring.py output/senate_analysis_2026.csv
git commit -m "feat(scoring): tarea 5.3 — tabla maestra senate_analysis_2026 con score ponderado"
```

---

## Tarea 4 — Cerrar ROADMAP

**Archivos:**
- Modificar: `ROADMAP.md`

- [ ] **Paso 4.1: Marcar tareas completadas en ROADMAP**

Actualizar `ROADMAP.md`:
- `[ ] **2.6**` → `[x] **2.6**`
- `[ ] **5.3**` (o el número que corresponda) → `[x] **5.3**`

- [ ] **Paso 4.2: Actualizar BITACORA con sesión 3**

Agregar entrada en `BITACORA.md` documentando:
- Scripts creados: `03_bellwether.py`, `04_scoring.py`
- Outputs generados: `senate_bellwether.csv`, `senate_analysis_2026.csv`
- Corrección D-12
- Estado al cierre: tareas 2.6 y 5.3 completadas

- [ ] **Paso 4.3: Commit final de sesión**

```bash
git add ROADMAP.md BITACORA.md
git commit -m "docs: cerrar tareas 2.6 y 5.3, actualizar bitacora sesion 3"
```

---

## Notas de implementación

### Nomenclatura de archivos
Los scripts se nombran `analisis_03_bellwether.py` y `analisis_04_scoring.py`
(con prefijo `analisis_`) para que sean importables directamente en los tests.
Python no permite importar módulos que empiezan con número.

### Verificación de datos bellwether
Algunos estados swing pueden no tener data para todos los 6 años Class 2
si hubo elecciones especiales o el MIT data no los cubre. El script maneja
esto contando solo los años disponibles en `total`.

### Nota sobre 2020 y Georgia
Georgia tuvo dos carreras Senate en 2020 (Class 2 regular + especial Class 3).
El filtro `special == False` en `cargar_ganadores_class2` asegura que solo
se considere la carrera regular Class 2.
