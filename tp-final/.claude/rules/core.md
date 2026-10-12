---
# Se declaran los dos anclajes porque la documentación no aclara contra qué raíz
# se resuelven los paths de una rule anidada (ver spec, sección 10).
paths:
  - "sptero_core/**"
  - "tp-final/sptero_core/**"
---

# Motor científico (`sptero_core/`)

- Las funciones son copias del script original `Programa SPTERO.py`. **No se cambia
  ninguna fórmula, umbral ni valor por defecto**, aunque parezca mejorable. Si algo
  parece un error científico, se frena y se le consulta a Julián.
- Los únicos cambios permitidos son de entrada/salida: leer `bytes` en vez de una
  ruta, quitar `print`, devolver un indicador en vez de avisar por consola.
- Cada función copiada tiene un test en `tests/test_caracterizacion.py` que la
  compara con la original (tolerancia relativa 1e-9). Una función nueva o cambiada
  sin ese test no está terminada.
- El core no importa nada de `app/`, de FastAPI ni de matplotlib, no imprime y no
  lee ni escribe archivos. Recibe datos y devuelve datos.
- Errores: `ValueError` con mensaje en español. La traducción a HTTP la hace `app/service.py`.
- La secuencia del pipeline es la de la spec, sección 4. El cero por precarga y la
  rama t/10 sin MAO están documentados ahí: no "arreglarlos".
