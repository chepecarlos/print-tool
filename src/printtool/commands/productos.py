"""Comandos para consultar productos (proyectos PrintTool) y su vínculo con Dolibarr."""

import json
from pathlib import Path

import typer

from printtool.printtool import printtool

HELP_SETTINGS = {"help_option_names": ["-h", "-help", "--help"]}

app = typer.Typer(no_args_is_help=True, context_settings=HELP_SETTINGS)


@app.command("listar")
def listar(
    ruta: Path = typer.Argument(Path.cwd(), help="Carpeta raíz donde buscar proyectos recursivamente."),
    recalcular: bool = typer.Option(
        False, "--recalcular", "-r", help="Releer los archivos G-code en vez de usar los gramos/horas ya guardados."
    ),
) -> None:
    """📦  Busca proyectos recursivamente y muestra sus productos con id de Dolibarr (JSON)."""

    productos = []
    for folder in printtool.buscarProyectos(str(ruta)):
        proyecto = printtool()
        proyecto.folderProyecto = folder
        proyecto.iniciarSistema()

        if not proyecto.idProductoDolibarr:
            continue

        costo = proyecto.calcularCostoUnidad(recalcular)

        productos.append(
            {
                "ruta": folder,
                "nombre": proyecto.nombreModelo,
                "sku": proyecto.skuModelo,
                "tipo": proyecto.tipoModelo,
                "precio_venta": proyecto.precioVentaFinal,
                "precio_referencia": round(proyecto.precioVentaReferencia, 2),
                "costo": round(costo, 2),
                "id_producto_dolibarr": proyecto.idProductoDolibarr,
            }
        )

    print(json.dumps(productos, ensure_ascii=False, indent=2))
