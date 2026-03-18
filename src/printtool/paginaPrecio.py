from __future__ import annotations

from typing import TYPE_CHECKING

from nicegui import ui

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
            "humano": "Costo Fabricación",
            "formato": lambda x: f"{tool.símboloMoneda} {x:.2f}",
        },
        {
            "referencia": "porcentajeGananciaBase",
            "final": "porcentajeGananciaFinal",
            "humano": "Porcentaje de Ganancia",
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
            "humano": "Precio antes iva",
            "formato": lambda x: f"{tool.símboloMoneda} {x:.2f}",
        },
        {
            "referencia": "ivaReferencia",
            "final": "ivaFinal",
            "humano": "Iva",
            "formato": lambda x: f"{tool.símboloMoneda} {x:.2f}",
        },
        {
            "referencia": "precioVentaReferencia",
            "final": "precioVentaFinal",
            "humano": "Precio Venta",
            "formato": lambda x: f"{tool.símboloMoneda} {x:.2f}",
        },
    ]

    with ui.column().classes("w-full justify-center items-center"):
        with ui.grid(columns=3).classes("justify-center items-center w-full max-w-2xl gap-4"):
            ui.label("Calculo").classes("font-bold text-center")
            ui.label("Referencia").classes("font-bold text-center")
            ui.label("Final").classes("font-bold text-center")

            for idPrecio, precioActual in enumerate(dataPrecio):
                esUltimo = idPrecio == len(dataPrecio) - 1

                if esUltimo:
                    ui.separator().classes("col-span-3 my-2")

                ui.label(precioActual["humano"]).classes("text-left" + (" font-bold text-lg" if esUltimo else ""))
                ui.label().bind_text_from(
                    tool,
                    precioActual["referencia"],
                    lambda x, transform_func=precioActual["formato"]: transform_func(x),
                ).classes("text-center" + (" font-bold text-lg" if esUltimo else ""))
                ui.label().bind_text_from(
                    tool,
                    precioActual["final"],
                    lambda x, transform_func=precioActual["formato"]: transform_func(x),
                ).classes("text-center" + (" font-bold text-lg text-green-400" if esUltimo else ""))

        ui.separator().classes("my-4 w-full")
        with ui.row().classes("w-full justify-center"):
            with ui.column().classes("justify-center items-center gap-2"):
                ui.label("Actualizar Precio de Venta").classes("font-bold")
                with ui.row().props("rounded outlined").classes("items-center gap-2"):
                    tool.textoVenta = ui.number(
                        label="Nuevo Precio",
                        value=tool.precioVentaFinal,
                        validation=tool.validar_numero_no_negativo,
                        step=0.01,
                    ).classes("min-w-48")
                    ui.button(on_click=tool.actualizarPrecios, icon="check").props("color=positive").classes("h-full")
                    tool.textoVenta.on("keydown.enter", tool.actualizarPrecios)

        ui.separator().classes("my-4 w-full")
        with ui.row().classes("w-full justify-center"):
            with ui.column().classes("justify-center items-center gap-2"):
                ui.label("Dolibarr ERP").classes("font-bold")

                def _consultar():
                    precio = consultarPrecioDolibarr(
                        tool.urlDolibarr,
                        tool.tokenDolibarr,
                        tool.idProductoDolibarr,
                    )
                    if precio is not None:
                        tool.textoVenta.set_value(precio)
                        tool.actualizarPrecios()
                        ui.notify(
                            f"Precio consultado desde Dolibarr: {tool.símboloMoneda}{precio:.2f}", type="positive"
                        )

                def _actualizar():
                    actualizarPrecioDolibarr(
                        tool.urlDolibarr,
                        tool.tokenDolibarr,
                        tool.idProductoDolibarr,
                        tool.precioVentaFinal,
                    )

                with ui.row().classes("items-center gap-2"):
                    boton_consultar = ui.button(
                        "Consultar precio en Dolibarr",
                        on_click=_consultar,
                        icon="search",
                    ).props("outline")
                    with boton_consultar:
                        ui.tooltip("Consultar el precio actual registrado en Dolibarr.")
                    boton_actualizar = ui.button(
                        "Actualizar precio en Dolibarr",
                        on_click=_actualizar,
                        icon="publish",
                    ).props("outline")
                    with boton_actualizar:
                        ui.tooltip("Enviar el precio final del modelo a Dolibarr.")

                if not dolibarr_configurado:
                    boton_actualizar.disable()
                    boton_consultar.disable()
                    ui.label("Configure URL y token de Dolibarr para habilitar estas acciones.").classes(
                        "text-orange-300 text-sm"
                    )
