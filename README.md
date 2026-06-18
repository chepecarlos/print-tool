# print-tool
Herramientas para ayudar con emprendimiento impresión 3d


# TODO

[ ] Calcular Precios 
    [ ] Cantidad de Filamento
    [ ] Ensamblaje
    [ ] Costos de Electricidad
    [ ] Recuperación de inversion
    [ ] Costos Extras
[ ] Llevar información de modelos
    [ ] Nombre
    [ ] Tipo
    [ ] Tamaño
    [ ] Link
[ ] Sincronizar con Notion
[ ] Llevar inventario de Modelos
[ ] Mostrar todos los productos en un DashBoard
[ ] Crear folder de proyecto
[ ] Inventario de filamento
    [ ] Cantidad
    [ ] Color
    [ ] Fabricante
    [ ] Precio
    [ ] Fecha de Compra
    [ ] tag_RFID
    [ ] Cantidad gramos

# Info

https://pywebview.flowrl.com/guide/installation.html

## Lectura de información en titulo del archivo

- Piezas: {n}pc
- Tiempo: {n}h{n}m
- Gramos: {n}g
- Copias: {n}cc
- Color: -{color}-
- Punta: {n}p

Ejemplo: modelo_32g_5pc_2h10m.gcode
- 32 Gramos
- 5 Piezas
- 2 Horas 10 Minutos

## Para Cura Ultimaker

https://marketplace.ultimaker.com/app/cura/plugins/rgomezjnr/GcodeFilenameFormatPlus

https://github.com/rgomezjnr/GcodeFilenameFormatPlus

---

## Calculadora de Purga MMU3 (`/purga`)

La página `/purga` calcula cuántos mm³ de filamento hay que purgar al cambiar de un color a otro en una impresora con sistema multi-material (MMU3 de Prusa).

### ¿Qué es la purga?

Cuando la MMU cambia de color, queda filamento del color anterior en el hotend. Para evitar contaminación hay que extruir material de "limpieza" antes de imprimir con el nuevo color. La cantidad necesaria depende de la combinación:

- Cambiar de **negro → blanco** requiere mucha purga (el negro mancha mucho).
- Cambiar de **blanco → negro** requiere muy poca (el negro cubre bien).

Esa cantidad se guarda en una **matriz 5×5**: fila = color origen, columna = color destino, valor = mm³ de purga.

---

### Integración con Spoolman

PrintTool guarda la matriz de purga directamente en cada filamento de Spoolman usando un **campo personalizado** llamado `pruga`.

#### Crear el campo en Spoolman (solo la primera vez)

1. Abrir Spoolman → **Settings → Custom Fields → Filament**
2. Crear un campo de tipo **Text** con la clave exacta: `pruga`
3. Guardar. PrintTool lo llenará automáticamente al guardar la configuración.

#### Formato del campo `pruga`

Cada filamento almacena **su propia fila** de la matriz en formato compacto:

```
{id_filamento_destino}-{mm3},{id_filamento_destino}-{mm3},...
```

Ejemplo: el filamento con ID 52 necesita 120 mm³ para limpiar hacia el filamento 138, 80 mm³ hacia el 58 y 150 mm³ hacia el 129:

```
138-120,58-80,129-150
```

> El número antes del guión es el **ID numérico del filamento en Spoolman** (visible en la URL al editar el filamento, o como `#N` en la interfaz). **No es el número de slot** (Color 1, Color 2…).

#### Cómo lo lee PrintTool

Al cargar la página `/purga` con los 5 slots asignados:

1. Lee el campo `pruga` de cada filamento desde `filament.extra.pruga`.
2. Cada filamento aporta **su fila** de la matriz: busca los IDs destino en los otros slots y coloca el mm³ en la celda `[origen][destino]`.
3. Si un filamento no tiene el campo `pruga` o no reconoce el ID destino, esa celda queda vacía.

#### Cómo lo escribe PrintTool

Al presionar **"Guardar en proyecto"** o **"Guardar global"**:

1. Lee los valores de la matriz desde la UI.
2. Para cada slot origen, extrae los valores hacia los otros 4 slots.
3. Serializa en el formato compacto y hace un `PATCH /api/v1/filament/{id}` a Spoolman con:

```json
{ "extra": { "pruga": "\"138-120,58-80,129-150\"" } }
```

> El valor viaja como **string JSON-serializado** (con comillas escapadas) porque Spoolman valida los campos `extra` como JSON individual.

#### Flujo completo de uso

```
1. Asignar filamentos a Color 1..5 (desde Spoolman o OctoPrint)
2. Llenar la matriz de purga (valores en mm³)
3. Guardar → PrintTool actualiza el campo `pruga` en cada filamento de Spoolman
4. La próxima vez que abras el proyecto, la matriz se recarga desde Spoolman automáticamente
```

#### Fuentes de filamentos soportadas

| Fuente | Descripción |
|--------|-------------|
| **Spoolman** | Consulta `/api/v1/spool` y lee filamentos con color, material y campo `pruga` |
| **OctoPrint + Spoolman** | Lee `selectedSpoolIds` de `/api/settings` y consulta cada bobina en Spoolman |
| **Catálogo manual** | Lista local de filamentos sin conexión a servicios externos |