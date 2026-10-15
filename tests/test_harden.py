import requests

from printtool.paginaConfig import _validar_margen, _validar_porcentaje_uso, _validar_positivo
from printtool.printtool import printtool
from printtool.utilidades import miDolibarr


def test_validadores_config_bloquean_divisiones_invalidas():
    pt = printtool()
    assert _validar_margen(pt, 100) == "Debe ser menor que 100 %"
    assert _validar_margen(pt, 99.9) is None
    assert _validar_positivo(pt, 0) == "Debe ser mayor que 0"
    assert _validar_positivo(pt, None) == "Campo obligatorio"
    assert _validar_porcentaje_uso(pt, 101) == "Máximo 100 %"
    assert _validar_porcentaje_uso(pt, 50) is None


class _Respuesta:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self.text = ""
        self._data = data

    def json(self):
        if self._data is None:
            raise ValueError("no es JSON")
        return self._data


def test_dolibarr_errores_legibles(monkeypatch):
    def timeout(*args, **kwargs):
        raise requests.Timeout()

    monkeypatch.setattr(miDolibarr.requests, "put", timeout)
    assert "no respondió" in miDolibarr.actualizarPrecioDolibarr("http://x", "t", 1, 10.0)

    monkeypatch.setattr(miDolibarr.requests, "get", lambda *a, **k: _Respuesta(404))
    assert miDolibarr.consultarPrecioDolibarr("http://x", "t", 7) == (
        None,
        "El producto 7 no existe en Dolibarr. Revise el ID en la pestaña Modelo.",
    )

    monkeypatch.setattr(miDolibarr.requests, "get", lambda *a, **k: _Respuesta(200))
    assert miDolibarr.consultarPrecioDolibarr("http://x", "t", 7)[0] is None

    monkeypatch.setattr(miDolibarr.requests, "get", lambda *a, **k: _Respuesta(200, {"price_ttc": "12.5"}))
    assert miDolibarr.consultarPrecioDolibarr("http://x", "t", 7) == (12.5, None)


def test_abrir_proyecto_reinicia_estado(tmp_path, monkeypatch):
    from printtool import printtool as modulo

    monkeypatch.setattr(modulo.ui.navigate, "reload", lambda: None)
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    pt = printtool()
    pt.folderProyecto = str(a)
    pt.iniciarSistema()
    pt.costoUnidad = 99.0

    pt.abrirProyecto(str(b))

    assert pt.archivoInfo == str(b / ".printtool" / "info.md")
    assert pt.costoUnidad == 0
