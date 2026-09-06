# Prompts — TP 1

El registro del proceso, en orden. Cuatro prompts en una sola conversación de Gemini. El artefacto quedó terminado en el cuarto.

---

## 1 — Prompt inicial

```
Construí una página de registro de usuario con un selector de fecha de nacimiento deliberadamente incómodo basado en un sistema solar.

Estructura
<header> con:
un <h1> que diga "Registro de usuario";
un <p> breve indicando que se deben completar los datos personales.
<main> con un <form>.
El formulario debe tener:
<label> + <input> para nombre;
<label> + <input> para apellido;
<label> + <input type="email"> para correo electrónico.
Para la fecha de nacimiento NO usar <input type="date"> ni permitir escribir la fecha manualmente.
En su lugar, agregar una <section> denominada visualmente "Selector astronómico de fecha".
Dentro de esa sección mostrar:
un Sol en el centro;
una órbita circular alrededor del Sol;
una Tierra ubicada sobre esa órbita;
los nombres de los 12 meses distribuidos visualmente alrededor de la órbita;
debajo del sistema solar, un texto que muestre claramente el mes actualmente seleccionado.
Agregar un <button type="submit"> con el texto "Confirmar registro" al final del formulario.
Agregar un <footer> con un texto simple de copyright.
Usar HTML semántico siempre que corresponda. Evitar usar <div> para elementos que tengan una etiqueta semántica adecuada.

Estilo
La página debe tener una estética seria, sobria e institucional, similar a un formulario administrativo real. La intención es que el aspecto normal y profesional contraste con lo absurdo del selector astronómico.
Usar una tipografía sans-serif del sistema, sin cargar fuentes externas.
Definir en :root las siguientes variables CSS:

--color-bg: #eef2f7;
--color-surface: #ffffff;
--color-text: #1f2937;
--color-muted: #64748b;
--color-accent: #1d4ed8;
--color-border: #cbd5e1;
--color-sun: #f59e0b;
--color-earth: #2563eb;
--space-md: 16px;
--space-lg: 24px;
--radius: 8px;
Usar estas variables en lugar de repetir colores o espaciados hardcodeados.
Aplicación de la paleta:

--color-bg: fondo general de la página.
--color-surface: fondo del formulario y de la sección astronómica.
--color-text: texto principal.
--color-muted: instrucciones y textos secundarios.
--color-accent: botones, foco de inputs y elementos interactivos.
--color-border: bordes de inputs, formulario y separadores.
--color-sun: Sol.
--color-earth: Tierra.
Layout:

Centrar el contenido principal.
El formulario debe tener un max-width aproximado de 700px.
Usar flexbox con flex-direction: column y gap para organizar el formulario y sus campos.
Dar suficiente padding al formulario para que tenga una apariencia limpia y profesional.
Los campos de texto deben ocupar todo el ancho disponible.
La sección del selector astronómico debe tener suficiente altura y espacio para que el sistema solar sea claramente visible.
No usar una estética infantil, caricaturesca ni de videojuego.
No usar gradientes excesivos, efectos neon ni fondos espaciales.
El sistema solar debe conservar la misma identidad visual limpia del formulario.
El Sol, la Tierra y la órbita deben dibujarse exclusivamente con HTML y CSS. No usar imágenes externas.

Comportamiento
Crear un estado JavaScript:

mes
mes debe ser un número entre 1 y 12.
Inicializarlo con el mes actual.
La Tierra debe poder ocupar 12 posiciones discretas alrededor de la órbita, una por cada mes.
Al hacer click sobre el nombre de un mes:

actualizar el estado mes;
mover visualmente la Tierra hasta la posición correspondiente de la órbita;
actualizar el texto que muestra el mes seleccionado.
El estado mes debe ser la fuente de verdad. La posición de la Tierra y el texto mostrado en pantalla deben ser representaciones de ese estado en el DOM.
Por ahora el selector astronómico controla ÚNICAMENTE EL MES.
No implementar todavía:

selección del día;
selección del año;
Luna;
simulación física;
movimiento orbital continuo;
astronomía realista.
El resto del formulario debe funcionar normalmente.
Al enviar el formulario:

usar preventDefault() para evitar recargar la página;
mostrar debajo del formulario un mensaje simple con nombre, apellido, email y mes seleccionado.
Constraints
Todo debe estar contenido en un único archivo index.html.
CSS dentro de <style>.
JavaScript dentro de <script>.
Vanilla JavaScript.
Sin frameworks.
Sin librerías externas.
Sin dependencias.
Sin imágenes externas.
No usar <canvas>.
El archivo debe funcionar abriéndolo directamente con doble click en un navegador.
```

**Qué intentaba lograr:** construir una primera versión completa y funcional del artefacto, definiendo desde el inicio las capas principales: estructura HTML semántica, estilo mediante variables CSS, comportamiento basado en un estado mes y los constraints de empaque en un único archivo. Decidí limitar esta primera versión únicamente a la selección del mes para validar primero la interacción básica entre estado, DOM y movimiento de la Tierra.

**Qué devolvió:** un formulario de registro funcional con nombre, apellido y correo electrónico, más un selector astronómico donde los doce meses aparecen distribuidos alrededor del Sol. Al seleccionar un mes, se actualiza el estado mes, la Tierra se mueve hasta la posición correspondiente de la órbita y el DOM refleja el mes seleccionado. También respetó la paleta definida mediante variables CSS, el uso de HTML, CSS y JavaScript dentro de un único index.html, y la ausencia de dependencias externas.

**Qué hice con eso:** lo acepté como base porque resolvía correctamente el ciclo evento → estado → DOM que quería probar en esta primera iteración. La interfaz todavía era demasiado cómoda —el usuario podía elegir el mes haciendo click directamente sobre su nombre— y además faltaban el día y el año, pero preferí no pedir toda la mecánica de una sola vez. En el siguiente prompt mantuve esta estructura y extendí el estado para representar una fecha completa.

---

## 2 — Iterar sobre el estado: fecha completa.

```
Trabajá sobre el index.html actual.
NO reconstruyas la aplicación desde cero.
Conservá:

el <header>;
el <main>;
el <form>;
los campos de nombre, apellido y correo;
el <footer>;
la paleta y las variables CSS definidas en :root;
el selector astronómico existente;
el estado mes;
los 12 meses distribuidos alrededor de la órbita;
el comportamiento actual mediante el cual seleccionar un mes mueve la Tierra a su posición correspondiente.
El objetivo de esta iteración es ampliar el selector para que permita elegir una FECHA COMPLETA: día, mes y año.
La interfaz debe seguir siendo funcional pero deliberadamente frustrante.
1. Estado
Mantener el estado existente:

let mes = new Date().getMonth() + 1;
Agregar:

let dia = 1;
let anio = new Date().getFullYear();

let girandoDia = false;
let viajandoAnio = false;
Agregar también:

const ANIO_MIN = 1900;
const ANIO_MAX = new Date().getFullYear();
Los valores dia, mes y anio deben ser la única fuente de verdad de la fecha seleccionada.
No guardar el estado leyendo el contenido textual del DOM.
El DOM únicamente debe representar el estado.
2. Estructura HTML nueva
Dentro de la <section> del selector astronómico, conservar el sistema solar actual y agregar debajo una nueva zona de controles.
Usar una estructura semejante a:

<section class="astro-controls">
    <section class="day-control">
        ...
    </section>

    <section class="year-control">
        ...
    </section>
</section>
Control del día
Dentro de .day-control agregar:

un encabezado breve;
un <p id="day-output">;
un <button type="button" id="rotate-day">.
Texto del botón:
"Completar una rotación terrestre (+1 día)"

Control del año
Dentro de .year-control agregar:

un encabezado breve;
un <p id="year-output">;
dos <button type="button">:
id="year-back"
id="year-forward"
Textos:
"Viajar 1 año al pasado"
"Viajar 1 año al futuro"

Fecha completa
Debajo de ambos controles agregar:

<p class="date-display">
    Fecha seleccionada:
    <strong id="date-output"></strong>
</p>
No agregar ningún <input>, <select> o calendario para elegir día, mes o año.
3. Refactor de la Tierra
Actualmente el mismo elemento .earth utiliza transform para posicionarse sobre la órbita.
Necesito separar dos movimientos distintos:

traslación orbital alrededor del Sol;
rotación de la Tierra sobre su propio eje.
Modificar la estructura para utilizar dos elementos.
Conceptualmente:

<span id="earth-orbit-position">
    <span id="earth" class="earth">
        <span class="earth-marker"></span>
    </span>
</span>
El elemento exterior debe controlar únicamente la POSICIÓN de la Tierra alrededor del Sol.
El elemento interior .earth debe controlar únicamente la ROTACIÓN sobre su propio eje.
No permitir que dos animaciones escriban sobre la misma propiedad transform del mismo elemento.
Agregar sobre la Tierra un pequeño detalle visual, por ejemplo .earth-marker, para que una rotación de 360 grados resulte perceptible.
Ese detalle debe realizarse con CSS.
No usar imágenes.
4. Selección del día
El día debe seleccionarse únicamente mediante rotaciones terrestres.
No agregar un botón para retroceder un día.

Evento
Registrar un listener click sobre:

<button id="rotate-day">
Transición
Cuando se hace click:
Si:

girandoDia === true
o:

viajandoAnio === true
no hacer nada.
En caso contrario:

establecer:
girandoDia = true;
deshabilitar temporalmente los controles astronómicos;
ejecutar visualmente una rotación completa de 360 grados de .earth;
la animación debe durar aproximadamente 400ms;
cuando finaliza la rotación:
incrementar dia en 1;
validar el nuevo valor;
establecer girandoDia = false;
volver a habilitar los controles;
actualizar el DOM mediante la función de renderizado.
No incrementar dia al comienzo de la animación.
Incrementarlo cuando la rotación termina.
5. Cantidad de días de cada mes
Crear una función:

function diasDelMes(mes, anio)
Debe devolver correctamente la cantidad de días correspondiente al mes y año actual.
Contemplar:

meses de 31 días;
meses de 30 días;
febrero de 28 días;
febrero de 29 días en año bisiesto.
Crear también:

function esBisiesto(anio)
Cuando una rotación terrestre hace que:

dia > diasDelMes(mes, anio)
el estado debe pasar automáticamente a:

dia = 1;
Por ejemplo:
30 de abril → una rotación → 1 de abril.
Esto es deliberadamente frustrante.
NO avanzar automáticamente al mes siguiente.
El mes solamente puede cambiarse mediante el mecanismo orbital ya existente.
6. Validación del día cuando cambia mes o año
Cada vez que cambia mes o anio, comprobar si el día seleccionado sigue existiendo.
Crear una función:

function validarDia()
Si:

dia > diasDelMes(mes, anio)
entonces:

dia = diasDelMes(mes, anio);
Ejemplo:
Estado actual:
31 / MARZO / 2000
El usuario selecciona abril.
Nuevo estado:
30 / ABRIL / 2000
Otro ejemplo:
29 / FEBRERO / 2000
El usuario cambia el año a 2001.
Nuevo estado:
28 / FEBRERO / 2001
7. Selección del año
El año debe seleccionarse mediante viajes orbitales completos.
Cada click modifica exactamente UN año.
No agregar un campo numérico ni permitir mantener presionado para saltar varios años.

Viajar al pasado
Registrar un listener click sobre:

<button id="year-back">
Si:

viajandoAnio === true
o:

girandoDia === true
no hacer nada.
Si:

anio === ANIO_MIN
no modificar el estado.
En cualquier otro caso:

establecer:
viajandoAnio = true;
bloquear temporalmente todos los controles astronómicos;
animar una revolución completa de la Tierra alrededor del Sol en sentido antihorario;
duración aproximada: 700ms;
al finalizar:
anio = anio - 1;
conservar mes;
ejecutar validarDia();
establecer viajandoAnio = false;
volver a habilitar los controles;
actualizar el DOM.
Viajar al futuro
Registrar el listener equivalente sobre:

<button id="year-forward">
La transición debe ser simétrica:

revolución orbital en sentido horario;
anio = anio + 1;
nunca superar ANIO_MAX.
8. Animación orbital del año
La animación de cambio de año debe representar una revolución COMPLETA alrededor del Sol.
La Tierra debe:

comenzar en la posición correspondiente al mes seleccionado;
completar 360 grados alrededor del Sol;
terminar exactamente en la misma posición correspondiente al mes seleccionado.
La animación no debe modificar el estado mes.
Ejemplo:
Si mes === 5, la Tierra empieza en mayo, da una vuelta completa y termina nuevamente en mayo.
El año cambia.
El mes no.
Separar claramente:

estado lógico;
animación temporal;
posición final del DOM.
No utilizar la posición final de la animación como fuente de estado.
9. Renderizado
Crear o refactorizar una única función principal:

function updateUI()
Esta función debe tomar los valores actuales de:

dia
mes
anio
girandoDia
viajandoAnio
y reflejarlos en el DOM.
Debe encargarse de:

posicionar la Tierra según mes;
marcar visualmente el mes activo;
actualizar #month-output;
actualizar #day-output;
actualizar #year-output;
actualizar #date-output;
habilitar o deshabilitar los botones según el estado;
deshabilitar "Viajar 1 año al pasado" en ANIO_MIN;
deshabilitar "Viajar 1 año al futuro" en ANIO_MAX.
Mostrar #date-output con formato:

DD / MES / AAAA
Por ejemplo:

17 / MAYO / 1994
El nombre del mes debe mostrarse en mayúsculas.
10. Ciclo evento → estado → DOM
Mantener explícitamente este patrón en toda la aplicación:

evento del usuario
→ transición del estado
→ updateUI()
→ mutación del DOM
No utilizar textos, posiciones CSS o clases visuales para determinar el valor lógico de dia, mes o anio.
La fuente de verdad siempre debe ser el estado JavaScript.
11. Bloqueo durante animaciones
Mientras:

girandoDia === true
o:

viajandoAnio === true
ningún otro control astronómico debe modificar el estado.
Esto incluye:

meses;
rotación del día;
año anterior;
año siguiente.
Reflejar este bloqueo también en el DOM mediante disabled cuando corresponda.
Al terminar la animación debe existir siempre una transición de retorno que restablezca el estado y habilite nuevamente la interacción.
12. Layout
La página general debe conservar la estética institucional actual.
No cambiar la paleta.
Para .astro-controls usar:

display: grid;
grid-template-columns: 1fr 1fr;
gap: var(--space-md);
En pantallas angostas, permitir que pase a una sola columna mediante una media query.
Cada control debe tener:

padding: var(--space-md);
borde de 1px solid var(--color-border);
border-radius: var(--radius).
Los botones deben reutilizar la identidad visual existente:

--color-accent;
tipografía del sistema;
contraste suficiente;
sin efectos neon;
sin estética de videojuego.
El sistema solar debe seguir pareciendo una herramienta absurda dentro de un formulario institucional, no una aplicación de astronomía.
13. Confirmación del formulario
Modificar el listener submit existente.
Usar:

event.preventDefault();
El resumen final debe mostrar:

nombre;
apellido;
correo electrónico;
fecha de nacimiento completa.
Ejemplo:

Fecha de nacimiento: 17 / MAYO / 1994
Antes de confirmar, construir la fecha lógica a partir de:

dia
mes
anio
y verificar que no sea posterior a la fecha actual.
Si la fecha es posterior:

no ocultar el formulario;
no completar el registro;
mostrar un mensaje de error dentro del DOM;
no utilizar alert().
14. Constraints
Mantener los constraints del artefacto original:

un único archivo index.html;
HTML, CSS y JavaScript en ese mismo archivo;
CSS dentro de <style>;
JavaScript dentro de <script>;
Vanilla JavaScript;
sin frameworks;
sin librerías externas;
sin dependencias externas;
sin imágenes externas;
sin <canvas>;
HTML semántico cuando corresponda;
no introducir <input type="date">;
no introducir <input type="number"> para la fecha;
no introducir <select> para día, mes o año;
debe funcionar haciendo doble click sobre index.html.
No elimines funcionalidades que ya funcionan salvo que sea necesario refactorizarlas para separar correctamente la rotación terrestre de la posición orbital.
```

**Qué intentaba lograr:** extender la primera versión del selector para pasar de un único estado mes a una fecha completa formada por dia, mes y anio, sin abandonar la idea de que cada parte de la fecha se controle mediante movimientos astronómicos. El día debía avanzar mediante una rotación de la Tierra sobre sí misma y el año mediante una revolución completa alrededor del Sol.

**Por qué está escrito así:** esta iteración agregaba varios estados y animaciones que podían interferir entre sí. Por eso definí explícitamente los estados lógicos (dia, mes, anio) y los estados transitorios (girandoDia, viajandoAnio), además de las condiciones de entrada y de retorno de cada interacción. También pedí separar la posición orbital de la rotación propia de la Tierra en dos elementos distintos del DOM, porque ambas animaciones utilizan transform y podían pisarse si se aplicaban sobre el mismo elemento. Las reglas para meses, años bisiestos y bloqueo de controles durante las animaciones buscaban evitar estados imposibles o interacciones simultáneas difíciles de reproducir después.

**Qué devolvió:** una versión funcional capaz de representar una fecha completa. Gemini separó la posición orbital y la rotación terrestre en dos elementos, agregó los estados dia, mes, anio, girandoDia y viajandoAnio, e implementó funciones para años bisiestos, cantidad de días por mes y validación del día. También centralizó el reflejo del estado en una función updateUI() y bloqueó los controles mientras las animaciones estaban activas. La bad UI ya funcionaba, aunque el resultado todavía tenía demasiados controles directos para elegir la fecha, lo que motivó el cambio de enfoque del siguiente prompt.

---

## 3 — Cambiar el modelo de interacción: detener el tiempo

```
Trabajá sobre el index.html actual.
NO reconstruyas la aplicación desde cero.
Conservá:

el <header>, <main>, <form> y <footer>;
los campos de nombre, apellido y correo electrónico;
la paleta y todas las variables CSS existentes;
el Sol, la órbita y la Tierra;
la separación actual entre el elemento que controla la posición orbital de la Tierra y el elemento que controla su rotación;
las funciones existentes para años bisiestos y cantidad de días por mes;
el formato single-file;
Vanilla JavaScript y ausencia de dependencias externas.
El objetivo de esta iteración es cambiar completamente la forma de seleccionar la fecha.
La fecha ya NO debe elegirse mediante botones independientes para día, mes y año.
En su lugar, el sistema astronómico debe representar un TIEMPO EN MOVIMIENTO.
El usuario deberá dejar correr el tiempo hasta encontrar su fecha de nacimiento y detenerlo exactamente en esa fecha.
1. Eliminar la interacción anterior
Eliminar de la interfaz:

el botón "Completar una rotación terrestre (+1 día)";
el botón "Viajar 1 año al pasado";
el botón "Viajar 1 año al futuro";
los controles separados .day-control y .year-control.
Mantener las variables:

let dia;
let mes;
let anio;
pero modificar su comportamiento.
Inicializarlas con la fecha actual del sistema.
Por ejemplo, si la página se ejecuta el 6 de septiembre de 2026:

dia = 6;
mes = 9;
anio = 2026;
La fecha JavaScript almacenada en el estado debe ser la fuente de verdad.
2. Nuevo estado temporal
Agregar explícitamente los siguientes estados:

let tiempoCorriendo = true;
let direccionTiempo = -1;
let velocidadTiempo = 7;
Significado:

tiempoCorriendo: booleano. Indica si la fecha está avanzando automáticamente.
direccionTiempo: -1 significa viajar hacia el pasado y 1 significa viajar hacia el futuro.
velocidadTiempo: cantidad de días simulados que transcurren en cada tick.
Agregar también:

let intervaloTiempo = null;
para almacenar el identificador del temporizador.
Los estados deben ser independientes de su representación en el DOM.
3. Movimiento automático del tiempo
Al cargar la página, el selector debe comenzar automáticamente a viajar HACIA EL PASADO.
Usar un temporizador JavaScript.
Cada 250ms debe ocurrir un tick temporal.
En cada tick:

tick
→ modificar fecha según direccionTiempo y velocidadTiempo
→ actualizar dia, mes y anio
→ updateUI()
No calcular manualmente cambios entre meses.
Usar un objeto Date interno o una función equivalente que permita sumar o restar días correctamente y después copiar sus valores a:

dia
mes
anio
Esto debe manejar correctamente:

meses de 28, 29, 30 y 31 días;
cambio de mes;
cambio de año;
años bisiestos.
El límite mínimo continúa siendo el año 1900.
El sistema no debe viajar a una fecha posterior al día actual.
4. Representación astronómica del tiempo
El movimiento visual debe reflejar la fecha lógica.

Rotación terrestre
La Tierra debe rotar continuamente sobre su propio eje mientras tiempoCorriendo === true.
La animación debe ser visualmente continua.
No reiniciar bruscamente el transform en cada tick.
La rotación debe detenerse visualmente cuando tiempoCorriendo === false.
Debe reanudarse cuando el tiempo vuelve a correr.

Revolución alrededor del Sol
La posición de la Tierra alrededor del Sol ya no debe depender únicamente del número de mes.
Calcular una posición orbital aproximada a partir del día del año.
Conceptualmente:

día 1 del año → 0 grados
día 365/366 → aproximadamente 360 grados
La posición orbital debe actualizarse cuando cambia la fecha.
No busco precisión astronómica real.
Busco únicamente una representación visual coherente del paso del año.
La órbita sigue siendo circular y esquemática.
5. Meses
Mantener los nombres de los 12 meses alrededor de la órbita como referencias visuales.
PERO dejar de utilizarlos como botones.
Los meses ya no deben ser clickeables.
Deben ser solamente etiquetas.
El usuario no puede elegir directamente un mes.
El mes solo cambia cuando el tiempo en movimiento cruza de un mes a otro.
Esto es deliberado.
6. Visualización de la fecha
Mantener una única visualización destacada:

<p class="date-display">
    Fecha temporal actual:
    <strong id="date-output"></strong>
</p>
Mostrar:

DD / MES / AAAA
Ejemplo:

17 / MAYO / 1994
El texto debe actualizarse en cada tick.
Agregar debajo un texto secundario:

El tiempo está retrocediendo automáticamente.
Deténgalo exactamente en su fecha de nacimiento.
Este texto debe cambiar si se invierte la dirección temporal.
7. Control de velocidad
Agregar una nueva <section class="time-controls">.
Dentro agregar tres <button type="button">:

id="speed-slow" → "Lento — 1 día"
id="speed-medium" → "Rápido — 7 días"
id="speed-fast" → "Muy rápido — 30 días"
Eventos:

Lento
Al click:

velocidadTiempo = 1;
Rápido
Al click:

velocidadTiempo = 7;
Muy rápido
Al click:

velocidadTiempo = 30;
Después de cada cambio de velocidad llamar a:

updateUI();
Marcar visualmente cuál es la velocidad activa.
La velocidad inicial debe ser:

velocidadTiempo = 7;
Cambiar la velocidad NO debe pausar ni reiniciar el tiempo.
8. Invertir el sentido temporal
Agregar:

<button type="button" id="reverse-time">
    Invertir sentido temporal
</button>
Registrar un listener click.
Cuando se hace click:

direccionTiempo *= -1;
Luego:

updateUI();
Si:

direccionTiempo === -1
mostrar:

Dirección: HACIA EL PASADO
Si:

direccionTiempo === 1
mostrar:

Dirección: HACIA EL FUTURO
Este control existe para que el usuario pueda recuperarse si se pasa de su fecha de nacimiento.
No agregar botones "+1 día", "-1 día", "+1 año" ni "-1 año".
La única manera de corregir la fecha es invertir el flujo temporal y esperar.
9. Botón principal: detener el tiempo
Cambiar el texto del botón submit actual.
Debe decir exactamente:

Confirmar fecha (detener tiempo)
Mientras:

tiempoCorriendo === true
el sistema solar y la fecha continúan moviéndose.
Cuando el usuario hace click en el botón:

ejecutar preventDefault();
establecer:
tiempoCorriendo = false;
detener el temporizador;
congelar inmediatamente la animación orbital;
congelar inmediatamente la rotación visual de la Tierra;
conservar exactamente los valores actuales de:
dia
mes
anio
utilizar esos valores como fecha de nacimiento seleccionada;
validar el formulario;
mostrar el resumen final con nombre, apellido, email y fecha de nacimiento.
El botón de confirmación NO debe esperar a que termine una animación.
La metáfora es que el usuario está "deteniendo el tiempo" exactamente en ese instante.
10. Reinicio después de un error
Si falla la validación del formulario por nombre, apellido, email o una fecha inválida:

no perder la fecha seleccionada;
mostrar el error en el DOM;
agregar un botón:
Reanudar tiempo
Al hacer click:

tiempoCorriendo = true;
y volver a iniciar el temporizador desde la fecha actualmente seleccionada.
No recargar la página.
No reinicializar la fecha.
11. Renderizado
Refactorizar updateUI() para que sea la única función principal encargada de reflejar el estado en pantalla.
Debe representar:

dia
mes
anio
tiempoCorriendo
direccionTiempo
velocidadTiempo
Debe actualizar:

#date-output;
posición orbital de la Tierra;
estado visual de las etiquetas de mes;
texto de dirección temporal;
velocidad activa;
estado de los controles;
mensajes correspondientes.
Mantener explícitamente el ciclo:

evento / tick
→ mutación del estado
→ updateUI()
→ mutación del DOM
No leer la fecha desde el DOM para modificar el estado.
12. Layout de los controles
La nueva .time-controls debe ser un flex container.
Usar:

display: flex;
flex-wrap: wrap;
gap: var(--space-md);
justify-content: center;
Agrupar visualmente:

velocidades;
invertir tiempo;
información de dirección.
Mantener padding, bordes y border-radius usando las variables CSS existentes.
No cambiar la paleta.
No introducir estética espacial oscura, neon o de videojuego.
La página debe continuar pareciendo un formulario institucional serio con un mecanismo absurdamente inconveniente en el medio.
13. Estado detenido
Cuando:

tiempoCorriendo === false
la Tierra debe permanecer completamente inmóvil.
No debe continuar ninguna animación CSS aunque el JavaScript se haya detenido.
Cuando se reanuda:

tiempoCorriendo === true
la animación debe continuar desde la posición visual en la que estaba, sin saltos notorios.
Evitar crear múltiples setInterval simultáneos.
Crear funciones explícitas:

function iniciarTiempo()
function detenerTiempo()
iniciarTiempo() debe comprobar primero que no exista ya un intervalo activo.
detenerTiempo() debe hacer clearInterval() y establecer:

intervaloTiempo = null;
Esto debe evitar timers duplicados al detener y reanudar varias veces.
14. Constraints
Mantener:

un único archivo index.html;
CSS dentro de <style>;
JavaScript dentro de <script>;
Vanilla JavaScript;
sin frameworks;
sin librerías externas;
sin dependencias externas;
sin imágenes externas;
sin <canvas>;
HTML semántico cuando corresponda;
variables CSS existentes;
responsive layout;
funcionamiento mediante doble click sobre index.html.
No rehagas desde cero las partes que ya funcionan.
Refactorizá solamente lo necesario para reemplazar el selector manual de fecha por el sistema temporal continuo.
```

**Qué intentaba lograr:** reemplazar la selección manual de día, mes y año por una única mecánica coherente con la idea del sistema solar: un tiempo que transcurre continuamente. En vez de construir la fecha mediante controles separados, el usuario debía observar cómo la fecha retrocede automáticamente y detener el sistema exactamente en su fecha de nacimiento.

**Por qué está escrito así:** este prompt cambia el comportamiento central del artefacto sin reconstruir las partes que ya funcionaban. Por eso indiqué qué elementos debían eliminarse y cuáles debían conservarse. Introduje tres estados nuevos —tiempoCorriendo, direccionTiempo y velocidadTiempo— para separar claramente si el sistema está activo, hacia dónde se mueve y cuántos días avanza en cada tick.

También especifiqué iniciarTiempo() y detenerTiempo() porque detener y reanudar un setInterval puede generar timers duplicados si no se controla explícitamente. La regla de que intervaloTiempo vuelva a null después de detenerlo busca prevenir justamente ese bug.

La posición orbital pasó a depender del día del año y no solamente del mes para que el movimiento de la Tierra representara de manera continua el paso del tiempo. Los meses dejaron de ser botones y quedaron únicamente como referencias visuales. De esta manera, el DOM refleja el estado temporal pero ya no ofrece un atajo para modificarlo directamente.

**Qué devolvió:** un selector en movimiento continuo. La aplicación comienza en la fecha actual y retrocede automáticamente, la Tierra rota sobre su eje y cambia su posición alrededor del Sol a medida que transcurre el año. El usuario puede elegir entre distintas velocidades, invertir el sentido temporal si se pasa de la fecha buscada y detener el sistema mediante el botón “Confirmar fecha (detener tiempo)”.

---
## 4 — Iterar sobre el estado: revisión y corrección

```
Trabajá sobre el index.html actual.
NO reconstruyas la aplicación desde cero.
Conservá:

el formulario;
el selector astronómico;
el movimiento automático del tiempo;
los estados dia, mes, anio;
tiempoCorriendo, direccionTiempo y velocidadTiempo;
las funciones iniciarTiempo(), detenerTiempo() y updateUI();
la paleta y variables CSS;
el formato single-file;
todo el comportamiento que ya funciona.
El objetivo de esta iteración es agregar un PASO DE REVISIÓN antes de completar definitivamente el registro.
Quiero que el usuario pueda detectar que se equivocó en la fecha después de detener el tiempo y volver al formulario.
Pero, como se trata de una bad UI, si decide corregir cualquier dato deberá volver a completar TODO el formulario desde cero.
1. Nuevo estado paso
Agregar un estado:

let paso = "formulario";
Debe poder tomar tres valores:

"formulario"
"revision"
"confirmado"
Significado:

formulario
Se muestra:

nombre;
apellido;
correo electrónico;
selector astronómico;
tiempo en movimiento;
botón "Confirmar fecha (detener tiempo)".
revision
El tiempo está detenido.
El formulario y el selector astronómico deben ocultarse.
Mostrar una sección de revisión con todos los datos ingresados.

confirmado
Mostrar el mensaje final de registro completado.
El formulario y la revisión deben permanecer ocultos.
paso debe ser la fuente de verdad para determinar qué sección aparece en el DOM.
2. Modificar el botón actual
El botón:

Confirmar fecha (detener tiempo)
NO debe completar definitivamente el registro.
Cuando se hace submit:

ejecutar preventDefault();
validar nombre, apellido y email;
establecer:
tiempoCorriendo = false;
ejecutar:
detenerTiempo();
conservar exactamente la fecha temporal existente en ese instante;
guardar los datos del formulario en un estado:
let datosUsuario = {
    nombre: "",
    apellido: "",
    email: ""
};
copiar allí los valores ingresados;
establecer:
paso = "revision";
ejecutar:
updateUI();
No borrar todavía ningún dato.
3. Nueva sección de revisión
Agregar dentro de <main> una nueva:

<section id="revision-section">
Debe estar oculta cuando paso !== "revision".
Debe mostrar claramente:

Revise sus datos antes de continuar

Nombre: ...
Apellido: ...
Correo electrónico: ...
Fecha de nacimiento: DD / MES / AAAA
Agregar también un texto secundario:

Verifique especialmente la fecha seleccionada antes de confirmar el registro.
Debajo agregar dos botones:

<button type="button" id="confirm-final">
    Confirmar definitivamente
</button>

<button type="button" id="edit-data">
    Volver y corregir datos
</button>
Usar elementos semánticos y conservar la estética institucional existente.
4. Confirmación definitiva
Registrar un listener click sobre:

<button id="confirm-final">
Cuando se hace click:

paso = "confirmado";
Luego:

updateUI();
Mostrar una sección final con:

Registro completado correctamente
y un resumen de:

nombre;
apellido;
correo electrónico;
fecha de nacimiento.
No permitir volver atrás desde este estado.
5. Corregir datos
Registrar un listener click sobre:

<button id="edit-data">
Esta transición debe ser deliberadamente frustrante.
Cuando el usuario decide corregir los datos, NO conservar ninguno de los valores anteriores.
Ejecutar, en este orden:

vaciar el campo nombre;
vaciar el campo apellido;
vaciar el campo email;
vaciar el objeto datosUsuario;
reinicializar dia, mes y anio con la fecha actual real;
establecer:
direccionTiempo = -1;
conservar la velocidad temporal actual o restaurarla a:
velocidadTiempo = 7;
establecer:
paso = "formulario";
establecer:
tiempoCorriendo = true;
volver a iniciar el flujo temporal mediante:
iniciarTiempo();
ejecutar:
updateUI();
Por lo tanto, aunque el usuario solamente haya cometido un error en la fecha de nacimiento, deberá volver a ingresar:

nombre;
apellido;
correo electrónico;
fecha de nacimiento completa.
Esta pérdida de información es deliberada y forma parte de la bad UI.
6. Mensaje al volver
Cuando el usuario vuelve desde la pantalla de revisión al formulario, mostrar temporalmente dentro del DOM un mensaje:

Por motivos de seguridad, todos los datos anteriores fueron descartados. Complete nuevamente el formulario.
No usar alert().
El mensaje puede desaparecer después de algunos segundos.
7. Renderizado según paso
Refactorizar updateUI() para que además de los estados actuales tome en cuenta:

paso
Debe controlar la visibilidad de:

formulario
revision-section
confirmed-section
Comportamiento esperado:

paso === "formulario"
→ mostrar formulario
→ ocultar revisión
→ ocultar confirmado
paso === "revision"
→ ocultar formulario
→ mostrar revisión
→ ocultar confirmado
paso === "confirmado"
→ ocultar formulario
→ ocultar revisión
→ mostrar confirmado
No determinar el paso observando qué elementos tienen display: none.
El estado paso es la fuente de verdad.
8. Ciclo de estados esperado
La aplicación debe seguir este flujo:

FORMULARIO
tiempo corriendo
        ↓
click "Confirmar fecha (detener tiempo)"
        ↓
detener tiempo
guardar datos
        ↓
REVISIÓN
        ↓
 ┌─────────────────────┐
 │                     │
confirmar          corregir
 │                     │
 ↓                     ↓
CONFIRMADO        borrar TODO
                  reiniciar fecha
                  reiniciar tiempo
                       ↓
                  FORMULARIO
No debe existir una transición directa desde revision a formulario que conserve los datos anteriores.
9. Layout
La sección de revisión debe conservar la estética institucional.
Usar:

fondo var(--color-surface);
borde 1px solid var(--color-border);
padding: var(--space-lg);
border-radius: var(--radius);
max-width: 700px.
Para los botones de revisión usar un flex container:

display: flex;
gap: var(--space-md);
flex-wrap: wrap;
"Confirmar definitivamente" debe utilizar el color de acento principal.
"Volver y corregir datos" debe verse como una acción secundaria.
No modificar la paleta general.
10. Constraints
Mantener:

un único archivo index.html;
HTML, CSS y JavaScript dentro del mismo archivo;
Vanilla JavaScript;
sin frameworks;
sin librerías externas;
sin dependencias;
sin imágenes externas;
sin <canvas>;
HTML semántico;
variables CSS existentes;
responsive layout;
funcionamiento mediante doble click sobre index.html.
No reescribir componentes que ya funcionan.
Agregar únicamente el nuevo flujo de revisión, confirmación y corrección sobre la implementación existente.
```
**Qué intentaba lograr:** agregar una etapa de revisión antes de completar definitivamente el registro. Hasta esta iteración, detener el tiempo equivalía prácticamente a confirmar la fecha. Quería que el usuario tuviera una última oportunidad de detectar un error, pero sin hacer que la interfaz dejara de ser una bad UI. Por eso decidí que pudiera volver atrás, aunque a cambio perdiera todos los datos ingresados y tuviera que comenzar nuevamente desde cero.

**Qué devolvió:** una versión con tres etapas claramente diferenciadas. Al presionar “Confirmar fecha (detener tiempo)”, el tiempo se detiene y aparece una pantalla de revisión con los datos ingresados y la fecha seleccionada. Desde allí se puede confirmar definitivamente el registro o volver para corregirlo. Si se elige corregir, se descartan los datos personales y la fecha, el sistema vuelve a la fecha actual y el tiempo comienza nuevamente hacia el pasado. De esta forma la corrección sigue siendo posible, pero deliberadamente costosa para el usuario.


## Conversación completa

Una sola conversación de Gemini, sin reiniciar el hilo. El artefacto final tiene 815 líneas en un archivo.
