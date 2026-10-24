from printtool.printtool import formatearHoras


def test_formatear_horas():
    assert formatearHoras(0.5) == "0 h 30 m"
    assert formatearHoras(23.99) == "23 h 59 m"
    assert formatearHoras(24) == "1 d 0 h 0 m"
    assert formatearHoras(176.1) == "7 d 8 h 6 m"
