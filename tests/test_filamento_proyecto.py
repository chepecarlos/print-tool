import pytest

from printtool.printtool import printtool


@pytest.fixture
def pt():
    return printtool()


def test_usa_precio_del_sistema_si_no_hay_override(pt):
    pt.precioFilamento = 20
    pt.nombreFilamento = "PLA Genérico"
    pt.precioFilamentoProyecto = 0
    pt.nombreFilamentoProyecto = ""

    pt.cargarCostoPorGramo()

    assert pt.costoGramo == pytest.approx(20 / 1000)
    assert pt.nombreFilamentoActivo == "PLA Genérico"


def test_usa_precio_del_proyecto_si_esta_definido(pt):
    pt.precioFilamento = 20
    pt.nombreFilamento = "PLA Genérico"
    pt.precioFilamentoProyecto = 35
    pt.nombreFilamentoProyecto = "PETG Premium"

    pt.cargarCostoPorGramo()

    assert pt.costoGramo == pytest.approx(35 / 1000)
    assert pt.nombreFilamentoActivo == "PETG Premium"


def test_validar_numero_opcional_no_negativo_vacio_es_valido(pt):
    assert pt.validar_numero_opcional_no_negativo("") is None
    assert pt.validar_numero_opcional_no_negativo(None) is None


def test_validar_numero_opcional_no_negativo_negativo(pt):
    assert pt.validar_numero_opcional_no_negativo("-1") == "No puede ser negativo"
