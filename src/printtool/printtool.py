from nicegui import ui
import codecs
import re
import os
from printtool.MiLibrerias import ObtenerArchivo, SalvarValor, SalvarArchivo
from pathlib import Path


class printtool:

    totalGramos: float = 0
    # Total de gramos de la impresión
    totalHoras: float = 0
    # Total de horas de la impresión

    # Información de la impresión
    nombreModelo: str = ""
    # Nombre del modelo
    linkModelo: str = ""
    # Link del modelo
    cantidadModelo = 1

    def __init__(self):
        self.totalGramos = 0
        self.totalHoras = 0

        self.precioVenta = 0

    def calcularPrecios(self):

        self.folderActual = Path.cwd()
        self.archivoInfo = os.path.join(self.folderActual, "info.md")
        self.archivoExtras = os.path.join(self.folderActual, "extras.md")

        print(f"Buscando en: {self.archivoInfo}")

        if not os.path.exists(self.archivoInfo):
            data = {
                "nombre": "",
                "link": "",
                "tamaño": "",
                "costo": None,
                "tiempo_ensamblaje": 0,
                "precio_venta": 0,
            }
            SalvarArchivo(self.archivoInfo, data)
            print(f"Creando data base de {self.archivoInfo}")

        if not os.path.exists(self.archivoExtras):
            data = dict()
            SalvarArchivo(self.archivoExtras, data)
            print(f"Creando data base de {self.archivoExtras}")

        self.infoBase = ObtenerArchivo("data/costos.md")
        self.infoCostos = ObtenerArchivo(self.archivoInfo, False)
        self.infoExtras = ObtenerArchivo("extras.md", False)

        print(f"Data Costos: {self.infoCostos}")
        print(f"Data Extras: {self.infoExtras}")

        self.costoExtras = 0
        if self.infoCostos is not None:
            for extra in self.infoExtras:
                costoExtras += float(self.infoExtras[extra])
        print(f"Costo extras: {self.costoExtras}")
        self.cargarInfoBasica()

    def cargarInfoBasica(self):
        self.nombreModelo = self.infoCostos.get("nombre")
        self.linkModelo = self.infoCostos.get("link")

    def cargarDataGcode(self, archivo: str, tipoArchivo: str):
        with codecs.open(archivo, "r", encoding="utf-8", errors="ignore") as fdata:
            info = {
                "material": -1.0,
                "tiempo": -1.0,
                "tipo": -1.0,
                "color": -1.0,
            }

            data = fdata.read()
            lineas = data.split("\n")
            if tipoArchivo == ".bgcode":
                lineasDocumento = "\n".join(lineas[:30])
            else:
                lineasDocumento = data
            # print(f"Primera lineas: {lineasDocumento}")
            # print("-"*80)

            buscarImpresora = re.search(r"printer_model=.*(MMU3)", lineasDocumento)

            if buscarImpresora:
                self.multiMaterial = True
            else:
                self.multiMaterial = False

            print(f"MultiMaterial de impresora: {self.multiMaterial}")

            if self.multiMaterial:
                # Formato de la línea: printer_model=MMU3
                # filament used [g]=81.79, 17.95, 41.29, 0.00, 0.00
                buscarGramos = re.search(
                    r"filament used \[g\]=([0-9.]+), ([0-9.]+), ([0-9.]+), ([0-9.]+), ([0-9.]+)",
                    lineasDocumento,
                )
                if buscarGramos:
                    info["material"] = (
                        float(buscarGramos.group(1))
                        + float(buscarGramos.group(2))
                        + float(buscarGramos.group(3))
                        + float(buscarGramos.group(4))
                        + float(buscarGramos.group(5))
                    )
            else:
                buscarGramos = re.search(
                    r"filament used \[g\]\s?=\s?([0-9.]+)", lineasDocumento
                )

                if buscarGramos:
                    info["material"] = float(buscarGramos.group(1))

            print(f"Buscar Gramos : { info['material']}")

            time_match = re.search(
                r"estimated printing time \(normal mode\)\s?=\s?(([0-9]+)h )?([0-9]+)m ([0-9]+)s",
                lineasDocumento,
            )

            if time_match:
                hours = (
                    int(time_match.group(2)) if time_match.group(2) else 0
                )  # Si no hay horas, usar 0
                minutes = int(time_match.group(3))
                seconds = int(time_match.group(4))
                info["tiempo"] = hours + minutes / 60 + seconds / 3600

            return info

    def dataArchivos(self):
        ui.label("Info Modelo")

        sufijoArchivo = (".bgcode", ".gcode")

        infoArchivo = [
            {
                "name": "nombre",
                "label": "Nombre",
                "field": "nombre",
                "required": True,
                "align": "left",
            },
            # {'name': 'archivo', 'label': 'Archivo', 'field': 'archivo'},
            {
                "name": "material",
                "label": "Material",
                "field": "material",
                "sortable": True,
            },
            {"name": "tiempo", "label": "Tiempo", "field": "tiempo", "sortable": True},
            {"name": "tipo", "label": "Material", "field": "tipo"},
            {"name": "color", "label": "Color", "field": "color"},
        ]

        dataArchivo = []

        folderActual = os.getcwd()

        self.totalGramos = 0
        self.totalHoras = 0
        print(f"Buscando en {folderActual}")
        for archivo in os.listdir(folderActual):
            if archivo.endswith(sufijoArchivo):
                print(f"Archivo encontrado: {archivo}")
                for subfijo in sufijoArchivo:
                    if subfijo in archivo:
                        tipoArchivo = subfijo
                        nombreArchivo = archivo.removesuffix(subfijo)
                rutaCompleta = os.path.join(folderActual, archivo)
                dataGcode = self.cargarDataGcode(rutaCompleta, tipoArchivo)

                horas = int(dataGcode["tiempo"])
                minutos = int((dataGcode["tiempo"] - horas) * 60)
                tiempo_formateado = f"{horas}h {minutos}m"
                dataArchivo.append(
                    {
                        "nombre": nombreArchivo,
                        "archivo": archivo,
                        "material": f"{dataGcode['material']}g",
                        "tiempo": f"{tiempo_formateado}",
                    }
                )
                self.totalGramos += float(dataGcode["material"])
                self.totalHoras += float(dataGcode["tiempo"])

        minutos = int((self.totalHoras - int(self.totalHoras)) * 60)

        dataArchivo.append(
            {
                "nombre": "Total",
                "archivo": "",
                "material": f"{self.totalGramos}g",
                "tiempo": f"{int(self.totalHoras)}h {minutos}m",
            }
        )

        ui.table(columns=infoArchivo, rows=dataArchivo, row_key="nombre")

        for file in self.tablaInfo.rows:
            if file["nombre"] == "Total Filamento (g)":
                file["valor"] = f"{self.totalGramos}g"
            elif file["nombre"] == "Tiempo impresión":
                file["valor"] = f"{int(self.totalHoras)}h {minutos}m"

        self.tablaInfo.update()
        self.calcularCostos()

    def calcularCostos(self):
        """Calcular costos"""

        data = ObtenerArchivo("data/costos.md")
        # dataExtras = ObtenerArchivo("costos.md", False)
        # dataVentas = ObtenerArchivo("ventas.md", False)
        dataVentas = self.infoCostos
        print(f"Data ventas: {dataVentas}")

        if dataVentas is None:
            tiempoEnsamblaje = 0
        else:
            tiempoEnsamblaje = float(dataVentas.get("tiempo_ensamblaje"))
        horaTrabajo = float(data.get("hora_trabajo"))
        costoEmsanblado = (tiempoEnsamblaje / 60) * horaTrabajo

        self.costoGramo = float(data.get("precio_filamento")) / 1000

        self.costoFilamento = self.totalGramos * self.costoGramo
        self.costoEficiencia = (
            self.costoFilamento * float(data.get("eficiencia_material")) / 100
        )

        self.costoImpresora = int(data.get("costo_impresora"))
        self.envioImpresora = int(data.get("envio_impresora"))
        self.mantenimientoImpresora = int(data.get("mantenimiento_impresora"))
        self.vidaUtil = int(data.get("vida_util"))
        self.tiempoTrabajo = (int(data.get("tiempo_trabajo")) / 100) * 8760
        self.consumoPotencia = int(data.get("consumo"))
        self.costoElectricidad = float(data.get("costo_electricidad"))
        self.errorFabricacion = float(data.get("error_fabricacion")) / 100

        costoTotalImpresora = (
            self.costoImpresora
            + self.envioImpresora
            + self.mantenimientoImpresora * self.vidaUtil
        )

        costoRecuperacionInversion = costoTotalImpresora / (
            self.tiempoTrabajo * self.vidaUtil
        )
        costoHora = (self.consumoPotencia / 1000) * self.costoElectricidad
        costoHoraImpresion = (costoRecuperacionInversion + costoHora) * (
            1 + self.errorFabricacion
        )

        print(f"costo extras: {self.costoExtras}")
        print(f"costo hora impresión: {costoHoraImpresion:.2f}")
        print(f"Precio por gramo: {self.costoGramo}")

        costoHoraImpresion = costoHoraImpresion * self.totalHoras
        self.costoTotal = (
            self.costoFilamento
            + self.costoEficiencia
            + costoHoraImpresion
            + costoEmsanblado
            + self.costoExtras
        )

        for data in self.tablaCostos.rows:
            if data["nombre"] == "Total filamento (g)":
                data["valor"] = f"{self.totalGramos}g"
            elif data["nombre"] == "Tiempo  Ensamblaje (m)":
                data["valor"] = f"{int(tiempoEnsamblaje)} m"
            elif data["nombre"] == "Costo Material":
                data["valor"] = f"${self.costoFilamento:.2f}"
            elif data["nombre"] == "Eficiencia filamento":
                data["valor"] = f"${self.costoEficiencia:.2f}"
            elif data["nombre"] == "Costo de impresión hora":
                data["valor"] = f"${costoHoraImpresion:.2f}"
            elif data["nombre"] == "Costo ensamblado":
                data["valor"] = f"${costoEmsanblado:.2f}"
            elif data["nombre"] == "Costo Extra":
                data["valor"] = f"${self.costoExtras:.2f}"
            elif data["nombre"] == "Cantidad":
                data["valor"] = 1
            elif data["nombre"] == "Costo total":
                data["valor"] = f"${self.costoTotal:.2f}"

    def mostarModelos(self):

        infoBásica = [
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
            {"nombre": "Tiempo  Ensamblaje (m)", "valor": 0},
            {"nombre": "Costo Material", "valor": 0},
            {"nombre": "Eficiencia filamento", "valor": 0},
            {"nombre": "Costo de impresión hora", "valor": 0},
            {"nombre": "Costo ensamblado", "valor": 0},
            {"nombre": "Costo Extra", "valor": 0},
            {"nombre": "Cantidad", "valor": 1},
            {"nombre": "Costo total", "valor": 0},
        ]
        self.tablaCostos = ui.table(
            columns=infoBásica, rows=dataCostos, row_key="nombre"
        )

        self.dataArchivos()

        self.costosExtras()

    def costosExtras(self):
        ui.label("Costos Extras")

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

        dataExtras = ObtenerArchivo("costos.md", False)

        dataCostos = []

        if dataExtras is not None:
            for extra in dataExtras:
                dataCostos.append({"nombre": extra, "valor": f"${dataExtras[extra]}"})

        ui.table(columns=infoCostos, rows=dataCostos, row_key="nombre")

    def mostarPrecio(self):

        ui.label("Costo Precio")
        print("cargando precios")

        data = ObtenerArchivo("data/costos.md")
        venta = ObtenerArchivo("ventas.md", False)
        ganancia = float(data.get("ganancia"))

        precioAntesIva = self.costoTotal / (1 - ganancia / 100)
        cantidadGanancia = precioAntesIva - self.costoTotal
        iva = precioAntesIva * 0.13
        precioSugerido = precioAntesIva + iva

        if venta is not None:
            self.precioVenta = self.infoCostos.get("precio_venta")

        print(f"Precio venta: {self.precioVenta}")
        if self.precioVenta is None:
            self.precioVenta = precioSugerido

        for valor in self.tablaInfo.rows:
            if valor["nombre"] == "Precio":
                valor["valor"] = f"${self.precioVenta:.2f}"
        self.tablaInfo.update()

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

        rows = [
            {
                "nombre": "Costo fabricación",
                "valor": f"${self.costoTotal:.2f}",
                "final": f"${self.costoTotal:.2f}",
            },
            {"nombre": "Porcentaje de Ganancia", "valor": f"{ganancia} %"},
            {"nombre": "Ganancia", "valor": f"${cantidadGanancia:.2f}"},
            {"nombre": "Precio antes de iva", "valor": f"${precioAntesIva:.2f}"},
            {"nombre": "Iva", "valor": f"${iva:.2f}"},
            {
                "nombre": "Costo de venta",
                "valor": f"${precioSugerido:.2f}",
                "final": f"${self.precioVenta:.2f}",
            },
        ]

        with ui.row().props("rounded outlined dense"):
            self.textoVenta = ui.input(
                label="Precio de Venta",
                value=self.precioVenta,
                validation=self.validar_numero,
            ).props("rounded outlined dense")
            ui.button("Actualizar", on_click=self.actualizarPrecios)

        self.tablaPrecio = ui.table(columns=columns, rows=rows, row_key="nombre")

        self.actualizarPrecios()

    def validar_numero(self, value):
        try:
            float(value)  # Intentar convertir el valor a float
            return None  # Si es válido, no hay error
        except ValueError:
            return "No es un número válido"
        # Si falla, devolver mensaje de error

    def actualizarPrecios(self):
        print(f"Actualizar precios {self.textoVenta.value}")
        self.precioVenta = float(self.textoVenta.value)
        preciosinIva = self.precioVenta / 1.13
        iva = self.precioVenta - preciosinIva
        ganancia = preciosinIva - self.costoTotal
        if ganancia < 0 or preciosinIva == 0:
            porcentajeGanancia = 0
        else:
            porcentajeGanancia = (1 - (self.costoTotal / preciosinIva)) * 100

        SalvarValor(
            "ventas.md", "precio_venta", self.precioVenta, local=False, depuracion=True
        )

        for valor in self.tablaPrecio.rows:
            if valor["nombre"] == "Costo de venta":
                valor["final"] = f"${self.precioVenta:.2f}"
            if valor["nombre"] == "Precio antes de iva":
                valor["final"] = f"${preciosinIva:.2f}"
            if valor["nombre"] == "Iva":
                valor["final"] = f"${iva:.2f}"
            if valor["nombre"] == "Ganancia":
                valor["final"] = f"${ganancia:.2f}"
            if valor["nombre"] == "Porcentaje de Ganancia":
                valor["final"] = f"{porcentajeGanancia:.2f} %"

        self.tablaPrecio.update()

    def dataModelo(self):
        ui.label("Data del modelo")
        self.textoNombre = ui.input(label="Nombre", value=self.nombreModelo)
        self.textoCantidad = ui.input(
            label="Cantidad", value=self.cantidadModelo, validation=self.validar_numero
        )
        self.textoLink = ui.input(
            label="Link",
        )
        ui.button("Guardar", on_click=self.guardarModelo)

    def guardarModelo(self):
        self.nombreModelo = self.textoNombre.value
        ui.notify(f"Nombre: {self.nombreModelo}")
        SalvarValor(self.archivoInfo, "nombre", self.nombreModelo, local=False)

        for file in self.tablaInfo.rows:
            if file["nombre"] == "Nombre":
                file["valor"] = f"{self.nombreModelo}"

        self.tablaInfo.update()

    def cargarGUI(self):
        print("Cargando GUI")

        with ui.tabs().classes("w-full bg-teal-700 text-white").style(
            "padding: 0px"
        ) as tabs:
            info = ui.tab("info", icon="home")
            costo = ui.tab("Costos", icon="view_in_ar")
            precio = ui.tab("Precio", icon="paid")
            data = ui.tab("Modelo", icon="assignment")

        with ui.tab_panels(tabs, value=info).classes("w-full"):
            with ui.tab_panel(info):
                infoBásica = [
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

                dataBásica = [
                    {"nombre": "Nombre", "valor": self.nombreModelo},
                    {"nombre": "Cantidad", "valor": self.cantidadModelo},
                    {"nombre": "Material", "valor": "PLA"},
                    {"nombre": "Total Filamento (g)", "valor": self.totalGramos},
                    {"nombre": "Tiempo impresión", "valor": "10 H 5 M"},
                    {"nombre": "Precio", "valor": "123.00$"},
                ]

                ui.label("Información Modelo")
                self.tablaInfo = ui.table(
                    columns=infoBásica, rows=dataBásica, row_key="nombre"
                )

            with ui.tab_panel(costo).style("padding: 0px"):
                with ui.scroll_area().classes(
                    "w-full h-100 border border-2 border-teal-600h"
                ).style("height: 75vh"):

                    ui.label("Costo Modelo")

                    self.mostarModelos()

            with ui.tab_panel(precio):

                self.mostarPrecio()

            with ui.tab_panel(data):

                self.dataModelo()

        ui.run(native=True, window_size=(600, 800), reload=False)
