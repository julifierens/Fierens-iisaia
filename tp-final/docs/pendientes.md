# Hallazgos pendientes

Observaciones de las revisiones que no se corrigieron en la etapa donde
aparecieron. Cada una indica de dónde sale y cuándo conviene resolverla. Cuando
se resuelve, se tacha o se borra en el mismo commit que la corrige.

## Etapa 2 — motor científico (revisiones del 12/10/2026)

Resueltos antes del PR, para referencia:

- ~~`leer_raw` dejaba escapar `csv.Error` con un `.raw` dañado~~: ahora lanza
  `ValueError` (test `test_archivo_corrupto`).
- ~~El docstring de `analisis.py` decía que todos los valores por defecto eran los
  del original~~: ahora aclara que `aplicar_correccion = False` no lo es (ver README).
- ~~La spec §4 no registraba esa diferencia de default~~: agregada.

### Para la etapa 3 (API)

1. ~~**Espesor no finito.** Con `thickness_mm` = NaN, `rm_from_beta` no lo rechaza
   (`nan <= 0` es falso) y devuelve Rm = NaN sin error. La spec (§8) solo pide
   rechazar espesores ≤ 0. La API tiene que rechazar también NaN e infinito con
   400 `INVALID_PARAMETERS`; el core no se toca.~~ Resuelto en la etapa 3: todas
   las entradas numéricas de la API usan `allow_inf_nan=False` (tests
   `test_post_espesor_no_finito`, `test_patch_espesor_infinito`,
   `test_put_beta_infinito`).
2. **Mensaje de Rm con t ≤ 0.** `analizar` informa "dm tiene que ser mayor que
   cero" también cuando el problema es el espesor (`rm_from_beta` devuelve `None`
   en los dos casos). La API rechaza t ≤ 0 antes de llamar al core, así que en la
   web no se ve; si se quiere el mensaje correcto igual, es un cambio de una línea
   en `analisis.py`, sin tocar fórmulas.

### Tests que se podrían reforzar

3. **Caracterización con otro `.raw`.** `test_pipeline_igual_al_original` da por
   hecho que hay cruce t/10: con un archivo sin cruce fallaría con `TypeError` en
   vez de un fallo de comparación claro. Con `P3_304L_L.raw` no pasa.
4. **Lectura (`test_raw.py`):** falta un caso con solo x negativa, uno con filas no
   numéricas que se descartan, y `test_encabezado_cp1252` solo cuenta puntos.
5. **Cálculos (`test_calculos.py`):** sin test de la rama `"mao"` de
   `sigma_y_from_py`, del método inválido, de la regresión con menos de 2 puntos,
   de `shift_force=True` ni de curvas con menos de 3 puntos. Son copias textuales
   cubiertas por la comparación de AST con el original.
6. **Caracterización (`test_caracterizacion.py`):** el caso con corrección usa el
   C_P por defecto del core en lugar de pasarlo explícito, y los valores de
   referencia se comparan con `==` sobre números redondeados.

## Etapa 3 — API (revisiones del 12/10/2026)

Resueltos antes del PR, para referencia:

- ~~Un `testId` mayor que 2^63−1 daba 500 (`OverflowError` de sqlite3)~~: ahora
  responde 400 `INVALID_PARAMETERS` (`test_id_fuera_de_int64`).
- ~~Los mensajes de validación salían en inglés (los armaba Pydantic)~~: se
  traducen por tipo de error.
- ~~Un espesor como 1e-170 hacía fallar al core con `ZeroDivisionError` (500), y
  β = 1e308 guardaba Rm infinito~~: ahora es 422 `PROCESSING_FAILED`.
- ~~`{"thickness_mm": true}` se guardaba como 1 mm~~: los cuerpos JSON validan
  tipos en modo estricto.
- ~~Un `DELETE` entre dos lecturas del mismo pedido daba 500~~: `archivo()` hace
  una sola consulta.

### ~~Decisión pendiente antes de la etapa 4~~ Resuelta antes del PR

Julián eligió la primera opción: `PATCH` y `PUT` se serializan con
`BEGIN IMMEDIATE` (`repository.transaccion`, tests en
`tests/test_concurrencia.py`). Si la espera del lock (5 s) se vence, el pedido
termina en 500 con el formato por defecto de Starlette y sin guardar nada (ver
punto 7). El análisis original queda abajo como referencia.

1. **Pedidos concurrentes sobre el mismo ensayo (resuelto).** `PATCH` y `PUT` leen el ensayo,
   calculan y después escriben; la lectura queda fuera de la transacción de
   escritura. Si un `PUT` con otros parámetros llega mientras corre un `PATCH`,
   el `PUT` responde 200 con sus parámetros pero lo guardado termina con los del
   `PATCH` (lo reprodujo la revisión final con dos conexiones intercaladas). No
   rompe la atomicidad que pide la spec: si el recálculo falla, no cambia nada.
   Con el guardado automático (D4), la interfaz puede mandar los dos pedidos
   seguidos. Opciones:
   - Hacer lectura, cálculo y escritura dentro de `BEGIN IMMEDIATE`. Obliga a
     reorganizar las transacciones del repositorio, porque hoy cada escritura hace
     su propio `with con:`.
   - Que la interfaz no mande un pedido nuevo sobre un ensayo hasta que termine el
     anterior (ya está previsto: primero `PATCH`, después `PUT`), y documentarlo.

### Decisiones de contrato o de dependencias

2. **Campos desconocidos en el cuerpo.** `PATCH {"thickness_mm": 0.4, "material": "X"}`
   responde 200 e ignora `material`; un `PUT` con `{"bta": 0.3}` reprocesa con los
   valores por defecto. Rechazarlos (`extra="forbid"`) equivale a
   `additionalProperties: false`: es un cambio de contrato.
3. **`material` con solo espacios o con caracteres de control** se acepta. La spec
   habla de "falta `material`"; se puede recortar o validar con un `pattern`.
4. **`/docs` de FastAPI anuncia un 422 `HTTPValidationError`** en rutas que en
   realidad responden 400. El contrato es `openapi.yaml`; una opción es servirlo
   como esquema de la app.
5. **Aviso de deprecación en los tests.** Starlette avisa que `TestClient` con
   `httpx` está deprecado y sugiere `httpx2`. Se dejó visible: cambiar la
   dependencia o silenciar el aviso es una decisión aparte.
6. ~~**Validar `openapi.yaml` en Swagger Editor** (paso manual de la Task 5).~~
   Resuelto: se validó con `openapi-spec-validator` 0.9.0 (OpenAPI 3.1.0, sin
   errores).
7. **404 y 405 de rutas que no existen, y 500 inesperados,** salen con el formato
   por defecto de Starlette (`{"detail": ...}`), no con `Error`. Darles formato
   exige códigos nuevos en el enum.

### Tests que se podrían reforzar

8. `test_contrato` compara los códigos de estado de cada operación, pero no qué
   schema usa cada respuesta.
9. Sin test de: FK al insertar un resultado de un ensayo inexistente; `processed_at`
   nuevo al reprocesar con otros parámetros; el nombre por defecto `ensayo.raw`
   cuando el archivo llega sin nombre.
10. `curva()` no envuelve `leer_raw` en `ErrorApi`. Es teórico: el archivo ya se
    validó al subirlo.
11. El mensaje de `GET /tests/0` es "valor inválido" (falta traducir
    `greater_than_equal` con su límite). Está en español y es 400, así que solo es
    un mensaje menos preciso.
12. `conectar` crea el esquema en cada pedido. No hace daño; podría hacerse una vez
    al crear la app.

## Etapa 4 — interfaz (revisiones del 12/10/2026)

Resueltos antes del PR, para referencia:

- ~~Un doble clic en **Analizar ensayo** mandaba dos `POST` y dejaba el ensayo
  duplicado~~: los botones del formulario se deshabilitan mientras hay un pedido
  en curso.
- ~~Plotly interpreta etiquetas HTML en el nombre de las trazas~~: el nombre de
  archivo y el material se escapan antes de pasarlos a la leyenda de la
  comparación (probado con `<b>dos</b>.raw`).
- ~~El gráfico de comparación seguía mostrando la curva de un ensayo ya
  eliminado~~: se limpia cuando la selección deja de ser el par comparado o
  cuando cambia el resultado de alguno (con curvas procesadas).
- ~~Al abrir un ensayo desde el historial quedaba el aviso de error del ensayo
  anterior, y un ensayo sin procesar heredaba β, C_P y la corrección del que
  estaba abierto~~: "Abrir" limpia el aviso y vuelve esos campos a sus valores por
  defecto antes de cargar el ensayo.

### Decisiones tomadas por el agente durante la ejecución (revisar)

1. **El mockup (`index_sptero_mockup.html`) no está en el repositorio.** Se tomó
   el HTML/CSS del plan como la versión ya derivada del mockup.
2. **Carga del `.raw` real por la interfaz.** El navegador integrado no puede
   elegir archivos locales. Para que el `POST` lo hiciera la interfaz con el
   archivo real, se subió una copia por la API, se leyeron sus bytes desde el
   navegador, se borró la copia y se soltó el archivo sobre la zona de carga. Falta
   probar a mano el selector de archivos nativo.
3. **Diálogo de confirmación.** Para aceptar o cancelar `confirm()` desde la
   automatización se reemplazó la función en la consola. Se comprobó el texto y
   que cancelar no borra, pero el diálogo nativo no se vio.
4. **Base limpia de la verificación.** En vez de `SPTERO_DB=data/verificacion.db`
   (el plan), se borró `data/sptero.db`, que había creado la misma sesión:
   `launch.json` no pasa variables de entorno.
5. **Capturas en JPG** (`docs/capturas/*.jpg`), no PNG como dice el plan: es lo
   que guarda la herramienta de captura. La Task 13 tiene que referenciarlas como
   `.jpg`.

### Mejoras posibles (no bloquean)

6. El hover del gráfico muestra "0,1234 mm / 456,7 N" sin las etiquetas
   "Desplazamiento" y "Carga" que nombra la spec §7.
7. Los errores de `GET /tests` y `GET /curve` aparecen en el aviso de "Datos del
   ensayo", no en la tarjeta del historial o del gráfico (spec §8).
8. Eliminar un ensayo desde una fila mientras otro se está guardando vuelve a
   habilitar **Analizar** antes de tiempo, y eso reabre la posibilidad de un
   duplicado.
9. Si falla el `GET` que reabre el ensayo justo después de un `POST` exitoso, el
   indicador queda en "Guardando…" y otro clic en **Analizar** sube el archivo de
   nuevo. Si falla `GET /curve`, el gráfico conserva la curva anterior.
10. "Parámetros usados" muestra los números con punto (`0.5`, `0.0002281`)
    mientras las tarjetas usan coma.
11. `test_sirve_la_interfaz` solo comprueba que `/` y `/static/app.js` respondan.
    No hay tests automáticos del JS (no hay Node); la interfaz se verificó en el
    navegador.

## Etapa 5 — entrega (verificación del 12/10/2026)

### Clasificación para la entrega

Se revisaron todos los puntos abiertos de este archivo. **Ninguno impide instalar,
ejecutar o usar la aplicación**: la instalación limpia, la suite (131 passed con los
archivos originales) y el recorrido en el navegador salieron bien.

- **Limitaciones conocidas del MVP** (documentadas en el README): t/10 sin MAO, sin
  corrección por defecto, Plotly por CDN, uso local de un solo usuario y espera del
  lock de 5 s (etapa 3, punto 7), y los bordes del contrato de la etapa 3 (puntos 2,
  4 y 7).
- **Falta probar a mano** (etapa 4, puntos 2 y 3): el selector de archivos nativo y
  el diálogo real de `confirm()`. Es una prueba de un minuto en un navegador común.
- **Mejoras para otra versión:** el resto (etapa 2, puntos 2 a 6; etapa 3, puntos 3,
  5 y 8 a 12; etapa 4, puntos 6 a 11).

### Hallazgos nuevos

1. **Codificación del encabezado.** El original abre el `.raw` con la codificación
   del sistema (cp1252 en Windows) y `leer_raw` decodifica como UTF-8 con reemplazo.
   En los cuatro ensayos reales comparados no hay diferencia, porque las columnas
   numéricas son ASCII. Podría haberla con un encabezado no ASCII que afecte la
   detección de la fila `"Time` o los nombres de columna. Lo señaló el
   `verificador-cientifico`; no se probó con un archivo así.
2. **`GET /favicon.ico` responde 404** en el log del servidor. Es cosmético.
3. **El plan tiene dos comandos con rutas locales** (la carpeta de ensayos de
   Julián). No exponen datos y ya están en el historial público; se dejan.
4. **`test_caracterizacion.py` no compara `py_t10_displacement_mm` contra la tabla de
   la spec** (la tabla no lo tiene). Sí lo compara contra el original en
   `test_pipeline_igual_al_original`.
