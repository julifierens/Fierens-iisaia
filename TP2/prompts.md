# Prompts — TP 2

El registro del proceso, en orden: seis prompts en una sola conversación con Claude Code. Los prompts están copiados textualmente. "Qué buscaba" lo escribo yo; "Qué devolvió" resume la respuesta del modelo.

---

## 1 — Prompt inicial

Adjuntos: `index_sptero_mockup.html` (mockup de SPTERO Web) y `Programa SPTERO.py` (el programa original).

```
Vamos a realizar el TP2 de IISAIA. Revisá la consigna del repositorio oficial de la materia.

Quiero diseñar una API REST para SPTERO, un programa que desarrollé en Python para procesar ensayos Small Punch Test.

Te adjunto el código original y un mockup HTML de la futura aplicación web.

La idea es poder subir archivos CSV de los ensayos, almacenarlos para consultarlos posteriormente, visualizar las curvas carga-desplazamiento y obtener los resultados del procesamiento.

Quiero que el TP2 sea sencillo, pero que nos sirva como base para el trabajo final.

Revisá los archivos, proponeme qué recursos y endpoints conviene utilizar y ayudame a definir el alcance.

Sigamos la metodología del profesor, registrando los prompts y las decisiones tomadas.

Por ahora no generes código ni modifiques archivos. Primero discutamos el diseño.
```

**Qué buscaba:** Definir una API para SPTERO que cumpla la consigna y pueda reutilizarse en el trabajo final.

**Qué devolvió:** Leyó la consigna oficial (`semanas/03/source_material/09-trabajo-practico-2.md`) y el ejemplo resuelto de la cátedra. Señaló una inconsistencia en mi pedido: yo hablaba de CSV, pero el programa y el mockup usan archivos `.raw`. Propuso separar el ensayo (datos fijos) del análisis (cálculo con parámetros), con varios análisis por ensayo bajo `/ensayos/{ensayoId}/analisis`. Sugirió limitar el alcance a probetas lisas con Pm, dm y Rm, y dejar afuera MAO, t/10, Fe, ESP, probetas entalladas y el PDF. Listó siete decisiones abiertas para mí: dónde va el espesor, guardar vs. descartar, curva cruda vs. corregida, material como recurso o como campo, borrado en cascada, 400 vs. 422 e idioma de los nombres.

---

## 2 — Definir el alcance

```
Ok, vamos a definir prácticamente todo el alcance para avanzar con el TP2.

Me parece bien trabajar con dos recursos: ensayos y resultados. Cada ensayo tendrá su archivo CSV original, sus datos y un único resultado asociado. Si se vuelve a procesar, se actualiza ese resultado, sin guardar distintas versiones.

Quiero que la API permita cargar y almacenar ensayos, consultar el historial, visualizar las curvas, procesar los datos, consultar los resultados y eliminar ensayos.

Por ahora trabajemos solamente con probetas lisas. Los resultados principales serán Pm, dm y Rm. Dejamos los demás cálculos de SPTERO para futuras ampliaciones.

Sobre el procesamiento, la corrección por compliance será opcional y exclusivamente mediante un valor de C_P ingresado manualmente, con el valor predeterminado de 2.281e-4 mm/N. No vamos a implementar los métodos numérico ni experimental para obtener C_P. Para Rm usamos β configurable, con valor predeterminado 0.277.

El espesor y el material serán datos del ensayo. Conservamos siempre el CSV original, aunque se procese la curva.

Utilicemos endpoints e identificadores en inglés y documentación en español.

Sobre el formato, vamos a trabajar con archivos .csv. El programa original utiliza .raw, así que habrá que verificar la compatibilidad con un CSV real antes de implementar el backend.

Proponé ahora el contrato completo: endpoints, campos obligatorios y opcionales, schemas, códigos HTTP y errores.

Quiero que el diseño sea sencillo, que cumpla la consigna y que nos sirva para SPTERO Web.

Si encontrás algún problema técnico con estas decisiones, explicámelo antes de modificarlas. Todavía no generes el YAML.
```

**Qué buscaba:** Acotar el alcance y establecer los recursos, parámetros y funcionalidades.

**Qué devolvió:** Antes de proponer el contrato señaló dos problemas técnicos en mi alcance. El primero: yo no había incluido el cero por precarga del programa original, y sin él dm arrastra el recorrido previo al contacto y Rm sale subestimado. El segundo: si se aplica la corrección por C_P, el dm del resultado queda en coordenadas de la curva corregida, así que marcar Pm sobre la curva cruda lo deja corrido. Propuso `?source=raw|processed` para la curva y `PUT` (idempotente) para procesar. También propuso guardar en el resultado los parámetros con que se calculó y distinguir con un campo `code` los dos casos de 404 en `GET /result`. Propuso siete endpoints bajo `/tests`, los schemas `Test`, `Result`, `ProcessingParameters`, `Curve` y `Error`, y separar 400 (pedido inválido) de 422 (datos que no permiten calcular). Me dejó tres decisiones abiertas: el cero por precarga, el parámetro `source` y 400 vs. 422.

---

## 3 — Cerrar decisiones y generar el contrato

```
Ok, me parece bien el contrato. Vamos a cerrar las decisiones para avanzar.

El cero por precarga lo aplicaría siempre, con F0 = 5 N. La corrección por compliance será opcional, utilizando únicamente el C_P ingresado manualmente, con el valor predeterminado de 2.281e-4 mm/N.

Me gusta poder consultar tanto la curva original como la procesada mediante source=raw|processed. También mantendría separados los errores 400, 404 y 422.

Agregaría un endpoint para descargar el CSV original, porque quiero que los ensayos queden almacenados y puedan recuperarse desde la web.

El resto de los endpoints y schemas me parece bien. Un solo resultado por ensayo, que se reemplaza si volvemos a procesarlo. Cuidemos que el PUT sea idempotente.

Para el TP2 trabajemos con CSV, dejando pendiente verificar los encabezados y separadores exactos con un archivo real.

Utilicemos la carpeta TP2, como en el TP1.

Con esto, avancemos a generar el contrato OpenAPI y los archivos de documentación. Recordá registrar los prompts textuales de esta conversación, sin inventar decisiones ni errores.

Después quiero que validemos el YAML y revisemos si realmente cumple con la consigna.
```

**Qué buscaba:** Cerrar las decisiones técnicas y generar el contrato OpenAPI.

**Qué devolvió:** Generó `openapi.yaml` (OpenAPI 3.1, ocho endpoints), este `prompts.md` y un borrador de `README.md`. El endpoint de descarga lo nombró `GET /tests/{testId}/file`. Para cumplir con que el `PUT` sea idempotente, agregó dos reglas que yo no había escrito explícitamente: los campos que no se mandan toman su valor por defecto (no el del resultado anterior), y si los parámetros coinciden con los vigentes el resultado no se modifica, ni siquiera `processed_at`. Las marcó para que yo las revisara. Para validar me propuso dos caminos: instalar `openapi-spec-validator` o pegar el YAML en editor.swagger.io, y avisó que no sabía si `format: binary` junto con `contentMediaType` iba a mostrar bien el selector de archivo.

---

## 4 — Contrastar con un archivo real y cerrar el TP

Adjunto: `P3_304L_L.raw` (archivo real de la máquina de ensayos SPT).

```
Listo, validé el OpenAPI en Swagger Editor Next y no aparecen errores.

Te adjunto un .raw real de la máquina de ensayos SPT. Quiero que lo compares con el programa Python que te pasé y revises si el contrato contempla correctamente el formato de entrada. Si hace falta modificar algo, hacelo.

Recordá que para el trabajo final queremos reutilizar las funciones de procesamiento de SPTERO, no desarrollar los cálculos nuevamente.

Después terminemos el TP2: revisá el openapi.yaml, completá prompts.md y README.md siguiendo la consigna del profesor y documentá la validación que hicimos en Swagger, incluyendo los errores de referencias que aparecieron en el editor anterior.

Verificá que los archivos estén en TP2 y que estemos trabajando en una rama específica, sin modificar el TP1.

Mostrame un resumen final de los cambios y dejá todo preparado para entregar. No hagas commit ni push todavía.
```

**Qué buscaba:** Verificar el contrato con datos experimentales reales y corregir las incompatibilidades.

**Qué devolvió:** Leyó el archivo real. Es texto separado por `;`, con unas 40 líneas de metadatos, la fila de encabezado `"Time sec";"Extension mm";"Load N";...`, punto decimal y valores negativos. Corrió las funciones de SPTERO sobre el archivo: 582 puntos, y sin corrección Pm = 2372,2 N, dm = 2,2709 mm y Rm = 578,7 MPa, que coinciden con el mockup. Con C_P = 2.281e-4 dio dm = 1,7319 mm y Rm = 758,8 MPa. Al correrlas, `cargar_raw_a_listas` falló con `UnicodeEncodeError` por un `print` con emoji en la consola de Windows, y hubo que usar Python en modo UTF-8. Cambios en el contrato:
- describe el formato real y acepta `.raw` o `.csv`, validando por contenido;
- aclara que `source=raw` devuelve la curva con el signo invertido y ordenada;
- enumera los pasos del procesamiento con las funciones que se reutilizan;
- corrige el ejemplo del 422, que contradecía a `cero_automatico_por_precarga`;
- saca `contentMediaType: text/csv` del campo `file`.

También creó la rama `feature/tp2-contrato-openapi` y completó el README. No conocía los errores de referencias del primer editor, así que dejó esa parte pendiente en lugar de inventarla.

---

## 5 — Cerrar la documentación

```
Listo, cerremos el TP2.
Revisé los archivos y me parecen bien. Para completar el prompts.md, en "Qué buscaba" pondría:

1. Definir una API para SPTERO que cumpla la consigna y pueda reutilizarse en el trabajo final.
2. Acotar el alcance y establecer los recursos, parámetros y funcionalidades.
3. Cerrar las decisiones técnicas y generar el contrato OpenAPI.
4. Verificar el contrato con datos experimentales reales y corregir las incompatibilidades.

Sobre Swagger, el editor original mostró errores al resolver las referencias a los schemas Test y TestUpload. Al utilizar Swagger Editor Next, esas referencias se interpretaron correctamente.
Revisá que el README refleje esto sin atribuir una causa que no hayamos comprobado. También quiero que distingas la validación inicial de la última versión del YAML.
Completá la documentación, agregá los enlaces a TP1 y TP2 en el README principal y realizá una revisión final contra la consigna.
No modifiques el TP1. Mostrame el resultado antes de hacer commit y push.
```

**Qué buscaba:** Completar la documentación, registrar los problemas encontrados y verificar que cumplamos con la consigna antes de entregar.

**Qué devolvió:** Completó "Qué buscaba" de los prompts 1 a 4 con mis textos. En el README separó dos validaciones: la de la versión inicial (errores de referencias a `Test` y `TestUpload` en el editor original, sin errores en Swagger Editor Next, sin atribuir causa) y la de la versión final. Para la final listó qué cambió desde la validación anterior y dejó pendiente el resultado, porque esa versión todavía no se había validado en Swagger. Agregó a la tabla de la consigna la conversación única, los entregables y el informe, y sumó los enlaces a TP1 y TP2 en el README principal.

---

## 6 — Commit, push y pull request

```
Listo, validé la versión final del OpenAPI en Swagger Editor Next y no aparecen errores.

Para el prompt 5, en "Qué buscaba" pondría: completar la documentación, registrar los problemas encontrados y verificar que cumplamos con la consigna antes de entregar.

Con esto, terminemos el TP2. Completá lo pendiente del README y prompts.md, verificá que todo esté correcto y hacé el commit.

Después subí la rama a GitHub y prepará el pull request para integrarla a main. No modifiques el TP1.

Mostrame el resultado antes de hacer el merge.
```

**Qué buscaba:** Cerrar la entrega: dejar la documentación sin pendientes, hacer el commit, subir la rama y preparar el pull request a `main`.

**Qué devolvió:** Registró en el README la validación de la versión final y completó "Qué buscaba" del prompt 5. Hizo el commit en `feature/tp2-contrato-openapi` y subió la rama. Como `gh` no está instalado, no pudo abrir el pull request: dejó preparados el enlace y la descripción para abrirlo desde GitHub. El merge quedó para después de mi revisión.
