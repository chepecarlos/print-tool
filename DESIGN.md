---
name: PrintTool
description: Hoja de cálculo del taller de impresión 3D — costo, precio y purga trazables, en oscuro.
colors:
  teal-taller: "#0F766E"
  teal-claro: "#4DB6AC"
  grafito-pagina: "#121212"
  grafito-panel: "#1D1D1D"
  tinta: "#FFFFFF"
  tinta-secundaria: "#9E9E9E"
  linea: "rgba(255, 255, 255, 0.28)"
  verde-precio: "#4ADE80"
  verde-confirmacion: "#15803D"
  ambar-costo: "#FACC15"
  rojo-error: "#C10015"
  rojo-texto: "#F87171"
  muestra-vacia: "#222222"
  borde-muestra: "#6B7280"
typography:
  headline:
    fontFamily: "Roboto, -apple-system, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 400
    lineHeight: "2rem"
  title:
    fontFamily: "Roboto, -apple-system, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 500
    lineHeight: "2rem"
    letterSpacing: "0.0125em"
  subtitle:
    fontFamily: "Roboto, -apple-system, Helvetica Neue, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: "1.75rem"
  body:
    fontFamily: "Roboto, -apple-system, Helvetica Neue, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  number:
    fontFamily: "Roboto, -apple-system, Helvetica Neue, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "\"tnum\" 1"
  total:
    fontFamily: "Roboto, -apple-system, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 700
    lineHeight: "1.75rem"
    fontFeature: "\"tnum\" 1"
  label:
    fontFamily: "Roboto, -apple-system, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: "1.25rem"
rounded:
  sm: "4px"
spacing:
  sm: "8px"
  md: "12px"
  lg: "16px"
components:
  button-primary:
    backgroundColor: "{colors.teal-taller}"
    textColor: "{colors.tinta}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "4px 16px"
    height: "36px"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.teal-claro}"
    rounded: "{rounded.sm}"
    padding: "4px 16px"
    height: "36px"
  button-destructivo:
    backgroundColor: "transparent"
    textColor: "{colors.rojo-texto}"
    rounded: "{rounded.sm}"
    padding: "4px 16px"
    height: "36px"
  input-campo:
    backgroundColor: "transparent"
    textColor: "{colors.tinta}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "0 12px"
    height: "40px"
  barra-superior:
    backgroundColor: "{colors.teal-taller}"
    textColor: "{colors.tinta}"
    typography: "{typography.title}"
    height: "48px"
  panel:
    backgroundColor: "{colors.grafito-panel}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.sm}"
    padding: "{spacing.lg}"
  fila-total:
    textColor: "{colors.tinta}"
    typography: "{typography.total}"
  muestra-color:
    backgroundColor: "{colors.muestra-vacia}"
    rounded: "{rounded.sm}"
    size: "32px"
---

# Design System: PrintTool

## Overview

**Creative North Star: "La hoja de cálculo del taller"**

PrintTool es la planilla donde el taller cuadra cada modelo antes de venderlo: filas de conceptos, columnas de valores y un total al pie que se puede rastrear hasta su origen (G-code, configuración, extras). La interfaz se comporta como esa hoja: etiqueta a la izquierda, cifra alineada a la derecha, una línea antes del total. El valor visual está en que los números se lean y se comparen, no en la decoración.

El mundo es oscuro y plano: una página grafito, paneles un tono más claros y una sola voz de color, el teal del taller, en la barra superior, en la acción principal y en el foco. El resto del color tiene significado: verde para el precio y lo confirmado, ámbar para el costo y lo que pide atención, rojo para el error y lo que borra. Densidad media-alta, pensada para una PC de escritorio justo después de laminar, con la ventana nativa de 1024×786 como lienzo de referencia.

Se apoya en Quasar/NiceGUI (Roboto, iconos Material) y no lo pelea: el sistema define tokens y las reglas para usarlos, no un framework visual propio.

**Key Characteristics:**
- Filas etiqueta → valor, cifras tabulares alineadas a la derecha, totales separados por una línea.
- Un solo color de marca (teal) para la estructura y la acción principal.
- Color de acento solo con significado (precio, costo, error); nunca decorativo.
- Profundidad por capas tonales, sin sombras en reposo.
- Controles compactos: inputs con borde, botones sólidos solo para la acción principal.

## Colors

Una paleta grafito con una voz teal y tres colores semánticos; todo lo demás es tinta blanca o gris.

### Primary
- **Teal del taller** (`teal-taller`): barra superior, pie, botón de la acción principal de cada sección, indicador de pestaña activa y anillo de foco. Con texto blanco encima cumple 5,5:1.
- **Teal claro** (`teal-claro`): la misma voz cuando va como texto o icono sobre grafito (botones outline/flat, paso activo del asistente, enlaces). El teal del taller sobre grafito solo da 3,1:1 y no sirve para texto.

### Neutral
- **Grafito de página** (`grafito-pagina`): fondo de toda ventana.
- **Grafito de panel** (`grafito-panel`): tarjetas, paneles de pestaña, tablas, menús y diálogos; la capa que separa sin sombra.
- **Tinta** (`tinta`): texto principal y cifras.
- **Tinta secundaria** (`tinta-secundaria`): ayudas bajo los campos, estado de la fuente de datos (Spoolman/OctoPrint/catálogo), etiquetas de columna; 7:1 sobre grafito.
- **Línea** (`linea`): separadores antes de un total y entre secciones.
- **Muestra vacía** (`muestra-vacia`) y **borde de muestra** (`borde-muestra`): el cuadro de color de un slot sin filamento y su contorno, que lo mantiene visible sobre el grafito.

### Semánticos
- **Verde precio** (`verde-precio`): el precio de venta final y los valores confirmados, como texto sobre grafito.
- **Verde confirmación** (`verde-confirmacion`): fondo de notificaciones y botones de confirmar con texto blanco (5:1). Reemplaza el verde por defecto de Quasar (`#21BA45`), que con texto blanco no llega a 3:1.
- **Ámbar costo** (`ambar-costo`): el costo total por unidad y los avisos en texto (configuración incompleta, valores fallidos de purga).
- **Rojo error** (`rojo-error`): fondo de notificaciones de error y de botones destructivos sólidos.
- **Rojo texto** (`rojo-texto`): acciones destructivas como texto o icono (Salir, borrar extra, limpiar slots); 6:1 sobre panel. Sustituye al `text-red-500` actual, que se queda en 4,48:1.

### Named Rules
**The One Voice Rule.** El teal es el único color de marca. Ningún botón, pestaña o paso usa el azul por defecto de Quasar: `ui.colors(primary="#0F766E", positive="#15803D", negative="#C10015")` se fija una vez al iniciar.

**The Meaning-Only Rule.** Un acento de color siempre significa algo: verde = precio u ok, ámbar = costo o atención, rojo = error o borrar. Si un color no responde a "¿qué significa?", se quita (el cian decorativo del estado de fuente pasa a tinta secundaria).

## Typography

**Body Font:** Roboto (incluida con NiceGUI; con -apple-system, Helvetica Neue, Arial como respaldo)
**Label/Mono Font:** la misma Roboto; las cifras usan números tabulares, no monoespaciada.

**Character:** Una sola familia neutra que se lee como una planilla. La jerarquía sale del tamaño y el peso, y las cifras se alinean por columnas gracias a `tnum`.

### Hierarchy
- **Headline** (400, 1.5rem, 2rem): el nombre "PrintTool" en la barra superior.
- **Title** (500, 1.25rem, 2rem): nombre del modelo activo en la barra y título de cada página.
- **Subtitle** (400, 1rem, 1.75rem): título de cada panel ("Matriz de purga", "Datos de fabricación").
- **Body** (400, 14px, 1.5): etiquetas de filas, textos de botones, celdas de tabla.
- **Number** (400, 14px, 1.5, `tnum`): toda cifra con unidad (g, h m, %, moneda), alineada a la derecha.
- **Total** (700, 1.125rem, 1.75rem, `tnum`): la fila final de una ficha de cálculo (Costo Total, Precio Venta).
- **Label** (400, 0.75rem): etiquetas flotantes de inputs y ayudas bajo un campo.

### Named Rules
**The Tabular Figures Rule.** Toda cifra se escribe con números tabulares, alineada a la derecha y con su unidad en el mismo formato en todas las pantallas (`55.15 g`, `2 h 53 m`, `$ 10.00`). Un número que no se alinea con su columna no se puede comparar.

## Layout

Lienzo de escritorio: ventana nativa de 1024×786, contenido centrado con un ancho máximo de 72rem (`max-w-6xl`) en páginas de trabajo y 42rem (`max-w-2xl`) en fichas de cálculo. Barra superior y pie fijos. Las pestañas (Info, Costos, Precio, Modelo) van dentro de la barra; debajo, los paneles a lo ancho.

El ritmo usa tres pasos: 8px dentro de un grupo (`spacing.sm`), 12px entre controles relacionados (`spacing.md`) y 16px como relleno de panel y separación entre secciones (`spacing.lg`). Las fichas de cálculo son rejillas de dos columnas (etiqueta | valor) o tres (concepto | referencia | final).

La matriz de purga es una rejilla de 6×6 (encabezado + 5 colores) con un ancho mínimo de 720px; en ventanas más estrechas hace scroll horizontal dentro de su panel y nunca desborda la página. Lo mismo vale para tablas con nombres de archivo largos (G-code). El área de trabajo no tiene alturas fijas: la página es la única que hace scroll vertical. La pestaña Costos se limita a 64rem (`max-w-5xl`) para que las dos fichas no se separen en pantallas anchas, y por debajo de unos 700px se apilan.

**The Fixed Chrome Rule.** La barra superior y el pie usan altura mínima en píxeles (48px y 32px), nunca `vh`: con `5vh` la barra medía 30px en una ventana de 600px y el título se cortaba. Con `min-height`, si el texto crece por zoom, la barra crece con él.

## Elevation & Depth

Plano por capas tonales. La página es grafito (`grafito-pagina`) y todo lo que agrupa (paneles, tablas, pestañas) sube un tono a `grafito-panel`; esa diferencia es la única separación en reposo. Solo lo que flota sobre el contenido (menú de la barra, diálogos, notificaciones, desplegables de select) usa la sombra por defecto de Quasar, porque realmente está por encima.

### Named Rules
**The Flat-At-Rest Rule.** Paneles y tarjetas usan `flat` (sin sombra) y se distinguen por tono. Una sombra significa "esto flota y se va a cerrar".

## Shapes

Esquinas apenas suavizadas de 4px (`rounded.sm`) en todo: botones, campos, paneles, muestras de color. Nada en forma de píldora: ningún input lleva `rounded`. Los bordes son de 1px y solo aparecen en campos outlined, en el contorno de las muestras de color y como línea antes de un total.

## Components

### Buttons
Directos y sobrios: un solo botón sólido por sección.
- **Shape:** esquinas suaves (4px), alto de 36px, relleno 4px 16px, texto en mayúsculas (default de Quasar).
- **Primary:** fondo teal del taller con texto blanco; solo para la acción principal de la sección (Guardar, Aplicar, Salvar).
- **Outline / flat:** borde y texto en teal claro para acciones secundarias (Consultar en Dolibarr, Anterior, cargar desde OctoPrint).
- **Destructivo:** texto o icono en rojo texto, en flat u outline; sólido en rojo error solo dentro de un diálogo de confirmación.
- **Solo icono:** siempre con `aria-label` y tooltip con la misma frase.
- **Ocupado:** prop `loading` mientras hay una petición de red; el botón hermano que haría otra petición queda deshabilitado.

### Inputs / Fields
Compactos y con borde.
- **Style:** `outlined dense` (40px de alto, borde de 1px, esquinas de 4px), etiqueta flotante en estilo Label, prefijo o sufijo con la unidad (`$`, `%`, `watts`, `años`).
- **Focus:** borde de 2px en teal claro (color primario de Quasar en oscuro).
- **Error / Disabled:** mensaje de validación en español bajo el campo ("Campo obligatorio", "Debe ser menor que 100 %"); deshabilitado con la opacidad por defecto de Quasar y una línea en tinta secundaria que explique por qué.

### Navigation
- **Barra superior:** fondo teal del taller, 48px. A la izquierda, "PrintTool" en Headline y el nombre del modelo en Subtitle (se recorta con «…» si falta espacio). En el centro, las pestañas de la página, si las hay. A la derecha, el menú (icono `menu`, flat, texto blanco). El menú lista Inicio, Cambiar Proyecto, Configurar, Cálculo Purga MMU y, separado, Salir en rojo texto.
- **Pestañas:** viven dentro de la barra superior, con el icono al lado de la etiqueta (`inline-label`, 48px de alto), texto blanco y subrayado blanco en la activa. Se centran con márgenes automáticos; si no caben, muestran flechas de desplazamiento y nunca empujan el menú fuera de la barra.
- **Pie:** fondo teal, "Creado por ChepeCarlos" centrado en blanco (compromiso de marca).

### Ficha de cálculo (signature)
La pieza que define el producto: una rejilla de filas etiqueta → valor.
- Etiqueta en Body a la izquierda y valor en Number a la derecha, con unidad.
- Una línea (`linea`) antes de la fila total; la fila total en estilo Total.
- El total lleva su color semántico: ámbar costo para "Costo Total" y verde precio para "Precio Venta" final.
- En Precio, tres columnas: Cálculo | Referencia | Final.

### Muestra de color (signature)
Cuadro de 32px (16px en los encabezados de la matriz) con esquinas de 4px y borde de 1px en borde de muestra, relleno con el hex del filamento (Spoolman u OctoPrint) o muestra vacía si no hay. Siempre va junto al nombre del filamento: el color nunca es el único dato.

### Tablas
Tabla de Quasar en oscuro sobre grafito de panel, paginada (5–8 filas). Columnas numéricas alineadas a la derecha y en Number. Buscador en la esquina superior derecha y acción sobre la selección (Editar, Borrar) en la superior izquierda, visible solo cuando hay una fila seleccionada.

## Do's and Don'ts

### Do:
- **Do** fijar `ui.colors(primary="#0F766E", positive="#15803D", negative="#C10015")` al iniciar, para que botones, foco, pasos y notificaciones hablen teal.
- **Do** usar teal claro (`#4DB6AC`, `color=teal-4` en Quasar) para texto o icono teal sobre grafito.
- **Do** alinear las cifras a la derecha con `tabular-nums` y la unidad en el formato común (`g`, `h m`, `%`, símbolo de moneda configurable).
- **Do** separar el total con una línea y darle peso 700 a 1.125rem.
- **Do** acompañar cada muestra de color con su nombre de filamento.
- **Do** usar `outlined dense` en todos los campos de entrada.

### Don't:
- **Don't** dejar el azul por defecto de Quasar (`#1976D2`) en ningún control.
- **Don't** usar color sin significado: nada de cian decorativo ni de colores distintos para el mismo estado (ámbar y naranja para un mismo aviso).
- **Don't** poner sombras a paneles en reposo; la separación es tonal.
- **Don't** usar esquinas de píldora (`rounded` en inputs) ni radios distintos de 4px.
- **Don't** fijar alturas de barra o paneles en `vh`.
- **Don't** escribir clases de color inexistentes (`bg-teal-00`, `border-teal-600h`, `color=bg-teal-700`): fallan en silencio.
