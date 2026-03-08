from __future__ import annotations

import re
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from nicegui import ui

from printtool.MiLibrerias import ConfigurarLogging, SalvarValor

logger = ConfigurarLogging(__name__)

if TYPE_CHECKING:
    from printtool.printtool import printtool


def _validar_link(value):
    if value is None or str(value).strip() == "":
        return None
    parsed = urlparse(str(value).strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "URL invalida. Use http:// o https://"
    return None


def _validar_sku(value):
    if value is None or str(value).strip() == "":
        return None
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,40}", str(value).strip()):
        return "SKU invalido (3-40, letras, numeros, . _ -)"
    return None


def _validar_descripcion(value):
    if value is None:
        return None
    if len(str(value)) > 500:
        return "Maximo 500 caracteres"
    return None


def cargarPaginaActualizar(tool: "printtool") -> None:
    """Construir la interfaz para editar informacion del modelo."""

    def guardarModelo() -> None:
        nombre = tool.textoNombre.value if tool.textoNombre.value is not None else ""
        inventario = tool.parse_int_seguro(tool.textoInventario.value)
        link = tool.textoLink.value if tool.textoLink.value is not None else ""
        sku = tool.textoSKU.value if tool.textoSKU.value is not None else ""
        propiedad = tool.textoPropiedad.value if tool.textoPropiedad.value is not None else ""
        tipo = tool.tipoImpresion.value if tool.tipoImpresion.value is not None else "desconocido"
        descripcion = tool.textoDescripcion.value if tool.textoDescripcion.value is not None else ""

        if str(nombre).strip() == "":
            ui.notify("El nombre del modelo es obligatorio", type="negative")
            return

        if inventario is None or inventario < 0:
            ui.notify("El inventario debe ser un entero >= 0", type="negative")
            return

        valid_link = _validar_link(link)
        if valid_link:
            ui.notify(valid_link, type="negative")
            return

        valid_sku = _validar_sku(sku)
        if valid_sku:
            ui.notify(valid_sku, type="negative")
            return

        valid_desc = _validar_descripcion(descripcion)
        if valid_desc:
            ui.notify(valid_desc, type="negative")
            return

        if tipo not in tool.tipoProductos:
            tipo = "desconocido"

        tool.nombreModelo = str(nombre).strip()
        tool.inventario = inventario
        tool.linkModelo = str(link).strip()
        tool.skuModelo = str(sku).strip()
        tool.propiedadModelo = str(propiedad).strip()
        tool.tipoModelo = tipo
        tool.descripciónModelo = str(descripcion).strip()

        SalvarValor(tool.archivoInfo, "nombre", tool.nombreModelo, local=False)
        SalvarValor(tool.archivoInfo, "link", tool.linkModelo, local=False)
        SalvarValor(tool.archivoInfo, "tipo", tool.tipoModelo, local=False)
        SalvarValor(tool.archivoInfo, "inventario", tool.inventario, local=False)
        SalvarValor(tool.archivoInfo, "propiedad", tool.propiedadModelo, local=False)
        SalvarValor(tool.archivoInfo, "descripción", tool.descripciónModelo, local=False)
        SalvarValor(tool.archivoInfo, "sku", tool.skuModelo, local=False)

        logger.info("Guardando informacion del modelo")
        ui.notify("Salvando informacion")

    with ui.column().classes("w-full items-center"):
        ui.label("Editar informacion").classes("text-h5 font-bold text-center w-full q-mb-sm")
        ui.separator().classes("w-64 q-mb-md")
        ui.label(f"Ruta proyecto: {tool.folderProyecto}").classes("text-white w-64 text-center break-words")

    with ui.grid(columns=2).classes("gap-3 max-w-3xl mx-auto justify-items-center"):
        tool.textoNombre = ui.input(
            label="Nombre",
            value=tool.nombreModelo,
            validation=tool.validar_texto_requerido,
        ).classes("w-64")
        tool.textoPropiedad = ui.input(label="Propiedad", value=tool.propiedadModelo).classes("w-64")
        tool.tipoImpresion = ui.select(tool.tipoProductos, label="tipo", value=tool.tipoModelo).classes("w-64")
        tool.textoInventario = ui.number(
            label="Inventario",
            value=tool.inventario,
            validation=tool.validar_entero_no_negativo,
            step=1,
        ).classes("w-64")
        tool.textoSKU = ui.input(label="SKU", value=tool.skuModelo, validation=_validar_sku).classes("w-64")
        tool.textoLink = ui.input(label="Link", value=tool.linkModelo, validation=_validar_link).classes("w-64")
        tool.textoDescripcion = (
            ui.textarea(
                label="Descripcion",
                value=tool.descripciónModelo,
                validation=_validar_descripcion,
            )
            .props("clearable")
            .classes("col-span-2 w-full max-w-[33rem] mx-auto")
        )

    with ui.row().classes("w-full justify-center mt-2"):
        ui.button("Guardar", on_click=guardarModelo).classes("w-64")

    for entrada in [
        tool.textoNombre,
        tool.textoPropiedad,
        tool.tipoImpresion,
        tool.textoInventario,
        tool.textoSKU,
        tool.textoLink,
    ]:
        entrada.on("keydown.enter", lambda: guardarModelo())
