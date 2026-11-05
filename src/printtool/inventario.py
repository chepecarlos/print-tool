import json
import subprocess
import sys

from nicegui import Client, run, ui

from printtool.MiLibrerias import ConfigurarLogging, ObtenerArchivo
from printtool.printtool import printtool
from printtool.tema import aplicarTema

logger = ConfigurarLogging(__name__)


class inventario:

    listaProyectos: list[str]
    "Lista de proyectos en el sistema de inventario"

    def __init__(self):
        self.listaProyectos = []
        self.procesos: dict[str, subprocess.Popen] = {}

    def abrirProyecto(self, proyecto: list[dict]):
        """Abrir un proyecto en su propia ventana de PrintTool.

        Args:
            proyecto (list[dict]): Fila de la tabla, dentro de una lista.
        """
        if not proyecto:
            return
        rutaProyecto = proyecto[0]["ruta"]
        nombre = proyecto[0]["nombre"]

        # la ventana tarda unos segundos en aparecer: un segundo clic no abre otra copia
        abierto = self.procesos.get(rutaProyecto)
        if abierto is not None and abierto.poll() is None:
            ui.notify(f"{nombre} ya está abierto en otra ventana", type="info")
            return

        logger.info(f"Abriendo proyecto {rutaProyecto}")
        try:
            # ponytail: proceso aparte, PrintTool registra sus propias rutas "/" y no convive en este servidor
            self.procesos[rutaProyecto] = subprocess.Popen([sys.executable, "-m", "printtool.main"], cwd=rutaProyecto)
        except OSError as error:
            logger.error(f"No se pudo abrir {rutaProyecto}: {error}")
            ui.notify(
                f"No se pudo abrir {nombre}. Compruebe que la carpeta {rutaProyecto} sigue existiendo.",
                type="negative",
                multi_line=True,
            )
            return
        ui.notify(f"Abriendo {nombre}…")

    def cargarDatos(self, infoBase: dict | None = None) -> tuple[list[dict], int, list[str]]:
        """Leer info.md de cada proyecto.

        Args:
            infoBase: costos.md ya leído; si falta se lee aquí, una sola vez para todos.

        Returns:
            Filas de la tabla, cuántos proyectos no están vinculados a Dolibarr
            y las carpetas que no se pudieron leer.
        """

        if infoBase is None:
            infoBase = ObtenerArchivo(printtool.archivoConfig) or {}
        dataInfo = []
        sinDolibarr = 0
        conError: list[str] = []
        for folderProyecto in self.listaProyectos:
            proyectoPrint = printtool()
            proyectoPrint.folderProyecto = folderProyecto
            # un info.md roto (colores o precio mal escritos a mano) salta esa fila, no la página
            try:
                proyectoPrint.iniciarSistema(infoBase)

                # igual que `productos listar`: es producto si está vinculado a Dolibarr
                if not proyectoPrint.idProductoDolibarr:
                    sinDolibarr += 1
                    continue

                fila = {
                    "nombre": proyectoPrint.nombreModelo or folderProyecto.rstrip("/").split("/")[-1],
                    "propiedad": proyectoPrint.propiedadModelo or "",
                    "tipo": proyectoPrint.tipoModelo,
                    # hex de mayor a menor gramos, como en la pestaña Info
                    "colores": [
                        str(c) for c, _ in sorted(proyectoPrint.coloresTotales.items(), key=lambda x: -float(x[1]))
                    ],
                    "precio": float(proyectoPrint.precioVentaFinal or 0),
                    "inventario": proyectoPrint.inventario,
                    "ruta": folderProyecto,
                }
            except Exception as error:
                logger.error(f"No se pudo leer {folderProyecto}: {error}")
                conError.append(folderProyecto)
                continue

            dataInfo.append(fila)
        return dataInfo, sinDolibarr, conError

    def cargarGUI(self):
        "Cargar la interfaz gráfica de usuario (GUI) del sistema de inventario."

        @ui.page("/")
        async def paginaInventario(client: Client):
            aplicarTema()

            with ui.header() as cabecera:
                cabecera.classes("bg-primary items-center justify-between")
                cabecera.style("min-height: 48px; padding: 0 16px")
                with ui.row().classes("w-full items-center no-wrap"):
                    ui.label("Inventario de PrintTool").classes("text-h5 truncate min-w-0").props(
                        "role=heading aria-level=1"
                    )

            # costos.md una sola vez: da el símbolo de moneda y se comparte con cada proyecto
            infoBase = ObtenerArchivo(printtool.archivoConfig)
            if infoBase is None:
                logger.error("Falta data/costos.md; se usan valores por defecto")
                infoBase = {}
            simbolo = infoBase.get("simbolo", "$")

            columnaInfo = [
                {
                    "name": "nombre",
                    "label": "Nombre",
                    "field": "nombre",
                    "align": "left",
                    "sortable": True,
                    # orden natural en español: "Maceta 2" antes que "Maceta 10", sin importar tildes ni mayúsculas
                    ":sort": "(a, b) => String(a).localeCompare(String(b), 'es', {numeric: true, sensitivity: 'base'})",
                    # nombres largos se recortan con «…»; el texto completo sigue en el DOM
                    "classes": "ellipsis",
                    "style": "max-width: 24rem",
                },
                {"name": "propiedad", "label": "Propiedad", "field": "propiedad", "align": "left", "sortable": True},
                {"name": "tipo", "label": "Tipo", "field": "tipo", "align": "left", "sortable": True},
                {"name": "colores", "label": "Colores", "field": "colores", "align": "left"},
                {
                    "name": "precio",
                    "label": "Precio",
                    "field": "precio",
                    "align": "right",
                    "sortable": True,
                    ":format": f"value => {json.dumps(simbolo + ' ')} + Number(value).toFixed(2)",
                },
                {"name": "inventario", "label": "Inventario", "field": "inventario", "align": "right", "sortable": True},
                {"name": "abrir", "label": "", "field": "ruta", "align": "right"},
            ]

            # ancho de página de trabajo (DESIGN.md): la tabla no se estira en pantallas anchas
            area = ui.column().classes("w-full max-w-6xl mx-auto gap-2")
            with area, ui.table(
                columns=columnaInfo,
                rows=[],
                row_key="ruta",
                # orden alfabético al abrir: el orden de las carpetas en disco no dice nada
                pagination={"rowsPerPage": 8, "sortBy": "nombre"},
            ) as tabla:
                tabla.classes("w-full")
                tabla.props(
                    # hide-no-data mientras carga: el icono de aviso del estado vacío parecería un error
                    'loading hide-no-data '
                    'no-data-label="Ningún proyecto de esta carpeta tiene ID de producto en Dolibarr. '
                    'Asígnelo en la pestaña Modelo de cada proyecto." '
                    'no-results-label="Ningún producto coincide con la búsqueda"'
                )
                # abrir es navegación, no acción sobre una selección: botón en cada fila,
                # alcanzable con Tab en el orden de lectura; doble clic como atajo de ratón
                tabla.on("row-dblclick", lambda e: self.abrirProyecto([e.args[1]]))
                tabla.on("abrir", lambda e: self.abrirProyecto([e.args]))
                tabla.add_slot(
                    "body-cell-abrir",
                    """
                    <q-td :props="props" auto-width>
                        <q-btn flat dense icon="open_in_new" color="teal-4"
                            :aria-label="'Abrir ' + props.row.nombre"
                            @click="() => $parent.$emit('abrir', props.row)">
                            <q-tooltip>{{ 'Abrir ' + props.row.nombre }}</q-tooltip>
                        </q-btn>
                    </q-td>
                    """,
                )
                tabla.add_slot(
                    "body-cell-colores",
                    """
                    <q-td :props="props">
                        <span v-if="!props.value.length" class="text-tinta-secundaria">Sin calcular</span>
                        <span v-for="color in props.value" :key="color" :title="color" role="img" :aria-label="'Color ' + color"
                            class="inline-block w-4 h-4 rounded border border-muestra q-mr-xs align-middle"
                            :style="{background: color}"></span>
                    </q-td>
                    """,
                )
                # precio 0 = nunca se fijó (valor por defecto de info.md), no un producto gratis
                tabla.add_slot(
                    "body-cell-precio",
                    """
                    <q-td :props="props">
                        <span v-if="props.row.precio > 0">{{ props.value }}</span>
                        <span v-else class="text-ambar-costo">Sin precio</span>
                    </q-td>
                    """,
                )
                # "desconocido" es el valor por defecto, no un tipo elegido
                tabla.add_slot(
                    "body-cell-tipo",
                    """
                    <q-td :props="props">
                        <span v-if="props.value !== 'desconocido'">{{ props.value }}</span>
                        <span v-else class="text-tinta-secundaria">Sin tipo</span>
                    </q-td>
                    """,
                )

                with tabla.add_slot("top-right"):
                    with (
                        ui.input(placeholder="Buscar")
                        .props('type=search aria-label="Buscar productos"')
                        .bind_value(tabla, "filter")
                        .add_slot("append")
                    ):
                        ui.icon("search")

            def proyectos(n: int) -> str:
                return f"{n} {'proyecto' if n == 1 else 'proyectos'}"

            with area:
                etiquetaResumen = (
                    ui.label(f"Leyendo {proyectos(len(self.listaProyectos))}…")
                    .classes("text-sm text-tinta-secundaria")
                    .props('aria-live="polite"')
                )

            with ui.footer() as pie:
                pie.classes("bg-primary")
                pie.style("min-height: 32px; padding: 4px 16px")
                with ui.row().classes("w-full justify-center items-center"):
                    ui.label("Creado por ChepeCarlos").classes("text-white")

            # la ventana se muestra antes de leer: con cientos de proyectos el escaneo tarda segundos
            await client.connected()
            dataInfo, sinDolibarr, conError = await run.io_bound(self.cargarDatos, infoBase)
            tabla.rows = dataInfo
            tabla.props(remove="loading hide-no-data")

            # lo que no aparece en la tabla también se cuenta: el inventario no esconde proyectos
            resumen = f"{len(dataInfo)} {'producto' if len(dataInfo) == 1 else 'productos'}"
            omitidos = []
            if sinDolibarr:
                omitidos.append(f"{proyectos(sinDolibarr)} sin ID de producto en Dolibarr")
            if conError:
                omitidos.append(f"{proyectos(len(conError))} con info.md ilegible")
            if omitidos:
                verbo = "lista" if sinDolibarr + len(conError) == 1 else "listan"
                resumen += f". No se {verbo} " + " y ".join(omitidos) + "."
            etiquetaResumen.text = resumen
            if conError:
                nombres = ", ".join(c.rstrip("/").split("/")[-1] for c in conError[:3])
                if len(conError) > 3:
                    nombres += f" y {len(conError) - 3} más"
                ui.notify(
                    f"No se pudo leer el info.md de {proyectos(len(conError))}: {nombres}. "
                    "Suele ser un valor editado a mano con formato incorrecto (precio, inventario o colores); "
                    "el error exacto está en el log de PrintTool.",
                    type="warning",
                    multi_line=True,
                    timeout=0,
                    # cerrar en tinta oscura: el teal de close_button sobre amarillo no llega a 4.5:1
                    actions=[{"label": "Cerrar", "color": "black"}],
                )

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
