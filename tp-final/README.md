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

## Cómo gestioné el contexto

## Qué salió mal y cómo lo corregí

## Prompts
