from dataclasses import dataclass


@dataclass
class dataGcode:
    material: int = 0
    tiempo: int = 0
    tipo: str = "pla"
    color: str = "no"
