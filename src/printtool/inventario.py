from nicegui import ui

# import multiprocessing

# multiprocessing.set_start_method("spawn", force=True)

from printtool.printtool import printtool
from printtool.tema import aplicarTema


class inventario:

    listaProyectos: list[str]
    "Lista de proyectos en el sistema de inventario"

    def __init__(self):
        self.listaProyectos = []

    def agregar_proyecto(self, proyecto: str):
        """Agregar un proyecto al sistema de inventario.

        Args:
            proyecto (str): Ruta del proyecto a agregar.
        """
        self.listaProyectos.append(proyecto)

    def abrirProyecto(self, proyecto: list[dict]):
        """Abrir un proyecto en el sistema de inventario.

        Args:
            proyecto (list[dict]): Información del proyecto a abrir.
        """
        rutaProyecto = proyecto[0]["ruta"]

        objetoPrintTool = printtool()
        objetoPrintTool.folderProyecto = rutaProyecto
        objetoPrintTool.iniciarSistema()

        with ui.dialog() as dialog, ui.card():
            with ui.element("q-toolbar"):
                with ui.element("q-toolbar-title"):
                    ui.label(objetoPrintTool.nombreModelo)
                ui.button(icon="close", on_click=dialog.close).props('flat round dense aria-label="Cerrar"')
            with ui.element("q-card-section"):
                objetoPrintTool.cargarGui(True)

        dialog.open()

    def cargarGUI(self):
        "Cargar la interfaz gráfica de usuario (GUI) del sistema de inventario."

        aplicarTema()

        with ui.header() as cabecera:
            cabecera.classes("bg-primary items-center justify-between")
            cabecera.style("min-height: 48px; padding: 0 16px")
            with ui.row().classes("w-full items-center no-wrap"):
                ui.label("Inventario de PrintTool").classes("text-h5 truncate min-w-0").props('role=heading aria-level=1')

        columnaInfo = [
            {"name": "nombre", "label": "Nombre", "field": "nombre", "align": "left", "sortable": True},
            {
                "name": "propiedad",
                "label": "Propiedad",
                "field": "propiedad",
                "align": "left",
            },
            {"name": "tipo", "label": "Tipo", "field": "tipo", "align": "left"},
            {
                "name": "precio",
                "label": "Precio",
                "field": "precio",
                "align": "right",
                "sortable": True,
            },
            {
                "name": "inventario",
                "label": "Inventario",
                "field": "inventario",
                "align": "right",
                "sortable": True,
            },
        ]

        dataInfo = []

        for folderProyecto in self.listaProyectos:
            proyectoPrint = printtool()
            proyectoPrint.folderProyecto = folderProyecto
            proyectoPrint.iniciarSistema()
            nombreProyecto = proyectoPrint.nombreModelo

            if nombreProyecto == "":
                nombreProyecto = folderProyecto.split("/")[-1]
            dataInfo.append(
                {
                    "nombre": nombreProyecto,
                    "propiedad": proyectoPrint.propiedadModelo,
                    "tipo": proyectoPrint.tipoModelo,
                    "precio": proyectoPrint.precioVentaFinal,
                    "inventario": proyectoPrint.inventario,
                    "ruta": folderProyecto,
                }
            )

        # el símbolo viene de la configuración global, igual para todos los proyectos
        simbolo = dataInfo and proyectoPrint.símboloMoneda or "$"
        columnaInfo[3][":format"] = f'value => "{simbolo} " + Number(value).toFixed(2)'

        self.tablaInfo = ui.table(
            columns=columnaInfo,
            rows=dataInfo,
            selection="single",
            row_key="ruta",
            pagination=8,
        )

        with self.tablaInfo as tabla:
            tabla.classes("w-full h-full")
            # tabla.style("height: 70vh; overflow-y: auto")

            with tabla.add_slot("top-right"):
                with (
                    ui.input(placeholder="Buscar").props("type=search").bind_value(tabla, "filter").add_slot("append")
                ):
                    ui.icon("search")
            with tabla.add_slot("top-left"):
                ui.button("Abrir proyecto", on_click=lambda: self.abrirProyecto(tabla.selected)).bind_visibility_from(
                    tabla, "selected", backward=lambda val: bool(val)
                )
        self.tablaInfo.update()

        with ui.footer() as pie:
            pie.classes("bg-primary")
            pie.style("min-height: 32px; padding: 4px 16px")
            with ui.row().classes("w-full justify-center items-center"):
                ui.label("Creado por ChepeCarlos").classes("text-white")

        ui.run(
            native=False,
            # window_size=(1200, 800),
            reload=False,
            dark=True,
            language="es",
            title="Inventario de PrintTool",
        )
