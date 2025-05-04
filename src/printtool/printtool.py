from nicegui import ui
import codecs
import re
import os
from printtool.MiLibrerias import ObtenerArchivo

class printtool:
    def __init__(self):
        self.totalGramos = 0
        self.totalHoras = 0

    def cargarDataGcode(self, archivo: str):
        with codecs.open(archivo, 'r', encoding='utf-8', errors='ignore') as fdata:
            info = {
                "material": -1.0,
                "tiempo": -1.0,
                "tipo": -1.0,
                "color": -1.0,
            }

            data = fdata.read()
            lineas = data.split("\n")
            primerasLineas = "\n".join(lineas[:30])

            buscarGramos = re.search(
                r'filament used \[g\]=([0-9.]+)', primerasLineas)
            time_match = re.search(
                r'estimated printing time \(normal mode\)=(([0-9]+)h )?([0-9]+)m ([0-9]+)s', primerasLineas)

            if buscarGramos:
                info["material"] = float(buscarGramos.group(1))

            if time_match:
                hours = int(time_match.group(2)) if time_match.group(
                    2) else 0  # Si no hay horas, usar 0
                minutes = int(time_match.group(3))
                seconds = int(time_match.group(4))
                info['tiempo'] = hours + minutes/60 + seconds/3600

            return info


    def dataArchivos(self):
        ui.label('Info Modelo')

        sufijoArchivo = ".bgcode"

        infoArchivo = [
            {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre',
                'required': True, 'align': 'left'},
            # {'name': 'archivo', 'label': 'Archivo', 'field': 'archivo'},
            {'name': 'material', 'label': 'Material', 'field': 'material', 'sortable': True},
            {'name': 'tiempo', 'label': 'Tiempo', 'field': 'tiempo', 'sortable': True},
            {'name': 'tipo', 'label': 'Material', 'field': 'tipo'},
            {'name': 'color', 'label': 'Color', 'field': 'color'},
        ]

        dataArchivo = [
        ]

        folderActual = os.getcwd()
        
        self.totalGramos = 0
        self.totalHoras = 0
        print(f"Buscando en {folderActual}")
        for archivo in os.listdir(folderActual):
            if archivo.endswith(sufijoArchivo):
                print(f"Archivo encontrado: {archivo}")
                nombreArchivo = archivo.removesuffix(sufijoArchivo)
                rutaCompleta = os.path.join(folderActual, archivo)
                dataGcode = self.cargarDataGcode(rutaCompleta)

                horas = int(dataGcode['tiempo'])
                minutos = int((dataGcode['tiempo'] - horas) * 60)
                tiempo_formateado = f"{horas}h {minutos}m"
                dataArchivo.append(
                    {
                        'nombre': nombreArchivo,
                        'archivo': archivo,
                        'material': f"{dataGcode['material']}g",
                        'tiempo': f"{tiempo_formateado}",
                    }
                )
                self.totalGramos += float(dataGcode['material'])
                self.totalHoras += float(dataGcode['tiempo'])
        
        minutos = int((self.totalHoras - int(self.totalHoras)) * 60)
        
        dataArchivo.append(
            {
                'nombre': "Total",
                'archivo': "",
                'material': f"{self.totalGramos}g",
                'tiempo': f"{int(self.totalHoras)}h {minutos}m",
            }
        )

        ui.table(columns=infoArchivo, rows=dataArchivo, row_key='nombre')
        
        for file in self.tablaInfo.rows:
            if file['nombre'] == "Total Filamento (g)":
                file['valor'] = f"{self.totalGramos}g"
            elif file['nombre'] == "Tiempo impresión":
                file['valor'] = f"{int(self.totalHoras)}h {minutos}m"
        
        self.tablaInfo.update()
        self.calcularCostos()
        
    def calcularCostos(self):
        """Calcular costos"""
        
        data = ObtenerArchivo("data/costos.md") 
        dataExtras = ObtenerArchivo("costos.md", False)
        dataVentas = ObtenerArchivo("ventas.md", False)
        
        costoExtras = 0
        for extra in dataExtras:
            costoExtras += float(dataExtras[extra])
            
        tiempoEnsamblaje = float(dataVentas.get("tiempoEnsamblaje"))
        horaTrabajo = float(data.get("hora_trabajo"))
        costoEmsanblado = (tiempoEnsamblaje/60) * horaTrabajo
        
        costoGramo = float(data.get("precio_filamento"))/1000
        
        costoFilamento = self.totalGramos * costoGramo
        costoEficiencia =costoFilamento * float(data.get("eficiencia_material"))/100
        
        costoImpresora = int(data.get("costo_impresora"))
        envioImpresora = int(data.get("envio_impresora"))
        mantenimientoImpresora = int(data.get("mantenimiento_impresora"))
        vidaUtil = int(data.get("vida_util"))
        tiempoTrabajo = (int(data.get("tiempo_trabajo"))/100) * 8760
        consumoPotencia = int(data.get("consumo"))
        costoElectricidad = float(data.get("costo_electricidad"))
        errorFabricacion = float(data.get("error_fabricacion"))/100
        
        costoTotalImpresora = costoImpresora + envioImpresora + mantenimientoImpresora * vidaUtil
        
        costoRecuperacionInversion = costoTotalImpresora /(tiempoTrabajo * vidaUtil)
        costoHora = (consumoPotencia/1000) *costoElectricidad
        costoHoraImpresion = (costoRecuperacionInversion +costoHora)*(1+errorFabricacion)
        
        print(f"costo extras: {costoExtras}")
        print(f"costo hora impresión: {costoHoraImpresion:.2f}")
        print(f"Precio por gramo: {costoGramo}")
        
        costoHoraImpresion = costoHoraImpresion * self.totalHoras
        self.costoTotal = costoFilamento + costoEficiencia + costoHoraImpresion + costoEmsanblado + costoExtras
        
        for data in self.tablaCostos.rows:
            if data['nombre'] == "Total filamento (g)":
                data['valor'] = f"{self.totalGramos}g"
            elif data['nombre'] == "Tiempo  Ensamblaje (m)":
                data['valor'] = f"{int(tiempoEnsamblaje)} m"
            elif data['nombre'] == "Costo Material":
                data['valor'] = f"${costoFilamento:.2f}"
            elif data['nombre'] == "Eficiencia filamento":
                data['valor'] = f"${costoEficiencia:.2f}"
            elif data['nombre'] == "Costo de impresión hora":
                data['valor'] = f"${costoHoraImpresion:.2f}"
            elif data['nombre'] == "Costo ensamblado":
                data['valor'] = f"${costoEmsanblado:.2f}"
            elif data['nombre'] == "Costo Extra":
                data['valor'] = f"${costoExtras:.2f}"
            elif data['nombre'] == "Cantidad":
                data['valor'] = 1
            elif data['nombre'] == "Costo total":
                data['valor'] = f"${self.costoTotal:.2f}"
        
    def mostarModelos(self):
        

        infoBásica = [
            {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre',
            'required': True, 'align': 'left'},
            {'name': 'valor', 'label': 'Referencia', 'field': 'valor',
            'required': True, 'align': 'center'},
        ]

        dataCostos = [
            {'nombre': 'Total filamento (g)', 'valor': 0},
            {'nombre': 'Tiempo  Ensamblaje (m)', 'valor': 0},
            {'nombre': 'Costo Material', 'valor': 0},
            {'nombre': 'Eficiencia filamento', 'valor': 0},
            {'nombre': 'Costo de impresión hora', 'valor': 0},
            {"nombre": "Costo ensamblado", "valor": 0},
            {'nombre': 'Costo Extra', 'valor': 0},
            {'nombre': 'Cantidad', 'valor': 1},
            {"nombre": "Costo total", "valor": 0},
        ]
        self.tablaCostos = ui.table(columns=infoBásica, rows=dataCostos, row_key='nombre')

        self.dataArchivos()
        
        self.costosExtras()

    def costosExtras(self):
        ui.label('Costos Extras')
        
        infoCostos = [
            {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre',
                'required': True, 'align': 'left'},
            {'name': 'valor', 'label': 'Referencia', 'field': 'valor',
                'required': True, 'align': 'center'},
        ]
        
        dataExtras = ObtenerArchivo("costos.md", False)
        
        dataCostos = []
        
        for extra in dataExtras:
            dataCostos.append(
                {'nombre': extra, 'valor': f"${dataExtras[extra]}"}
            )

        ui.table(columns=infoCostos, rows=dataCostos, row_key='nombre')
        
    def mostarPrecio(self):
        
        ui.label('Costo Precio')
        print("cargando precios")
        
        data = ObtenerArchivo("data/costos.md") 
        ganancia = float(data.get("ganancia"))
        
        
        precioAntesIva = self.costoTotal / (1 - ganancia/100)
        cantidadGanancia = precioAntesIva - self.costoTotal
        iva = precioAntesIva * 0.13
        precioSugerido = precioAntesIva + iva
        
        precioVenta = data.get("precio_venta")
        if precioVenta is None:
            precioVenta = precioSugerido
        
        columns = [
            {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre', 'required': True, 'align': 'left'},
            {'name': 'valor', 'label': 'Referencia', 'field': 'valor', 'required': True, 'align': 'center'},
            {'name': 'final', 'label': 'Final', 'field': 'final', 'required': True, 'align': 'center'},
        ]

        rows = [
            {"nombre": "Costo fabricación", "valor":  f"${self.costoTotal:.2f}"},
            {"nombre": "Porcentaje de Ganancia", "valor": f"{ganancia} %"},
            {"nombre": "Ganancia", "valor": f"${cantidadGanancia:.2f}"},
            {"nombre": "Precio antes de iva", "valor": f"${precioAntesIva:.2f}"},
            {"nombre": "Iva", "valor": f"${iva:.2f}"},
            {"nombre": "Costo de venta", "valor": f"${precioSugerido:.2f}", "final": f"${precioSugerido:.2f}"},
        ]


        def validar_numero(value):
            try:
                float(value)  # Intentar convertir el valor a float
                return None  # Si es válido, no hay error
            except ValueError:
                return 'No es un número válido'  # Si falla, devolver mensaje de error

        with ui.row().props('rounded outlined dense'):
            self.textoVenta = ui.input(label="Costo Venta",
                    value=0,
                    validation=validar_numero).props('rounded outlined dense')
            ui.button('Actualizar', on_click=self.actualizarPrecios)

        ui.table(columns=columns, rows=rows, row_key='nombre')

    def actualizarPrecios(self):
        print(f"Actualizar precios {self.textoVenta.value}")


    def cargarGUI(self):
        print("Cargando GUI")
        
        with ui.tabs().classes("w-full bg-teal-700 text-white").style("padding: 0px") as tabs:
            info = ui.tab('info', icon='home')
            costo = ui.tab('Costos', icon="view_in_ar")
            precio = ui.tab('Precio', icon="paid")
        
        with ui.tab_panels(tabs, value=info).classes('w-full'):
            with ui.tab_panel(info):
                infoBásica = [
                    {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre',
                        'required': True, 'align': 'left'},
                    {'name': 'valor', 'label': 'Referencia', 'field': 'valor',
                        'required': True, 'align': 'center'},
                ]

                dataBásica = [
                    {'nombre': 'Nombre', 'valor': "Alcancía Creeper"},
                    {'nombre': 'Material', 'valor': "PLA"},
                    {'nombre': 'Total Filamento (g)', 'valor': self.totalGramos},
                    {'nombre': 'Tiempo impresión', 'valor': "10 H 5 M"},
                    {'nombre': 'Precio', 'valor': "123.00$"},
                ]

                ui.label('Información Modelo')
                self.tablaInfo = ui.table(columns=infoBásica, rows=dataBásica, row_key='nombre')

            with ui.tab_panel(costo).style("padding: 0px"):
                with ui.scroll_area().classes("w-full h-100 border border-2 border-teal-600h").style("height: 75vh"):

                    ui.label('Costo Modelo')

                    self.mostarModelos()

            with ui.tab_panel(precio):

                self.mostarPrecio()

        ui.run(native=True, window_size=(600, 800), reload=False)
