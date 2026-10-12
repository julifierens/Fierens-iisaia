# TP 2 — API de SPTERO Web

Un `openapi.yaml` que describe la API de SPTERO Web, la versión web de SPTERO, un programa en Python que desarrollé para procesar ensayos Small Punch Test (SPT). La API permite cargar ensayos, consultarlos, graficar la curva carga–desplazamiento, procesarla para obtener Pm, dm y Rm, y borrarlos. No hay nada implementado: el entregable es el contrato.

## Cómo se lee

Pegar el contenido de [openapi.yaml](openapi.yaml) en [editor.swagger.io](https://editor.swagger.io) o en Swagger Editor Next.

## Qué me propuse construir

Un contrato chico que me sirviera como base del trabajo final. Partí del programa original y de un mockup de la aplicación web. Del programa tomé solo el flujo de probeta lisa y los resultados que muestra el mockup: carga máxima Pm, desplazamiento a carga máxima dm y resistencia estimada Rm = β·Pm/(dm·t).

Hay dos recursos: el **ensayo** (el archivo original y los datos de la probeta) y su **resultado**. El resultado vive adentro del ensayo, en `/tests/{testId}/result`, igual que la curva y el archivo original.

```
POST   /tests                   cargar ensayo (multipart)          201 · 400
GET    /tests                   historial                           200
GET    /tests/{testId}          detalle                             200 · 404
DELETE /tests/{testId}          borrar ensayo, archivo y resultado  204 · 404
GET    /tests/{testId}/file     descargar el archivo original       200 · 404
GET    /tests/{testId}/curve    curva (?source=raw|processed)       200 · 400 · 404
PUT    /tests/{testId}/result   procesar / reprocesar               200 · 400 · 404 · 422
GET    /tests/{testId}/result   consultar resultado                 200 · 404
```

Para el trabajo final quiero reutilizar las funciones de cálculo de SPTERO, no reescribirlas. Por eso el contrato describe la entrada y el procesamiento tal como los resuelven esas funciones (`cargar_raw_a_listas`, `corregir_desplazamiento_por_flexibilidad_A1`, `cero_automatico_por_precarga`, `max_load_and_dm` y `rm_from_beta`).

## Decisiones que tomé yo

**Un único resultado por ensayo, que se reemplaza al reprocesar.** Al principio el modelo me propuso varios análisis por ensayo, uno por cada combinación de parámetros. Lo descarté: para SPTERO Web me alcanza con el último procesamiento, y guardar versiones agrega identificadores y endpoints que no necesito. Como consecuencia, el resultado es un subrecurso singular, sin id propio.

**Procesar con `PUT` y que sea idempotente.** Esto lo propuso el modelo y lo acepté. Como hay un solo resultado y reprocesar lo reemplaza, `PUT /tests/{testId}/result` describe exactamente eso. El `POST` que pide la consigna queda en la carga de ensayos. Para que la idempotencia sea real, el contrato fija dos reglas. Un campo que no se manda toma su valor por defecto y no el del resultado anterior. Y si los parámetros son iguales a los vigentes, el resultado no cambia, ni siquiera la fecha de procesamiento.

**Espesor y material son datos del ensayo, no del procesamiento.** El espesor es una propiedad física de la probeta. Si fuera un parámetro del procesamiento, se podría calcular Rm con un espesor distinto del que tiene la probeta. El costo es que no hay forma de editar un ensayo: si cargo mal el espesor, tengo que borrarlo y volver a subirlo. El archivo real confirmó que el espesor no se puede sacar del encabezado: ahí dice `Thickness: 0.06 in`, que es un valor de la plantilla de la máquina y no el de la probeta.

**Cero por precarga siempre, con F0 = 5 N.** No es un parámetro del pedido. Se toma como contacto el primer punto con carga mayor o igual a 5 N y ahí el desplazamiento pasa a ser 0. Esto es un cambio respecto del programa original, que solo aplica el cero cuando se corrige la flexibilidad. Las funciones se reutilizan sin cambios; lo que cambia es en qué orden las llama la API.

**Compliance opcional, solo con C_P manual.** Por defecto el procesamiento no corrige (`apply_compliance_correction: false`), y el C_P por defecto es 2.281e-4 mm/N. Dejé afuera los métodos numérico y experimental del programa original para obtener C_P. β también se puede configurar, con 0.277 por defecto.

**El resultado guarda con qué parámetros se calculó.** Si reprocesar pisa el resultado anterior, un Rm sin su β y su C_P no se puede interpretar después.

**La curva se puede pedir cruda o procesada (`?source=raw|processed`).** Si se aplica la corrección por C_P, dm queda en las coordenadas de la curva corregida. Si el frontend marcara Pm sobre la curva cruda, el punto quedaría corrido.

**Conservar y poder descargar el archivo original.** Quiero que los ensayos queden almacenados y se puedan recuperar desde la web, no solo sus resultados.

**400, 404 y 422 separados.** 400 cuando el pedido está mal (falta un campo, un número no es positivo, el archivo no tiene el formato esperado). 404 cuando el ensayo no existe. 422 cuando el pedido está bien pero la curva no permite calcular Rm. El cuerpo del error trae un `code` para distinguir los dos casos de 404 en el resultado: ensayo inexistente (`TEST_NOT_FOUND`) o ensayo sin procesar (`RESULT_NOT_FOUND`).

**Nombres en inglés, documentación en español.**

Estas propuestas del modelo las acepté sin cambios:
- el resultado viaja adentro de cada ensayo en el historial (`result`, o `null`), para que la tabla del mockup salga de una sola llamada;
- las unidades van en el nombre de los campos (`thickness_mm`, `pm_n`, `rm_mpa`);
- la curva se manda como dos arreglos paralelos y no como una lista de puntos;
- los ids son enteros.

**Alcance que dejé afuera:** probetas entalladas, Py por MAO y t/10, Fe según UNE, ESP y εf, cálculo de C_P, el reporte PDF, editar ensayos y filtrar el historial.

## Qué salió mal y cómo lo corregí

**Diseñé la entrada para un formato que no conocía.** Pedí trabajar con CSV sin darme cuenta de que el programa original y mi propio mockup usan `.raw`. El modelo marcó la inconsistencia en la primera respuesta, pero yo seguí con CSV y dejé el formato como "provisorio". Cuando lo comparé con un archivo real de la máquina (`P3_304L_L.raw`), resultó que el `.raw` ya es texto separado por `;`. Tiene unas 40 líneas de metadatos arriba y después la tabla, con las columnas `"Extension mm"` y `"Load N"`, punto decimal y valores negativos, porque la máquina registra la compresión con signo negativo. Un "CSV limpio" no existe como export de la máquina, y si la API hubiera exigido uno, no habría podido reutilizar `cargar_raw_a_listas`. Corregí el contrato: ahora acepta el archivo como sale de la máquina (`.raw` o `.csv`), lo valida por contenido con las mismas reglas que el lector de SPTERO y describe el formato exacto.

**La curva "cruda" no era cruda.** El contrato decía que `source=raw` devolvía la curva leída del archivo. Pero `cargar_raw_a_listas` invierte el signo y ordena por desplazamiento, así que lo que devuelve no es literalmente lo que está en el archivo. Lo aclaré en la descripción, y el archivo sin ninguna transformación queda disponible en `GET /tests/{testId}/file`.

**Un ejemplo de error que contradecía al programa.** El modelo puso como ejemplo de 422 "la carga nunca llega a 5 N". Al revisar `cero_automatico_por_precarga` vi que en ese caso la función no falla: deja la curva como está. El contrato prometía un error que la función reutilizada nunca iba a producir. Lo corregí: el 422 queda solo para el caso en que `rm_from_beta` no puede calcular (dm ≤ 0), y el comportamiento sin contacto quedó documentado en el paso 3 del procesamiento.

**Me olvidé del cero por precarga.** Al definir el alcance describí la corrección por compliance y el cálculo de Rm, pero no el paso intermedio que hace el programa original. El modelo lo detectó antes de escribir el contrato. En el archivo real el primer punto ya marca 9,3 N, así que el cero no cambia nada en ese ensayo. Igual lo dejo, porque no puedo garantizar que todos los archivos arranquen en contacto.

**La curva y el resultado en coordenadas distintas.** Con mi planteo original la curva del ensayo era solo la cruda. Combinada con la corrección por C_P, eso hacía que el marcador de Pm del mockup no coincidiera con la curva. Lo resolví con el parámetro `source`.

## Validación

**Contra el archivo real.** Corrí las funciones de SPTERO sobre `P3_304L_L.raw`, en el mismo orden que describe el `PUT`, con t = 0,5 mm y β = 0,277. El lector devolvió 582 puntos.

| | Pm [N] | dm [mm] | Rm [MPa] |
|---|---|---|---|
| sin corrección | 2372,2 | 2,2709 | 578,7 |
| con C_P = 2.281e-4 mm/N | 2372,2 | 1,7319 | 758,8 |

La fila sin corrección coincide con los valores del mockup (2372 N, 2,271 mm, 579 MPa). Eso confirma que el contrato se puede cumplir llamando a las funciones existentes. La segunda fila muestra por qué el resultado tiene que guardar si se corrigió y con qué C_P: el mismo ensayo da un Rm un 31 % más alto.

**En Swagger, versión inicial.** La primera versión del contrato, la que se generó en el prompt 3, la validé en dos editores. El editor original de Swagger mostró errores al resolver las referencias a los schemas `Test` y `TestUpload`. En Swagger Editor Next, el mismo archivo abrió sin errores y esas referencias se interpretaron correctamente. No investigué por qué el editor original no las resolvía, así que no le atribuyo ninguna causa.

**En Swagger, versión final.** El contrato cambió después de esa validación, en el prompt 4. Cambiaron las descripciones del formato de entrada, del procesamiento, de `source=raw` y del 422, los ejemplos de `Test`, y se sacó `contentMediaType` del campo `file` de `TestUpload`. No cambió ningún path, method, status code ni referencia. Validé esta versión final en Swagger Editor Next y no marcó errores.

**Contra la consigna.**

| requisito | dónde se cumple |
|---|---|
| `GET`, `POST` y `DELETE` | `GET /tests`, `POST /tests`, `DELETE /tests/{testId}` (además hay un `PUT`) |
| jerarquía en el path | `/tests/{testId}/result`, `/tests/{testId}/curve`, `/tests/{testId}/file` |
| al menos un 400 o 404 | 400 en `POST /tests`; 404 en todos los endpoints con `{testId}`; además 422 |
| schemas tipados | `type` y `required` en todos los schemas; `format` en `int64`, `double`, `date-time` y `binary` |
| una sola conversación de IA | los seis prompts de [prompts.md](prompts.md) son de la misma sesión de Claude Code |
| entregables | `openapi.yaml`, `prompts.md` y `README.md` en la carpeta `TP2/` |
| informe | qué API elegí, qué decidí yo, qué salió mal y cómo lo corregí, prompts |

## Notas para el trabajo final

Al correr las funciones de SPTERO fuera del programa aparecieron tres cosas que el backend va a tener que resolver:

- **El módulo importa `tkinter`, `matplotlib` y `reportlab` al principio.** Para usar solo las funciones de cálculo, habría que separarlas en un módulo propio. Si no, el servidor tiene que instalar dependencias de interfaz gráfica que no usa.
- **`cargar_raw_a_listas` hace `print` con emojis.** En una consola de Windows con codificación cp1252 eso tira `UnicodeEncodeError` y corta la lectura. En la verificación lo esquivé corriendo Python en modo UTF-8. En el backend esos mensajes tendrían que pasar a ser logs o desaparecer.
- **El lector recibe una ruta, no los bytes del archivo.** Encaja con guardar el archivo original en disco, que ya era una decisión del contrato.

## Prompts

El registro completo está en [prompts.md](prompts.md). El que más pesó fue el segundo, que fijó el alcance, porque la respuesta del modelo a ese prompt detectó el cero por precarga y el problema de coordenadas. El cuarto fue el que contrastó el contrato con un archivo real y obligó a reescribir la descripción de la entrada. El quinto y el sexto cierran la documentación y la entrega.
