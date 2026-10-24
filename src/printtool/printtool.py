from nicegui import ui, app, run
import os
import codecs
import re
import shutil
from pathlib import Path

from printtool.dataGcode import dataGcode
from printtool.costosImpresora import dataImpresora

from printtool.MiLibrerias import (
    ObtenerArchivo,
    SalvarValor,
    SalvarArchivo,
    agregarValor,
    configurarArchivo,
    obtenerArchivoPaquete,
    ConfigurarLogging,
)

from printtool.extrasGui import seleccionarFolderThinter
from printtool.paginaConfig import registraPaginaConfig
from printtool.paginaPurga import registraPaginaPurga
from printtool.paginaActualizar import cargarPaginaActualizar
from printtool.paginaPrecio import cargarPaginaPrecio
from printtool.tema import aplicarTema


logger = ConfigurarLogging(__name__)


def formatearHoras(horas: float) -> str:
    """Formatea horas decimales como 'X h Y m', o 'D d X h Y m' si pasa de 24 horas."""
    dias, minutos = divmod(int(horas * 60), 24 * 60)
    texto = f"{minutos // 60} h {minutos % 60} m"
    return f"{dias} d {texto}" if dias else texto


class printtool:
    """Clase principal para la herramienta de emprendimiento de impresión 3D"""

    totalGramos: float = 0
    "Total de gramos de la impresión"
    costoFilamento: float = 0
    "Costo por modelos"
    costoEficiencia: float = 0
    "Costo por posible error"
    costoHoraImpresion: float = 0
    "Costo por uso de la maquina"
    costoEnsamblado: float = 0
    "Costo por ensamblado"
    costoUnidad: float = 0
    "Costos por unidad"
    porcentajeInpuesto: float = 13

    porcentajeGananciaBase: float = 0
    "Porcentaje Ganancia sobre la impresión"
    porcentajeGananciaExtras: float = 15
    "Porcentaje Ganancia sobre extras (LED, botones, tornillos)"
    porcentajeGananciaEnsamblado: float = 15
    "Porcentaje Ganancia sobre ensamblado"
    porcentajeGananciaReferencia: float = 0
    "Porcentaje Ganancia combinado de referencia"
    porcentajeGananciaFinal: float = 0
    "Porcentaje Ganancia Final"

    gananciaBase: float = 0
    gananciaFinal: float = 0
    precioSinIvaReferencia: float = 0
    precioSinIvaFinal: float = 0
    ivaReferencia: float = 0
    ivaFinal: float = 0
    precioVentaReferencia: float = 0
    precioVentaFinal: float = 0
    precioFilamento: float = 0
    "Costo por kilogramos del filamento seleccionado"
    costoGramo: float = 0

    nombreFilamento: str = ""
    "Nombre del filamento base del sistema"
    nombreFilamentoProyecto: str = ""
    "Nombre del filamento específico de este proyecto (vacío = usar el del sistema)"
    precioFilamentoProyecto: float = 0
    "Precio por kg del filamento de este proyecto (0 = usar el precio del sistema)"
    nombreFilamentoActivo: str = ""
    "Nombre del filamento que se está usando actualmente (proyecto o sistema)"

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

    precioVentaFinal: float = 0
    "Precio de venta ingresado por el usuario"

    tipoProductos: list[str] = ["desconocido", "alcancía", "maceta", "figuras", "otro"]

    folderProyecto: str = None
    "Folder del proyecto"

    mostrarCostos: bool = False
    "Bandera que controla si la sección de costos se muestra"
    archivoInfo: str = None
    "Archivo de información del modelo "
    archivoExtras: str = None
    "Archivos de costos Extras del modelo como pegamento o tornillo"
    archivoConfig: str = "data/costos.md"
    "Archivo de información para calculo de costos"

    infoBase: dict[str, float] = None
    """Información base para cálculos de costos

    Ejemplo:
        Costo Maquina
        Vida Util
        Ganancia
    """
    infoCostos: dict[str, float] = None

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

    símboloMoneda: str = "$"
    "Símbolo de Moneda para interface"

    infoImpresora: dataImpresora = dataImpresora()
    "Información del impresora para calculo de costos"

    urlSpoolman: str = ""
    "Url para hacer consultas de filamentos"

    urlDolibarr: str = ""
    "Url para hacer consultas a Dolibarr y actualizar precios y stock"
    tokenDolibarr: str = ""
    "Token para autenticación en Dolibarr"

    def __init__(self) -> None:
        self.totalGramos: float = 0
        self.totalHoras: float = 0
        self.precioVentaFinal: float = 0
        self.costoTotalImpresion: float = 0
        self.costoExtras: float = 0

    @staticmethod
    def esProyecto(folder: str) -> bool:
        "confirma si el proyecto es válido"
        nuevo = os.path.exists(os.path.join(folder, ".printtool", "info.md")) and os.path.exists(
            os.path.join(folder, ".printtool", "extras.md")
        )
        legacy = os.path.exists(os.path.join(folder, "info.md")) and os.path.exists(os.path.join(folder, "extras.md"))
        return nuevo or legacy

    @staticmethod
    def buscarProyectos(ruta: str) -> list[str]:
        """Busca proyectos (carpetas con .printtool/info.md) en la ruta y subcarpetas."""

        proyectos: list[str] = []
        for carpeta, subcarpetas, _archivos in os.walk(ruta):
            subcarpetas[:] = [d for d in subcarpetas if not d.startswith(".")]
            if printtool.esProyecto(carpeta):
                proyectos.append(carpeta)
        return proyectos

    def iniciarSistema(self) -> None:

        self.configurarData()

        logger.debug(f"Buscando en: {self.archivoInfo}")

        if not os.path.exists(self.archivoExtras):
            data = dict()
            SalvarArchivo(self.archivoExtras, data)
            logger.info(f"Creando data base de {self.archivoExtras}")

        self.infoBase = ObtenerArchivo(self.archivoConfig)
        if self.infoBase is None:
            logger.error("Error falta información para calculo de costos")
            self.infoBase = dict()
        self.infoCostos = ObtenerArchivo(self.archivoInfo, False)
        self.infoExtras = ObtenerArchivo(self.archivoExtras, False)

        self.cargarConfig()
        self.cargarInfoBasica()

    def cargarConfig(self):

        self.urlSpoolman = self.infoBase.get("url_spoolman", "")
        self.precioFilamento = self.infoBase.get("precio_filamento", 0)
        self.nombreFilamento = self.infoBase.get("nombre_filamento", "")
        self.urlDolibarr = self.infoBase.get("url_dolibarr", "")
        self.tokenDolibarr = self.infoBase.get("token_dolibarr", "")

    def configurarData(self) -> None:
        """Configurar la carpeta del proyecto y los archivos de información."""

        if self.folderProyecto is None:
            logger.info("Usando folder actual para proyecto")
            self.folderProyecto = Path.cwd()

        folderData = os.path.join(self.folderProyecto, ".printtool")
        os.makedirs(folderData, exist_ok=True)

        archivoInfoLegacy = os.path.join(self.folderProyecto, "info.md")
        archivoExtrasLegacy = os.path.join(self.folderProyecto, "extras.md")

        self.archivoInfo = os.path.join(folderData, "info.md")
        self.archivoExtras = os.path.join(folderData, "extras.md")

        # Migracion suave: si existe data antigua en la raiz del proyecto,
        # se copia al nuevo folder oculto la primera vez.
        if not os.path.exists(self.archivoInfo) and os.path.exists(archivoInfoLegacy):
            shutil.copy2(archivoInfoLegacy, self.archivoInfo)
            logger.info(f"Migrando info.md a {self.archivoInfo}")

        if not os.path.exists(self.archivoExtras) and os.path.exists(archivoExtrasLegacy):
            shutil.copy2(archivoExtrasLegacy, self.archivoExtras)
            logger.info(f"Migrando extras.md a {self.archivoExtras}")

        dataBaseInfo = obtenerArchivoPaquete("printtool", "config/info.md")
        if dataBaseInfo is None:
            logger.error("Error fatal con paquete falta config/info.md")
            exit(1)

        configurarArchivo(self.archivoInfo, dataBaseInfo)

    def cargarInfoBasica(self) -> None:
        """Cargar información básica del modelo desde archivo info.md"""

        self.símboloMoneda = self.infoBase.get("simbolo", "$")

        self.infoImpresora.nombre = self.infoBase.get("nombre_impresora", "")
        self.infoImpresora.costo = self.infoBase.get("costo_impresora", 0)
        self.infoImpresora.envio = self.infoBase.get("envio_impresora", 0)
        self.infoImpresora.mantenimiento = self.infoBase.get("mantenimiento_impresora", 0)
        self.infoImpresora.vidaUtil = self.infoBase.get("vida_util_impresora", 1)
        self.infoImpresora.consumo = self.infoBase.get("consumo_impresora", 0)
        self.infoImpresora.tiempoTrabajo = self.infoBase.get("tiempo_trabajo_impresora", 50)

        self.errorFabricacion = float(self.infoBase.get("error_fabricacion", 0))
        self.costoElectricidad: float = float(self.infoBase.get("costo_electricidad", 0))
        self.costoHoraTrabajo = float(self.infoBase.get("hora_trabajo", 0))

        self.porcentajeGananciaBase: float = float(self.infoBase.get("ganancia", 10))
        self.porcentajeGananciaExtras: float = float(self.infoBase.get("ganancia_extras", 15))
        self.porcentajeGananciaEnsamblado: float = float(self.infoBase.get("ganancia_ensamblado", 15))

        self.nombreModelo = self.infoCostos.get("nombre")
        self.linkModelo = self.infoCostos.get("link")
        self.inventario = int(self.infoCostos.get("inventario", 0))
        self.precioVentaFinal = self.infoCostos.get("precio_venta")
        self.skuModelo = self.infoCostos.get("sku", "")
        self.propiedadModelo = self.infoCostos.get("propiedad", "")
        self.descripciónModelo = self.infoCostos.get("descripción", "")
        self.tipoModelo = self.infoCostos.get("tipo", "desconocido")
        self.tiempoEnsamblado = float(self.infoCostos.get("tiempo_ensamblaje", 0))
        self.idProductoDolibarr = float(self.infoCostos.get("id_producto_dolibarr", 0))

        if self.tipoModelo not in self.tipoProductos:
            self.tipoModelo = "desconocido"

        self.totalGramos = float(self.infoCostos.get("total_gramos", 0))
        self.totalHoras = float(self.infoCostos.get("total_horas", 0))

        self.costoFilamento = float(self.infoCostos.get("precio_filamento", 0))

        self.nombreFilamentoProyecto = self.infoCostos.get("nombre_filamento", "") or ""
        self.precioFilamentoProyecto = float(self.infoCostos.get("precio_filamento_kg", 0) or 0)

        # self.filamentosDisponibles: list[dict] = self.infoBase.get("filamentos")

        # self.filamentoSeleccionado = int(self.infoCostos.get("filamento_seleccionado", 1))
        # self.listaFilamentos = dict()
        # for filamento in self.filamentosDisponibles:
        #     id = filamento.get("id", "")
        #     nombre = filamento.get("nombre", "")
        #     precio = filamento.get("precio", "")
        #     material = filamento.get("material", "")
        #     if id is not None:
        #         self.listaFilamentos[id] = f"{nombre}-{material} {self.símboloMoneda}{precio:.02f}"

        # if self.filamentoSeleccionado not in self.listaFilamentos:
        #     self.filamentoSeleccionado = 1

    def cargarGuiInfo(self) -> None:
        """Cargar la interfaz gráfica de usuario para la información básica del modelo."""

        dataInfo = [
            {"key": "nombreModelo", "humano": "Nombre", "formato": lambda x: f"{x}"},
            {"key": "propiedadModelo", "humano": "Propiedad", "formato": lambda x: f"{x}"},
            {"key": "tipoModelo", "humano": "Tipo", "formato": lambda x: f"{x}"},
            {"key": "inventario", "humano": "Inventario", "formato": lambda x: f"{x}"},
            {"key": "skuModelo", "humano": "SKU", "formato": lambda x: f"{x}"},
            # {"key": "Material", "humano": "Material", "formato": "PLA"},
            {"key": "totalGramos", "humano": "Filamento total", "formato": lambda x: f"{x:.2f} g"},
            {
                "key": "totalHoras",
                "humano": "Tiempo de impresión",
                "formato": formatearHoras,
            },
            {"key": "precioVentaFinal", "humano": "Precio de venta", "formato": lambda x: f"{self.símboloMoneda} {x:.2f}"},
        ]
        with ui.grid(columns=2).classes("gap-x-8 gap-y-3"):

            for item in dataInfo:
                ui.label(item["humano"])
                ui.label().bind_text_from(
                    self,
                    item["key"],
                    lambda x, transform_func=item["formato"]: transform_func(x),
                ).classes("text-right")

    def cargarGuiCostos(self) -> None:
        """Cargar la interfaz gráfica de usuario para la pestaña de costos."""
        with ui.column() as area:
            area.classes("w-full max-w-5xl mx-auto px-4")

            # separar datos generales de los costos monetarios
            dataTotales = [
                {
                    "key": "nombreFilamentoActivo",
                    "humano": "Filamento",
                    "formato": lambda x: x if x else "Predeterminado (sin nombre)",
                },
                {"key": "totalGramos", "humano": "Filamento por unidad", "formato": lambda x: f"{x:.2f} g"},
                {
                    "key": "totalHoras",
                    "humano": "Tiempo de impresión",
                    "formato": formatearHoras,
                },
                {
                    "key": "tiempoEnsamblado",
                    "humano": "Tiempo de ensamblaje",
                    "formato": lambda x: formatearHoras(x / 60),
                },
            ]

            dataCostos = [
                {
                    "key": "costoFilamento",
                    "humano": "Filamento",
                    "formato": lambda x: f"{self.símboloMoneda} {x:.2f}",
                },
                {
                    "key": "costoEficiencia",
                    "humano": "Merma",
                    "formato": lambda x: f"{self.símboloMoneda} {x:.2f}",
                },
                {
                    "key": "costoHoraImpresion",
                    "humano": "Uso de la impresora",
                    "formato": lambda x: f"{self.símboloMoneda} {x:.2f}",
                },
                {
                    "key": "costoEnsamblado",
                    "humano": "Ensamblaje",
                    "formato": lambda x: f"{self.símboloMoneda} {x:.2f}",
                },
                {"key": "costoExtras", "humano": "Extras", "formato": lambda x: f"{self.símboloMoneda} {x:.2f}"},
                {"key": "costoUnidad", "humano": "Costo total", "formato": lambda x: f"{self.símboloMoneda} {x:.2f}"},
            ]

            with ui.column().classes("w-full justify-center items-center"):
                with ui.button("Calcular costos", on_click=self.cargarCostos).classes("w-64"):
                    ui.tooltip("Vuelve a leer los G-code, los extras y la configuración, y recalcula.")

            with ui.column().bind_visibility_from(self, "mostrarCostos") as panelCostos:
                panelCostos.classes("w-full justify-center items-center")

                # mostrar ambas tablas en columnas separadas
                with ui.row().classes("w-full justify-center items-start gap-x-16 gap-y-6"):
                    # izquierda: totales de fabricación
                    with ui.column().classes("justify-center items-center"):
                        ui.label("Datos de fabricación").classes("text-subtitle1").props('role=heading aria-level=2')
                        with ui.grid(columns=2).classes("justify-center items-center"):
                            for item in dataTotales:
                                ui.label(item["humano"]).classes("pr-6")
                                ui.label().bind_text_from(
                                    self,
                                    item["key"],
                                    lambda x, transform_func=item["formato"]: transform_func(x),
                                ).classes("text-right")
                    # derecha: costos monetarios
                    with ui.column().classes("justify-center items-center"):
                        ui.label("Costos por unidad").classes("text-subtitle1").props('role=heading aria-level=2')
                        with ui.grid(columns=2).classes("justify-center items-center"):
                            for idx, item in enumerate(dataCostos):
                                is_total = idx == len(dataCostos) - 1  # es el último elemento (Costo Total)
                                if is_total:
                                    ui.separator().classes("col-span-2 my-2")
                                ui.label(item["humano"]).classes("pr-6" + (" font-bold text-lg" if is_total else ""))
                                ui.label().bind_text_from(
                                    self,
                                    item["key"],
                                    lambda x, transform_func=item["formato"]: transform_func(x),
                                ).classes("text-right" + (" font-bold text-lg text-ambar-costo" if is_total else ""))

                with ui.row().classes("w-full justify-center items-center"):
                    with ui.column().classes("justify-center items-center"):
                        with ui.row():
                            self.textoTiempoEnsamblado = ui.number(
                                label="Tiempo de ensamblaje",
                                value=self.tiempoEnsamblado,
                                validation=self.validar_numero_no_negativo,
                                step=1,
                            ).props("suffix=min")
                            ui.button(on_click=self.actualizarEnsamblado, icon="send").props(
                                'aria-label="Guardar tiempo de ensamblado"'
                            )
                            self.textoTiempoEnsamblado.on("keydown.enter", self.actualizarEnsamblado)

                    with ui.column().classes("justify-center items-center"):
                        with ui.row():
                            self.inputNombreFilamento = ui.input(
                                label="Filamento del modelo",
                                value=self.nombreFilamentoProyecto,
                            ).classes("w-56")
                            self.inputPrecioFilamento = ui.number(
                                label="Precio por kg",
                                value=self.precioFilamentoProyecto or None,
                                validation=self.validar_numero_opcional_no_negativo,
                                step=1,
                            ).classes("w-44")
                            self.inputPrecioFilamento.props(f"prefix={self.símboloMoneda}")
                            ui.button(on_click=self.actualizarFilamentoProyecto, icon="send").props(
                                'aria-label="Guardar filamento del proyecto"'
                            )
                            ui.button(on_click=self.borrarFilamentoProyecto, icon="delete").props(
                                'flat color=rojo-texto aria-label="Usar el filamento predeterminado"'
                            )
                        ui.label("Deje el precio vacío para usar el filamento predeterminado (Menú › Configurar).").classes(
                            "text-xs text-tinta-secundaria"
                        )

                infoArchivo = [
                    {
                        "name": "copias",
                        "label": "Copias",
                        "field": "copias",
                    },
                    {
                        "name": "nombre",
                        "label": "Archivo",
                        "field": "nombre",
                        "required": True,
                        "align": "left",
                    },
                    # {'name': 'archivo', 'label': 'Archivo', 'field': 'archivo'},
                    {
                        "name": "cantidad",
                        "label": "Piezas",
                        "field": "cantidad",
                    },
                    {
                        "name": "costo",
                        "label": "Costo",
                        "field": "costo",
                    },
                    {
                        "name": "material",
                        "label": "Filamento",
                        "field": "material",
                    },
                    {
                        "name": "tiempo",
                        "label": "Tiempo",
                        "field": "tiempo",
                    },
                ]

                # nombres de archivo largos: QTable hace scroll horizontal dentro de sí misma, no la página
                self.tablaDataGcode = ui.table(
                    columns=infoArchivo,
                    rows=[],
                    row_key="nombre",
                    pagination=5,
                ).classes("w-full")

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
        except (TypeError, ValueError):
            return "No es un número válido"
        # Si falla, devolver mensaje de error

    def validar_numero_no_negativo(self, value):
        """Validar que el valor sea numérico y no negativo."""
        if value is None or value == "":
            return "Campo obligatorio"
        try:
            if float(value) < 0:
                return "No puede ser negativo"
            return None
        except (TypeError, ValueError):
            return "No es un número válido"

    def validar_entero_no_negativo(self, value):
        """Validar que el valor sea entero y no negativo."""
        if value is None or value == "":
            return "Campo obligatorio"
        try:
            numero = float(value)
            if numero < 0:
                return "No puede ser negativo"
            if not numero.is_integer():
                return "Debe ser un número entero"
            return None
        except (TypeError, ValueError):
            return "No es un número válido"

    def validar_numero_opcional_no_negativo(self, value):
        """Validar que el valor, si se ingresa, sea numérico y no negativo. Vacío es válido."""
        if value is None or value == "":
            return None
        try:
            if float(value) < 0:
                return "No puede ser negativo"
            return None
        except (TypeError, ValueError):
            return "No es un número válido"

    def validar_texto_requerido(self, value):
        if value is None or str(value).strip() == "":
            return "Campo obligatorio"
        return None

    def parse_float_seguro(self, value):
        """Convierte a float aceptando coma decimal. Retorna None si falla."""
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip().replace(",", ".")
            if value == "":
                return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def parse_int_seguro(self, value):
        """Convierte a int de forma segura. Retorna None si falla."""
        numero = self.parse_float_seguro(value)
        if numero is None or not float(numero).is_integer():
            return None
        return int(numero)

    def actualizarEnsamblado(self):
        tiempo = self.parse_float_seguro(self.textoTiempoEnsamblado.value)
        if tiempo is None or tiempo < 0:
            ui.notify("El tiempo de ensamblaje debe ser un número de minutos mayor o igual a 0.", type="negative")
            return

        self.tiempoEnsamblado = tiempo
        SalvarValor(self.archivoInfo, "tiempo_ensamblaje", self.tiempoEnsamblado, local=False)
        # self.cargarCostos()
        ui.notify(f"Tiempo de ensamblaje guardado: {self.tiempoEnsamblado} min", type="positive")

    def actualizarFilamentoProyecto(self):
        """Guardar el nombre y precio (por kg) del filamento específico de este proyecto."""
        precio = self.parse_float_seguro(self.inputPrecioFilamento.value)
        if precio is not None and precio < 0:
            ui.notify("El precio por kg debe ser un número mayor o igual a 0.", type="negative")
            return

        self.nombreFilamentoProyecto = (self.inputNombreFilamento.value or "").strip()
        self.precioFilamentoProyecto = precio or 0

        SalvarValor(self.archivoInfo, "nombre_filamento", self.nombreFilamentoProyecto, local=False)
        SalvarValor(self.archivoInfo, "precio_filamento_kg", self.precioFilamentoProyecto, local=False)

        self.cargarCostos()
        ui.notify("Filamento de este modelo guardado", type="positive")

    def borrarFilamentoProyecto(self):
        """Quitar el filamento específico del proyecto y volver a usar el del sistema."""
        self.nombreFilamentoProyecto = ""
        self.precioFilamentoProyecto = 0
        self.inputNombreFilamento.value = ""
        self.inputPrecioFilamento.value = None

        SalvarValor(self.archivoInfo, "nombre_filamento", "", local=False)
        SalvarValor(self.archivoInfo, "precio_filamento_kg", 0, local=False)

        self.cargarCostos()
        ui.notify("Este modelo usará el filamento predeterminado", type="positive")

    def cargarCostos(self):
        """Cargar y calcular los costos de impresión, ensamblado y extras."""
        # cuando se presiona el botón mostramos la información
        self.mostrarCostos = True
        self.cargarDataArchivos()
        self.costosExtras()
        self.calcularCostos()
        self.calculandoPrecioVenta()

    def calcularCostoExtras(self) -> float:
        """Sumar los costos extras desde el archivo extras.md (sin tocar la interfaz)."""

        self.costoExtras = 0
        self.infoExtras = ObtenerArchivo(self.archivoExtras, False)

        if self.infoExtras is not None:
            for extra in self.infoExtras:
                self.costoExtras += float(self.infoExtras[extra])
        return self.costoExtras

    def calcularCostoUnidad(self, recalcularGcode: bool = False) -> float:
        """Calcular el costo por unidad (sin tocar la interfaz).

        Args:
            recalcularGcode (bool): Si es True, vuelve a leer los archivos G-code del proyecto
                en vez de usar los gramos/horas ya guardados en info.md.
        """

        if recalcularGcode:
            self.calcularDataArchivos()

        self.calcularCostoExtras()
        self.calcularCostos()
        self.calculandoPrecioVenta()
        return self.costoUnidad

    def costosExtras(self):
        """Cargar y mostrar los costos extras desde el archivo extras.md"""
        dataCostos = []
        self.calcularCostoExtras()
        self.tablaDataExtras.clear()

        if self.infoExtras is not None:
            for extra in self.infoExtras:
                dataCostos.append({"extra": extra, "precio": f"{self.símboloMoneda} {self.infoExtras[extra]:.2f}"})

        with self.tablaDataExtras as tabla:
            with tabla.add_slot("bottom-row"):
                with tabla.row():
                    with tabla.cell():
                        ui.button(on_click=self.agregarCostoExtra, icon="add").props(
                            'flat fab-mini aria-label="Agregar costo extra"'
                        )
                    with tabla.cell():
                        self.textoExtra = ui.input("Nuevo extra")
                    with tabla.cell():
                        self.textoCostoExtra = ui.number("Precio")
                with tabla.add_slot("top-right"):
                    with (
                        ui.input(placeholder="Buscar")
                        .props('type=search aria-label="Buscar extras"')
                        .bind_value(tabla, "filter")
                        .add_slot("append")
                    ):
                        ui.icon("search")
            with tabla.add_slot("top-left"):
                ui.button(icon="delete", color="rojo-texto", on_click=self.borrarExtra).props(
                    'flat aria-label="Borrar costo extra seleccionado"'
                ).bind_visibility_from(
                    self.tablaDataExtras, "selected", backward=lambda val: bool(val)
                )

        self.tablaDataExtras.rows = dataCostos
        self.tablaDataExtras.update()

    def calculandoPrecioVenta(self):

        # Cada parte lleva su propio margen: la impresión gana más que lo comprado o la mano de obra
        self.precioSinIvaReferencia = (
            self.costoTotalImpresion / (1 - self.porcentajeGananciaBase / 100)
            + self.costoExtras / (1 - self.porcentajeGananciaExtras / 100)
            + self.costoEnsamblado / (1 - self.porcentajeGananciaEnsamblado / 100)
        )
        self.gananciaBase = self.precioSinIvaReferencia - self.costoUnidad
        self.porcentajeGananciaReferencia = (
            self.gananciaBase / self.precioSinIvaReferencia * 100 if self.precioSinIvaReferencia else 0
        )
        self.ivaReferencia = self.precioSinIvaReferencia * self.porcentajeInpuesto / 100
        self.precioVentaReferencia = self.precioSinIvaReferencia + self.ivaReferencia

        if self.precioVentaFinal is None:
            self.precioVentaFinal = self.precioVentaReferencia

        if self.precioVentaFinal >= 0:
            self.precioSinIvaFinal = self.precioVentaFinal / (1 + self.porcentajeInpuesto / 100)
            self.ivaFinal = self.precioVentaFinal - self.precioSinIvaFinal
            self.gananciaFinal = self.precioSinIvaFinal - self.costoUnidad
            if self.gananciaFinal < 0 or self.precioSinIvaFinal == 0:
                self.porcentajeGananciaFinal = 0
            else:
                self.porcentajeGananciaFinal = (1 - (self.costoUnidad / self.precioSinIvaFinal)) * 100

    def calcularDataArchivos(self) -> list[dict]:
        """Escanear los archivos G-code del proyecto y calcular gramos/horas totales (sin tocar la interfaz)."""

        self.totalGramos = 0
        self.totalHoras = 0

        dataArchivo: list[dict] = []

        logger.info(f"Buscando en {self.folderProyecto}")
        sufijoArchivo = (".bgcode", ".gcode")
        costoHoraImpresion = self.calculoHoraImpresion()
        self.cargarCostoPorGramo()
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
                    ui.notify(f"No se pudo leer {archivo}; se omite del cálculo.", type="warning")
                    continue

                tiempoPorUnidad = infoGcode.tiempo
                materialPorUnidad = infoGcode.material

                if infoGcode.cantidad > 1:
                    logger.info(f"Archivo {archivo} tiene {infoGcode.cantidad} piezas.")
                    tiempoPorUnidad = tiempoPorUnidad / infoGcode.cantidad
                    materialPorUnidad = materialPorUnidad / infoGcode.cantidad
                    logger.info(f"Por pieza: {tiempoPorUnidad:.2f} horas, {materialPorUnidad:.2f} gramos.")

                infoGcode.costo = (materialPorUnidad * self.costoGramo + tiempoPorUnidad * costoHoraImpresion) * (
                    1 + float(self.errorFabricacion) / 100
                )
                dataArchivo.append(
                    {
                        "copias": infoGcode.copias,
                        "nombre": nombreArchivo,
                        "archivo": archivo,
                        "material": f"{materialPorUnidad:.2f} g",
                        "tiempo": formatearHoras(tiempoPorUnidad),
                        "cantidad": infoGcode.cantidad,
                        "costo": f"{self.símboloMoneda} {infoGcode.costo:.2f}",
                    }
                )
                self.totalGramos += materialPorUnidad * infoGcode.copias
                self.totalHoras += tiempoPorUnidad * infoGcode.copias

        if dataArchivo == []:
            logger.warning("No se encontraron archivos G-code en la carpeta del proyecto.")
            return dataArchivo

        SalvarValor(self.archivoInfo, "total_gramos", self.totalGramos, local=False)
        SalvarValor(self.archivoInfo, "total_horas", self.totalHoras, local=False)

        return dataArchivo

    def cargarDataArchivos(self):
        """Cargar datos de los archivos G-code en la carpeta del proyecto (interfaz)."""

        dataArchivo = self.calcularDataArchivos()

        if dataArchivo == []:
            ui.notify(
                "No hay archivos .gcode ni .bgcode en la carpeta del proyecto. "
                "Lamine el modelo y guarde el G-code en esa carpeta.",
                type="negative",
                close_button="Cerrar",
            )
            return

        dataArchivo.append(
            {
                "nombre": "Total por unidad",
                "archivo": "",
                "material": f"{self.totalGramos:.2f} g",
                "tiempo": formatearHoras(self.totalHoras),
            }
        )

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

            buscarImpresoraMultiMaterial = re.search(r";\s*printer_model\s*=\s*.*?(MMU\d+)", lineasDocumento)

            if buscarImpresoraMultiMaterial:
                self.multiMaterial = True
            else:
                self.multiMaterial = False

            buscarGramos = re.search(r"filament used \[g\]\s*=\s*([\d., ]+)", lineasDocumento)
            if buscarGramos:
                valores = [float(v.strip()) for v in buscarGramos.group(1).split(",") if v.strip()]
                infoGcode.material = sum(valores)
                if len(valores) > 1:
                    self.multiMaterial = True

            if infoGcode.material == 0:
                buscarGramos = re.search(r"(\d+)g", nombre)
                if buscarGramos:
                    infoGcode.material = float(buscarGramos.group(1))

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
                # TODO: Buscar dias
                buscarTiempo = re.search(r"(\d+)h", nombre)
                if buscarTiempo:
                    infoGcode.tiempo = float(buscarTiempo.group(1))
                buscarTiempo = re.search(r"(\d+)m", nombre)
                if buscarTiempo:
                    infoGcode.tiempo += float(buscarTiempo.group(1)) / 60

            buscarPiezas = re.search(r"(\d+)pc", nombre)

            if buscarPiezas:
                infoGcode.cantidad = int(buscarPiezas.group(1))

                infoGcode.materialPorPieza = infoGcode.material / infoGcode.cantidad
                infoGcode.tiempoPorPieza = infoGcode.tiempo / infoGcode.cantidad

            buscarCopias = re.search(r"(\d+)cc", nombre)
            if buscarCopias:
                infoGcode.copias = int(buscarCopias.group(1))

            horas, minutos = int(infoGcode.tiempo), int((infoGcode.tiempo - int(infoGcode.tiempo)) * 60)

            logger.info(
                f"Archivo: {nombre}, Material: {infoGcode.material}g, Tiempo: {horas}h {minutos}m, Cantidad: {infoGcode.cantidad}, Copias: {infoGcode.copias}"
            )

            return infoGcode

    def calculoHoraImpresion(self) -> float:
        """Calcular el costo por hora de impresión.
        En base a los costos de la impresora, consumo eléctrico y eficiencia.

        Returns:
            float: Costo por hora de impresión
        """

        costoTotalImpresora = (
            self.infoImpresora.costo
            + self.infoImpresora.envio
            + self.infoImpresora.mantenimiento * self.infoImpresora.vidaUtil
        )

        tiempoTrabajoHorasPorAño = (float(self.infoImpresora.tiempoTrabajo) / 100) * 365 * 24

        costoRecuperacionInversion = costoTotalImpresora / (tiempoTrabajoHorasPorAño * self.infoImpresora.vidaUtil)
        costoElectricidadHora = (self.infoImpresora.consumo / 1000) * self.costoElectricidad

        costoHoraImpresion = costoRecuperacionInversion + costoElectricidadHora
        logger.info(f"Costo por hora de impresión: {self.símboloMoneda}{costoHoraImpresion:.2f}")
        return costoHoraImpresion

    def cargarCostoPorGramo(self):
        """Cargar el costo por gramo del filamento, usando el del proyecto si está definido."""

        precioFilamento = self.precioFilamentoProyecto if self.precioFilamentoProyecto > 0 else self.precioFilamento
        self.nombreFilamentoActivo = self.nombreFilamentoProyecto if self.nombreFilamentoProyecto else self.nombreFilamento

        logger.info(f"Costo Kilogramo de Filamento ({self.nombreFilamentoActivo or 'sistema'}): {precioFilamento}")
        self.costoGramo = float(precioFilamento) / 1000

    def calcularCostos(self):
        """Calcular costos"""

        if self.infoBase is None:
            logger.error("Error fatal con data costos.md")
            exit(1)

        self.costoEnsamblado = (self.tiempoEnsamblado / 60) * self.costoHoraTrabajo

        # precioFilamento = self.precioFilamento
        self.cargarCostoPorGramo()

        costoHoraImpresion = self.calculoHoraImpresion()

        self.costoFilamento = self.totalGramos * self.costoGramo
        self.costoEficiencia = self.costoFilamento * float(self.errorFabricacion) / 100

        self.costoHoraImpresion = costoHoraImpresion * self.totalHoras

        logger.info(f"costo extras: {self.costoExtras}")
        logger.info(f"costo hora impresión: {self.costoHoraImpresion:.2f}")
        logger.info(f"Precio por gramo: {self.costoGramo}")

        self.costoTotalImpresion = self.costoFilamento + self.costoEficiencia + self.costoHoraImpresion
        self.costoUnidad = self.costoTotalImpresion + self.costoExtras + self.costoEnsamblado
        # TODO: Calcular costo por unidad en base a cuantos modelos hay en cada impresion
        # Considerar agregar en el nombre del archivo la cantidad de modelos
        # ejemplo 5pc

    def seleccionarFilamento(self):
        """Seleccionar filamento"""
        self.filamentoSeleccionado = self.selectorFilamento.value
        ui.notify(f"Filamento seleccionado: {self.listaFilamentos[self.filamentoSeleccionado]}")
        SalvarValor(self.archivoInfo, "filamento_seleccionado", self.filamentoSeleccionado, local=False)

    def agregarCostoExtra(self):
        extra = (self.textoExtra.value or "").strip()
        precio = self.textoCostoExtra.value

        if not extra or precio is None or precio < 0:
            ui.notify("Escriba el nombre del extra y un precio de 0 o más.", type="warning")
            return
        agregarValor(self.archivoExtras, extra, precio, False)
        self.textoExtra.value = ""
        self.textoCostoExtra.value = None
        self.cargarCostos()

    def borrarExtra(self):
        """Borrar costo extra seleccionado"""
        filaSeleccionada = self.tablaDataExtras.selected
        extra = filaSeleccionada[0].get("extra") if filaSeleccionada else None
        if not self.infoExtras or extra not in self.infoExtras:
            ui.notify("Seleccione en la tabla el extra que quiere borrar.", type="warning")
            return
        del self.infoExtras[extra]
        self.tablaDataExtras.selected = []

        SalvarArchivo(self.archivoExtras, self.infoExtras)

        self.costosExtras()

    def cargarGuiPrecio(self):
        cargarPaginaPrecio(self)

    def actualizarPrecios(self):
        precio = self.parse_float_seguro(self.textoVenta.value)
        if precio is None or precio < 0:
            ui.notify("El precio debe ser un número mayor o igual a 0.", type="negative")
            return

        self.precioVentaFinal = precio
        SalvarValor(self.archivoInfo, "precio_venta", self.precioVentaFinal, local=False)
        logger.info(f"Actualizar precios {self.precioVentaFinal}")

        self.cargarCostos()

        ui.notify(f"Precio de venta guardado: {self.símboloMoneda} {self.precioVentaFinal:.2f}", type="positive")

    def cargarGuiActualizar(self):
        "Crear interface para actualizar datos del modelo"
        cargarPaginaActualizar(self)

    async def buscarFolder(self) -> None:
        ui.notify("Abriendo el selector de carpetas…", type="info")

        folderBuscado: str = await run.io_bound(seleccionarFolderThinter)
        if folderBuscado:
            self.inputFolder.set_value(folderBuscado)
        else:
            ui.notify("No se seleccionó ninguna carpeta", type="info")

    def abrirProyecto(self, folder: str) -> None:
        """Cargar otro proyecto como si la app se abriera en esa carpeta."""
        if not folder or str(folder) == str(self.folderProyecto):
            return
        # ponytail: volver a los valores por defecto de la clase en vez de resetear campo por campo;
        # los widgets se recrean al recargar la página.
        vars(self).clear()
        self.__init__()
        self.folderProyecto = folder
        self.iniciarSistema()
        ui.navigate.reload()

    def cargarGui(self, interface: bool = False) -> None:
        """Cargar la interfaz gráfica de usuario.

        Args:
            interface (bool): Indica si se debe mostrar la interfaz completa con cabecera y pie de página.
        """

        @ui.page("/")
        def paginaInicio():

            # las pestañas viven en la barra superior (agregarInterface las mueve ahí)
            with ui.tabs().props("inline-label indicator-color=white outside-arrows mobile-arrows") as tabs:
                tabs.classes("text-white max-w-full")
                self.tabInfo = ui.tab("Info", icon="home")
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

            agregarInterface(interface, current_page="/", barra=tabs)

        def agregarInterface(interface: bool, current_page: str = "", barra=None):

            aplicarTema()

            if not interface:
                return

            with ui.dialog() as dialog, ui.card().classes("w-full max-w-lg mx-auto q-mt-xl p-4"):
                ui.label("Cambiar proyecto").classes("text-h6").props('role=heading aria-level=2')

                self.inputFolder = (
                    ui.input(
                        value=str(self.folderProyecto),
                        label="Ruta seleccionada",
                    )
                    .classes("w-full")
                    .props("readonly")
                )

                def abrir():
                    dialog.close()
                    self.abrirProyecto(self.inputFolder.value)

                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button("Elegir carpeta", icon="folder", on_click=self.buscarFolder).props("outline")
                    ui.button("Abrir proyecto", icon="folder_open", on_click=abrir)

            def show():
                dialog.open()

            with ui.header() as cabecera:
                cabecera.classes("bg-primary items-center justify-between")
                cabecera.style("min-height: 48px; padding: 0 8px 0 16px")
                # app y modelo a la izquierda, pestañas centradas con márgenes automáticos (ceden a 0 si falta
                # espacio y el nombre del modelo se recorta), menú a la derecha
                with ui.row().classes("w-full items-center no-wrap gap-4"):
                    ui.label("PrintTool").classes("text-h5 shrink-0")
                    ui.label(self.nombreModelo).bind_text_from(self, "nombreModelo").classes(
                        "text-subtitle1 truncate min-w-0"
                    ).props("role=heading aria-level=1")

                    centro = ui.element("div").classes("mx-auto min-w-0")
                    if barra is not None:
                        barra.move(centro)

                    with ui.button(icon="menu").classes("shrink-0") as botón:
                        botón.props('flat color=white aria-label="Menú"')
                        with ui.menu() as menu:
                            menu.classes("min-w-48 text-center")

                            estilo_menu = "w-full px-2 justify-center"

                            if current_page != "/":
                                ui.menu_item("Inicio", on_click=lambda: ui.navigate.to("/")).classes(
                                    estilo_menu
                                ).style("text-align: center;")

                            ui.menu_item("Cambiar proyecto", on_click=show).classes(estilo_menu).style(
                                "text-align: center;"
                            )

                            if current_page != "/config":
                                ui.menu_item("Configurar", on_click=lambda: ui.navigate.to("/config")).classes(
                                    estilo_menu
                                ).style("text-align: center;")

                            if current_page != "/purga":
                                ui.menu_item("Calculadora de purga MMU", on_click=lambda: ui.navigate.to("/purga")).classes(
                                    estilo_menu
                                ).style("text-align: center;")

                            ui.separator()
                            ui.menu_item("Salir", on_click=app.shutdown).classes(f"{estilo_menu} text-rojo-texto").style(
                                "text-align: center;"
                            )

            with ui.footer() as pie:
                pie.classes("bg-primary")
                pie.style("min-height: 32px; padding: 4px 16px")
                with ui.row().classes("w-full justify-center items-center"):
                    ui.label("Creado por ChepeCarlos").classes("text-white")

        registraPaginaConfig(self, agregarInterface, interface)
        registraPaginaPurga(self, agregarInterface, interface)

    def iniciarGui(self) -> None:
        """Iniciar la interfaz gráfica de usuario."""

        ui.run(
            native=True,
            window_size=(1024, 786),
            reload=False,
            dark=True,
            show=False,
            language="es",
            title="PrintTool",
            uvicorn_logging_level="warning",
        )
