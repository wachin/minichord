# ROADMAP - ChordPages v3

## Objetivo del programa

ChordPages v3 es un editor de canciones en texto plano para letras y acordes de guitarra. Su objetivo es aprovechar pantallas de ordenador mostrando tres paginas por fila, con comportamiento de escritura estable, paginas reales, margenes configurables y soporte para archivos `.txt`, `.pro`, `.cho` y `.chordpro`.

## Reglas tecnicas no negociables

[x] El texto fuente debe vivir en una sola cadena interna (`ThreeUpPageView.text`).

[x] Las paginas y lineas visuales son una representacion recalculada del texto fuente; nunca deben modificar, recortar ni reordenar el texto real.

[x] Cada `PageLine` debe guardar offsets reales `start_idx` y `end_idx` dentro del texto fuente.

[x] El wrap visual de lineas largas no debe usar `strip`, `rstrip`, `lstrip` ni ninguna transformacion que cambie el mapeo entre caracteres visibles y posiciones del texto.

[x] El cursor, la seleccion, los clics y la navegacion por teclado deben usar los offsets reales, no indices aproximados por pagina.

[x] Al pegar o abrir archivos, los saltos de linea deben normalizarse a `\n` para evitar errores de posicion con `\r\n` o `\r`.

[x] Al cambiar margenes, fuente, papel o zoom, el programa debe recalcular la vista completa sin perder el texto ni mover el cursor a una posicion incorrecta.

[x] El area util de la pagina debe recortar visualmente el texto para que no se dibuje fuera de los margenes.

[x] No se debe usar un `QTextEdit` con scroll interno para resolver el desbordamiento de una pagina. Si el texto no cabe, se crean mas paginas visuales.

## Logrado en v3.1

[x] Vista 3-up: tres paginas por fila dentro de un scroll vertical general.

[x] Modelo de texto unico separado del layout visual.

[x] Paginador propio para dividir texto plano en paginas segun caracteres por linea y lineas por pagina.

[x] Reflujo automatico al cambiar zoom, papel, fuente y margenes.

[x] Edicion basica: escribir, Enter, Tab, Backspace, Delete.

[x] Seleccion con mouse y con teclado.

[x] Copiar, cortar, pegar y seleccionar todo.

[x] Abrir y guardar archivos de texto.

[x] Dialogo de fuente.

[x] Dialogo de margenes en milimetros.

[x] Cursor corregido para que la escritura no salte hacia la izquierda ni se asocie con una linea visual equivocada despues del wrap.

[x] Paginador corregido para preservar offsets exactos cuando una linea larga se parte en varias lineas visuales.

[x] Seleccion y cursor medidos con el ancho real del texto dibujado, no solo con una columna aproximada.

[x] Los margenes vuelven a funcionar con reflow completo y calculo de capacidad desde el area util real.

[x] Cursor, seleccion y clics recalculados con `QTextLayout`, usando el motor de texto de Qt para alinear el cursor como en un editor nativo.

[x] Navegacion vertical ajustada por posicion X real del cursor, no solo por numero de caracter.

[x] Texto dibujado con `QTextLayout.draw` para que la posicion de letras, espacios, tabs y cursor se calcule con el mismo motor.

[x] Zoom manual agregado: acercar, alejar, zoom 100% y ajuste de tres paginas al ancho.

[x] Atajos de zoom agregados: `Ctrl++`, `Ctrl+=`, `Ctrl+-` y `Ctrl+0`.

[x] Barra de herramientas agregada para controles de zoom.

## Pendiente

[ ] Agregar pruebas automaticas para `SimplePager`: lineas largas, lineas vacias, saltos de pagina, texto con `\r\n`, tabs y seleccion entre paginas.

[ ] Agregar pruebas automaticas de edicion para confirmar que escribir caracter por caracter mantiene `caret_idx` y `text` correctos despues de cada reflow.

[ ] Medir el wrap por ancho real en pixeles usando `QTextLayout`/`QFontMetrics`, no solo por cantidad aproximada de caracteres.

[ ] Agregar undo/redo.

[ ] Agregar busqueda y reemplazo.

[ ] Agregar opcion de auto-scroll para tocar guitarra, sin reemplazar la vista de paginas.

[ ] Agregar soporte semantico opcional para ChordPro: directivas, titulos, comentarios, transpose y bloques.

[ ] Agregar impresion/exportacion a PDF respetando las paginas visuales.

[ ] Guardar preferencias del usuario: papel, margenes, fuente, zoom y ultimo directorio usado.

[ ] Mejorar rendimiento para canciones muy largas con cache de layout y repintado parcial.

[ ] Agregar indicador de pagina, posicion del cursor y cantidad total de paginas.

## Instrucciones para futuras versiones

[ ] Si se cambia el layout, primero comprobar que `PageLine.text == source_text[PageLine.start_idx:PageLine.end_idx]` para todas las lineas visuales.

[ ] Si se cambia el wrap, conservar todos los espacios del texto fuente. Los espacios son importantes para alinear acordes.

[ ] Si se cambia el comportamiento del cursor, probar escritura continua, Enter, Backspace, Delete, flechas, Home, End, PageUp y PageDown.

[ ] Si se agrega soporte ChordPro, mantener dos capas separadas: texto fuente editable y representacion interpretada. No reemplazar el texto escrito por el usuario con una version renderizada.

[ ] Si se agrega auto-scroll, debe desplazarse el `QScrollArea` general, no crear scroll interno en cada pagina.

[ ] Si se agregan columnas reales dentro de una pagina, deben paginarse como regiones de flujo con capacidad fija. Cuando una columna se llena, el texto pasa a la siguiente columna; cuando se llenan las columnas de la pagina, se crea otra pagina.
