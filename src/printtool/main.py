import argparse

from printtool.MiLibrerias import ConfigurarLogging
from printtool.printtool import printtool

logger = ConfigurarLogging(__name__)


def Parámetros():

    parser = argparse.ArgumentParser(description="Herramientas para emprendimiento de impresión 3D")
    parser.add_argument("--inventario", "-i", help="Sistema de inventario", action="store_true")
    parser.add_argument("--depuracion", "-d", help="Activa la depuración", action="store_true")
    return parser.parse_args()


def main():

    args = Parámetros()

    logger.info("Empezando Print-Tool")
    app = printtool()
    app.iniciarSistema()
    app.cargarGui(True)
    app.iniciarGui()


if __name__ == "__main__":
    main()
