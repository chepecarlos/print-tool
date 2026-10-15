from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from nicegui import ui

from printtool.MiLibrerias import SalvarValor

if TYPE_CHECKING:
    from printtool.printtool import printtool


def _validar_positivo(tool: "printtool", value) -> str | None:
    """Obligatorio y > 0: se usa como divisor en el costo de la impresora."""
    error = tool.validar_numero_no_negativo(value)
    if error:
        return error
    return "Debe ser mayor que 0" if float(value) == 0 else None


def _validar_porcentaje_uso(tool: "printtool", value) -> str | None:
    """Porcentaje del año que trabaja la impresora: 0 < x <= 100."""
    error = _validar_positivo(tool, value)
    if error:
        return error
    return "Máximo 100 %" if float(value) > 100 else None


def _validar_margen(tool: "printtool", value) -> str | None:
    """Margen sobre el precio: con 100 % o más el cálculo divide por cero o da negativo."""
    error = tool.validar_numero_no_negativo(value)
    if error:
        return error
    return "Debe ser menor que 100 %" if float(value) >= 100 else None


def registraPaginaConfig(tool: "printtool", add_interface: Callable[[bool, str], None], interface: bool) -> None:
    """Registrar la pagina /config fuera del archivo principal."""

    @ui.page("/config")
    def pagina_configurar():
        def guardar_simbolo() -> None:
            simbolo = (input_simbolo.value or "").strip()
            if simbolo != "" and simbolo != tool.símboloMoneda:
                tool.símboloMoneda = simbolo
                SalvarValor(tool.archivoConfig, "simbolo", simbolo)
                ui.notify(f"Símbolo de moneda guardado: {simbolo}", type="positive")
                for entrada in entradas_moneda:
                    entrada.props(f"prefix={simbolo}")

        def siguiente_basico() -> None:
            guardar_simbolo()
            pasos.next()

        def salvar_configuration() -> None:
            invalidos = [entrada for entrada in entradas_numericas if not entrada.validate()]
            if invalidos:
                nombres = ", ".join(entrada.props["label"] for entrada in invalidos)
                ui.notify(f"No se guardó. Corrija: {nombres}", type="negative", multi_line=True)
                return

            guardar_simbolo()

            def _salvar(campo: str, valor) -> None:
                SalvarValor(tool.archivoConfig, campo, valor)

            tool.urlSpoolman = input_spoolman.value
            tool.urlDolibarr = input_dolibarr.value
            tool.tokenDolibarr = input_dolibarr_token.value

            tool.infoImpresora.nombre = input_nombre.value
            tool.infoImpresora.costo = input_costo_impresora.value
            tool.infoImpresora.envio = input_envio_impresora.value
            tool.infoImpresora.mantenimiento = input_mantenimiento.value
            tool.infoImpresora.vidaUtil = input_vida_util.value
            tool.infoImpresora.consumo = input_consumo.value
            tool.infoImpresora.tiempoTrabajo = input_tiempo_trabajo.value

            tool.costoHoraTrabajo = input_trabajo.value
            tool.costoElectricidad = input_kwh.value
            tool.errorFabricacion = input_merma.value

            tool.porcentajeGananciaBase = input_ganancia.value
            tool.porcentajeGananciaExtras = input_ganancia_extras.value
            tool.porcentajeGananciaEnsamblado = input_ganancia_ensamblado.value

            if input_filamento.value is not None and input_filamento.value != "":
                tool.precioFilamento = input_filamento.value
                _salvar("precio_filamento", tool.precioFilamento)

            tool.nombreFilamento = input_nombre_filamento.value or ""
            _salvar("nombre_filamento", tool.nombreFilamento)

            data_base = {
                "url_spoolman": tool.urlSpoolman,
                "url_dolibarr": tool.urlDolibarr,
                "token_dolibarr": tool.tokenDolibarr,
                "costo_hora_trabajo": tool.costoHoraTrabajo,
                "costo_electricidad": tool.costoElectricidad,
                "error_fabricacion": tool.errorFabricacion,
                "ganancia": tool.porcentajeGananciaBase,
                "ganancia_extras": tool.porcentajeGananciaExtras,
                "ganancia_ensamblado": tool.porcentajeGananciaEnsamblado,
            }

            data_impresora = {
                "nombre_impresora": tool.infoImpresora.nombre,
                "costo_impresora": tool.infoImpresora.costo,
                "envio_impresora": tool.infoImpresora.envio,
                "mantenimiento_impresora": tool.infoImpresora.mantenimiento,
                "vida_util_impresora": tool.infoImpresora.vidaUtil,
                "consumo_impresora": tool.infoImpresora.consumo,
                "tiempo_trabajo_impresora": tool.infoImpresora.tiempoTrabajo,
            }

            for campo, valor in data_base.items():
                _salvar(campo, valor)

            for campo, valor in data_impresora.items():
                _salvar(campo, valor)

            ui.notify("Configuración guardada", type="positive")

        with ui.stepper().props("vertical header-nav").classes("w-full") as pasos:
            with ui.step("Básico"):
                input_simbolo = ui.input(label="Símbolo de moneda", value=tool.símboloMoneda)
                input_nombre = ui.input(label="Nombre de la impresora", value=tool.infoImpresora.nombre)

                with ui.stepper_navigation():
                    ui.button("Siguiente", on_click=siguiente_basico)

            with ui.step("Impresora"):
                input_costo_impresora = ui.number(label="Precio de la impresora", value=tool.infoImpresora.costo, step=1, validation=tool.validar_numero_no_negativo)
                input_costo_impresora.props(f"prefix={tool.símboloMoneda}")

                input_envio_impresora = ui.number(label="Envío de la impresora", value=tool.infoImpresora.envio, validation=tool.validar_numero_no_negativo)
                input_envio_impresora.props(f"prefix={tool.símboloMoneda}")

                input_mantenimiento = ui.number(label="Mantenimiento anual", value=tool.infoImpresora.mantenimiento, validation=tool.validar_numero_no_negativo)
                input_mantenimiento.props(f"prefix={tool.símboloMoneda}")

                input_vida_util = ui.number(label="Vida útil", value=tool.infoImpresora.vidaUtil, validation=lambda v: _validar_positivo(tool, v))
                input_vida_util.props("suffix=años")

                input_tiempo_trabajo = ui.number(label="Uso de la impresora", value=tool.infoImpresora.tiempoTrabajo, validation=lambda v: _validar_porcentaje_uso(tool, v))
                input_tiempo_trabajo.props('suffix="% del año" hint="Horas al año que imprime, en %. Reparte el costo de la impresora."')

                input_consumo = ui.number(label="Consumo eléctrico", value=tool.infoImpresora.consumo, validation=tool.validar_numero_no_negativo)
                input_consumo.props("suffix=W")

                with ui.stepper_navigation():
                    ui.button("Siguiente", on_click=pasos.next)
                    ui.button("Anterior", on_click=pasos.previous).props("flat")

            with ui.step("Operación"):
                input_trabajo = ui.number(label="Costo por hora de trabajo", value=tool.costoHoraTrabajo, validation=tool.validar_numero_no_negativo)
                input_trabajo.props(f"prefix={tool.símboloMoneda}")

                input_kwh = ui.number(label="Costo del kWh", value=tool.costoElectricidad, validation=tool.validar_numero_no_negativo)
                input_kwh.props(f"prefix={tool.símboloMoneda}")

                input_merma = ui.number(label="Merma de fabricación", value=tool.errorFabricacion, validation=tool.validar_numero_no_negativo)
                input_merma.props('suffix=% hint="Filamento extra por impresiones fallidas; se suma como costo de merma."')

                with ui.stepper_navigation():
                    ui.button("Siguiente", on_click=pasos.next)
                    ui.button("Anterior", on_click=pasos.previous).props("flat")

            with ui.step("Filamento"):
                ui.label("Precio predeterminado del filamento y conexión con Spoolman.")

                input_spoolman = ui.input(label="URL de Spoolman (para la purga)", value=tool.urlSpoolman)

                input_nombre_filamento = ui.input(label="Nombre del filamento predeterminado", value=tool.nombreFilamento)

                input_filamento = ui.number(label="Precio por kg del filamento predeterminado", value=tool.precioFilamento, validation=tool.validar_numero_opcional_no_negativo)
                input_filamento.props(f"prefix={tool.símboloMoneda}")

                with ui.stepper_navigation():
                    ui.button("Siguiente", on_click=pasos.next)
                    ui.button("Anterior", on_click=pasos.previous).props("flat")

            with ui.step("Dolibarr"):
                ui.label(
                    "Con la URL y el token de Dolibarr puede traer y enviar el precio de venta de cada modelo."
                )

                input_dolibarr = ui.input(label="URL de Dolibarr", value=tool.urlDolibarr)

                input_dolibarr_token = ui.input(
                    label="Token de la API de Dolibarr",
                    value=tool.tokenDolibarr,
                    password=True,
                    password_toggle_button=True,
                )

                with ui.stepper_navigation():
                    ui.button("Siguiente", on_click=pasos.next)
                    ui.button("Anterior", on_click=pasos.previous).props("flat")

            with ui.step("Márgenes"):
                input_ganancia = ui.number(label="Margen sobre impresión", value=tool.porcentajeGananciaBase, validation=lambda v: _validar_margen(tool, v))
                input_ganancia.props('suffix=% hint="Porcentaje del precio sin IVA. Debe ser menor que 100."')
                input_ganancia_extras = ui.number(label="Margen sobre extras", value=tool.porcentajeGananciaExtras, validation=lambda v: _validar_margen(tool, v))
                input_ganancia_extras.props("suffix=%")
                input_ganancia_ensamblado = ui.number(label="Margen sobre ensamblaje", value=tool.porcentajeGananciaEnsamblado, validation=lambda v: _validar_margen(tool, v))
                input_ganancia_ensamblado.props("suffix=%")

                with ui.stepper_navigation():
                    ui.button("Anterior", on_click=pasos.previous).props("flat")

            input_impresora = {
                input_simbolo,
                input_nombre,
                input_costo_impresora,
                input_envio_impresora,
                input_mantenimiento,
                input_vida_util,
                input_tiempo_trabajo,
                input_consumo,
                input_spoolman,
                input_nombre_filamento,
                input_dolibarr,
                input_dolibarr_token,
                input_filamento,
                input_trabajo,
                input_ganancia,
                input_ganancia_extras,
                input_ganancia_ensamblado,
                input_merma,
                input_kwh,
            }

            entradas_numericas = [entrada for entrada in input_impresora if isinstance(entrada, ui.number)]
            entradas_moneda = [
                input_costo_impresora,
                input_envio_impresora,
                input_mantenimiento,
                input_trabajo,
                input_kwh,
                input_filamento,
            ]

            ancho_input: str = "w-80"
            for entrada in input_impresora:
                entrada.classes(ancho_input)

        with ui.row().classes("w-full justify-center q-mt-md"):
            ui.button("Guardar configuración", icon="save", on_click=salvar_configuration)

        add_interface(interface, current_page="/config")
