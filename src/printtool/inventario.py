from nicegui import ui

from printtool.printtool import printtool


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
                ui.button(icon="close", on_click=dialog.close).props("flat round dense")
            with ui.element("q-card-section"):
                objetoPrintTool.cargarGUI(True)

        dialog.open()

    def cargarGUI(self):
        "Cargar la interfaz gráfica de usuario (GUI) del sistema de inventario."

        with ui.header(elevated=True) as cabecera:
            cabecera.classes("bg-teal-700 items-center justify-between")
            cabecera.style("height: 5vh; padding: 1px")
            with ui.row().classes("w-full justify-center items-center"):
                ui.label("Inventario de PrintTool").classes("text-h5 px-8")

        columnaInfo = [
            {"name": "nombre", "label": "Nombre", "field": "nombre", "align": "center"},
            {
                "name": "propiedad",
                "label": "Propiedad",
                "field": "propiedad",
                "align": "center",
            },
            {"name": "tipo", "label": "Tipo", "field": "tipo", "align": "center"},
            {
                "name": "precio",
                "label": "Precio",
                "field": "precio",
                "align": "center",
                "sortable": True,
                ":format": 'value => "$" + value',
            },
            {
                "name": "inventario",
                "label": "Inventario",
                "field": "inventario",
                "align": "center",
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
                    "precio": proyectoPrint.precioVenta,
                    "inventario": proyectoPrint.inventario,
                    "ruta": folderProyecto,
                }
            )

        self.tablaInfo = ui.table(
            columns=columnaInfo,
            rows=dataInfo,
            selection="single",
            row_key="ruta",
            pagination=5,
        )

        with self.tablaInfo as tabla:
            tabla.classes("w-full")
            tabla.style("height: 70vh; overflow-y: auto")

            with tabla.add_slot("top-right"):
                with ui.input(placeholder="Search").props("type=search").bind_value(
                    tabla, "filter"
                ).add_slot("append"):
                    ui.icon("search")
            with tabla.add_slot("top-left"):
                ui.button(
                    "Editar", on_click=lambda: self.abrirProyecto(tabla.selected)
                ).bind_visibility_from(
                    tabla, "selected", backward=lambda val: bool(val)
                )
            with tabla.add_slot("bottom-row"):
                with tabla.row():
                    with tabla.cell():
                        ui.button("pollo", icon="add").props("flat fab-mini")
                    with tabla.cell():
                        new_name = ui.input("Name")
                    with tabla.cell():
                        new_age = ui.number("Age")

        ui.label().bind_text_from(
            tabla, "selected", lambda val: f"Current selection: {val}"
        )
        self.tablaInfo.update()

        with ui.footer() as pie:
            pie.classes("bg-teal-700")
            pie.style("height: 5vh; padding: 1px")
            with ui.row().classes("w-full justify-center items-center"):
                ui.label("Creado por ChepeCarlos").classes("text-white")

        ui.run(
            native=True,
            window_size=(1200, 800),
            reload=False,
            dark=True,
            language="es",
        )
