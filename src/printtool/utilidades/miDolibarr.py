import requests

from printtool.MiLibrerias.FuncionesLogging import ConfigurarLogging

logger = ConfigurarLogging(__name__)

TIMEOUT_DOLIBARR = 15


def _error_http(response: requests.Response, idProducto) -> str:
    """Traducir un código HTTP de Dolibarr a un mensaje que diga qué revisar."""
    if response.status_code in (401, 403):
        return "Dolibarr rechazó el token. Revise el token en Configurar."
    if response.status_code == 404:
        return f"El producto {idProducto} no existe en Dolibarr. Revise el ID en la pestaña Modelo."
    return f"Dolibarr respondió {response.status_code}. Intente de nuevo o revise el servidor."


def consultarPrecioDolibarr(urlServidor: str, token: str, idProducto) -> tuple[float | None, str | None]:
    """Consultar el precio actual desde Dolibarr.

    No toca la interfaz: se puede ejecutar fuera del event loop (run.io_bound).

    Returns:
        tuple: (precio, None) si salió bien, o (None, mensaje de error) si falló.
    """

    endpoint = f"{urlServidor.rstrip('/')}/api/index.php/products/{idProducto}"
    headers = {"DOLAPIKEY": token}

    try:
        response = requests.get(endpoint, headers=headers, timeout=TIMEOUT_DOLIBARR)
    except requests.Timeout:
        return None, f"Dolibarr no respondió en {TIMEOUT_DOLIBARR} s."
    except requests.RequestException as exc:
        logger.warning(f"Error de conexión con Dolibarr {endpoint}: {exc}")
        return None, "No se pudo conectar con Dolibarr. Revise la URL en Configurar."

    if response.status_code != 200:
        logger.warning(f"Error en la consulta a Dolibarr: {response.status_code} - {response.text}")
        return None, _error_http(response, idProducto)

    try:
        producto = response.json()
        precio = float(producto.get("price_ttc", 0) or 0)
    except (ValueError, AttributeError):
        logger.warning(f"Respuesta inesperada de Dolibarr: {response.text[:200]}")
        return None, "Dolibarr devolvió una respuesta que no es un producto. Revise la URL en Configurar."

    logger.info(f"Producto {producto.get('id')} {producto.get('ref', '')}: precio TTC {precio:.2f}")
    return precio, None


def actualizarPrecioDolibarr(urlServidor: str, token: str, idProducto, precio: float) -> str | None:
    """Actualizar el precio de un producto en Dolibarr.

    No toca la interfaz: se puede ejecutar fuera del event loop (run.io_bound).

    Returns:
        str | None: None si se actualizó, o el mensaje de error.
    """

    endpoint = f"{urlServidor.rstrip('/')}/api/index.php/products/{idProducto}"
    headers = {"DOLAPIKEY": token, "Content-Type": "application/json"}
    data = {"price": precio, "price_ttc": precio}

    try:
        response = requests.put(endpoint, headers=headers, json=data, timeout=TIMEOUT_DOLIBARR)
    except requests.Timeout:
        return f"Dolibarr no respondió en {TIMEOUT_DOLIBARR} s. El precio no se actualizó."
    except requests.RequestException as exc:
        logger.warning(f"Error de conexión con Dolibarr {endpoint}: {exc}")
        return "No se pudo conectar con Dolibarr. El precio no se actualizó."

    if response.status_code != 200:
        logger.warning(f"Error al actualizar el precio en Dolibarr: {response.status_code} - {response.text}")
        return _error_http(response, idProducto)

    logger.info(f"Precio actualizado correctamente en Dolibarr: {precio:.2f}")
    return None
