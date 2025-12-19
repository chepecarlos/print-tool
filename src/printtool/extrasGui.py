import tkinter as tk
from tkinter import filedialog


def seleccionarFolderThinter() -> str:
    """Selecciona un folder

    Return:
        str: Ruta seleccionada
    """
    # Inicializar Tkinter sin mostrar la ventana principal
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)  # Forzar que aparezca encima

    # Abrir el selector
    ruta = filedialog.askdirectory(title="Selecciona una Carpeta")

    root.destroy()  # Limpiar
    return ruta
