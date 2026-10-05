import pytest
import sys
import os
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
        ganadores = {1990: 'D', 1996: 'R', 2002: 'R', 2008: 'D', 2014: 'R', 2020: 'D'}
        assert calcular_coincidencia_estado(ganadores, CONTROL_SENADO) == 6

    def test_sin_coincidencia(self):
        ganadores = {1990: 'R', 1996: 'D', 2002: 'D', 2008: 'R', 2014: 'D', 2020: 'R'}
        assert calcular_coincidencia_estado(ganadores, CONTROL_SENADO) == 0

    def test_coincidencia_parcial(self):
        # 1990:D=D✓, 1996:D≠R✗, 2002:R=R✓, 2008:D=D✓, 2014:R=R✓, 2020:D=D✓ => 5
        ganadores = {1990: 'D', 1996: 'D', 2002: 'R', 2008: 'D', 2014: 'R', 2020: 'D'}
        assert calcular_coincidencia_estado(ganadores, CONTROL_SENADO) == 5

    def test_anio_faltante_ignorado(self):
        ganadores = {2002: 'R', 2008: 'D', 2014: 'R', 2020: 'D'}
        assert calcular_coincidencia_estado(ganadores, CONTROL_SENADO) == 4


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
