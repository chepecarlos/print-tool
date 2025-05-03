
import argparse
from printtool.MiLibrerias import  ConfigurarLogging
from printtool.printtool import printtool
logger = ConfigurarLogging(__name__)

def Parámetros():

    parser = argparse.ArgumentParser(description="Herramientas para emprendimiento de impresión 3D")
    parser.add_argument("--gui", "-g", help="Sistema interface gráfica", action="store_true")
    parser.add_argument("--depuracion", "-d", help="Activa la depuración", action="store_true")

    return parser.parse_args()

def main() -> None:
    
    args = Parámetros()
    logger.info("Empezando Print-Tool")
    objetoPrintTool = printtool()
    objetoPrintTool.cargarGUI()

if __name__ == "__main__":
    main()