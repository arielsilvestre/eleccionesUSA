import pytest
import sys
import os
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
        assert calcular_score_historico(20.0) == 0

    def test_margen_negativo_clamp_100(self):
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

    def test_umbral_exacto_5_es_disputado(self):
        assert derivar_tendencia_historica(5.0) == 'Disputado'

    def test_umbral_exacto_10_es_leve_r(self):
        assert derivar_tendencia_historica(10.0) == 'Leve R'


class TestDerivarTipoCompetitividad:
    def test_sin_flip(self):
        # Ambos ciclos ganados por R (margenes positivos)
        assert derivar_tipo_competitividad('5.9,1.8', '2016,2020') == 'Competitivo'

    def test_flip_reciente(self):
        # 2018: margen 3.0 > 0 → R gana; 2020: margen -2.0 < 0 → D gana
        # Flip en el ciclo más reciente (2020) → 'Flip reciente'
        assert derivar_tipo_competitividad('3.0,-2.0', '2018,2020') == 'Flip reciente'

    def test_flip_ocasional(self):
        # 2016→2018: flip (5.0 a -3.0), pero 2018→2020: sin flip (-3.0 a -2.0)
        assert derivar_tipo_competitividad('5.0,-3.0,-2.0', '2016,2018,2020') == 'Flip ocasional'

    def test_un_solo_ciclo_sin_flip(self):
        assert derivar_tipo_competitividad('3.0', '2020') == 'Competitivo'


class TestCalcularScoreEconomico:
    def test_estado_peor_desempleo(self):
        score = calcular_score_economico(
            tasa=6.0, var=1.0,
            tasa_min=3.0, tasa_max=6.0,
            var_min=-1.0, var_max=1.0,
        )
        assert score == 100

    def test_estado_mejor_desempleo(self):
        score = calcular_score_economico(
            tasa=3.0, var=-1.0,
            tasa_min=3.0, tasa_max=6.0,
            var_min=-1.0, var_max=1.0,
        )
        assert score == 0

    def test_estado_medio(self):
        score = calcular_score_economico(
            tasa=4.5, var=0.0,
            tasa_min=3.0, tasa_max=6.0,
            var_min=-1.0, var_max=1.0,
        )
        assert score == 50

    def test_sin_variacion_entre_estados_nivel_neutro(self):
        # Todos misma tasa → nivel_norm=50; var=0.5 de 0-1 → var_norm=50
        score = calcular_score_economico(
            tasa=4.0, var=0.5,
            tasa_min=4.0, tasa_max=4.0,
            var_min=0.0, var_max=1.0,
        )
        assert score == 50


class TestCalcularScoreTotal:
    def test_ponderacion_correcta(self):
        esperado = round(80 * 0.5 + 60 * 0.3 + 40 * 0.2, 1)
        assert calcular_score_total(80, 60, 40) == esperado

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
