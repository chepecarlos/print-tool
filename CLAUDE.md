# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos

```bash
# Instalar en modo desarrollo
pip install -e .

# Instalar con dependencias de test
pip install -e ".[dev]"

# Ejecutar
printtool

# Ejecutar tests
pytest

# Formatear código
black src/
```

## Arquitectura

Aplicación de escritorio nativa construida con **NiceGUI** (`ui.run(native=True)`). Toda la interfaz corre como servidor web local embebido en una ventana nativa (pywebview/GTK).

### Flujo principal

`main.py` → `printtool.iniciarSistema()` → `printtool.cargarGui()` → `printtool.iniciarGui()`

La clase `printtool` en `printtool.py` es el estado central: contiene tanto los datos del modelo (gramos, horas, costos) como los widgets NiceGUI. Las páginas adicionales se registran como rutas NiceGUI independientes durante `cargarGui()`.

### Persistencia de datos

`MiLibrerias/FuncionesArchivos.py` es la capa de acceso a datos. Usa archivos `.md` con frontmatter YAML como base de datos:

- **`data/costos.md`** (en `~/.config/printtool/`) — configuración global: costos de impresora, electricidad, URLs de servicios externos.
- **`.printtool/info.md`** (en el directorio del proyecto) — datos del modelo activo: nombre, SKU, gramos, horas, precio de venta.
- **`.printtool/extras.md`** (en el directorio del proyecto) — costos extras del modelo (tornillos, pegamento, etc.).
- **`data/purga_colores.md`** (en `~/.config/printtool/`) — matriz de purga MMU3 global.
- **`data/impresoras.md`** (en `~/.config/printtool/`) — lista de máquinas OctoPrint.

`ObtenerArchivo(archivo, EnConfig=True)` lee desde `~/.config/printtool/` cuando `EnConfig=True`, y desde ruta absoluta/relativa cuando es `False`.

### Páginas (rutas NiceGUI)

| Ruta | Archivo | Descripción |
|------|---------|-------------|
| `/` | `printtool.py` | Tabs: Info, Costos, Precio, Modelo |
| `/config` | `paginaConfig.py` | Configuración global (impresora, filamento, URLs) |
| `/purga` | `paginaPurga.py` | Calculadora de purga MMU3 con matriz 5×5 |

### Integraciones externas

- **Spoolman** (`utilidades/miSpoolman.py`) — consulta filamentos via API REST. El campo `pruga` en cada filamento almacena la matriz de purga en formato compacto: `"destino_id-mm3.destino_id-mm3"`.
- **Dolibarr** (`utilidades/miDolibarr.py`) — actualiza precio y stock de productos via API REST con `DOLAPIKEY`.
- **OctoPrint** (`utilidades/miOctoprint.py`) — obtiene filamentos cargados en la MMU desde el endpoint `/api/settings`.

### Lectura de G-code

`printtool.cargarDataGcode()` extrae material (gramos) y tiempo de impresión del texto del archivo `.gcode`/`.bgcode` usando regex. Como fallback, también parsea el nombre del archivo con el formato: `nombre_{n}g_{n}pc_{n}h{n}m.gcode`.

### Submodulo MiLibrerias

`src/printtool/MiLibrerias/` es un submódulo git con utilidades reutilizables (logging con colorlog, archivos YAML/JSON, MQTT, Telegram). Actualizar con `git submodule update --remote`.
