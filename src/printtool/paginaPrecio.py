from __future__ import annotations

from typing import TYPE_CHECKING

from nicegui import run, ui

if TYPE_CHECKING:
    from printtool.printtool import printtool

from .utilidades.miDolibarr import consultarPrecioDolibarr, actualizarPrecioDolibarr


def cargarPaginaPrecio(tool: "printtool") -> None:
    """Construir la interfaz de la pestana de precios."""

    dolibarr_configurado = bool(tool.urlDolibarr and tool.tokenDolibarr)

    dataPrecio = [
        {
            "referencia": "costoUnidad",
            "final": "costoUnidad",
            "humano": "Costo de fabricación",
            "formato": lambda x: f"{tool.símboloMoneda} {x:.2f}",
        },
        {
            "referencia": "porcentajeGananciaReferencia",
            "final": "porcentajeGananciaFinal",
            "humano": "Margen de ganancia",
            "formato": lambda x: f"{x:.2f} %",
        },
        {
            "referencia": "gananciaBase",
            "final": "gananciaFinal",
            "humano": "Ganancia",
            "formato": lambda x: f"{tool.símboloMoneda} {x:.2f}",
        },
        {
            "referencia": "precioSinIvaReferencia",
            "final": "precioSinIvaFinal",
            "humano": "Precio sin IVA",
            "formato": lambda x: f"{tool.símboloMoneda} {x:.2f}",
        },
        {
            "referencia": "ivaReferencia",
            "final": "ivaFinal",
            "humano": "IVA",
            "formato": lambda x: f"{tool.símboloMoneda} {x:.2f}",
        },
        {
            "referencia": "precioVentaReferencia",
            "final": "precioVentaFinal",
            "humano": "Precio de venta",
            "formato": lambda x: f"{tool.símboloMoneda} {x:.2f}",
        },
    ]

    with ui.column().classes("w-full justify-center items-center"):
        with ui.grid(columns=3).classes("justify-center items-center w-full max-w-2xl gap-4"):
            ui.label("Concepto").classes("font-bold")
            ui.label("Referencia").classes("font-bold text-right")
            ui.label("Final").classes("font-bold text-right")

            for idPrecio, precioActual in enumerate(dataPrecio):
                esUltimo = idPrecio == len(dataPrecio) - 1

                if esUltimo:
                    ui.separator().classes("col-span-3 my-2")

                ui.label(precioActual["humano"]).classes("text-left" + (" font-bold text-lg" if esUltimo else ""))
                ui.label().bind_text_from(
                    tool,
                    precioActual["referencia"],
                    lambda x, transform_func=precioActual["formato"]: transform_func(x),
                ).classes("text-right" + (" font-bold text-lg" if esUltimo else ""))
                ui.label().bind_text_from(
                    tool,
                    precioActual["final"],
                    lambda x, transform_func=precioActual["formato"]: transform_func(x),
                ).classes("text-right" + (" font-bold text-lg text-verde-precio" if esUltimo else ""))

        ui.separator().classes("my-4 w-full")
        with ui.row().classes("w-full justify-center"):
            with ui.column().classes("justify-center items-center gap-2"):
                ui.label("Fijar precio de venta").classes("text-subtitle1").props('role=heading aria-level=2')
                with ui.row().classes("items-center gap-2"):
                    tool.textoVenta = ui.number(
                        label="Precio de venta final",
                        value=tool.precioVentaFinal,
                        validation=tool.validar_numero_no_negativo,
                        step=0.01,
                    ).classes("min-w-48")
                    ui.button(on_click=tool.actualizarPrecios, icon="check").props(
                        'color=positive aria-label="Guardar precio de venta"'
                    ).classes("h-full")
                    tool.textoVenta.on("keydown.enter", tool.actualizarPrecios)

        ui.separator().classes("my-4 w-full")
        with ui.row().classes("w-full justify-center"):
            with ui.column().classes("justify-center items-center gap-2"):
                ui.label("Dolibarr").classes("text-subtitle1").props('role=heading aria-level=2')

                def _id_producto_valido() -> bool:
                    if not tool.idProductoDolibarr:
                        ui.notify(
                            "Este modelo no tiene ID de producto en Dolibarr. Asígnelo en la pestaña Modelo.",
                            type="warning",
                        )
                        return False
                    return True

                async def _consultar():
                    if not _id_producto_valido():
                        return
                    boton_consultar.props("loading")
                    boton_actualizar.disable()
                    try:
                        precio, error = await run.io_bound(
                            consultarPrecioDolibarr,
                            tool.urlDolibarr,
                            tool.tokenDolibarr,
                            tool.idProductoDolibarr,
                        )
                    finally:
                        boton_consultar.props(remove="loading")
                        boton_actualizar.enable()
                    if error:
                        ui.notify(error, type="negative")
                        return
                    tool.textoVenta.set_value(precio)
                    tool.actualizarPrecios()
                    ui.notify(f"Precio traído de Dolibarr: {tool.símboloMoneda} {precio:.2f}", type="positive")

                async def _actualizar():
                    if not _id_producto_valido():
                        return
                    boton_actualizar.props("loading")
                    boton_consultar.disable()
                    try:
                        error = await run.io_bound(
                            actualizarPrecioDolibarr,
                            tool.urlDolibarr,
                            tool.tokenDolibarr,
                            tool.idProductoDolibarr,
                            tool.precioVentaFinal,
                        )
                    finally:
                        boton_actualizar.props(remove="loading")
                        boton_consultar.enable()
                    if error:
                        ui.notify(error, type="negative")
                        return
                    ui.notify(
                        f"Precio enviado a Dolibarr: {tool.símboloMoneda} {tool.precioVentaFinal:.2f}",
                        type="positive",
                    )

                with ui.row().classes("items-center gap-2"):
                    boton_consultar = ui.button(
                        "Traer precio de Dolibarr",
                        on_click=_consultar,
                        icon="search",
                    ).props("outline")
                    with boton_consultar:
                        ui.tooltip("Reemplaza el precio final por el que tiene el producto en Dolibarr.")
                    boton_actualizar = ui.button(
                        "Enviar precio a Dolibarr",
                        on_click=_actualizar,
                        icon="publish",
                    ).props("outline")
                    with boton_actualizar:
                        ui.tooltip("Publica el precio de venta final en el producto de Dolibarr.")

                if not dolibarr_configurado:
                    boton_actualizar.disable()
                    boton_consultar.disable()
                    ui.label("Para usar Dolibarr, agregue su URL y token en Menú › Configurar.").classes(
                        "text-ambar-costo text-sm"
                    )
