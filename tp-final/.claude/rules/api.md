---
# Se declaran los dos anclajes porque la documentación no aclara contra qué raíz
# se resuelven los paths de una rule anidada (ver spec, sección 10).
paths:
  - "app/**"
  - "openapi.yaml"
  - "tp-final/app/**"
  - "tp-final/openapi.yaml"
---

# API (`app/` y `openapi.yaml`)

- `openapi.yaml` es la fuente de verdad. Si hace falta un endpoint, campo o código
  distinto, primero se propone el cambio del contrato a Julián; recién después se
  toca el código.
- Todos los errores responden `{"code": ..., "message": ...}` con los códigos de la
  spec, sección 8. Nunca el formato por defecto de FastAPI: los errores de
  validación se devuelven como 400 `INVALID_PARAMETERS`, no como 422.
- `PUT /tests/{testId}/result` es idempotente: los campos que no se envían toman su
  valor por defecto, y si los parámetros no cambian no se toca nada (tampoco
  `processed_at`).
- `PATCH /tests/{testId}` solo corrige `thickness_mm`. Si hay resultado, lo recalcula
  con los parámetros guardados en la **misma transacción**: si el recálculo falla,
  no queda nada a medias. Igual espesor = sin cambios. Nunca se crean versiones.
- Las rutas no hacen cálculos ni SQL: delegan en `service.py`, que usa
  `sptero_core` y `repository.py`.
- SQL explícito con parámetros (`?`), nunca armado con f-strings. `GET /tests` no
  trae el BLOB del archivo.
- Cada endpoint y cada código de error tiene su test en `tests/test_api.py`, y
  `tests/test_contrato.py` mantiene alineadas las rutas con `openapi.yaml`.
