"""Colores y superficies del navegador según DESIGN.md (La hoja de cálculo del taller)."""

from nicegui import ui

# Roles de Quasar + colores propios; los propios generan clases text-<nombre> / bg-<nombre>
# y se pueden usar como color=<nombre> en botones.
COLORES = {
    "primary": "#0F766E",  # teal-taller
    "positive": "#15803D",  # verde-confirmacion
    "negative": "#C10015",  # rojo-error
    "dark": "#1D1D1D",  # grafito-panel
    "dark_page": "#121212",  # grafito-pagina
    "teal_claro": "#4DB6AC",
    "verde_precio": "#4ADE80",
    "ambar_costo": "#FACC15",
    "rojo_texto": "#F87171",
}

CSS = """
/* Teal sobre grafito: como texto el teal del taller no llega a 4.5:1, se usa teal claro. */
.body--dark .text-primary { color: #4DB6AC !important; }

/* Cifras tabulares en toda la app: los números se comparan por columnas. */
body { font-variant-numeric: tabular-nums; caret-color: #4DB6AC; }

::selection { background: rgba(77, 182, 172, 0.35); color: #FFFFFF; }

.q-btn:focus-visible, .q-tab:focus-visible, .q-item:focus-visible {
  outline: 2px solid #4DB6AC;
  outline-offset: 2px;
}

* { scrollbar-width: thin; scrollbar-color: #4A4A4A #121212; }
"""

_cssRegistrado = False


def aplicarTema() -> None:
    """Aplicar los colores en la página actual; el CSS compartido se registra una sola vez."""
    global _cssRegistrado
    if not _cssRegistrado:
        ui.add_css(CSS, shared=True)
        _cssRegistrado = True
    ui.colors(**COLORES)
