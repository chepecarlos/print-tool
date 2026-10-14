import pytest

from printtool.printtool import printtool


def test_margen_separado_por_impresion_extras_y_ensamblado():
    pt = printtool()
    pt.costoTotalImpresion = 10
    pt.costoExtras = 8.5
    pt.costoEnsamblado = 1.7
    pt.costoUnidad = 10 + 8.5 + 1.7
    pt.porcentajeGananciaBase = 50
    pt.porcentajeGananciaExtras = 15
    pt.porcentajeGananciaEnsamblado = 15
    pt.porcentajeInpuesto = 0
    pt.precioVentaFinal = None

    pt.calculandoPrecioVenta()

    # 10/0.5 + 8.5/0.85 + 1.7/0.85 = 20 + 10 + 2
    assert pt.precioSinIvaReferencia == pytest.approx(32)
    assert pt.gananciaBase == pytest.approx(11.8)
    assert pt.porcentajeGananciaReferencia == pytest.approx(11.8 / 32 * 100)
