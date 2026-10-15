from __future__ import annotations

from typing import Any

import requests

from printtool.MiLibrerias.FuncionesLogging import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def _token_mascarado(token: str) -> str:
    texto = str(token or "").strip()
    if texto == "":
        return "(vacío)"
    if len(texto) <= 6:
        return "*" * len(texto)
    return f"{texto[:3]}...{texto[-3:]}"


def _texto_respuesta_seguro(response: requests.Response, limite: int = 260) -> str:
    try:
        texto = str(response.text or "").replace("\n", " ").strip()
    except Exception:
        return ""
    if len(texto) <= limite:
        return texto
    return f"{texto[:limite]}..."


def _valor_path(data: Any, path: str) -> Any:
    """Obtiene valor por ruta tipo a.b.c sobre dict/list de forma segura."""
    actual = data
    for segmento in str(path or "").split("."):
        clave = segmento.strip()
        if clave == "":
            continue

        if isinstance(actual, dict):
            if clave not in actual:
                return None
            actual = actual[clave]
            continue

        if isinstance(actual, list) and clave.isdigit():
            idx = int(clave)
            if idx < 0 or idx >= len(actual):
                return None
            actual = actual[idx]
            continue

        return None

    return actual


def _normalizar_hex(valor: Any) -> str:
    color = str(valor or "").strip()
    if color == "":
        return ""
    if not color.startswith("#"):
        color = f"#{color}"
    return color.upper()


def _normalizar_id(valor: Any) -> str:
    texto = str(valor or "").strip()
    if texto == "":
        return ""
    if texto.startswith("filament-") or texto.startswith("spool-"):
        return texto
    if texto.isdigit():
        return f"filament-{texto}"
    return texto


def _filamento_desde_item(item: dict, fallback_idx: int) -> dict | None:
    filament = item.get("filament") if isinstance(item.get("filament"), dict) else {}

    filament_id = filament.get("id") or item.get("filament_id") or item.get("id")
    spool_id = item.get("id") if isinstance(item.get("id"), (int, str)) else None

    uid = _normalizar_id(filament_id)
    if uid == "":
        if spool_id is not None and str(spool_id).strip() != "":
            uid = f"spool-{spool_id}"
        else:
            uid = f"octo-{fallback_idx}"

    vendor = filament.get("vendor") if isinstance(filament.get("vendor"), dict) else {}
    marca = vendor.get("name") or item.get("brand") or item.get("vendor") or ""

    nombre = (
        filament.get("name") or item.get("name") or item.get("display_name") or item.get("label") or f"Filamento {uid}"
    )

    material = filament.get("material") or item.get("material") or ""
    color_hex = _normalizar_hex(filament.get("color_hex") or item.get("color_hex") or item.get("color"))

    try:
        filament_id_num = int(str(uid).split("-")[-1])
    except (TypeError, ValueError):
        filament_id_num = None

    return {
        "id": uid,
        "filament_id": filament_id_num,
        "nombre": str(nombre),
        "material": str(material),
        "marca": str(marca),
        "color_hex": color_hex,
        "pruga": "",
        "pruga_negativa": "",
    }


def _config_spoolman_desde_payload(payload: dict) -> dict:
    plugins = payload.get("plugins") if isinstance(payload.get("plugins"), dict) else {}

    for key in ("Spoolman", "spoolman"):
        valor = plugins.get(key)
        if isinstance(valor, dict):
            return valor

    # Fallback cuando endpoint ya devuelve la seccion del plugin directamente.
    if isinstance(payload.get("selectedSpoolIds"), dict) and payload.get("spoolmanUrl"):
        return payload

    return {}


def _filamento_desde_spool(spool: dict, fallback_idx: int) -> dict | None:
    if not isinstance(spool, dict):
        return None

    filament = spool.get("filament") if isinstance(spool.get("filament"), dict) else {}
    vendor = filament.get("vendor") if isinstance(filament.get("vendor"), dict) else {}

    spool_id = spool.get("id")
    filament_id = filament.get("id")

    uid = _normalizar_id(filament_id)
    if uid == "":
        uid = _normalizar_id(spool_id)
    if uid == "":
        uid = f"spool-{fallback_idx}"

    try:
        filament_id_num = int(str(uid).split("-")[-1])
    except (TypeError, ValueError):
        filament_id_num = None

    return {
        "id": uid,
        "filament_id": filament_id_num,
        "nombre": str(filament.get("name") or spool.get("name") or f"Filamento {uid}"),
        "material": str(filament.get("material") or spool.get("material") or ""),
        "marca": str(vendor.get("name") or ""),
        "color_hex": _normalizar_hex(filament.get("color_hex") or spool.get("color_hex") or ""),
        "pruga": "",
        "pruga_negativa": "",
    }


def _extraer_desde_settings_spoolman(
    payload_settings: dict,
    timeout: int,
) -> tuple[list[dict], list[str], str | None]:
    config = _config_spoolman_desde_payload(payload_settings)
    if not config:
        logger.debug("No se encontro config del plugin Spoolman en /api/settings")
        return [], ["", "", "", "", ""], None

    logger.debug(f"Plugin Spoolman detectado | keys={list(config.keys())}")

    spoolman_url = str(config.get("spoolmanUrl") or "").strip().rstrip("/")
    if spoolman_url == "":
        logger.debug("Spoolman plugin detectado, pero sin spoolmanUrl")
        return [], ["", "", "", "", ""], None

    logger.debug(f"Spoolman URL configurada en OctoPrint: {spoolman_url}")

    selected_spool_ids = config.get("selectedSpoolIds")
    if not isinstance(selected_spool_ids, dict):
        logger.debug(
            f"selectedSpoolIds no es dict | tipo={type(selected_spool_ids)} valor={selected_spool_ids!r}"
        )
        return [], ["", "", "", "", ""], spoolman_url

    logger.debug(f"selectedSpoolIds recibido: {selected_spool_ids}")

    api_key = None
    if bool(config.get("isSpoolmanApiKeyEnabled")):
        api_key = str(config.get("spoolmanApiKey") or "").strip() or None
    api_key_header = str(config.get("spoolmanApiKeyHeader") or "").strip() or None

    headers_spoolman = {"Accept": "application/json"}
    if api_key and api_key_header:
        headers_spoolman[api_key_header] = api_key
        logger.debug(f"Spoolman API key activa | header={api_key_header} key={_token_mascarado(api_key)}")

    filamentos: list[dict] = []
    ids: set[str] = set()
    slots = ["", "", "", "", ""]

    for extrusor, spool_data in sorted(selected_spool_ids.items(), key=lambda item: str(item[0])):
        if not isinstance(spool_data, dict):
            logger.debug(f"  extrusor={extrusor}: spool_data no es dict ({spool_data!r}), saltando")
            continue

        spool_id = str(spool_data.get("spoolId") or "").strip()
        if spool_id == "":
            logger.debug(f"  extrusor={extrusor}: sin spoolId en {spool_data!r}, saltando")
            continue

        logger.debug(f"  extrusor={extrusor} → spool_id={spool_id}")

        url_spool = f"{spoolman_url}/api/v1/spool/{spool_id}"
        try:
            response_spool = requests.get(url_spool, headers=headers_spoolman, timeout=timeout)
        except requests.RequestException as exc:
            logger.warning(f"No se pudo consultar spool {spool_id} en {url_spool}: {exc}")
            continue

        logger.debug(f"  spool {spool_id} → HTTP {response_spool.status_code}")

        if response_spool.status_code != 200:
            logger.warning(
                "Spoolman devolvio respuesta no valida para spool | "
                f"status={response_spool.status_code} url={url_spool} "
                f"body='{_texto_respuesta_seguro(response_spool)}'"
            )
            continue

        try:
            spool_payload = response_spool.json()
        except ValueError:
            logger.warning(f"JSON invalido en respuesta de spool {spool_id} ({url_spool})")
            continue

        logger.debug(
            f"  spool {spool_id} payload | keys={list(spool_payload.keys()) if isinstance(spool_payload, dict) else type(spool_payload)}"
        )

        filamento = _filamento_desde_spool(spool_payload, len(filamentos) + 1)
        if filamento is None:
            logger.debug(f"  spool {spool_id}: _filamento_desde_spool retorno None")
            continue

        logger.debug(
            f"  spool {spool_id} → filamento | id={filamento.get('id')} nombre={filamento.get('nombre')} "
            f"material={filamento.get('material')} color={filamento.get('color_hex')}"
        )

        filamento_id = str(filamento.get("id") or "").strip()
        if filamento_id and filamento_id not in ids:
            ids.add(filamento_id)
            filamentos.append(filamento)

        try:
            idx = int(str(extrusor).strip())
        except (TypeError, ValueError):
            logger.debug(f"  extrusor={extrusor!r} no es entero, no se puede asignar a slot")
            continue
        if 0 <= idx < 5:
            slots[idx] = filamento_id
            logger.debug(f"  slot[{idx}] = {filamento_id}")

    logger.debug(f"Spoolman via OctoPrint | filamentos={len(filamentos)} slots={slots}")
    return filamentos, slots, spoolman_url


def _extraer_lista_filamentos(payload: dict, maquina: dict) -> list[dict]:
    candidatos_paths = []

    path_config = str(maquina.get("filamentos_path") or "").strip()
    if path_config:
        candidatos_paths.append(path_config)

    candidatos_paths.extend(
        [
            "plugins.spoolman.spools",
            "plugins.spoolman.filaments",
            "plugins.Spoolman.spools",
            "plugins.Spoolman.filaments",
            "spools",
            "filaments",
        ]
    )

    logger.debug(f"Buscando filamentos en rutas: {candidatos_paths}")

    for ruta in candidatos_paths:
        valor = _valor_path(payload, ruta)
        if not isinstance(valor, list):
            logger.debug(f"  ruta '{ruta}' -> {type(valor).__name__} (no es lista, saltando)")
            continue

        logger.debug(f"  ruta '{ruta}' -> lista con {len(valor)} elementos")

        resultado: list[dict] = []
        ids: set[str] = set()
        for idx, item in enumerate(valor):
            if not isinstance(item, dict):
                continue
            filamento = _filamento_desde_item(item, idx + 1)
            if filamento is None:
                continue
            item_id = str(filamento.get("id") or "").strip()
            if item_id == "" or item_id in ids:
                continue
            ids.add(item_id)
            resultado.append(filamento)
            logger.debug(
                f"    [{idx}] id={filamento.get('id')} nombre={filamento.get('nombre')} "
                f"material={filamento.get('material')} color={filamento.get('color_hex')}"
            )

        if len(resultado) > 0:
            logger.debug(f"  filamentos validos extraidos de '{ruta}': {len(resultado)}")
            return resultado

        logger.debug(f"  ruta '{ruta}' tenia la lista pero sin filamentos validos")

    logger.debug(
        f"No se encontraron filamentos en ninguna ruta | keys_payload={list(payload.keys())}"
    )
    return []


def _extraer_slots(payload: dict, maquina: dict) -> list[str]:
    path_slots = str(maquina.get("slots_path") or "").strip()
    candidatos_paths = []
    if path_slots:
        candidatos_paths.append(path_slots)

    candidatos_paths.extend(
        [
            "plugins.spoolman.slots",
            "plugins.spoolman.tools",
            "plugins.Spoolman.slots",
            "plugins.Spoolman.tools",
            "slots",
            "tools",
        ]
    )

    for ruta in candidatos_paths:
        valor = _valor_path(payload, ruta)

        if isinstance(valor, list):
            slots = [""] * 5
            for idx in range(min(len(valor), 5)):
                item = valor[idx]
                if isinstance(item, dict):
                    candidato = item.get("filament_id") or item.get("id") or item.get("spool_id")
                else:
                    candidato = item
                slots[idx] = _normalizar_id(candidato)
            if any(slots):
                logger.debug(f"OctoPrint slots detectados en ruta list '{ruta}': {slots}")
                return slots

        if isinstance(valor, dict):
            slots = [""] * 5
            for idx in range(5):
                key = f"tool{idx}"
                item = valor.get(key)
                if isinstance(item, dict):
                    candidato = item.get("filament_id") or item.get("id") or item.get("spool_id")
                else:
                    candidato = item
                slots[idx] = _normalizar_id(candidato)
            if any(slots):
                logger.debug(f"OctoPrint slots detectados en ruta dict '{ruta}': {slots}")
                return slots

    return [""] * 5


def consultarFilamentosOctoprint(maquina: dict, timeout: int = 10) -> dict[str, Any]:
    """Consulta OctoPrint y normaliza filamentos/slots de forma tolerante."""

    url_base = str(maquina.get("url") or "").strip().rstrip("/")
    token = str(maquina.get("token") or "").strip()
    endpoint = str(maquina.get("endpoint_filamentos") or "/api/settings").strip()

    if url_base == "":
        return {"ok": False, "error": "La máquina seleccionada no tiene URL. Agréguela en data/impresoras.md."}

    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"

    headers = {"Accept": "application/json"}
    if token:
        headers["X-Api-Key"] = token
        headers["Authorization"] = f"Bearer {token}"

    url = f"{url_base}{endpoint}"

    logger.debug(
        "Consultando OctoPrint | "
        f"maquina={maquina.get('id', 'desconocida')} "
        f"url={url} timeout={timeout}s token={_token_mascarado(token)}"
    )

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        logger.warning(f"No se pudo consultar OctoPrint en {url}: {exc}")
        return {"ok": False, "error": f"No se pudo conectar con OctoPrint en {url}. Revise que la máquina esté encendida."}

    logger.debug(
        "Respuesta OctoPrint | "
        f"status={response.status_code} content-type={response.headers.get('Content-Type', '')} "
        f"len={len(response.text or '')}"
    )

    if response.status_code != 200:
        body_resumen = _texto_respuesta_seguro(response)
        if response.status_code in (401, 403):
            logger.warning(
                "OctoPrint rechazo autenticacion/autorizacion | "
                f"status={response.status_code} url={url} token={_token_mascarado(token)} "
                f"body='{body_resumen}'"
            )
            logger.warning(
                "Sugerencia: verificar API Key de OctoPrint, permisos de usuario y endpoint configurado "
                f"(actual: {endpoint})."
            )
            logger.warning("Tip: /api/settings suele requerir token de usuario con permisos de admin.")
        else:
            logger.warning(
                "OctoPrint respuesta no valida | " f"status={response.status_code} url={url} body='{body_resumen}'"
            )
        return {
            "ok": False,
            "error": (
                "OctoPrint rechazó el token: /api/settings necesita un token de administrador."
                if response.status_code in (401, 403)
                else f"OctoPrint respondió con error {response.status_code}. Inténtelo de nuevo."
            ),
        }

    try:
        payload = response.json()
    except ValueError:
        logger.warning("OctoPrint devolvio JSON invalido | " f"url={url} body='{_texto_respuesta_seguro(response)}'")
        return {"ok": False, "error": "OctoPrint devolvió una respuesta que no se pudo leer."}

    if not isinstance(payload, dict):
        logger.warning(f"Respuesta inesperada de OctoPrint | tipo={type(payload)} url={url}")
        return {"ok": False, "error": "OctoPrint devolvió una respuesta inesperada."}

    filamentos = _extraer_lista_filamentos(payload, maquina)
    slots = _extraer_slots(payload, maquina)

    # Estrategia basada en el flujo validado en demo/main.py:
    # 1) leer plugins.Spoolman en /api/settings
    # 2) obtener selectedSpoolIds por extrusor
    # 3) consultar spoolmanUrl/api/v1/spool/{id}
    filamentos_cfg, slots_cfg, spoolman_url_cfg = _extraer_desde_settings_spoolman(payload, timeout)
    if len(filamentos_cfg) > 0:
        filamentos = filamentos_cfg
        slots = slots_cfg
        logger.debug(
            "Filamentos cargados desde configuracion Spoolman en OctoPrint | "
            f"spoolman_url={spoolman_url_cfg} filamentos={len(filamentos)} slots={slots}"
        )

    logger.debug(
        "OctoPrint parseado | " f"filamentos={len(filamentos)} slots_detectados={len([x for x in slots if x])}"
    )

    if len(filamentos) == 0:
        logger.warning(
            "No se detectaron filamentos en OctoPrint con las rutas configuradas. "
            f"Revisar filamentos_path en impresoras.md. Endpoint usado: {endpoint}"
        )

    return {
        "ok": True,
        "filamentos": filamentos,
        "slots": slots,
        "url": url,
    }
