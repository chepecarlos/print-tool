import os

# WebKitGTK falla con "Could not create GBM EGL display" en algunos drivers
os.environ.setdefault("WEBKIT_DISABLE_DMABUF_RENDERER", "1")

import typer

from printtool.MiLibrerias import ConfigurarLogging
from printtool.printtool import printtool
from printtool.inventario import inventario
from printtool.commands import productos

logger = ConfigurarLogging(__name__)

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(
    name="printtool",
    help="Herramientas para emprendimiento de impresión 3D.",
    invoke_without_command=True,
    context_settings=HELP_SETTINGS,
)

app.add_typer(productos.app, name="productos", help="📦  Consulta productos y su id de Dolibarr.")


@app.callback()
def main(
    ctx: typer.Context,
    inventario_flag: bool = typer.Option(False, "--inventario", "-i", help="Sistema de inventario"),
    depuracion: bool = typer.Option(False, "--depuracion", "-d", help="Activa la depuración"),
) -> None:
    """printtool — Herramientas para emprendimiento de impresión 3D."""

    if ctx.invoked_subcommand is not None:
        return

    if inventario_flag:
        logger.info("Empezando Inventario de Print-Tool")
        inventarioProyectos = inventario()
        inventarioProyectos.listaProyectos = printtool.buscarProyectos(os.getcwd())
        inventarioProyectos.cargarGUI()
    else:
        logger.info("Empezando Print-Tool")
        app_printtool = printtool()
        app_printtool.iniciarSistema()
        app_printtool.cargarGui(True)
        app_printtool.iniciarGui()


if __name__ == "__main__":
    app()
