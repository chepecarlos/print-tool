from dataclasses import dataclass


@dataclass
class dataGcode:
    "Información del archivo gcode"

    nombre: str = ""
    "nombre del archivo gcode"
    material: float = 0
    "Cantidad de material en gramos"
    tiempo: float = 0
    "Tiempo de impresión en horas"
    tipo: str = "pla"
    "Tipo de material"
    color: str = "no"
    "Color del material"
    cantidad: int = 1
    "Cantidad de veces que se repiten las piezas en el modelo"
    copias: int = 1
    "Cantidad de copias a imprimir"
    materialPorPieza: float = 0.0
    "Cantidad de material por pieza en gramos"
    tiempoPorPieza: float = 0.0
    "Tiempo de impresión por pieza en horas"
