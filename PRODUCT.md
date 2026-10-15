# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

El equipo de un taller de impresión 3D (emprendimiento de ChepeCarlos): varias personas del mismo taller usan la herramienta. Roles concretos dentro del equipo (operación, ventas, administración) aún no definidos.

Situación típica: en la PC de escritorio, justo después de laminar un modelo (G-code) y antes de publicarlo o venderlo. No es una herramienta de consulta rápida junto a la impresora.

## Product Purpose

PrintTool cubre tres trabajos igual de centrales para el taller:

1. **Precio correcto** — calcular el costo real por unidad (filamento, electricidad, desgaste/inversión de la impresora, ensamblaje, extras) y fijar un precio de venta con margen.
2. **Catálogo sincronizado** — mantener cada producto como proyecto en una carpeta (`.printtool/info.md`) y sincronizar precio y stock con Dolibarr.
3. **Producción multicolor** — preparar impresiones MMU3: matriz de purga por par de colores, filamentos cargados en la máquina (OctoPrint) y su inventario (Spoolman).

Funciona cuando el número que sale (costo, precio, purga) es confiable sin recalcular a mano.

## Positioning

Lee los datos directamente del G-code/bgcode laminado (o del nombre del archivo, `nombre_{n}g_{n}pc_{n}h{n}m.gcode`) y guarda todo en archivos Markdown con frontmatter dentro de la carpeta de cada proyecto, conectado a las herramientas que el taller ya usa (Dolibarr, Spoolman, OctoPrint). No es una calculadora genérica ni un SaaS: es el flujo del taller, local y basado en archivos.

## Operating Context

- Aplicación de escritorio: NiceGUI servido localmente dentro de una ventana nativa (pywebview/GTK) en Linux. También CLI con Typer (`printtool`, `printtool productos listar`, `printtool --inventario`).
- Se abre sobre la carpeta de un proyecto; un modo inventario recorre carpetas y lista todos los proyectos.
- Configuración global en `~/.config/printtool/` (costos, purga, impresoras); datos por proyecto en `.printtool/`.
- Servicios externos: Dolibarr (API con `DOLAPIKEY`), Spoolman (campo personalizado `pruga` en filamentos), OctoPrint (`/api/settings`, plugin Spoolman).
- Hardware de referencia: Prusa con MMU3 (5 colores).

## Capabilities and Constraints

- Rutas: `/` (pestañas Info, Costos, Precio, Modelo), `/config` (asistente de configuración global), `/purga` (matriz de purga 5×5), página de edición de información del modelo.
- Terminología del taller: modelo/proyecto, SKU, gramos, horas, piezas (`pc`), copias (`cc`), purga (mm³), costos extras, ensamblado, símbolo de moneda configurable.
- Todos los datos deben seguir siendo archivos legibles y editables a mano (Markdown + YAML).
- Interfaz y documentación en español.
- Sin decidir: roles y permisos dentro del equipo; si la herramienta se distribuirá a otros talleres.

## Brand Commitments

- Nombre: **PrintTool**. Crédito "Creado por ChepeCarlos" presente en la interfaz.
- Idioma: español.

## Evidence on Hand

- README.md documenta el formato del nombre de archivo y la integración de purga con Spoolman.
- `demo/` en el repo; no hay testimonios, clientes, métricas ni capturas de marketing. No inventarlos.

## Product Principles

1. Los números mandan: cada costo y precio debe ser trazable a su origen (G-code, configuración, extras).
2. Archivos primero: el proyecto vive en su carpeta y se puede leer sin la app.
3. Integrar, no reemplazar: Dolibarr, Spoolman y OctoPrint siguen siendo la fuente de su propio dato.
4. Un flujo de preparación en escritorio: laminar → calcular → fijar precio → sincronizar, sin pasos manuales repetidos.
