from nicegui import ui
import codecs
import re
import os


def cargarDataGcode(archivo: str):
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
            print(f"Filamento usado: {info['material']} g")

        if time_match:
            print(time_match)
            hours = int(time_match.group(2)) if time_match.group(
                2) else 0  # Si no hay horas, usar 0
            minutes = int(time_match.group(3))
            seconds = int(time_match.group(4))
            info['tiempo'] = hours + minutes/60 + seconds/3600
            print(f"Tiempo estimado de impresión: {info['tiempo']:.2f} minutos")

        return info


def dataArchivos():
    ui.label('Info Modelo')

    sufijoArchivo = ".bgcode"

    infoArchivo = [
        {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre',
            'required': True, 'align': 'left'},
        {'name': 'archivo', 'label': 'Archivo', 'field': 'archivo'},
        {'name': 'material', 'label': 'Material', 'field': 'material', 'sortable': True},
        {'name': 'tiempo', 'label': 'Tiempo', 'field': 'tiempo', 'sortable': True},
        {'name': 'tipo', 'label': 'Material', 'field': 'tipo'},
        {'name': 'color', 'label': 'Color', 'field': 'color'},
    ]

    dataArchivo = [

    ]

    folderActual = os.getcwd()
    print(f"Buscando en {folderActual}")
    for archivo in os.listdir(folderActual):
        if archivo.endswith(sufijoArchivo):
            print(f"Archivo encontrado: {archivo}")
            nombreArchivo = archivo.removesuffix(sufijoArchivo)
            rutaCompleta = os.path.join(folderActual, archivo)
            dataGcode = cargarDataGcode(rutaCompleta)

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

    ui.table(columns=infoArchivo, rows=dataArchivo, row_key='nombre')


def main():
    def mostarModelos():

        infoBásica = [
            {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre',
             'required': True, 'align': 'left'},
            {'name': 'valor', 'label': 'Referencia', 'field': 'valor',
             'required': True, 'align': 'center'},
        ]

        dataCostos = [
            {'nombre': 'Costo filamento (g)', 'valor': 0},
            {'nombre': 'Eficiencia filamento', 'valor': 0},
            {'nombre': 'Costo de impresión hora', 'valor': 0},
            {"nombre": "Costo ensamblado", "valor": 0},
            {'nombre': 'Costo Extra', 'valor': 0},
            {'nombre': 'Cantidad', 'valor': 1},
            {"nombre": "Costo total", "valor": 0},
        ]
        ui.table(columns=infoBásica, rows=dataCostos, row_key='nombre')

        dataArchivos()

        ui.label('Costos Extras')

        costoExtras = [
            {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre',
             'required': True, 'align': 'left'},
            {'name': 'costo unitario', 'label': 'Costo unitario', 'field': 'valor'},
            {'name': 'cantidad', 'label': 'Cantidad', 'field': 'valor'},
            {'name': 'total', 'label': 'Total', 'field': 'valor'},
        ]

        ui.table(columns=costoExtras, rows=dataCostos, row_key='nombre')

    with ui.tabs().classes('w-full') as tabs:
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
                {'nombre': 'Nombre', 'valor': "Alcancia Creeper"},
                {'nombre': 'Material', 'valor': "PLA"},
                {'nombre': 'Total Filamento (g)', 'valor': 255.80},
                {'nombre': 'Tiempo impresión', 'valor': "10 H 5 M"},
                {'nombre': 'Precio', 'valor': "123.00$"},
            ]

            ui.label('Información Modelo')
            ui.table(columns=infoBásica, rows=dataBásica, row_key='nombre')

        with ui.tab_panel(costo):

            ui.label('Costo Modelo')

            mostarModelos()

        with ui.tab_panel(precio):

            columns = [
                {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre',
                    'required': True, 'align': 'left'},
                {'name': 'valor', 'label': 'Referencia', 'field': 'valor',
                    'required': True, 'align': 'center'},
                {'name': 'final', 'label': 'Final', 'field': 'final',
                    'required': True, 'align': 'center'},
            ]

            rows = [
                {"nombre": "Costo total", "valor": 0},
                {"nombre": "Porcentaje de Ganancia", "valor": "30%"},
                {"nombre": "Ganancia", "valor": 0},
                {"nombre": "Precio antes de iva", "valor": 0},
                {"nombre": "Iva", "valor": 0},
                {"nombre": "Costo de venta", "valor": 0},
            ]

            ui.label('Costo Modelo')

            def validar_numero(value):
                try:
                    float(value)  # Intentar convertir el valor a float
                    return None  # Si es válido, no hay error
                except ValueError:
                    return 'No es un número válido'  # Si falla, devolver mensaje de error

            with ui.row().props('rounded outlined dense'):
                ui.input(label="Costo Venta",
                         value=0,
                         validation=validar_numero).props('rounded outlined dense')
                ui.button('Actualizar', on_click=lambda: ui.notify(
                    'You clicked me!'))

            ui.table(columns=columns, rows=rows, row_key='nombre')

    ui.run(native=True, window_size=(600, 800), reload=False)


if __name__ == "__main__":
    main()
