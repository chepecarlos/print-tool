import subprocess
import sys

from nicegui import ui

from printtool.MiLibrerias import ConfigurarLogging
from printtool.printtool import printtool
from printtool.tema import aplicarTema

logger = ConfigurarLogging(__name__)


class inventario:

    listaProyectos: list[str]
    "Lista de proyectos en el sistema de inventario"

    def __init__(self):
        self.listaProyectos = []

    def abrirProyecto(self, proyecto: list[dict]):
        """Abrir un proyecto en su propia ventana de PrintTool.

        Args:
            proyecto (list[dict]): Fila seleccionada de la tabla.
        """
        if not proyecto:
            return
        rutaProyecto = proyecto[0]["ruta"]
        logger.info(f"Abriendo proyecto {rutaProyecto}")
        # ponytail: proceso aparte, PrintTool registra sus propias rutas "/" y no convive en este servidor
        subprocess.Popen([sys.executable, "-m", "printtool.main"], cwd=rutaProyecto)

    def cargarDatos(self) -> tuple[list[dict], str]:
        "Leer info.md de cada proyecto; devuelve filas de la tabla y símbolo de moneda."

        dataInfo = []
        simbolo = "$"
        for folderProyecto in self.listaProyectos:
            proyectoPrint = printtool()
            proyectoPrint.folderProyecto = folderProyecto
            try:
                proyectoPrint.iniciarSistema()
            except Exception as error:
                logger.error(f"No se pudo leer {folderProyecto}: {error}")
                continue

            # igual que `productos listar`: es producto si está vinculado a Dolibarr
            if not proyectoPrint.idProductoDolibarr:
                continue

            # el símbolo viene de la configuración global, igual para todos los proyectos
            simbolo = proyectoPrint.símboloMoneda
            dataInfo.append(
                {
                    "nombre": proyectoPrint.nombreModelo or folderProyecto.rstrip("/").split("/")[-1],
                    "propiedad": proyectoPrint.propiedadModelo,
                    "tipo": proyectoPrint.tipoModelo,
                    # hex de mayor a menor gramos, como en la pestaña Info
                    "colores": [c for c, _ in sorted(proyectoPrint.coloresTotales.items(), key=lambda x: -x[1])],
                    "precio": proyectoPrint.precioVentaFinal or 0,
                    "inventario": proyectoPrint.inventario,
                    "ruta": folderProyecto,
                }
            )
        return dataInfo, simbolo

    def cargarGUI(self):
        "Cargar la interfaz gráfica de usuario (GUI) del sistema de inventario."

        @ui.page("/")
        def paginaInventario():
            aplicarTema()

            with ui.header() as cabecera:
                cabecera.classes("bg-primary items-center justify-between")
                cabecera.style("min-height: 48px; padding: 0 16px")
                with ui.row().classes("w-full items-center no-wrap"):
                    ui.label("Inventario de PrintTool").classes("text-h5 truncate min-w-0").props(
                        "role=heading aria-level=1"
                    )

            dataInfo, simbolo = self.cargarDatos()

            columnaInfo = [
                {"name": "nombre", "label": "Nombre", "field": "nombre", "align": "left", "sortable": True},
                {"name": "propiedad", "label": "Propiedad", "field": "propiedad", "align": "left"},
                {"name": "tipo", "label": "Tipo", "field": "tipo", "align": "left"},
                {"name": "colores", "label": "Colores", "field": "colores", "align": "left"},
                {
                    "name": "precio",
                    "label": "Precio",
                    "field": "precio",
                    "align": "right",
                    "sortable": True,
                    ":format": f'value => "{simbolo} " + Number(value).toFixed(2)',
                },
                {"name": "inventario", "label": "Inventario", "field": "inventario", "align": "right", "sortable": True},
            ]

            with ui.table(
                columns=columnaInfo,
                rows=dataInfo,
                selection="single",
                row_key="ruta",
                pagination=8,
            ) as tabla:
                tabla.classes("w-full h-full")
                tabla.add_slot(
                    "body-cell-colores",
                    """
                    <q-td :props="props">
                        <span v-for="color in props.value" :key="color" :title="color" role="img" :aria-label="color"
                            class="inline-block w-4 h-4 rounded-full border border-gray-400 q-mr-xs"
                            :style="{background: color}"></span>
                    </q-td>
                    """,
                )

                with tabla.add_slot("top-right"):
                    with (
                        ui.input(placeholder="Buscar")
                        .props('type=search aria-label="Buscar proyectos"')
                        .bind_value(tabla, "filter")
                        .add_slot("append")
                    ):
                        ui.icon("search")
                with tabla.add_slot("top-left"):
                    ui.button("Abrir proyecto", on_click=lambda: self.abrirProyecto(tabla.selected)).bind_visibility_from(
                        tabla, "selected", backward=lambda val: bool(val)
                    )

            with ui.footer() as pie:
                pie.classes("bg-primary")
                pie.style("min-height: 32px; padding: 4px 16px")
                with ui.row().classes("w-full justify-center items-center"):
                    ui.label("Creado por ChepeCarlos").classes("text-white")

        # native busca un puerto libre solo, igual que la ventana principal
        ui.run(
            native=True,
            window_size=(1024, 786),
            reload=False,
            dark=True,
            show=False,
            language="es",
            title="Inventario de PrintTool",
            uvicorn_logging_level="warning",
        )
