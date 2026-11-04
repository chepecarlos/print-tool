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


def test_inventario_no_reescribe_y_cuenta_omitidos(tmp_path):
    import os

    from printtool.inventario import inventario

    def proyecto(nombre, cuerpo):
        carpeta = tmp_path / nombre / ".printtool"
        carpeta.mkdir(parents=True)
        (carpeta / "info.md").write_text(f"---\n{cuerpo}---\n")
        return str(tmp_path / nombre)

    base = "link: ''\ntamaño: ''\ncosto: None\ncantidad: 1\ntiempo_ensamblaje: 0\ntipo: ''\n"
    bueno = proyecto("bueno", f"nombre: Llavero\nprecio_venta: 5\nid_producto_dolibarr: 3\n{base}")
    suelto = proyecto("suelto", f"nombre: Prueba\nprecio_venta: 0\n{base}")
    roto = proyecto("roto", f"nombre: Roto\nprecio_venta: 0\nid_producto_dolibarr: 4\ncolores: [1, 2]\n{base}")

    info = os.path.join(bueno, ".printtool", "info.md")
    inv = inventario()
    inv.listaProyectos = [bueno, suelto, roto]
    inv.cargarDatos()  # primera lectura: crea extras.md
    antes = os.path.getmtime(info)
    filas, _, sinDolibarr, conError = inv.cargarDatos()

    assert os.path.getmtime(info) == antes
    assert [f["nombre"] for f in filas] == ["Llavero"]
    assert filas[0]["precio"] == 5.0
    assert sinDolibarr == 1
    assert conError == [roto]
