# TP final — SPTERO Web

> En construcción. Este README va a ser el informe de la entrega; por ahora el
> diseño está en la [spec](docs/superpowers/specs/2026-10-12-sptero-web-design.md)
> y el registro de prompts en [prompts.md](prompts.md).

## Cómo se ejecuta

## Qué me propuse construir

## Arquitectura

## Decisiones que tomé yo

Decisiones cerradas al revisar la spec (12/10/2026). El detalle técnico de cada
una está en la [spec](docs/superpowers/specs/2026-10-12-sptero-web-design.md). Las
justifico con cuatro criterios: simplicidad, reutilización del SPTERO original,
trazabilidad científica y un alcance razonable para el MVP.

**Sumar la fluencia por t/10 al MVP con un contrato v1.1.** La presentación la
incluía y el contrato del TP2 no. El `Result` suma `py_t10_n` y `sigma_y_t10_mpa`.
Por qué: el cálculo ya existe en SPTERO (`estimar_py_t10`) y se reutiliza tal cual,
así que suma un resultado científico relevante con poco costo y sin salirse del
alcance del MVP.

**Reutilizar el motor científico copiándolo a un módulo propio, sin cambiar
fórmulas.** Se quita solo la interfaz de consola, y cada función se compara con la
original en tests. Por qué: reutiliza el SPTERO original sin arrastrar tkinter,
matplotlib ni los `print` al servidor, y la comparación función por función da
trazabilidad científica: cada número de la web se puede rastrear hasta el script.

**SQLite con `sqlite3` de la biblioteca estándar, y el `.raw` original guardado
como BLOB** junto con parámetros y resultados. Por qué: es lo más simple que
alcanza para dos tablas (sin ORM ni dependencias extra), y guardar el archivo
original con los parámetros usados permite reproducir cualquier resultado desde su
fuente.

**D1 — Seguir la secuencia de preprocesamiento del SPTERO original.** El cero por
precarga se aplica solo junto con la corrección de flexibilidad, como en el
script. Esto revierte la decisión 4 del TP2, que lo aplicaba siempre; el cambio
vive en el contrato v1.1 de esta carpeta. Por qué: trazabilidad científica; si la
secuencia difiere, los resultados dejan de ser comparables con los de SPTERO.

**D2 — Poder corregir el espesor de un ensayo guardado y recalcular, sin
versiones.** Se agrega `PATCH /tests/{id}` en el contrato v1.1; el TP2 no se toca.
Si el recálculo falla, no cambia ni el espesor ni el resultado anterior. Por qué:
un espesor mal cargado no debería obligar a borrar y volver a subir el ensayo, y no
tener versiones mantiene el modelo simple (un ensayo, un resultado), dentro del
alcance del MVP.

**D3 — Comparar dos curvas del mismo tipo, crudas o procesadas, a elección.** Por
qué: superponer curvas de distinto tipo mezclaría coordenadas distintas (con y sin
corrección de flexibilidad); comparar del mismo tipo mantiene la comparación
científicamente válida. Limitarla a dos curvas la deja dentro del MVP.

**D4 — Guardado automático con estado visible, sin botón Guardar, y eliminación
con confirmación.** Por qué: simplicidad; el contrato ya persiste el ensayo al
subirlo, así que un botón Guardar sería redundante. Como todo queda guardado,
eliminar es la única acción destructiva y por eso pide confirmación.

**D5 — La configuración del agente vive en `tp-final/.claude/` y las sesiones
arrancan en `tp-final/`.** Se verificó que, si no, Claude Code no carga los
permisos ni el subagente. Por qué: es lo que pide la consigna y lo más simple de
mantener, con todo el TP final en una sola carpeta.

**No publicar el `.raw` experimental ni el script original.** Los tests que los
necesitan leen rutas locales y se saltean si no están. Por qué: por ahora prefiero
no publicar esos archivos. La trazabilidad científica se conserva igual: los
valores de referencia quedan fijados en la spec y la comparación con el original
se puede repetir localmente.

### Decisiones de la etapa 2 (motor científico)

**Sin corrección de flexibilidad por defecto, como en el TP2.**
`ParametrosProcesamiento.aplicar_correccion` vale `False`, igual que
`apply_compliance_correction` en el contrato. Esto es distinto del SPTERO
original: en la consola, Enter aplica la corrección. Con el mismo `.raw`, la web
con los valores por defecto da el caso sin corrección (en `P3_304L_L.raw`,
dm = 2,2709 mm) y Enter en la consola da el caso con corrección (dm = 1,7319 mm).
Por qué: mantener el default del contrato del TP2, del que evoluciona el v1.1. La
diferencia queda escrita en el docstring de `sptero_core/analisis.py`.

**Un `.raw` dañado es un error de archivo, no una caída.** El original deja
escapar `csv.Error` cuando el archivo tiene, por ejemplo, una comilla sin cerrar.
`leer_raw` lo convierte en `ValueError`, que la API va a traducir a 400
`INVALID_FILE`. Por qué: es un cambio de entrada/salida, no toca las reglas de
lectura, y así el core cumple su regla de errores y la web nunca responde 500 por
un archivo malo. Lo detectó la revisión final de la rama y tiene su test.

**Comparar también `encontrar_inicio_tabla` con el original.** El plan comparaba
8 funciones por AST y dejaba afuera esta, que también es copia textual. La sumé
(la caracterización tiene 14 tests en vez de 13) porque la regla del core pide
comparar cada función copiada.

### Decisiones de la etapa 3 (API)

Esta etapa la ejecutó el agente con autonomía delegada: le pedí que no me
consultara entre tareas y que frenara solo ante decisiones de alcance o de
arquitectura. Las decisiones de abajo las tomó el agente al implementar o al
revisar, y las dejo escritas para revisarlas antes del PR.

**Rechazar números no finitos en todas las entradas.** Pydantic acepta `inf`, y
el parser JSON de Starlette acepta `Infinity` y `NaN`. Un espesor infinito pasaba
el `gt=0`, se guardaba y rompía la respuesta con un 500. Todas las entradas
numéricas usan `allow_inf_nan=False`. Con esto se resolvió el pendiente 1 de la
etapa 2.

**Un `testId` fuera de int64 es un parámetro inválido.** El contrato ya declara
`format: int64`, así que un id más grande responde 400 `INVALID_PARAMETERS` y no
404. Antes daba 500 porque sqlite3 no puede ligar ese número.

**Los mensajes de validación se traducen.** El plan armaba el `message` con el
texto de Pydantic, que está en inglés, y eso contradecía la restricción de
mensajes en español. Se traduce cada tipo de error, con un mensaje genérico de
respaldo.

**Un recálculo que no da un número finito es `PROCESSING_FAILED`.** Con un
espesor absurdamente chico (1e-170) el core lanzaba `ZeroDivisionError` y la API
respondía 500. Con β = 1e308 se guardaba un Rm infinito. El servicio captura
también `ArithmeticError` y rechaza resultados no finitos con 422, sin tocar el
core.

**Cuerpos JSON con tipos estrictos.** `{"thickness_mm": true}` se guardaba como
1 mm. Los cuerpos de `PATCH` y `PUT` validan tipos en modo estricto, como dice el
contrato (`type: number`/`boolean`). Los números enteros siguen valiendo. El
formulario de `POST` sigue aceptando texto, porque los campos multipart llegan
como texto.

**El test de contrato compara más que las rutas.** Ahora la app declara sus
respuestas de error con un modelo `Error`, y `test_contrato.py` compara también
los campos requeridos y los códigos de estado de cada operación contra
`openapi.yaml`. Antes un código o un `required` faltante pasaba sin aviso.

**Nombres de archivo no ASCII en la descarga.** Starlette codifica las cabeceras
en latin-1, así que "ensayo_€.raw" daba 500. Se usa `filename*=utf-8''…`, igual
que `FileResponse`.

**Queda para decidir: pedidos concurrentes sobre el mismo ensayo.** La revisión
final encontró que un `PUT` que llega mientras corre un `PATCH` puede quedar
pisado sin aviso. La atomicidad que pide la spec se cumple: si el recálculo falla,
no cambia nada. Arreglarlo exige elegir entre reorganizar las transacciones del
repositorio o serializar los pedidos desde la interfaz, y esa elección es mía.
Está descrita en [docs/pendientes.md](docs/pendientes.md) y la tengo que resolver
antes de la etapa 4.

Los hallazgos de las revisiones que quedaron para más adelante están en
[docs/pendientes.md](docs/pendientes.md).

## Cómo gestioné el contexto

**Etapa 2.**
- Comprobé la regla `deny` sobre `TP1/`: la sesión, abierta en `tp-final/`,
  intentó editar `../TP1/README.md` y la herramienta lo rechazó ("File is in a
  directory that is denied by your permission settings"). Era el chequeo que la
  spec (§10) dejaba pendiente.
- Las cuatro tareas se hicieron con subagentes: uno implementaba cada tarea y otro
  la revisaba contra la spec y el original. Al final, una revisión de toda la rama
  y el subagente `verificador-cientifico`. Así, la sesión principal no tuvo que
  cargar las 1.500 líneas del script.
- Cada commit lleva el `Co-Authored-By` del modelo que lo escribió (Haiku en las
  tareas 1 a 3, Sonnet en la 4).

**Etapa 3.**
- Igual que en la etapa 2: un subagente implementaba cada tarea y otro la revisaba
  contra la spec, el contrato y la atomicidad del `PATCH`. Al final hubo una
  revisión de toda la rama, una ronda de correcciones con su re-revisión y el
  `verificador-cientifico`.
- El verificador comparó la API contra el script original con `P3_304L_L.raw`:
  sin corrección, con corrección y con `PATCH` a 0,25 mm. La diferencia relativa
  fue 0 en las seis magnitudes.
- Además se levantó uvicorn sobre una base temporal y se probó todo con `curl`:
  alta, procesamiento, idempotencia, `PATCH`, curva, descarga byte a byte y
  borrado.

## Qué salió mal y cómo lo corregí

**Etapa 2.**
- **Un comando colgado.** El agente principal dejó un `cat` sin entrada al armar
  un script de comparación, y el comando se colgó hasta que lo cortó. No tuvo
  efectos.
- **El plan no cubría el archivo dañado.** La revisión final encontró que un
  `.raw` con una comilla sin cerrar hacía fallar a `leer_raw` con `csv.Error`, que
  no es `ValueError`. Lo corregí con un test que primero falló.
- **El docstring contradecía el código.** Decía que se usaban los valores por
  defecto del original, y `aplicar_correccion` no lo es. Lo detectó el
  verificador científico y lo corregí.

**Etapa 3.**
- **El plan contradecía su propia restricción.** El handler de validación que
  traía el plan armaba los mensajes con el texto de Pydantic, en inglés. Lo
  notamos al probar con el servidor real ("Input should be greater than 0") y la
  revisión final lo confirmó. Se tradujo por tipo de error, con tests.
- **El test de contrato era débil.** Solo comparaba rutas y nombres de campos. La
  revisión de la Task 8 lo marcó y se reforzó (ver decisiones).
- **Entradas que terminaban en 500.** Ids fuera de int64, números infinitos,
  espesores absurdamente chicos y nombres de archivo con "€". Ninguno estaba en el
  plan; los encontraron las revisiones y cada uno tiene su test.
- **Una decisión que se tomó mal y se corrigió.** Al empezar, el agente dio por
  aceptable la lectura fuera de la transacción en el `PATCH`, pensando que lo
  único que podía pasar era un 500 si se borraba el ensayo en el medio. La
  revisión final mostró que también se puede perder una actualización sin aviso.
  Se corrigió la descripción y quedó como decisión pendiente.
- **Un permiso que bloqueó la copia del contrato.** El `cp` desde `../TP2` fue
  denegado. El subagente copió el contrato leyéndolo y escribiéndolo de nuevo, y
  después se comprobó con `diff` que solo cambiaban las ediciones del plan.

## Prompts
