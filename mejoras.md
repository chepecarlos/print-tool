# Mejoras (auditoría de sobre-ingeniería)

Ordenadas por tamaño del recorte. Estimado: -6.600 líneas (~700 de código, ~5.900 de docs generadas), -4 dependencias y el paquete apt `python3-tk`.

- [ ] **Docs generadas en git** — `docs/` es salida de pdoc (~5.900 líneas). Regenerar con `make docs` y añadir `docs/` a `.gitignore` (salvo que GitHub Pages lo sirva desde ahí).
- [ ] **TokenSearchSelect** — componente propio (py + js + css) más `_opcion_filamento`, `_tokens_busqueda` y `_alias_busqueda_material` (búsqueda por typos "ptge", "tup"). Reemplazar por `ui.select(opciones, with_input=True)` usando `_texto_filamento()` como etiqueta (ya contiene id, nombre, material y marca). `utilidades/token_search_select.*`, `paginaPurga.py:204-272`
- [ ] **miOctoprint: rutas adivinadas** — borrar `_valor_path`, `_filamento_desde_item`, `_extraer_lista_filamentos`, `_extraer_slots`, las 12 rutas candidatas y la config `endpoint_filamentos`/`filamentos_path`/`slots_path`. Dejar solo `_extraer_desde_settings_spoolman` (el flujo validado con `plugins.Spoolman.selectedSpoolIds`). Enviar solo `X-Api-Key`, no también `Bearer`. `utilidades/miOctoprint.py:31-114,273-378`
- [ ] **Selector de carpeta con tkinter** — usar el diálogo nativo de pywebview: `await app.native.main_window.create_file_dialog(webview.FOLDER_DIALOG)`. Elimina `extrasGui.py` y el paquete apt `python3-tk`. `printtool.py` (`buscarFolder`)
- [ ] **miSpoolman: `_extraer_campo_extra`** — revisa `extra`, `custom_fields`, `field_values` (dict y lista) y un fallback, más los alias `purga`/`pruga`. Spoolman v1 solo usa `extra`: `_extraer_valor_custom(item.get("extra", {}).get(campo))`. `utilidades/miSpoolman.py:39-85`
- [ ] **`_normalizar_maquinas`** — adivina 6 nombres de clave para el token (incluida la errata `'token"'`) y recorre las claves. Fijar el esquema `{id, nombre, url, token}` y corregir `impresoras.md` una vez. `paginaPurga.py:95-149`
- [ ] **Migración legacy** — `info.md`/`extras.md` en la raíz (`configurarData`, `esProyecto`) y el separador "." en `_parsear_pruga_compacto`. Migrar una vez (script o `mv`) y borrar el código.
- [ ] **Código muerto** — `validar_numero`, `seleccionarFilamento`, el bloque comentado de `filamentosDisponibles`, `inventario.agregar_proyecto`, `_linea_slot`, `self.multiMaterial` (se asigna, nunca se lee), `dataGcode.materialPorPieza/tiempoPorPieza/tipo/color` y las columnas `tipo`/`color` de la tabla (siempre vacías).
- [ ] **Validadores duplicados** — 4 `validar_*` casi idénticos más `_validar_numero_no_negativo_opcional` (copia de `validar_numero_opcional_no_negativo`). Unificar en `validar(value, requerido=True, entero=False)`. `printtool.py`, `paginaPurga.py:430`
- [ ] **`TokenSearchSelect.__init__`** — solo reenvía argumentos a `Select` (27 líneas). Si se conserva el componente, borrar el `__init__`. `token_search_select.py:14-39`
- [ ] **Stdlib en `cargarDataGcode`/`calcularDataArchivos`** — `os.path.splitext(archivo)` en lugar del bucle `for subfijo in sufijoArchivo`; `open(..., errors="ignore")` en lugar de `codecs.open`.
- [ ] **Hex duplicado** — `_normalizar_color_hex` (miSpoolman) duplica `_normalizar_hex` (miOctoprint). Dejar uno.
- [ ] **Guardado en páginas** — en `paginaConfig.py`, juntar los dos dicts y el wrapper `_salvar` en un dict con un solo `for`. En `paginaActualizar.py`, usar `x or ""` en lugar de `x if x is not None else ""`, y crear siempre `textoIdProducto` para quitar el `getattr`/`hasattr`.
- [ ] **Restos varios** — `show()` notifica "You chose None" (usar `on_click=dialog.open`). Los atributos `tabInfo`/`tabCosto`/`tabPrecio`/`tabData` pueden ser variables locales. La clase declara atributos que `__init__` vuelve a declarar.
- [ ] **Dependencias** — quitar `rich` (ya lo trae typer) e `importlib-resources` (usar `importlib.resources.files`, stdlib desde 3.9, en el submódulo). Dejar `pywebview` en una sola línea (`pywebview[gtk]`). `python-telegram-bot` y `paho-mqtt` solo hacen falta porque `MiLibrerias/__init__.py` hace `import *` de módulos que no se usan: quitarlos de ahí.

## Bugs vistos (fuera de la auditoría)

- [ ] `pyyaml` se usa pero no está en `requirements.txt`.
- [ ] `inventario.py:69`: el `:format` muestra el texto literal `{self.símboloMoneda}`.
- [ ] `paginaConfig.py:21`: al `ui.notify` le falta la `f` del f-string.
