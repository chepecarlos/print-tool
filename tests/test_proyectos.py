from printtool.printtool import printtool


def test_esProyecto_falso_si_faltan_archivos(tmp_path):
    assert printtool.esProyecto(str(tmp_path)) is False


def test_esProyecto_formato_nuevo(tmp_path):
    carpeta = tmp_path / ".printtool"
    carpeta.mkdir()
    (carpeta / "info.md").write_text("")
    (carpeta / "extras.md").write_text("")

    assert printtool.esProyecto(str(tmp_path)) is True


def test_esProyecto_formato_legacy(tmp_path):
    (tmp_path / "info.md").write_text("")
    (tmp_path / "extras.md").write_text("")

    assert printtool.esProyecto(str(tmp_path)) is True


def test_buscarProyectos_encuentra_subcarpetas(tmp_path):
    proyecto = tmp_path / "modelo_a" / ".printtool"
    proyecto.mkdir(parents=True)
    (proyecto / "info.md").write_text("")
    (proyecto / "extras.md").write_text("")

    otra = tmp_path / "no_es_proyecto"
    otra.mkdir()

    encontrados = printtool.buscarProyectos(str(tmp_path))

    assert encontrados == [str(tmp_path / "modelo_a")]


def test_buscarProyectos_ignora_carpetas_ocultas(tmp_path):
    proyecto = tmp_path / ".oculta" / ".printtool"
    proyecto.mkdir(parents=True)
    (proyecto / "info.md").write_text("")
    (proyecto / "extras.md").write_text("")

    assert printtool.buscarProyectos(str(tmp_path)) == []
