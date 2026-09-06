# TP 1 — Selector astronómico de fecha

Un formulario de registro donde ingresar la fecha de nacimiento se convierte en un problema innecesariamente complicado: el tiempo corre dentro de un sistema solar y el usuario tiene que detenerlo exactamente en el día en que nació.

Funciona, pero completar una fecha es mucho más difícil de lo que debería. Esa era la idea.

## Cómo se ejecuta

Doble click en `index.html`.

Todo el proyecto está contenido en un único archivo HTML, con CSS y JavaScript embebidos y sin dependencias externas.

## Qué me propuse construir

La idea fue tomar una acción completamente cotidiana —ingresar una fecha de nacimiento en un formulario— y reemplazar el calendario convencional por una interfaz deliberadamente incómoda.

El formulario comienza como cualquier registro normal: nombre, apellido y correo electrónico. Para completar la fecha de nacimiento aparece un pequeño sistema solar.

En la versión final, la fecha no se selecciona directamente. El tiempo comienza a retroceder automáticamente y la Tierra se mueve alrededor del Sol mientras la fecha cambia. El usuario puede modificar la velocidad e invertir el sentido temporal, pero para elegir su fecha debe presionar **“Confirmar fecha (detener tiempo)”** exactamente en el momento correcto.

Si se pasa de su fecha, tiene que invertir el sentido del tiempo y esperar a volver.

El desarrollo se realizó iterativamente en una única conversación con Gemini.

## Decisiones que tomé yo

**Un formulario serio alrededor de una interacción absurda.**
Quise que la interfaz general pareciera un formulario institucional normal. El sistema solar aparece en el medio de una tarea cotidiana y rompe deliberadamente una interacción que podría resolverse con un simple calendario.

**El sistema solar no intenta ser una simulación astronómica.**
El Sol, la Tierra y la órbita son representaciones esquemáticas construidas con HTML y CSS. El objetivo no era simular físicamente el sistema solar, sino utilizar sus movimientos como interfaz.

**El estado es independiente del DOM.**
La fecha vive en variables de JavaScript (`dia`, `mes` y `anio`). La posición de la Tierra, el texto de la fecha y los controles son solamente representaciones visuales de ese estado.

**Separar rotación y traslación.**
En una primera versión, la Tierra tenía que utilizar `transform` tanto para ubicarse sobre la órbita como para rotar sobre sí misma. Para evitar que ambas animaciones se pisaran, se separó la posición orbital en un elemento y la rotación del planeta en otro.

**Hacer que el tiempo corra solo.**
La primera implementación permitía seleccionar manualmente día, mes y año. Funcionaba, pero todavía se parecía demasiado a un selector convencional con controles extraños. La decisión más importante fue eliminar esa selección directa y hacer que la fecha avanzara automáticamente.

**“Confirmar” significa detener el tiempo.**
El botón principal no simplemente lee la fecha. Detiene el temporizador y congela el sistema en el instante actual. De esa manera, la acción absurda y la función real del formulario son la misma interacción.

**Permitir corregir, pero hacerlo doloroso.**
Después de detener el tiempo aparece una pantalla de revisión. Si el usuario descubre que se equivocó puede volver, pero todos los datos cargados se descartan y tiene que empezar nuevamente desde cero, incluida la búsqueda de su fecha de nacimiento.

## Cómo fue evolucionando

La primera versión tenía únicamente el mes. Los doce meses estaban distribuidos alrededor del Sol y seleccionar uno movía la Tierra hasta esa posición de la órbita.

En la segunda iteración agregué el día y el año como estados independientes. El día avanzaba mediante rotaciones de la Tierra y el año mediante revoluciones alrededor del Sol. Esta versión ya era incómoda, pero seguía ofreciendo controles demasiado directos.

En la tercera iteración cambié la idea central: eliminé los controles individuales y convertí el sistema en un reloj temporal continuo. La fecha comienza en el presente y viaja automáticamente hacia el pasado. El usuario solamente puede controlar la velocidad, invertir el sentido y detener el tiempo.

Finalmente agregué una etapa de revisión. Detener el tiempo ya no confirma inmediatamente el registro: primero se muestran los datos seleccionados. Si el usuario decide corregirlos, se eliminan todos y debe repetir el proceso.

## Qué salió mal y cómo lo corregí

El principal problema no fue que las primeras versiones no funcionaran, sino que eran demasiado cómodas.

En la primera versión el usuario podía hacer click directamente sobre un mes. Técnicamente el selector era astronómico, pero elegir “Mayo” seguía siendo prácticamente tan sencillo como presionar un botón normal.

La segunda versión agregó una interacción más hostil para día y año, pero terminó creando varios controles separados. Eso hacía que la metáfora del sistema solar quedara fragmentada: cada movimiento representaba algo distinto, pero el usuario seguía controlando cada parte de la fecha de manera explícita.

La solución fue cambiar el modelo de interacción completo. En vez de pedirle al usuario que construyera una fecha, hice que la fecha existiera como un estado en movimiento. A partir de ahí, la tarea pasó a ser detener el sistema en el instante correcto.

También fue necesario separar la rotación terrestre de la posición orbital en distintos elementos del DOM. Esto evitó que dos animaciones modificaran simultáneamente la misma propiedad CSS `transform`.

Otro punto importante fue controlar los temporizadores. Al detener y reanudar el tiempo se debía evitar crear varios `setInterval` simultáneos, por lo que el temporizador quedó administrado mediante funciones específicas para iniciarlo y detenerlo.

## Prompts

El registro completo de la conversación con Gemini está en [prompts.md](prompts.md).

Los cambios más importantes fueron el tercer prompt, donde la selección manual se convirtió en un flujo temporal continuo que debía detenerse, y el cuarto, donde se agregó el paso de revisión y la pérdida deliberada de todos los datos al intentar corregir un error.
