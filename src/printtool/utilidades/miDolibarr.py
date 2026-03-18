import requests
import json
from nicegui import ui

from printtool.MiLibrerias.FuncionesLogging import ConfigurarLogging

logger = ConfigurarLogging(__name__)


def consultarPrecioDolibarr(urlServidor: str, token: str, idProducto: str) -> float | None:
    """Consultar el precio actual desde Dolibarr.

    Args:
        urlServidor(str): URL base del servidor Dolibarr (ej. http://localhost/dolibarr)
        token(str): Clave API de Dolibarr
        idProducto(str): ID del producto a consultar en Dolibarr
    Returns:
        float | None: Precio del producto consultado, o None si hubo un error.
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


def actualizarPrecioDolibarr(urlServidor: str, token: str, idProducto: str, precio: float) -> bool:
    """Actualizar el precio de un producto en Dolibarr.

    Args:
        urlServidor(str): URL base del servidor Dolibarr (ej. http://localhost/dolibarr)
        token(str): Clave API de Dolibarr
        idProducto(str): ID del producto a actualizar en Dolibarr
        precio(float): Nuevo precio a establecer en Dolibarr
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario.
    """

    endpoint = f"{urlServidor.rstrip('/')}/api/index.php/products/{idProducto}"
    headers = {"DOLAPIKEY": token, "Content-Type": "application/json"}
    data = {"price": precio, "price_ttc": precio}

    response = requests.put(endpoint, headers=headers, json=data)

    if response.status_code == 200:
        logger.info(f"Precio actualizado correctamente en Dolibarr: {precio:.2f}")
        ui.notify(f"Precio actualizado correctamente en Dolibarr: {precio:.2f}", type="success")
        return True
    else:
        logger.warning(f"Error al actualizar el precio en Dolibarr: {response.status_code} - {response.text}")
        ui.notify(f"Error al actualizar el precio en Dolibarr: {response.status_code} - {response.text}", type="error")

    return False
