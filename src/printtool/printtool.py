from nicegui import ui, app
import os
import codecs
import re
from pathlib import Path

from printtool.dataGcode import dataGcode

from printtool.MiLibrerias import (
    ObtenerArchivo,
    SalvarValor,
    SalvarArchivo,
    agregarValor,
    configurarArchivo,
    obtenerArchivoPaquete,
    ConfigurarLogging,
)

logger = ConfigurarLogging(__name__)


class printtool:
    """Clase principal para la herramienta de emprendimiento de impresión 3D."""

    totalGramos: float = 0
    "Total de gramos de la impresión"

    totalHoras: float = 0
    "Total de horas de la impresión"

    # Información de la impresión
    nombreModelo: str = ""
    "Nombre del modelo"
    propiedadModelo: str = ""
    "Propiedad del modelo"
    tipoModelo: str = "desconocido"
    "Tipo de modelo (alcancía, maceta, figuras, otro)"
    descripciónModelo: str = ""
    "Descripción del modelo"

    tiempoEnsamblado: float = 0
    "Tiempo de ensamblado del modelo (Minutos)"

    skuModelo: str = ""
    "SKU del modelo"
    linkModelo: str = ""
    "Link del modelo"

    precioVenta: float = 0
    "Precio de venta ingresado por el usuario"

    tipoProductos: list[str] = ["desconocido", "alcancía", "maceta", "figuras", "otro"]

    folderProyecto: str = None
    "Folder del proyecto"

    archivoInfo: str = None
    archivoExtras: str = None

    infoBase: dict[str, float] = None
    """Información base para cálculos de costos

    Ejemplo:
        Costo Maquina
        Vida Util
        Ganancia
    """

    inventario: int = 0
    "Cantidad de productos en inventario"

    tablaDataGcode = None
    "Tabla de datos de los archivos G-code (material, tiempo, tipo, color), para pestaña Modelo"

    tabInfo: ui.tab = None
    "tab para información básica"
    tabCosto: ui.tab = None
    "tab para costos"
    tabPrecio: ui.tab = None
    "tab para precios"
    tabData: ui.tab = None
    "tab para datos"

    def __init__(self) -> None:
        self.totalGramos: float = 0
        self.totalHoras: float = 0
        self.precioVenta: float = 0
        self.costoTotalImpresion: float = 0
        self.costoExtras: float = 0

    #     @staticmethod
    #     def esProyecto(folder: str) -> bool:
    #         "confirma si el proyecto es válido"
    #         return os.path.exists(os.path.join(folder, "info.md")) and os.path.exists(os.path.join(folder, "extras.md"))

    def iniciarSistema(self) -> None:

        self.configurarData()

        logger.debug(f"Buscando en: {self.archivoInfo}")

        if not os.path.exists(self.archivoExtras):
            data = dict()
            SalvarArchivo(self.archivoExtras, data)
            logger.info(f"Creando data base de {self.archivoExtras}")

        self.infoBase = ObtenerArchivo("data/costos.md")
        if self.infoBase is None:
            logger.error("Error fatal con data/costos.md")
            exit(1)
        self.infoCostos = ObtenerArchivo(self.archivoInfo, False)
        self.infoExtras = ObtenerArchivo(self.archivoExtras, False)

        self.cargarInfoBasica()

    def configurarData(self) -> None:
        """Configurar la carpeta del proyecto y los archivos de información."""

        if self.folderProyecto is None:
            logger.info("Usando folder actual para proyecto")
            self.folderProyecto = Path.cwd()
        self.archivoInfo = os.path.join(self.folderProyecto, "info.md")
        self.archivoExtras = os.path.join(self.folderProyecto, "extras.md")

        dataBaseInfo = obtenerArchivoPaquete("printtool", "config/info.md")
        if dataBaseInfo is None:
            logger.error("Error fatal con paquete falta config/info.md")
            exit(1)

        configurarArchivo(self.archivoInfo, dataBaseInfo)

    def cargarInfoBasica(self) -> None:
        """Cargar información básica del modelo desde archivo info.md"""
        self.nombreModelo = self.infoCostos.get("nombre")
        self.linkModelo = self.infoCostos.get("link")
        self.inventario = int(self.infoCostos.get("inventario", 0))
        self.precioVenta = self.infoCostos.get("precio_venta")
        self.skuModelo = self.infoCostos.get("sku", "")
        self.propiedadModelo = self.infoCostos.get("propiedad", "")
        self.descripciónModelo = self.infoCostos.get("descripción", "")
        self.tipoModelo = self.infoCostos.get("tipo", "desconocido")
        self.tiempoEnsamblado = float(self.infoCostos.get("tiempo_ensamblaje", 0))

        if self.tipoModelo not in self.tipoProductos:
            self.tipoModelo = "desconocido"

        self.totalGramos = float(self.infoCostos.get("total_gramos", 0))
        self.totalHoras = float(self.infoCostos.get("total_horas", 0))

        self.filamentosDisponibles: list[dict] = self.infoBase.get("filamentos")

        self.filamentoSeleccionado = int(self.infoCostos.get("filamento_seleccionado", 1))
        self.listaFilamentos = dict()
        for filamento in self.filamentosDisponibles:
            id = filamento.get("id", "")
            nombre = filamento.get("nombre", "")
            precio = filamento.get("precio", "")
            material = filamento.get("material", "")
            if id is not None:
                self.listaFilamentos[id] = f"{nombre}-{material} ${precio:.02f}"

        if self.filamentoSeleccionado not in self.listaFilamentos:
            self.filamentoSeleccionado = 1

    def cargarGuiInfo(self) -> None:
        """Cargar la interfaz gráfica de usuario para la información básica del modelo."""

        dataInfo = [
            {"key": "nombreModelo", "humano": "Nombre", "formato": lambda x: f"{x}"},
            {"key": "propiedadModelo", "humano": "Propiedad", "formato": lambda x: f"{x}"},
            {"key": "tipoModelo", "humano": "Tipo", "formato": lambda x: f"{x}"},
            {"key": "inventario", "humano": "Inventario", "formato": lambda x: f"{x}"},
            {"key": "skuModelo", "humano": "SKU", "formato": lambda x: f"{x}"},
            # {"key": "Material", "humano": "Material", "formato": "PLA"},
            {"key": "totalGramos", "humano": "Total Filamento", "formato": lambda x: f"{x:.2f}g"},
            {
                "key": "totalHoras",
                "humano": "Tiempo impresión",
                "formato": lambda x: f"{int(x)}h {int((x - int(x)) * 60)}m",
            },
            {"key": "precioVenta", "humano": "Precio", "formato": lambda x: f"${x:.2f}"},
        ]
        with ui.grid(columns=2):

            for item in dataInfo:
                ui.label(item["humano"])
                ui.label().bind_text_from(
                    self,
                    item["key"],
                    lambda x, transform_func=item["formato"]: transform_func(x),
                )

    def cargarGuiCostos(self):
        with ui.scroll_area().classes("w-full h-100 border border-2 border-teal-600h").style("height: 75vh"):
            with ui.row().classes("w-full justify-center items-center"):
                with ui.column().classes("justify-center items-center"):
                    ui.button("Recargar Costos", on_click=self.cargarCostos).classes("w-64")

                    with ui.row().props("rounded outlined dense"):
                        self.textoTiempoEnsamblado = ui.input(
                            label="Tiempo Ensamblado (Minutos)",
                            value=self.tiempoEnsamblado,
                            validation=self.validar_numero,
                        ).props("rounded outlined dense")
                        ui.button(on_click=self.actualizarEnsamblado, icon="send")
                        self.textoTiempoEnsamblado.on("keydown.enter", self.actualizarEnsamblado)

                    if self.filamentosDisponibles is not None:
                        self.selectorFilamento = ui.select(
                            self.listaFilamentos,
                            value=self.filamentoSeleccionado,
                            label="Material",
                            on_change=self.seleccionarFilamento,
                        ).classes("min-w-64")

                infoCostos = [
                    {
                        "name": "nombre",
                        "label": "Nombre",
                        "field": "nombre",
                        "required": True,
                        "align": "left",
                    },
                    {
                        "name": "valor",
                        "label": "Referencia",
                        "field": "valor",
                        "required": True,
                        "align": "center",
                    },
                ]

                dataCostos = [
                    {"nombre": "Total filamento (g)", "valor": 0},
                    {"nombre": "Tiempo Ensamblaje (m)", "valor": 0},
                    {"nombre": "Costo Material", "valor": 0},
                    {"nombre": "Eficiencia filamento", "valor": 0},
                    {"nombre": "Costo de impresión hora", "valor": 0},
                    {"nombre": "Costo ensamblado", "valor": 0},
                    {"nombre": "Costo Extra", "valor": 0},
                    {"nombre": "Costo Unidad", "valor": 0},
                ]
                self.tablaCostos = ui.table(
                    columns=infoCostos,
                    rows=dataCostos,
                    row_key="nombre",
                )
                self.tablaCostos.classes("w-100")

                infoArchivo = [
                    {
                        "name": "nombre",
                        "label": "Modelos",
                        "field": "nombre",
                        "required": True,
                        "align": "left",
                    },
                    # {'name': 'archivo', 'label': 'Archivo', 'field': 'archivo'},
                    {
                        "name": "cantidad",
                        "label": "Cantidad",
                        "field": "cantidad",
                        "sortable": False,
                    },
                    {
                        "name": "material",
                        "label": "Material",
                        "field": "material",
                        "sortable": True,
                    },
                    {
                        "name": "tiempo",
                        "label": "Tiempo",
                        "field": "tiempo",
                        "sortable": True,
                    },
                    {"name": "tipo", "label": "Material", "field": "tipo"},
                    {"name": "color", "label": "Color", "field": "color"},
                ]

                with ui.scroll_area().classes("w-full h-100 border border-2 border-teal-600h"):
                    with ui.row().classes("w-full justify-center items-center"):
                        self.tablaDataGcode = ui.table(
                            columns=infoArchivo,
                            rows=[],
                            row_key="nombre",
                            pagination=5,
                        )

                infoCostos = [
                    {
                        "name": "extra",
                        "label": "Extras",
                        "field": "extra",
                        "required": True,
                        "align": "left",
                    },
                    {
                        "name": "precio",
                        "label": "Precio",
                        "field": "precio",
                        "required": True,
                        "align": "left",
                    },
                ]

                self.tablaDataExtras = ui.table(
                    columns=infoCostos,
                    rows=[],
                    row_key="extra",
                    selection="single",
                    pagination=5,
                )

    def validar_numero(self, value):
        try:
            float(value)  # Intentar convertir el valor a float
            return None  # Si es válido, no hay error
        except ValueError:
            return "No es un número válido"
        # Si falla, devolver mensaje de error

    def actualizarEnsamblado(self):
        self.tiempoEnsamblado = float(self.textoTiempoEnsamblado.value)
        SalvarValor(self.archivoInfo, "tiempo_ensamblaje", self.tiempoEnsamblado, local=False)
        self.cargarCostos()
        ui.notify(f"Tiempo de ensamblado actualizado a {self.tiempoEnsamblado} minutos")

    def cargarCostos(self):
        # ui.notify("Cargando Costos...")
        self.cargarDataArchivos()
        self.costosExtras()
        self.calcularCostos()
        self.calculandoPrecioVenta()

    def costosExtras(self):
        """Cargar y mostrar los costos extras desde el archivo extras.md"""
        dataCostos = []
        self.costoExtras = 0
        self.tablaDataExtras.clear()

        self.infoExtras = ObtenerArchivo(self.archivoExtras, False)

        if self.infoExtras is not None:
            for extra in self.infoExtras:
                dataCostos.append({"extra": extra, "precio": f"${self.infoExtras[extra]:.2f}"})
                self.costoExtras += float(self.infoExtras[extra])
        dataCostos.append({"extra": "Total", "precio": f"${self.costoExtras:.2f}"})

        with self.tablaDataExtras as tabla:
            with tabla.add_slot("bottom-row"):
                with tabla.row():
                    with tabla.cell():
                        ui.button(on_click=self.agregarCostoExtra, icon="add").props("flat fab-mini")
                    with tabla.cell():
                        self.textoExtra = ui.input("Extra")
                    with tabla.cell():
                        self.textoCostoExtra = ui.number("Precio")
                with tabla.add_slot("top-right"):
                    with (
                        ui.input(placeholder="Search")
                        .props("type=search")
                        .bind_value(tabla, "filter")
                        .add_slot("append")
                    ):
                        ui.icon("search")
            with tabla.add_slot("top-left"):
                ui.button(icon="delete", color="red", on_click=self.borrarExtra).bind_visibility_from(
                    self.tablaDataExtras, "selected", backward=lambda val: bool(val)
                )

        self.tablaDataExtras.rows = dataCostos
        self.tablaDataExtras.update()

    def calculandoPrecioVenta(self):

        ganancia: float = float(self.infoBase.get("ganancia", 10))

        precioAntesIva = self.costoUnidad / (1 - ganancia / 100)
        cantidadGanancia = precioAntesIva - self.costoUnidad
        iva = precioAntesIva * 0.13
        precioSugerido = precioAntesIva + iva

        if self.precioVenta is None:
            self.precioVenta = precioSugerido

        if self.precioVenta >= 0:
            ventaPrecioSinIva = self.precioVenta / 1.13
            ventaIva = self.precioVenta - ventaPrecioSinIva
            ventaGanancia = ventaPrecioSinIva - self.costoUnidad
            if ventaGanancia < 0 or ventaPrecioSinIva == 0:
                VentaPorcentajeGanancia = 0
            else:
                VentaPorcentajeGanancia = (1 - (self.costoUnidad / ventaPrecioSinIva)) * 100

        dataPrecio = [
            {
                "nombre": "Costo fabricación",
                "valor": f"${self.costoUnidad:.2f}",
                "final": f"${self.costoUnidad:.2f}",
            },
            {
                "nombre": "Porcentaje de Ganancia",
                "valor": f"{ganancia:.2f} %",
                "final": f"{VentaPorcentajeGanancia:.2f} %",
            },
            {
                "nombre": "Ganancia",
                "valor": f"${cantidadGanancia:.2f}",
                "final": f"${ventaGanancia:.2f}",
            },
            {
                "nombre": "Precio antes de iva",
                "valor": f"${precioAntesIva:.2f}",
                "final": f"${ventaPrecioSinIva:.2f}",
            },
            {"nombre": "Iva", "valor": f"${iva:.2f}", "final": f"${ventaIva:.2f}"},
            {
                "nombre": "Costo de venta",
                "valor": f"${precioSugerido:.2f}",
                "final": f"${self.precioVenta:.2f}",
            },
        ]

        self.tablaPrecio.rows = dataPrecio
        self.tablaPrecio.update()

    def cargarDataArchivos(self):
        """Cargar datos de los archivos G-code en la carpeta del proyecto."""

        self.totalGramos = 0
        self.totalHoras = 0

        dataArchivo: list[dict] = []

        logger.info(f"Buscando en {self.folderProyecto}")
        sufijoArchivo = (".bgcode", ".gcode")
        for archivo in os.listdir(self.folderProyecto):
            if archivo.endswith(sufijoArchivo):
                logger.info(f"Archivo encontrado: {archivo}")
                for subfijo in sufijoArchivo:
                    if subfijo in archivo:
                        tipoArchivo = subfijo
                        nombreArchivo = archivo.removesuffix(subfijo)
                rutaCompleta = os.path.join(self.folderProyecto, archivo)
                infoGcode = self.cargarDataGcode(nombreArchivo, rutaCompleta, tipoArchivo)

                if infoGcode.material is None or infoGcode.tiempo is None:
                    logger.warning(f"No se pudo obtener información de {archivo}, saltando...")
                    ui.notify(f"No se pudo obtener información de {archivo}, saltando...")
                    continue

                tiempo = infoGcode.tiempo
                material = infoGcode.material

                if infoGcode.cantidad > 1:
                    logger.info(f"Archivo {archivo} tiene {infoGcode.cantidad} piezas.")
                    tiempo = tiempo / infoGcode.cantidad
                    material = material / infoGcode.cantidad
                    logger.info(f"Por pieza: {tiempo:.2f} horas, {material:.2f} gramos.")

                horas = int(tiempo)
                minutos = int((tiempo - horas) * 60)
                tiempo_formateado = f"{horas}h {minutos}m"
                dataArchivo.append(
                    {
                        "nombre": nombreArchivo,
                        "archivo": archivo,
                        "material": f"{material:.2f}g",
                        "tiempo": f"{tiempo_formateado}",
                        "cantidad": infoGcode.cantidad,
                    }
                )
                self.totalGramos += material
                self.totalHoras += tiempo

        minutosTotal = int((self.totalHoras - int(self.totalHoras)) * 60)

        if dataArchivo == []:
            ui.notify(
                "No se encontraron archivos G-code en la carpeta del proyecto.",
                type="negative",
                close_button="OK",
            )
            logger.warning("No se encontraron archivos G-code en la carpeta del proyecto.")
            return

        dataArchivo.append(
            {
                "nombre": "Total por unidad",
                "archivo": "",
                "material": f"{self.totalGramos:.2f}g",
                "tiempo": f"{int(self.totalHoras)}h {minutosTotal}m",
            }
        )

        SalvarValor(self.archivoInfo, "total_gramos", self.totalGramos, local=False)
        SalvarValor(self.archivoInfo, "total_horas", self.totalHoras, local=False)

        self.tablaDataGcode.rows = dataArchivo
        self.tablaDataGcode.update()

    def cargarDataGcode(self, nombre: str, archivo: str, tipoArchivo: str) -> dataGcode:
        """Cargar datos de un archivo G-code.

        Args:
            nombre (str): Nombre del archivo G-code.
            archivo (str): Ruta al archivo G-code.
            tipoArchivo (str): Tipo de archivo (ejemplo: .bgcode o .gcode).

        Returns:
            dataGcode: Objeto con la información extraída del archivo (material, tiempo, tipo, color).
        """

        with codecs.open(archivo, "r", encoding="utf-8", errors="ignore") as fdata:

            infoGcode: dataGcode = dataGcode()

            infoGcode.nombre = nombre

            data = fdata.read()
            lineas = data.split("\n")
            if tipoArchivo == ".bgcode":
                lineasDocumento = "\n".join(lineas[:30])
            else:
                lineasDocumento = data

            buscarImpresora = re.search(r"printer_model=.*(MMU3)", lineasDocumento)

            if buscarImpresora:
                self.multiMaterial = True
            else:
                self.multiMaterial = False

            logger.info(f"MultiMaterial de impresora: {self.multiMaterial}")

            if self.multiMaterial:
                # Formato de la línea: printer_model=MMU3
                # filament used [g]=81.79, 17.95, 41.29, 0.00, 0.00
                buscarGramos = re.search(
                    r"filament used \[g\]\s*=\s*([0-9.]+), ([0-9.]+), ([0-9.]+), ([0-9.]+), ([0-9.]+)",
                    lineasDocumento,
                )
                if buscarGramos:
                    infoGcode.material = (
                        float(buscarGramos.group(1))
                        + float(buscarGramos.group(2))
                        + float(buscarGramos.group(3))
                        + float(buscarGramos.group(4))
                        + float(buscarGramos.group(5))
                    )
            else:
                buscarGramos = re.search(r"filament used \[g\]\s?=\s?([0-9.]+)", lineasDocumento)

                if buscarGramos:
                    infoGcode.material = float(buscarGramos.group(1))

            if infoGcode.material == 0:
                buscarGramos = re.search(r"(\d+)g", nombre)
                if buscarGramos:
                    infoGcode.material = float(buscarGramos.group(1))

            logger.info(f"Gramos : {infoGcode.material}")

            time_match = re.search(
                r"estimated printing time \(normal mode\)\s?=\s?(([0-9]+)h )?([0-9]+)m ([0-9]+)s",
                lineasDocumento,
            )

            if time_match:
                hours = int(time_match.group(2)) if time_match.group(2) else 0  # Si no hay horas, usar 0
                minutes = int(time_match.group(3))
                seconds = int(time_match.group(4))
                infoGcode.tiempo = hours + minutes / 60 + seconds / 3600

            if infoGcode.tiempo == 0:
                buscarTiempo = re.search(r"(\d+)h", nombre)
                if buscarTiempo:
                    infoGcode.tiempo = float(buscarTiempo.group(1))
                buscarTiempo = re.search(r"(\d+)m", nombre)
                if buscarTiempo:
                    infoGcode.tiempo += float(buscarTiempo.group(1)) / 60

            logger.info(f"Tiempo(Horas) : {infoGcode.tiempo}")

            buscarPiezas = re.search(r"(\d+)pc", nombre)

            if buscarPiezas:
                infoGcode.cantidad = int(buscarPiezas.group(1))

                infoGcode.materialPorPieza = infoGcode.material / infoGcode.cantidad
                infoGcode.tiempoPorPieza = infoGcode.tiempo / infoGcode.cantidad

            return infoGcode

    def calcularCostos(self):
        """Calcular costos"""

        if self.infoBase is None:
            logger.error("Error fatal con data costos.md")
            exit(1)
        dataVentas = self.infoCostos

        costoHoraTrabajo = float(self.infoBase.get("hora_trabajo", 0))
        costoEnsamblado = (self.tiempoEnsamblado / 60) * costoHoraTrabajo

        if self.filamentoSeleccionado is not None:
            for filamento in self.filamentosDisponibles:
                id_filamento = filamento.get("id", "")
                if id_filamento == self.filamentoSeleccionado:
                    precioFilamento = filamento.get("precio", 0)
                    self.costoGramo = precioFilamento / 1000
        else:
            self.costoGramo = float(self.infoBase.get("precio_filamento", 0)) / 1000

        self.costoFilamento = self.totalGramos * self.costoGramo
        self.costoEficiencia = self.costoFilamento * float(self.infoBase.get("eficiencia_material")) / 100

        self.costoImpresora: float = float(self.infoBase.get("costo_impresora"))
        self.envióImpresora: float = float(self.infoBase.get("envio_impresora"))
        self.mantenimientoImpresora: float = float(self.infoBase.get("mantenimiento_impresora"))
        self.vidaUtil: float = float(self.infoBase.get("vida_util"))
        self.tiempoTrabajo: float = (float(self.infoBase.get("tiempo_trabajo")) / 100) * 8760
        self.consumoPotencia: float = float(self.infoBase.get("consumo"))
        self.costoElectricidad: float = float(self.infoBase.get("costo_electricidad"))
        self.errorFabricacion: float = float(self.infoBase.get("error_fabricacion")) / 100

        costoTotalImpresora = self.costoImpresora + self.envióImpresora + self.mantenimientoImpresora * self.vidaUtil

        costoRecuperacionInversion = costoTotalImpresora / (self.tiempoTrabajo * self.vidaUtil)
        costoHora = (self.consumoPotencia / 1000) * self.costoElectricidad
        costoHoraImpresion = (costoRecuperacionInversion + costoHora) * (1 + self.errorFabricacion)

        logger.info(f"costo extras: {self.costoExtras}")
        logger.info(f"costo hora impresión: {costoHoraImpresion:.2f}")
        logger.info(f"Precio por gramo: {self.costoGramo}")

        costoHoraImpresion = costoHoraImpresion * self.totalHoras
        self.costoTotalImpresion = self.costoFilamento + self.costoEficiencia + costoHoraImpresion
        self.costoUnidad = self.costoTotalImpresion + self.costoExtras + costoEnsamblado
        # TODO: Calcular costo por unidad en base a cuantos modelos hay en cada impresion
        # Considerar agregar en el nombre del archivo la cantidad de modelos
        # ejemplo 5pc

        for data in self.tablaCostos.rows:
            if data["nombre"] == "Total filamento (g)":
                data["valor"] = f"{self.totalGramos:.2f}g"
            elif data["nombre"] == "Tiempo Ensamblaje (m)":
                data["valor"] = f"{self.tiempoEnsamblado:.2f} m"
            elif data["nombre"] == "Costo Material":
                data["valor"] = f"${self.costoFilamento:.2f}"
            elif data["nombre"] == "Eficiencia filamento":
                data["valor"] = f"${self.costoEficiencia:.2f}"
            elif data["nombre"] == "Costo de impresión hora":
                data["valor"] = f"${costoHoraImpresion:.2f}"
            elif data["nombre"] == "Costo ensamblado":
                data["valor"] = f"${costoEnsamblado:.2f}"
            elif data["nombre"] == "Costo Extra":
                data["valor"] = f"${self.costoExtras:.2f}"
            elif data["nombre"] == "Costo total Impresion":
                data["valor"] = f"${self.costoTotalImpresion:.2f}"
            elif data["nombre"] == "Costo Unidad":
                data["valor"] = f"${self.costoUnidad:.2f}"

        self.tablaCostos.update()

    def seleccionarFilamento(self):
        """Seleccionar filamento"""
        self.filamentoSeleccionado = self.selectorFilamento.value
        ui.notify(f"Filamento seleccionado: {self.listaFilamentos[self.filamentoSeleccionado]}")
        SalvarValor(self.archivoInfo, "filamento_seleccionado", self.filamentoSeleccionado, local=False)

    def agregarCostoExtra(self):
        extra = self.textoExtra.value
        precio = self.textoCostoExtra.value

        if extra and precio is not None:
            agregarValor(self.archivoExtras, extra, precio, False)
            self.cargarCostos()

    def borrarExtra(self):
        """Borrar costo extra seleccionado"""
        filaSeleccionada = self.tablaDataExtras.selected
        if self.infoExtras is not None:
            id = filaSeleccionada[0].get("extra")
            del self.infoExtras[id]

        SalvarArchivo(self.archivoExtras, self.infoExtras)

        self.costosExtras()

    def cargarGuiPrecio(self):

        columns = [
            {
                "name": "nombre",
                "label": "Nombre",
                "field": "nombre",
                "required": True,
                "align": "left",
            },
            {
                "name": "valor",
                "label": "Referencia",
                "field": "valor",
                "required": True,
                "align": "center",
            },
            {
                "name": "final",
                "label": "Final",
                "field": "final",
                "required": True,
                "align": "center",
            },
        ]

        dataPrecio = [
            {"nombre": "Costo fabricación"},
            {"nombre": "Porcentaje de Ganancia"},
            {"nombre": "Ganancia"},
            {"nombre": "Precio antes de iva"},
            {"nombre": "Iva"},
            {
                "nombre": "Costo de venta",
                "valor": f"${0:.2f}",
                "final": f"${self.precioVenta:.2f}",
            },
        ]

        with ui.row().props("rounded outlined dense"):
            self.textoVenta = ui.input(
                label="Precio de Venta",
                value=self.precioVenta,
                validation=self.validar_numero,
            ).props("rounded outlined dense")
            ui.button(on_click=self.actualizarPrecios, icon="send")
            self.textoVenta.on("keydown.enter", self.actualizarPrecios)

        self.tablaPrecio = ui.table(columns=columns, rows=dataPrecio, row_key="nombre")

    def actualizarPrecios(self):
        self.precioVenta = float(self.textoVenta.value)
        SalvarValor(self.archivoInfo, "precio_venta", self.precioVenta, local=False)
        logger.info(f"Actualizar precios {self.precioVenta}")

        self.cargarCostos()

        ui.notify(f"Actualizando precios a ${self.precioVenta:.2f}")

    def cargarGuiActualizar(self):
        "Crear interface para actualizar datos del modelo"

        ui.label("Editar información").classes("w-64")

        ui.label(f"Proyecto: {self.folderProyecto}").classes("w-64").classes("text-white w-64 text-center break-words")

        self.textoNombre = ui.input(label="Nombre", value=self.nombreModelo)
        self.textoNombre.classes("w-64")
        self.textoNombre.on("keydown.enter", self.guardarModelo)

        self.textoPropiedad = ui.input(label="Propiedad", value=self.propiedadModelo).classes("w-64")
        self.tipoImpresion = ui.select(self.tipoProductos, label="tipo", value=self.tipoModelo).classes("w-64")
        self.textoInventario = ui.input(
            label="Inventario", value=self.inventario, validation=self.validar_numero
        ).classes("w-64")

        self.textoSKU = ui.input(label="SKU", value=self.skuModelo).classes("w-64")

        self.textoDescripción = (
            ui.textarea(label="Descripción", value=self.descripciónModelo).props("clearable").classes("w-64")
        )

        self.textoLink = ui.input(value=self.linkModelo, label="Link").classes("w-64")

        ui.button("Guardar", on_click=self.guardarModelo).classes("w-64")

    def guardarModelo(self) -> None:
        "Guardar información del modelo en el archivo info.md"

        # Obtener valores de los campos
        self.nombreModelo = self.textoNombre.value
        self.inventario = int(self.textoInventario.value)
        self.linkModelo = self.textoLink.value
        self.skuModelo = self.textoSKU.value
        self.propiedadModelo = self.textoPropiedad.value
        self.tipoModelo = self.tipoImpresion.value
        self.descripciónModelo = self.textoDescripción.value

        SalvarValor(self.archivoInfo, "nombre", self.nombreModelo, local=False)
        SalvarValor(self.archivoInfo, "link", self.linkModelo, local=False)
        SalvarValor(self.archivoInfo, "tipo", self.tipoModelo, local=False)
        SalvarValor(self.archivoInfo, "inventario", self.inventario, local=False)
        SalvarValor(self.archivoInfo, "propiedad", self.propiedadModelo, local=False)
        SalvarValor(self.archivoInfo, "descripción", self.descripciónModelo, local=False)
        SalvarValor(self.archivoInfo, "sku", self.skuModelo, local=False)

        ui.notify("Salvando Información")

    def cargarGui(self, interface: bool = False) -> None:
        """Cargar la interfaz gráfica de usuario.

        Args:
            interface (bool): Indica si se debe mostrar la interfaz completa con cabecera y pie de página.
        """

        @ui.page("/")
        def paginaInicio():

            with ui.tabs().style("padding: 0px") as tabs:
                tabs.classes("w-full bg-teal-00 text-white")
                tabs.style("padding: 0px")
                self.tabInfo = ui.tab("info", icon="home")
                self.tabCosto = ui.tab("Costos", icon="view_in_ar")
                self.tabPrecio = ui.tab("Precio", icon="paid")
                self.tabData = ui.tab("Modelo", icon="assignment")

            with ui.tab_panels(tabs, value=self.tabInfo) as paneles:
                paneles.classes("w-full")

                with ui.tab_panel(self.tabInfo):
                    with ui.row() as row:
                        row.classes("w-full justify-center items-center")
                        self.cargarGuiInfo()
                with ui.tab_panel(self.tabCosto).style("padding: 0px"):
                    with ui.row() as row:
                        row.classes("w-full justify-center items-center")
                        self.cargarGuiCostos()
                with ui.tab_panel(self.tabPrecio):
                    with ui.row().classes("w-full justify-center items-center"):
                        self.cargarGuiPrecio()
                with ui.tab_panel(self.tabData):
                    with ui.row() as row:
                        row.classes("w-full justify-center items-center")
                        self.cargarGuiActualizar()

            if interface:
                with ui.header(elevated=True) as cabecera:
                    cabecera.classes("bg-teal-700 items-center justify-between")
                    cabecera.style("height: 5vh; padding: 1px")
                    with ui.row().classes("w-full justify-center items-center"):
                        ui.label("PrintTool").classes("text-h5")
                        ui.space()
                        ui.label(self.nombreModelo).bind_text_from(self, "nombreModelo").classes("text-h6")
                        ui.space()
                        ui.button(icon="power_settings_new", on_click=app.shutdown).props("color=negative")

                with ui.footer() as pie:
                    pie.classes("bg-teal-700")
                    pie.style("height: 5vh; padding: 1px")
                    with ui.row().classes("w-full justify-center items-center"):
                        ui.label("Creado por ChepeCarlos").classes("text-white")

    def iniciarGui(self) -> None:
        """Iniciar la interfaz gráfica de usuario."""

        ui.run(
            native=False,
            reload=False,
            dark=True,
            show=False,
            language="es",
            title="PrintTool",
            uvicorn_logging_level="warning",
        )
