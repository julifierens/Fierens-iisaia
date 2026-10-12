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

1. **Espesor no finito.** Con `thickness_mm` = NaN, `rm_from_beta` no lo rechaza
   (`nan <= 0` es falso) y devuelve Rm = NaN sin error. La spec (§8) solo pide
   rechazar espesores ≤ 0. La API tiene que rechazar también NaN e infinito con
   400 `INVALID_PARAMETERS`; el core no se toca.
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
