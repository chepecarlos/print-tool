import pytest

from printtool.printtool import printtool


@pytest.fixture
def pt():
    return printtool()


def test_validar_numero_no_negativo_campo_vacio(pt):
    assert pt.validar_numero_no_negativo("") == "Campo obligatorio"


def test_validar_numero_no_negativo_negativo(pt):
    assert pt.validar_numero_no_negativo("-1") == "No puede ser negativo"


def test_validar_numero_no_negativo_valido(pt):
    assert pt.validar_numero_no_negativo("3.5") is None


def test_validar_entero_no_negativo_rechaza_decimal(pt):
    assert pt.validar_entero_no_negativo("3.5") == "Debe ser un número entero"


def test_validar_entero_no_negativo_valido(pt):
    assert pt.validar_entero_no_negativo("3") is None


def test_validar_texto_requerido_vacio(pt):
    assert pt.validar_texto_requerido("   ") == "Campo obligatorio"


def test_validar_texto_requerido_valido(pt):
    assert pt.validar_texto_requerido("SKU-1") is None


@pytest.mark.parametrize(
    "valor,esperado",
    [
        ("3,5", 3.5),
        ("3.5", 3.5),
        ("", None),
        (None, None),
        ("abc", None),
    ],
)
def test_parse_float_seguro(pt, valor, esperado):
    assert pt.parse_float_seguro(valor) == esperado


@pytest.mark.parametrize(
    "valor,esperado",
    [
        ("4", 4),
        ("4.0", 4),
        ("4.5", None),
        ("abc", None),
    ],
)
def test_parse_int_seguro(pt, valor, esperado):
    assert pt.parse_int_seguro(valor) == esperado
