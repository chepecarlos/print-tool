from __future__ import annotations

import json
from typing import Any

import requests

from printtool.MiLibrerias.FuncionesLogging import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def _extraer_valor_custom(campo: Any) -> str:
    if campo is None:
        return ""
    if isinstance(campo, dict):
        for key in ("value", "default", "text"):
            valor = campo.get(key)
            if valor is not None:
                return str(valor).strip()
        return ""

    valor = str(campo).strip()
    if valor == "":
        return ""

    # Spoolman puede almacenar extras tipo texto como JSON serializado.
    # Si viene algo como "\"10-100.12-90\"", lo decodificamos.
    if len(valor) >= 2 and valor[0] == '"' and valor[-1] == '"':
        try:
            decodificado = json.loads(valor)
            return str(decodificado).strip()
        except (json.JSONDecodeError, TypeError, ValueError):
            return valor

    return valor


def _extraer_pruga(item: dict, fallback: dict | None = None) -> str:
    candidatos: list[Any] = []

    candidatos.append(item.get("pruga"))
    candidatos.append(item.get("purga"))

    extra = item.get("extra")
    if isinstance(extra, dict):
        candidatos.append(extra.get("pruga"))
        candidatos.append(extra.get("purga"))

    custom_fields = item.get("custom_fields")
    if isinstance(custom_fields, dict):
        candidatos.append(custom_fields.get("pruga"))
        candidatos.append(custom_fields.get("purga"))

    field_values = item.get("field_values")
    if isinstance(field_values, dict):
        candidatos.append(field_values.get("pruga"))
        candidatos.append(field_values.get("purga"))

    if isinstance(field_values, list):
        for field in field_values:
            if not isinstance(field, dict):
                continue
            key = str(field.get("key") or field.get("name") or "").strip().lower()
            if key in ("pruga", "purga"):
                candidatos.append(field.get("value"))

    if fallback and isinstance(fallback, dict):
        candidatos.append(fallback.get("pruga"))
        candidatos.append(fallback.get("purga"))

    for candidato in candidatos:
        valor = _extraer_valor_custom(candidato)
        if valor:
            return valor

    return ""


def _normalizar_color_hex(color: str | None) -> str:
    if not color:
        return ""

    color = str(color).strip()
    if color == "":
        return ""

    if not color.startswith("#"):
        color = f"#{color}"

    return color.upper()


def _parse_filamento_desde_spool(item: dict) -> dict | None:
    filament = item.get("filament") or {}

    filament_id = filament.get("id")
    spool_id = item.get("id")

    if filament_id is not None:
        uid = f"filament-{filament_id}"
    elif spool_id is not None:
        uid = f"spool-{spool_id}"
    else:
        return None

    nombre = filament.get("name") or item.get("name") or f"Filamento {uid}"
    material = filament.get("material") or item.get("material") or ""

    vendor = filament.get("vendor") or item.get("vendor") or {}
    marca = vendor.get("name") if isinstance(vendor, dict) else str(vendor)

    color_hex = _normalizar_color_hex(filament.get("color_hex") or item.get("color_hex"))
    pruga = _extraer_pruga(filament, fallback=item)

    return {
        "id": uid,
        "filament_id": int(filament_id) if filament_id is not None else None,
        "nombre": str(nombre),
        "material": str(material),
        "marca": str(marca or ""),
        "color_hex": color_hex,
        "pruga": pruga,
    }


def _parse_filamento(item: dict) -> dict | None:
    filament_id = item.get("id")
    if filament_id is None:
        return None

    vendor = item.get("vendor") or {}
    marca = vendor.get("name") if isinstance(vendor, dict) else str(vendor)

    return {
        "id": f"filament-{filament_id}",
        "filament_id": int(filament_id),
        "nombre": str(item.get("name") or f"Filamento {filament_id}"),
        "material": str(item.get("material") or ""),
        "marca": str(marca or ""),
        "color_hex": _normalizar_color_hex(item.get("color_hex")),
        "pruga": _extraer_pruga(item),
    }


def actualizarPrugaFilamentoSpoolman(
    urlServidor: str,
    filament_id: int,
    valor_pruga: str,
    timeout: int = 10,
) -> bool:
    """Actualizar campo custom `pruga` en un Filament de Spoolman.

    Intenta variantes de payload para mejorar compatibilidad entre versiones.
    """

    if not urlServidor or filament_id <= 0:
        return False

    base_url = urlServidor.rstrip("/")
    url = f"{base_url}/api/v1/filament/{filament_id}"

    # En Spoolman v1, el valor de campos personalizados viaja en `extra`.
    # PATCH con `extra` reemplaza todo el objeto, por eso primero leemos y luego mergeamos.
    extra_actual: dict[str, Any] = {}
    try:
        respuesta_get = requests.get(url, timeout=timeout)
        if respuesta_get.status_code == 200:
            data_get = respuesta_get.json()
            if isinstance(data_get, dict):
                extra_data = data_get.get("extra")
                if isinstance(extra_data, dict):
                    extra_actual = dict(extra_data)
    except (requests.RequestException, ValueError) as exc:
        logger.warning(f"No se pudo leer filament {filament_id} antes de guardar pruga: {exc}")

    extra_nuevo = dict(extra_actual)
    # El endpoint de campos extra valida JSON por campo.
    # Para tipo texto, enviar string JSON serializado evita el error 400.
    extra_nuevo["pruga"] = json.dumps(str(valor_pruga), ensure_ascii=True)

    try:
        response = requests.patch(url, json={"extra": extra_nuevo}, timeout=timeout)
    except requests.RequestException as exc:
        logger.warning(f"Error actualizando pruga en Spoolman ({url}): {exc}")
        return False

    if 200 <= response.status_code < 300:
        return True

    logger.warning(
        "No fue posible actualizar pruga en Spoolman para filament "
        f"{filament_id}: HTTP {response.status_code} {response.text[:240]}"
    )
    return False


def consultarFilamentosSpoolman(urlServidor: str, timeout: int = 10) -> list[dict] | None:
    """Consultar filamentos en Spoolman y devolver lista normalizada.

    Returns:
        list[dict] | None: Lista de filamentos normalizados.
        None si no se pudo consultar el servicio.
    """

    if not urlServidor:
        return None

    base_url = urlServidor.rstrip("/")
    endpoints = [
        ("/api/v1/spool", _parse_filamento_desde_spool),
        ("/api/v1/filament", _parse_filamento),
    ]

    for endpoint, parser in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=timeout)
        except requests.RequestException as exc:
            logger.warning(f"No se pudo conectar a Spoolman en {url}: {exc}")
            continue

        if response.status_code != 200:
            logger.warning(f"Respuesta no valida de Spoolman en {url}: {response.status_code}")
            continue

        try:
            data = response.json()
        except ValueError:
            logger.warning(f"Respuesta JSON invalida desde Spoolman en {url}")
            continue

        if not isinstance(data, list):
            logger.warning(f"Formato inesperado de Spoolman en {url}: {type(data)}")
            continue

        filamentos: list[dict] = []
        ids_agregados: set[str] = set()

        for item in data:
            if not isinstance(item, dict):
                continue
            filamento = parser(item)
            if filamento is None:
                continue

            item_id = filamento.get("id")
            if not item_id or item_id in ids_agregados:
                continue

            ids_agregados.add(item_id)
            filamentos.append(filamento)

        return filamentos

    return None
