import requests
from nicegui import ui

from printtool.MiLibrerias.FuncionesLogging import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def consultarPrecioDolibarr(urlServidor: str, token: str, idProducto: str) -> float | None:
    """Consultar el precio actual desde Dolibarr.

    Args:
        urlServidor: URL base del servidor Dolibarr (ej. http://localhost/dolibarr)
        token: Clave API de Dolibarr
        idProducto: ID del producto a consultar en Dolibarr
    Returns:
        Precio del producto consultado, o None si hubo un error.
    """

    endpoint = f"{urlServidor.rstrip('/')}/api/index.php/products/{idProducto}"
    headers = {"DOLAPIKEY": token}

    try:
        response = requests.get(endpoint, headers=headers, timeout=15)
    except requests.RequestException as exc:
        logger.warning(f"Error de conexión con Dolibarr {endpoint}: {exc}")
        return None

    if response.status_code == 200:
        producto = response.json()
        tipo = str(producto.get("type", ""))
        precio = float(producto.get("price_ttc", 0) or 0)
        logger.info("Producto encontrado:")
        logger.info(f"ID: {producto.get('id')}")
        logger.info(f"Referencia: {producto.get('ref', '')}")
        logger.info(f"Nombre: {producto.get('label', '')}")
        logger.info(f"Tipo: {'Producto' if tipo == '0' else 'Servicio'}")
        logger.info(f"Precio TTC: {precio:.2f}")
        return precio

    else:
        logger.warning(f"Error en la consulta a Dolibarr: {response.status_code} - {response.text}")
        ui.notify(f"Error en la consulta a Dolibarr: {response.status_code} - {response.text}", type="error")

    return None


def actualizarPrecioDolibarr(url: str, token: str, referencia: str, precio: float):
    """Placeholder para enviar el precio actual a Dolibarr."""
    ui.notify("Pendiente: actualizar precio en Dolibarr", type="info")
