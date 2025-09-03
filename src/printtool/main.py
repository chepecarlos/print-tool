
import argparse
import os
from printtool.MiLibrerias import  ConfigurarLogging, obtenerArchivoPaquete
from printtool.printtool import printtool
from printtool.inventario import inventario
logger = ConfigurarLogging(__name__)

def Parámetros():

    parser = argparse.ArgumentParser(description="Herramientas para emprendimiento de impresión 3D")
    parser.add_argument("--gui", "-g", help="Sistema interface gráfica", action="store_true")
    parser.add_argument("--inventario", "-i", help="Sistema de inventario", action="store_true")
    parser.add_argument("--depuracion", "-d", help="Activa la depuración", action="store_true")

    return parser.parse_args()

def buscarProyectos(Proyecto: list[str], ruta: str) -> list[str]:
    """Busca proyectos en la ruta especificada.

    Args:
        Proyecto (list[str]): Lista de proyectos encontrados.
        ruta (str): Ruta donde buscar los proyectos.

    Returns:
        list[str]: Lista de proyectos encontrados.
    """


    for carpeta, subcarpetas, archivos in os.walk(ruta):
        if printtool.esProyecto(carpeta):
            Proyecto.append(carpeta)
    return Proyecto


def main() -> None:
    """Función principal del programa."""
    
    args = Parámetros()
    
    if args.inventario:
        listaProyecto: list[str] = []
        "Lista de proyectos encontrados"
        directorioActual = os.getcwd()
        
        buscarProyectos(listaProyecto, directorioActual)
        
        inventarioProyectos: inventario = inventario()
        inventarioProyectos.listaProyectos = listaProyecto
        inventarioProyectos.cargarGUI()

    else:
        logger.info("Empezando Print-Tool")
        objetoPrintTool = printtool()
        objetoPrintTool.iniciarSistema()
        objetoPrintTool.cargarGUI()

if __name__ == "__main__":
    main()