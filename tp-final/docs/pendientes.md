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
