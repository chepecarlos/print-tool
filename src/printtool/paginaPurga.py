from __future__ import annotations

import time
from typing import TYPE_CHECKING, Callable

from nicegui import ui

from printtool.MiLibrerias import ObtenerArchivo, SalvarValor, ConfigurarLogging
from printtool.utilidades.miOctoprint import consultarFilamentosOctoprint
from printtool.utilidades.miSpoolman import consultarFilamentosSpoolman, actualizarPrugaFilamentoSpoolman
from printtool.utilidades.token_search_select import TokenSearchSelect

if TYPE_CHECKING:
    from printtool.printtool import printtool

logger = ConfigurarLogging(__name__)

ARCHIVO_PURGA_GLOBAL = "data/purga_colores.md"


def _matriz_default() -> dict[str, dict[str, float | None]]:
    return {
        str(fila): {str(columna): (0.0 if fila == columna else None) for columna in range(1, 6)}
        for fila in range(1, 6)
    }


def _normalizar_slots(slots_raw) -> list[str]:
    slots = ["", "", "", "", ""]
    if isinstance(slots_raw, list):
        for idx in range(min(len(slots_raw), 5)):
            valor = slots_raw[idx]
            slots[idx] = "" if valor is None else str(valor)
    return slots


def _normalizar_matriz(matriz_raw) -> dict[str, dict[str, float | None]]:
    matriz = _matriz_default()
    if not isinstance(matriz_raw, dict):
        return matriz

    for fila in range(1, 6):
        fila_key = str(fila)
        fila_data = matriz_raw.get(fila_key, {})
        if not isinstance(fila_data, dict):
            continue

        for columna in range(1, 6):
            columna_key = str(columna)
            valor = fila_data.get(columna_key)
            if valor is None:
                matriz[fila_key][columna_key] = 0.0 if fila == columna else None
                continue
            try:
                valor_num = float(valor)
            except (TypeError, ValueError):
                continue
            if valor_num < 0:
                continue
            matriz[fila_key][columna_key] = 0.0 if fila == columna else valor_num

    return matriz


def _normalizar_catalogo(catalogo_raw) -> list[dict]:
    if not isinstance(catalogo_raw, list):
        return []

    resultado = []
    for idx, item in enumerate(catalogo_raw):
        if not isinstance(item, dict):
            continue
        nombre = str(item.get("nombre") or "").strip()
        if nombre == "":
            continue

        item_id = str(item.get("id") or f"manual-{idx + 1}")
        resultado.append(
            {
                "id": item_id,
                "nombre": nombre,
                "material": str(item.get("material") or "").strip(),
                "marca": str(item.get("marca") or "").strip(),
                "color_hex": str(item.get("color_hex") or "").strip().upper(),
            }
        )

    return resultado


def _normalizar_maquinas(maquinas_raw) -> list[dict]:
    if isinstance(maquinas_raw, dict):
        if isinstance(maquinas_raw.get("maquinas"), list):
            maquinas_raw = maquinas_raw.get("maquinas")
        elif isinstance(maquinas_raw.get("impresoras"), list):
            maquinas_raw = maquinas_raw.get("impresoras")

    if not isinstance(maquinas_raw, list):
        return []

    resultado: list[dict] = []
    for idx, item in enumerate(maquinas_raw):
        if not isinstance(item, dict):
            continue

        maquina_id = str(item.get("id") or f"maquina-{idx + 1}").strip()
        nombre = str(item.get("nombre") or item.get("name") or maquina_id).strip()
        url = str(item.get("url") or item.get("url_octoprint") or "").strip()
        token = str(
            item.get("token")
            or item.get("token_octoprint")
            or item.get("api_key")
            or item.get("apiKey")
            or item.get('token"')
            or ""
        ).strip()

        # Tolerancia ante errores de escritura en la clave (ej: token")
        # o convenciones distintas del usuario.
        if token == "":
            for clave_raw, valor_raw in item.items():
                clave = str(clave_raw).strip().lower().replace(" ", "")
                if "token" not in clave and "apikey" not in clave:
                    continue
                valor = str(valor_raw or "").strip()
                if valor != "":
                    token = valor
                    break

        if url == "":
            continue

        resultado.append(
            {
                "id": maquina_id,
                "nombre": nombre,
                "url": url,
                "token": token,
                "endpoint_filamentos": str(item.get("endpoint_filamentos") or "/api/settings").strip(),
                "filamentos_path": str(item.get("filamentos_path") or "").strip(),
                "slots_path": str(item.get("slots_path") or "").strip(),
            }
        )

    return resultado


def _resolver_id_slot(id_raw: str, index_filamentos: dict[str, dict]) -> str:
    candidato = str(id_raw or "").strip()
    if candidato == "":
        return ""

    if candidato in index_filamentos:
        return candidato

    if candidato.isdigit():
        for prefijo in ("filament-", "spool-"):
            llave = f"{prefijo}{candidato}"
            if llave in index_filamentos:
                return llave

    if "-" in candidato:
        base = candidato.split("-")[-1]
        if base.isdigit():
            for prefijo in ("filament-", "spool-"):
                llave = f"{prefijo}{base}"
                if llave in index_filamentos:
                    return llave

    return ""


def _texto_filamento(item: dict) -> str:
    nombre = item.get("nombre", "")
    material = item.get("material", "")
    marca = item.get("marca", "")
    color_hex = item.get("color_hex", "")
    id_filamento = item.get("id", "")

    id_mostrar = ""
    id_filamento = str(id_filamento or "").strip()
    if id_filamento:
        # Mostrar solo el id numerico cuando venga con prefijos como
        # "filament-77" o "spool-77".
        id_mostrar = id_filamento.split("-")[-1]

    partes = [nombre]
    if id_mostrar:
        partes.insert(0, id_mostrar)
    if material:
        partes.append(material)
    if marca:
        partes.append(marca)
    if color_hex:
        partes.append(color_hex)

    return " | ".join(partes)


def _alias_busqueda_material(material: str) -> list[str]:
    material_normalizado = str(material or "").strip().lower()
    if material_normalizado == "":
        return []

    aliases = {
        "pla": ["pla"],
        "petg": ["petg", "ptge", "pteg", "pegt", "pgte"],
        "abs": ["abs"],
        "asa": ["asa"],
        "tpu": ["tpu", "tup"],
        "hips": ["hips", "hisp"],
    }

    return aliases.get(material_normalizado, [material_normalizado])


def _tokens_busqueda(texto: str) -> list[str]:
    base = str(texto or "").strip().lower()
    for separador in ("|", ",", "/", "_", "(", ")"):
        base = base.replace(separador, " ")
    return [token for token in base.split() if token]


def _opcion_filamento(item: dict) -> dict[str, str | list[str]]:
    """Construye una opcion con etiqueta visible limpia y tokens reales para busqueda."""
    visible = _texto_filamento(item)
    id_filamento = str(item.get("id") or "")
    nombre = str(item.get("nombre") or "")
    material = str(item.get("material") or "")
    marca = str(item.get("marca") or "")
    color_hex = str(item.get("color_hex") or "")

    tokens: list[str] = []
    for valor in (id_filamento, nombre, material, marca, color_hex):
        for token in _tokens_busqueda(valor):
            if token not in tokens:
                tokens.append(token)

    # Para IDs con prefijo como filament-77/spool-77, incluir tambien
    # la parte numerica para buscar por "77" directamente.
    if id_filamento and "-" in id_filamento:
        id_corto = id_filamento.split("-")[-1].strip().lower()
        if id_corto and id_corto not in tokens:
            tokens.append(id_corto)

    for alias in _alias_busqueda_material(material):
        if alias not in tokens:
            tokens.append(alias)

    return {
        "label": visible,
        "display_label": visible,
        "search_label": " ".join(tokens) or visible.lower(),
        "search_terms": tokens,
    }


def _filamento_por_id(filamentos: list[dict]) -> dict[str, dict]:
    return {str(item.get("id")): item for item in filamentos if item.get("id")}


def _nombre_slot(slot_idx: int, slots: list[str], index_filamentos: dict[str, dict]) -> str:
    slot_id = slots[slot_idx]
    if slot_id and slot_id in index_filamentos:
        return index_filamentos[slot_id].get("nombre", f"Color {slot_idx + 1}")
    if slot_id:
        return f"No disponible ({slot_id})"
    return f"Color {slot_idx + 1}"


def _texto_slot_par(slot_idx: int, slots: list[str], index_filamentos: dict[str, dict]) -> str:
    numero = slot_idx + 1
    slot_id = str(slots[slot_idx] or "").strip()

    if slot_id and slot_id in index_filamentos:
        nombre = str(index_filamentos[slot_id].get("nombre") or f"Color {numero}")
        id_corto = slot_id.split("-")[-1] if "-" in slot_id else slot_id
        return f"Color {numero} | {id_corto} | {nombre}"

    if slot_id:
        id_corto = slot_id.split("-")[-1] if "-" in slot_id else slot_id
        return f"Color {numero} | {id_corto} | No disponible"

    return f"Color {numero} | Sin asignar"


def _linea_slot(slot_idx: int, slots: list[str], index_filamentos: dict[str, dict]) -> str:
    slot_id = slots[slot_idx]
    if slot_id and slot_id in index_filamentos:
        item = index_filamentos[slot_id]
        texto = f"Color {slot_idx + 1}: {_texto_filamento(item)}"
        return texto
    if slot_id:
        return f"Color {slot_idx + 1}: {slot_id} (no disponible en la fuente actual)"
    return f"Color {slot_idx + 1}: Sin asignar"


def _color_hex_slot(slot_idx: int, slots: list[str], index_filamentos: dict[str, dict]) -> str:
    slot_id = slots[slot_idx]
    if slot_id and slot_id in index_filamentos:
        color_hex = str(index_filamentos[slot_id].get("color_hex") or "").strip()
        if color_hex.startswith("#") and len(color_hex) in (4, 7):
            return color_hex
    return "#222222"


def _id_corto_filamento(slot_id: str) -> str:
    slot_id = str(slot_id or "").strip()
    if slot_id == "":
        return ""

    id_corto = slot_id.split("-")[-1]
    return id_corto if id_corto.isdigit() else ""


def _parsear_pruga_compacto(valor_pruga: str) -> tuple[dict[str, float], int]:
    texto = str(valor_pruga or "").strip()
    if texto == "":
        return {}, 0

    resultado: dict[str, float] = {}
    invalidos = 0

    for bloque in texto.replace(",", ".").split("."):
        token = bloque.strip()
        if token == "":
            continue

        if "-" not in token:
            invalidos += 1
            continue

        destino_raw, mm3_raw = token.split("-", 1)
        destino = destino_raw.strip()
        if not destino.isdigit():
            invalidos += 1
            continue

        try:
            mm3 = float(str(mm3_raw).strip())
        except (TypeError, ValueError):
            invalidos += 1
            continue

        if mm3 < 0:
            invalidos += 1
            continue

        resultado[destino] = mm3

    return resultado, invalidos


def _formato_mm3_compacto(valor: float) -> str:
    texto = f"{float(valor):.3f}".rstrip("0").rstrip(".")
    return texto if texto != "" else "0"


def _serializar_pruga_compacto(mapa: dict[str, float]) -> str:
    pares: list[tuple[int, float]] = []
    for destino, mm3 in mapa.items():
        if not str(destino).isdigit():
            continue
        try:
            valor = float(mm3)
        except (TypeError, ValueError):
            continue
        if valor < 0:
            continue
        pares.append((int(destino), valor))

    pares.sort(key=lambda item: item[0])
    return ".".join(f"{destino}-{_formato_mm3_compacto(mm3)}" for destino, mm3 in pares)


def registraPaginaPurga(tool: "printtool", add_interface: Callable[[bool, str], None], interface: bool) -> None:
    """Registrar la pagina /purga para configurar purga color a color en mmu3."""

    @ui.page("/purga")
    def pagina_purga() -> None:
        data_global = ObtenerArchivo(ARCHIVO_PURGA_GLOBAL) or {}
        data_proyecto = ObtenerArchivo(tool.archivoInfo, False) or {}
        data_impresoras = ObtenerArchivo("data/impresoras.md") or {}
        maquinas = _normalizar_maquinas(data_impresoras)
        maquinas_por_id = {str(item.get("id")): item for item in maquinas}

        maquina_id_guardada = str(data_proyecto.get("purga_maquina_id") or "").strip()
        maquina_id_inicial = ""
        if maquina_id_guardada in maquinas_por_id:
            maquina_id_inicial = maquina_id_guardada
        elif len(maquinas) > 0:
            maquina_id_inicial = str(maquinas[0].get("id") or "")

        catalogo_manual = _normalizar_catalogo(data_global.get("catalogo_filamentos", []))

        filamentos_spoolman = []
        spoolman_activo = False
        octoprint_activo = False
        slots_octoprint = ["", "", "", "", ""]
        if tool.urlSpoolman:
            consulta_spoolman = consultarFilamentosSpoolman(tool.urlSpoolman)
            if isinstance(consulta_spoolman, list) and len(consulta_spoolman) > 0:
                filamentos_spoolman = consulta_spoolman
                spoolman_activo = True

        fuente_filamentos = filamentos_spoolman if spoolman_activo else catalogo_manual
        index_filamentos = _filamento_por_id(fuente_filamentos)

        slots = _normalizar_slots(data_proyecto.get("purga_slots", data_global.get("purga_slots")))
        matriz = _normalizar_matriz(data_proyecto.get("purga_mmu3", data_global.get("purga_mmu3")))

        opciones_filamentos = {item["id"]: _opcion_filamento(item) for item in fuente_filamentos}

        slot_selectores: list = []
        indicadores_color: dict[int, any] = {}
        labels_encabezado: dict[int, any] = {}
        indicadores_encabezado: dict[int, any] = {}
        labels_fila: dict[int, any] = {}
        indicadores_fila: dict[int, any] = {}
        inputs_matriz: dict[tuple[int, int], any] = {}

        with ui.column().classes("w-full items-center"):
            ui.label("Referencia de purga por cambio de color (MMU3)").classes("text-h6")

            estado_fuente = ui.label("").classes("text-sm text-cyan-300")

            with ui.row().classes("w-full max-w-6xl justify-center"):
                boton_recargar_spoolman = ui.button("Recargar Spoolman", icon="refresh")

            with ui.card().classes("w-full max-w-6xl"):
                ui.label("Seleccion de filamentos para Color 1..5").classes("text-subtitle1")

                with ui.column().classes("w-full gap-2"):
                    for idx in range(5):
                        with ui.row().classes("w-full items-center no-wrap gap-2"):
                            indicador = (
                                ui.element("div")
                                .classes("w-8 h-8 rounded border border-gray-500 shrink-0")
                                .style(f"background-color: {_color_hex_slot(idx, slots, index_filamentos)};")
                            )
                            indicadores_color[idx] = indicador

                            valor_slot = slots[idx] if slots[idx] and slots[idx] in opciones_filamentos else None
                            selector = TokenSearchSelect(
                                options=opciones_filamentos,
                                value=valor_slot,
                                label=f"Color {idx + 1}",
                                with_input=True,
                                clearable=True,
                                on_change=lambda e, slot_idx=idx: actualizar_slot(slot_idx, e.value),
                            ).classes("flex-1 min-w-0")

                        slot_selectores.append(selector)

                with ui.row().classes("w-full justify-between items-center mt-2 gap-2"):
                    with ui.row().classes("items-center gap-2"):
                        opciones_maquinas = {item["id"]: item["nombre"] for item in maquinas}
                        selector_maquina = ui.select(
                            opciones_maquinas,
                            label="Maquina",
                            value=maquina_id_inicial if maquina_id_inicial else None,
                        ).classes("w-60")

                        boton_cargar_octoprint = ui.button(
                            "Cargar filamento desde octoprint",
                            icon="cloud_download",
                        ).props("outline")
                        boton_autocompletar_slots = ui.button(
                            "Autocompletar Color 1..5",
                            icon="auto_fix_high",
                        ).props("outline")

                        if len(opciones_maquinas) == 0:
                            selector_maquina.disable()
                            boton_cargar_octoprint.disable()
                            boton_autocompletar_slots.disable()

                    with ui.row().classes("items-center gap-2"):
                        boton_guardar_slots_proyecto = ui.button(
                            "Guardar selecciones en proyecto",
                            icon="save",
                        ).props("outline")
                        boton_limpiar_slots_proyecto = ui.button(
                            "Limpiar slots del proyecto",
                            icon="delete_sweep",
                        ).props("outline color=negative")

            with ui.card().classes("w-full max-w-6xl"):
                ui.label("Edicion rapida por par de colores").classes("text-subtitle1")
                with ui.row().classes("items-center w-full gap-3"):
                    opciones_par_inicial = {
                        str(idx): _texto_slot_par(idx - 1, slots, index_filamentos) for idx in range(1, 6)
                    }
                    selector_origen = ui.select(opciones_par_inicial, label="Desde", value="1").classes("w-72")
                    selector_destino = ui.select(opciones_par_inicial, label="Hacia", value="2").classes("w-72")
                    input_par = ui.number(
                        label="Purga mmu3",
                        step=1,
                        validation=tool.validar_numero_no_negativo,
                    ).classes("min-w-40")
                    boton_aplicar_par = ui.button("Aplicar", icon="check")

            with ui.card().classes("w-full max-w-6xl"):
                ui.label("Matriz de purga (MMU3)").classes("text-subtitle1")

                with ui.grid(columns=6).classes("w-full gap-2 items-center"):
                    ui.label("Desde/Hacia").classes("font-bold")
                    for col in range(1, 6):
                        with ui.row().classes("items-center justify-center gap-2"):
                            indicadores_encabezado[col] = (
                                ui.element("div")
                                .classes("w-4 h-4 rounded border border-gray-500 shrink-0")
                                .style(f"background-color: {_color_hex_slot(col - 1, slots, index_filamentos)};")
                            )
                            labels_encabezado[col] = ui.label(f"Color {col}").classes("font-bold text-center")

                    for fila in range(1, 6):
                        with ui.row().classes("items-center gap-2"):
                            indicadores_fila[fila] = (
                                ui.element("div")
                                .classes("w-4 h-4 rounded border border-gray-500 shrink-0")
                                .style(f"background-color: {_color_hex_slot(fila - 1, slots, index_filamentos)};")
                            )
                            labels_fila[fila] = ui.label(f"Color {fila}").classes("font-bold")
                        for columna in range(1, 6):
                            valor = matriz[str(fila)][str(columna)]
                            if fila == columna:
                                ui.element("div").classes("w-28 h-10")
                                continue

                            entrada = ui.number(
                                value=valor,
                                step=1,
                            ).classes("w-28")

                            inputs_matriz[(fila, columna)] = entrada

                with ui.row().classes("w-full justify-center gap-2 mt-3"):
                    boton_guardar_proyecto = ui.button("Guardar en proyecto", icon="save")
                    boton_guardar_global = ui.button("Guardar global", icon="public")
                    boton_cargar_global = ui.button("Restaurar desde global", icon="download")

            with ui.expansion("Catalogo manual (respaldo cuando Spoolman no esta activo)").classes("w-full max-w-6xl"):
                ui.label("Filamentos manuales: nombre + material + marca + color").classes("text-sm")

                with ui.row().classes("w-full items-center gap-2"):
                    manual_nombre = ui.input(label="Nombre").classes("min-w-40")
                    manual_material = ui.input(label="Material").classes("min-w-32")
                    manual_marca = ui.input(label="Marca").classes("min-w-32")
                    manual_color = ui.input(label="Color HEX").classes("min-w-32")
                    boton_agregar_manual = ui.button("Agregar", icon="add")

                tabla_manual = ui.table(
                    columns=[
                        {"name": "id", "label": "ID", "field": "id"},
                        {"name": "nombre", "label": "Nombre", "field": "nombre"},
                        {"name": "material", "label": "Material", "field": "material"},
                        {"name": "marca", "label": "Marca", "field": "marca"},
                        {"name": "color_hex", "label": "Color", "field": "color_hex"},
                    ],
                    rows=list(catalogo_manual),
                    row_key="id",
                    selection="single",
                    pagination=8,
                ).classes("w-full")

                boton_borrar_manual = ui.button("Borrar seleccionado", icon="delete").props("color=negative")

        def actualizar_estado_fuente() -> None:
            if octoprint_activo:
                estado_fuente.set_text(f"Fuente activa: OctoPrint ({len(fuente_filamentos)} filamentos)")
            elif spoolman_activo:
                estado_fuente.set_text(f"Fuente activa: Spoolman ({len(fuente_filamentos)} filamentos)")
            else:
                estado_fuente.set_text(f"Fuente activa: Catalogo manual ({len(catalogo_manual)} filamentos)")

        def actualizar_opciones_filamentos() -> None:
            nonlocal opciones_filamentos
            opciones_filamentos = {item["id"]: _opcion_filamento(item) for item in fuente_filamentos}

            for idx, selector in enumerate(slot_selectores):
                opciones_actualizadas = dict(opciones_filamentos)
                slot_actual = slots[idx]
                if slot_actual and slot_actual not in opciones_actualizadas:
                    opciones_actualizadas[slot_actual] = f"{slot_actual} (no disponible)"
                selector.set_options(opciones_actualizadas)
                selector.set_value(slot_actual if slot_actual else None)

        def actualizar_encabezados_matriz() -> None:
            for idx in range(1, 6):
                texto = _nombre_slot(idx - 1, slots, index_filamentos)
                color = _color_hex_slot(idx - 1, slots, index_filamentos)
                labels_encabezado[idx].set_text(texto)
                indicadores_encabezado[idx].style(f"background-color: {color};")
                labels_fila[idx].set_text(texto)
                indicadores_fila[idx].style(f"background-color: {color};")

        def actualizar_selectores_par() -> None:
            opciones = {str(idx): _texto_slot_par(idx - 1, slots, index_filamentos) for idx in range(1, 6)}
            selector_origen.set_options(opciones)
            selector_destino.set_options(opciones)

            if selector_origen.value not in opciones:
                selector_origen.set_value("1")
            if selector_destino.value not in opciones:
                selector_destino.set_value("2")

        def actualizar_indicadores_color() -> None:
            for idx, indicador in indicadores_color.items():
                color = _color_hex_slot(idx, slots, index_filamentos)
                indicador.style(f"background-color: {color};")

        def actualizar_slot(slot_idx: int, value) -> None:
            slot_anterior = slots[slot_idx]
            slots[slot_idx] = str(value) if value is not None else ""

            if slot_anterior and slots[slot_idx] == "":
                limpiar_matriz_relacionada_slot(slot_idx)

            actualizar_indicadores_color()
            actualizar_encabezados_matriz()
            actualizar_selectores_par()
            cargar_desde_spoolman_si_hay_datos(notificar=False)

        def refrescar_ui_filamentos() -> None:
            actualizar_estado_fuente()
            actualizar_opciones_filamentos()
            actualizar_indicadores_color()
            actualizar_encabezados_matriz()
            actualizar_selectores_par()
            tabla_manual.rows = list(catalogo_manual)
            tabla_manual.update()

        def leer_matriz_desde_ui() -> dict[str, dict[str, float | None]] | None:
            resultado = _matriz_default()
            for fila in range(1, 6):
                for columna in range(1, 6):
                    if fila == columna:
                        resultado[str(fila)][str(columna)] = 0.0
                        continue

                    valor_raw = inputs_matriz[(fila, columna)].value
                    if valor_raw is None or str(valor_raw).strip() == "":
                        resultado[str(fila)][str(columna)] = None
                        continue

                    valor = tool.parse_float_seguro(valor_raw)
                    if valor is None or valor < 0:
                        ui.notify(
                            f"Valor invalido en {fila} -> {columna}. Debe ser numero >= 0",
                            type="negative",
                        )
                        return None
                    resultado[str(fila)][str(columna)] = float(valor)
            return resultado

        def aplicar_matriz_a_ui(matriz_actual: dict[str, dict[str, float | None]]) -> None:
            for fila in range(1, 6):
                for columna in range(1, 6):
                    if fila == columna:
                        continue
                    entrada = inputs_matriz[(fila, columna)]
                    valor = matriz_actual.get(str(fila), {}).get(str(columna), None)
                    if valor is None:
                        entrada.set_value(None)
                    else:
                        entrada.set_value(float(valor))

        def limpiar_matriz_relacionada_slot(slot_idx: int) -> None:
            fila_columna = slot_idx + 1

            for columna in range(1, 6):
                if columna == fila_columna:
                    continue
                inputs_matriz[(fila_columna, columna)].set_value(None)

            for fila in range(1, 6):
                if fila == fila_columna:
                    continue
                inputs_matriz[(fila, fila_columna)].set_value(None)

        def construir_matriz_desde_pruga_spoolman() -> tuple[dict[str, dict[str, float | None]], int, int]:
            matriz_spoolman = _matriz_default()
            celdas_cargadas = 0
            errores_formato = 0

            for origen_idx in range(5):
                slot_origen = slots[origen_idx]
                if slot_origen not in index_filamentos:
                    continue

                pruga_raw = str(index_filamentos[slot_origen].get("pruga") or "").strip()
                if pruga_raw == "":
                    continue

                mapa_origen, errores = _parsear_pruga_compacto(pruga_raw)
                errores_formato += errores

                for destino_idx in range(5):
                    if origen_idx == destino_idx:
                        continue

                    slot_destino = slots[destino_idx]
                    id_destino = _id_corto_filamento(slot_destino)
                    if id_destino == "":
                        continue

                    if id_destino in mapa_origen:
                        fila = str(origen_idx + 1)
                        columna = str(destino_idx + 1)
                        matriz_spoolman[fila][columna] = float(mapa_origen[id_destino])
                        celdas_cargadas += 1

            return matriz_spoolman, celdas_cargadas, errores_formato

        def cargar_desde_spoolman_si_hay_datos(notificar: bool = False) -> None:
            if not spoolman_activo:
                return

            matriz_spoolman, celdas_cargadas, errores_formato = construir_matriz_desde_pruga_spoolman()
            if celdas_cargadas > 0:
                aplicar_matriz_a_ui(matriz_spoolman)
                if notificar:
                    ui.notify(
                        f"Matriz actualizada desde Spoolman: {celdas_cargadas} pares de purga",
                        type="positive",
                    )

            if errores_formato > 0 and notificar:
                ui.notify(
                    "Se encontraron entradas invalidas en el campo pruga de algunos filamentos",
                    type="warning",
                )

        def sincronizar_pruga_spoolman(matriz_guardar: dict[str, dict[str, float | None]]) -> None:
            if not spoolman_activo or not tool.urlSpoolman:
                return

            total_origenes = 0
            exitos = 0
            errores = 0

            for origen_idx in range(5):
                slot_origen = slots[origen_idx]
                if slot_origen not in index_filamentos:
                    continue

                origen_info = index_filamentos[slot_origen]
                filament_id = origen_info.get("filament_id")
                try:
                    filament_id = int(filament_id)
                except (TypeError, ValueError):
                    continue

                actualizaciones: dict[str, float] = {}
                for destino_idx in range(5):
                    if origen_idx == destino_idx:
                        continue

                    valor = matriz_guardar[str(origen_idx + 1)][str(destino_idx + 1)]
                    if valor is None:
                        continue

                    id_destino = _id_corto_filamento(slots[destino_idx])
                    if id_destino == "":
                        continue

                    actualizaciones[id_destino] = float(valor)

                if len(actualizaciones) == 0:
                    continue

                total_origenes += 1

                mapa_actual, _ = _parsear_pruga_compacto(str(origen_info.get("pruga") or ""))
                mapa_actual.update(actualizaciones)
                valor_nuevo = _serializar_pruga_compacto(mapa_actual)

                if valor_nuevo == str(origen_info.get("pruga") or "").strip():
                    exitos += 1
                    continue

                guardado = actualizarPrugaFilamentoSpoolman(tool.urlSpoolman, filament_id, valor_nuevo)
                if guardado:
                    origen_info["pruga"] = valor_nuevo
                    exitos += 1
                else:
                    errores += 1

            if total_origenes == 0:
                ui.notify(
                    "No se enviaron datos a Spoolman (faltan pares origen/destino con filamentos asignados)",
                    type="warning",
                )
                return

            if errores == 0:
                ui.notify(f"Spoolman sincronizado: {exitos} filamentos actualizados", type="positive")
            else:
                ui.notify(
                    f"Spoolman parcial: {exitos} ok, {errores} con error",
                    type="warning",
                )

        def guardar_en_global() -> None:
            matriz_guardar = leer_matriz_desde_ui()
            if matriz_guardar is None:
                return

            SalvarValor(ARCHIVO_PURGA_GLOBAL, "purga_slots", list(slots))
            SalvarValor(ARCHIVO_PURGA_GLOBAL, "purga_mmu3", matriz_guardar)
            SalvarValor(ARCHIVO_PURGA_GLOBAL, "catalogo_filamentos", list(catalogo_manual))
            sincronizar_pruga_spoolman(matriz_guardar)
            ui.notify("Configuracion de purga guardada en global", type="positive")

        def guardar_slots_en_proyecto() -> None:
            SalvarValor(tool.archivoInfo, "purga_slots", list(slots), local=False)
            if selector_maquina.value:
                SalvarValor(tool.archivoInfo, "purga_maquina_id", str(selector_maquina.value), local=False)
            ui.notify("Selecciones de filamento guardadas en el proyecto", type="positive")

        def limpiar_slots_proyecto() -> None:
            slots[:] = ["", "", "", "", ""]
            SalvarValor(tool.archivoInfo, "purga_slots", ["", "", "", "", ""], local=False)
            for selector in slot_selectores:
                selector.set_value(None)
            actualizar_indicadores_color()
            actualizar_encabezados_matriz()
            actualizar_selectores_par()
            ui.notify("Slots de filamentos del proyecto limpiados", type="info")

        def guardar_en_proyecto() -> None:
            matriz_guardar = leer_matriz_desde_ui()
            if matriz_guardar is None:
                return

            SalvarValor(tool.archivoInfo, "purga_slots", list(slots), local=False)
            SalvarValor(tool.archivoInfo, "purga_mmu3", matriz_guardar, local=False)
            sincronizar_pruga_spoolman(matriz_guardar)
            ui.notify("Configuracion de purga guardada en el proyecto", type="positive")

        def cargar_global() -> None:
            nonlocal fuente_filamentos, index_filamentos, spoolman_activo

            data = ObtenerArchivo(ARCHIVO_PURGA_GLOBAL) or {}
            slots_global = _normalizar_slots(data.get("purga_slots"))
            matriz_global = _normalizar_matriz(data.get("purga_mmu3"))
            catalogo_actualizado = _normalizar_catalogo(data.get("catalogo_filamentos", []))

            slots[:] = slots_global
            aplicar_matriz_a_ui(matriz_global)

            catalogo_manual.clear()
            catalogo_manual.extend(catalogo_actualizado)

            if not spoolman_activo and not octoprint_activo:
                fuente_filamentos = catalogo_manual
                index_filamentos = _filamento_por_id(fuente_filamentos)

            refrescar_ui_filamentos()
            ui.notify("Valores cargados desde la configuracion global", type="info")

        def recargar_spoolman() -> None:
            nonlocal spoolman_activo, octoprint_activo, fuente_filamentos, index_filamentos

            if not tool.urlSpoolman:
                ui.notify("No hay URL de Spoolman configurada. Use /config.", type="warning")
                spoolman_activo = False
                octoprint_activo = False
                fuente_filamentos = catalogo_manual
                index_filamentos = _filamento_por_id(fuente_filamentos)
                refrescar_ui_filamentos()
                return

            consulta = consultarFilamentosSpoolman(tool.urlSpoolman)
            if isinstance(consulta, list) and len(consulta) > 0:
                spoolman_activo = True
                octoprint_activo = False
                fuente_filamentos = consulta
                index_filamentos = _filamento_por_id(fuente_filamentos)
                ui.notify(f"Spoolman activo: {len(consulta)} filamentos disponibles", type="positive")
            else:
                spoolman_activo = False
                octoprint_activo = False
                fuente_filamentos = catalogo_manual
                index_filamentos = _filamento_por_id(fuente_filamentos)
                ui.notify("Spoolman no disponible, usando catalogo manual", type="warning")

            refrescar_ui_filamentos()
            cargar_desde_spoolman_si_hay_datos(notificar=True)

        def agregar_manual() -> None:
            nonlocal fuente_filamentos, index_filamentos

            nombre = str(manual_nombre.value or "").strip()
            material = str(manual_material.value or "").strip()
            marca = str(manual_marca.value or "").strip()
            color_hex = str(manual_color.value or "").strip().upper()

            if nombre == "":
                ui.notify("Nombre de filamento obligatorio", type="negative")
                return

            nuevo = {
                "id": f"manual-{int(time.time() * 1000)}",
                "nombre": nombre,
                "material": material,
                "marca": marca,
                "color_hex": color_hex,
            }

            catalogo_manual.append(nuevo)
            SalvarValor(ARCHIVO_PURGA_GLOBAL, "catalogo_filamentos", list(catalogo_manual))

            manual_nombre.set_value("")
            manual_material.set_value("")
            manual_marca.set_value("")
            manual_color.set_value("")

            if not spoolman_activo and not octoprint_activo:
                fuente_filamentos = catalogo_manual
                index_filamentos = _filamento_por_id(fuente_filamentos)

            refrescar_ui_filamentos()
            ui.notify("Filamento agregado al catalogo manual", type="positive")

        def borrar_manual() -> None:
            nonlocal fuente_filamentos, index_filamentos

            seleccion = tabla_manual.selected
            if not seleccion:
                ui.notify("Seleccione un filamento manual para borrar", type="warning")
                return

            borrar_id = str(seleccion[0].get("id", ""))
            if borrar_id == "":
                ui.notify("No se pudo identificar el filamento seleccionado", type="negative")
                return

            catalogo_filtrado = [item for item in catalogo_manual if str(item.get("id")) != borrar_id]
            catalogo_manual.clear()
            catalogo_manual.extend(catalogo_filtrado)

            for idx in range(5):
                if slots[idx] == borrar_id:
                    slots[idx] = ""
                    limpiar_matriz_relacionada_slot(idx)

            SalvarValor(ARCHIVO_PURGA_GLOBAL, "catalogo_filamentos", list(catalogo_manual))

            if not spoolman_activo and not octoprint_activo:
                fuente_filamentos = catalogo_manual
                index_filamentos = _filamento_por_id(fuente_filamentos)

            tabla_manual.selected = []
            refrescar_ui_filamentos()
            ui.notify("Filamento eliminado del catalogo manual", type="info")

        def aplicar_par() -> None:
            origen = tool.parse_int_seguro(selector_origen.value)
            destino = tool.parse_int_seguro(selector_destino.value)
            valor = tool.parse_float_seguro(input_par.value)

            if origen is None or destino is None:
                ui.notify("Seleccione origen y destino validos", type="negative")
                return

            if origen < 1 or origen > 5 or destino < 1 or destino > 5:
                ui.notify("Origen y destino deben estar entre 1 y 5", type="negative")
                return

            if origen == destino:
                ui.notify("No se puede editar la diagonal (siempre 0)", type="warning")
                return

            if valor is None or valor < 0:
                ui.notify("Ingrese un valor de purga valido (>= 0)", type="negative")
                return

            inputs_matriz[(origen, destino)].set_value(float(valor))
            ui.notify(f"Actualizado: {origen} -> {destino} = {valor:.2f} mmu3", type="positive")

        def _maquina_actual() -> dict | None:
            maquina_id = str(selector_maquina.value or "").strip()
            if maquina_id == "":
                return None
            return maquinas_por_id.get(maquina_id)

        def cargar_filamentos_desde_octoprint() -> None:
            nonlocal spoolman_activo, octoprint_activo, fuente_filamentos, index_filamentos, slots_octoprint

            maquina = _maquina_actual()
            if maquina is None:
                ui.notify("Seleccione una maquina valida", type="warning")
                return

            consulta = consultarFilamentosOctoprint(maquina)
            if not consulta.get("ok"):
                error = str(consulta.get("error") or "No se pudo consultar OctoPrint")
                ui.notify(error, type="negative")
                return

            filamentos = consulta.get("filamentos")
            if not isinstance(filamentos, list) or len(filamentos) == 0:
                ui.notify("No se encontraron filamentos en la respuesta de OctoPrint", type="warning")
                return

            spoolman_activo = False
            octoprint_activo = True
            fuente_filamentos = filamentos
            index_filamentos = _filamento_por_id(fuente_filamentos)

            slots_data = consulta.get("slots")
            if isinstance(slots_data, list) and len(slots_data) == 5:
                slots_octoprint = [str(item or "") for item in slots_data]
            else:
                slots_octoprint = ["", "", "", "", ""]

            SalvarValor(tool.archivoInfo, "purga_maquina_id", maquina["id"], local=False)
            refrescar_ui_filamentos()
            ui.notify(f"OctoPrint activo: {len(filamentos)} filamentos disponibles", type="positive")

        def autocompletar_slots_octoprint() -> None:
            if not octoprint_activo:
                ui.notify("Primero cargue filamentos desde OctoPrint", type="warning")
                return

            ids_resueltos = ["", "", "", "", ""]
            for idx in range(5):
                ids_resueltos[idx] = _resolver_id_slot(slots_octoprint[idx], index_filamentos)

            if not any(ids_resueltos):
                ids_ordenados = [str(item.get("id") or "") for item in fuente_filamentos]
                ids_resueltos = ids_ordenados[:5] + [""] * max(0, 5 - len(ids_ordenados[:5]))
                ui.notify(
                    "No se detectaron tools en OctoPrint; se asignaron los primeros filamentos de la lista",
                    type="warning",
                )

            for idx in range(5):
                valor_nuevo = str(ids_resueltos[idx] or "")
                valor_anterior = slots[idx]
                slots[idx] = valor_nuevo
                if valor_anterior and valor_nuevo == "":
                    limpiar_matriz_relacionada_slot(idx)
                slot_selectores[idx].set_value(valor_nuevo if valor_nuevo else None)

            actualizar_indicadores_color()
            actualizar_encabezados_matriz()
            actualizar_selectores_par()
            ui.notify("Slots de Color 1..5 actualizados desde la maquina", type="positive")

        boton_guardar_global.on_click(guardar_en_global)
        boton_guardar_proyecto.on_click(guardar_en_proyecto)
        boton_guardar_slots_proyecto.on_click(guardar_slots_en_proyecto)
        boton_limpiar_slots_proyecto.on_click(limpiar_slots_proyecto)
        boton_cargar_global.on_click(cargar_global)
        boton_recargar_spoolman.on_click(recargar_spoolman)
        boton_cargar_octoprint.on_click(cargar_filamentos_desde_octoprint)
        boton_autocompletar_slots.on_click(autocompletar_slots_octoprint)
        boton_agregar_manual.on_click(agregar_manual)
        boton_borrar_manual.on_click(borrar_manual)
        boton_aplicar_par.on_click(aplicar_par)

        refrescar_ui_filamentos()
        aplicar_matriz_a_ui(matriz)
        cargar_desde_spoolman_si_hay_datos(notificar=False)

        add_interface(interface, current_page="/purga")
