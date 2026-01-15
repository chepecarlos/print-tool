from dataclasses import dataclass


@dataclass
class dataImpresora:
    """Información de la impresora 3D"""

    nombre: str = ""
    "Nombre de la impresora"
    costo: float = 0
    "Precio de compra de la impresora"
    envio: float = 0
    "Costo de envío de la impresora"
    mantenimiento: float = 0
    "Costo de mantenimiento anual de la impresora"
    vidaUtil: float = 0
    "Cuantos años dura la impresora"
    consumo: float = 0
    "Consumo eléctrico en watts"
    tiempoTrabajo: float = 0
    "Porcentaje de horas de trabajo al año"
