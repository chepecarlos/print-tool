from __future__ import annotations

import requests

from printtool.MiLibrerias.FuncionesLogging import ConfigurarLogging

logger = ConfigurarLogging(__name__)


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

    return {
        "id": uid,
        "nombre": str(nombre),
        "material": str(material),
        "marca": str(marca or ""),
        "color_hex": color_hex,
    }


def _parse_filamento(item: dict) -> dict | None:
    filament_id = item.get("id")
    if filament_id is None:
        return None

    vendor = item.get("vendor") or {}
    marca = vendor.get("name") if isinstance(vendor, dict) else str(vendor)

    return {
        "id": f"filament-{filament_id}",
        "nombre": str(item.get("name") or f"Filamento {filament_id}"),
        "material": str(item.get("material") or ""),
        "marca": str(marca or ""),
        "color_hex": _normalizar_color_hex(item.get("color_hex")),
    }


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
