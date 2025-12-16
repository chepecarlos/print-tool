from dataclasses import dataclass


@dataclass
class dataImpresora:
    nombre: str = ""
    costo: float = 0
    envio: float = 0
    mantenimiento: float = 0
    vidaUtil: float = 0
    consumo: float = 0
    tiempoTrabajo: float = 0
