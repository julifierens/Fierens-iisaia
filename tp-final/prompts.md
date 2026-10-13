# Prompts — TP final

Prompts relevantes del desarrollo de SPTERO Web con Claude Code, copiados textuales
y en orden. "Qué buscaba" lo escribe el autor; "Qué devolvió" resume lo que hizo el
modelo, errores incluidos. A diferencia del TP1 y el TP2, el trabajo final se hace
en varias sesiones; cada entrada indica a cuál pertenece.

Los "Qué buscaba" de las entradas 1 a 3 los redactó el modelo a pedido mío (prompt
4), a partir de los objetivos que habíamos acordado en la conversación, y los revisé.
Los de las entradas 4 a 15 los propuso Claude en la etapa 5 a partir del texto real
de cada prompt y de las decisiones que tomé en él; los revisé, les hice ajustes y los
aprobé.

Las entradas 6 a 15 se registraron en la etapa 5 y no en el momento, como acordamos
en el prompt 9. Un subagente copió los prompts de los transcripts de cada sesión y
resumió lo que hizo el modelo; los textos se verificaron por muestreo contra los
transcripts.

---

## 1 — Prompt inicial: análisis del material y plan por etapas

Sesión 1 (12/10/2026). Adjuntos: `Programa SPTERO.py`, `P3_304L_L.raw`, `index_sptero_mockup.html`, `SPTERO_Web_Entrega_Parcial_v3_7diapos.pdf`.

```
Vamos a desarrollar mi TP final de IISAIA: SPTERO Web.
Te adjunto el programa Python original, un ensayo .raw, el mockup HTML y la presentación del proyecto.
Antes de empezar, revisá:

* El repositorio de la materia: https://github.com/FIUBA-Posgrado-Inteligencia-Artificial/IISAIA
* Mi repositorio actual, incluyendo TP2 y sus ramas.

Leé el enunciado del TP final y las clases desde la semana 4. Quiero aplicar lo aprendido: Superpowers, skills, CLAUDE.md, subagentes, MCP, testing y buenas prácticas de Git, siempre que aporten valor al proyecto.
La idea es desarrollar SPTERO Web reutilizando el código científico original, con FastAPI, una interfaz similar al mockup y persistencia de ensayos y resultados.
Quiero que uses Superpowers para organizar el desarrollo, comenzando por brainstorming y planificación.
Trabajemos con la menor cantidad razonable de prompts: organizá tareas completas y ejecutables, sin pedirme confirmación por cada detalle menor. Consultame solamente las decisiones importantes.
Por ahora no modifiques archivos ni programes. Analizá todo el material, verificá que pudiste acceder a las consignas y proponeme un plan de implementación por etapas, incluyendo cómo documentaremos el uso de IA para la entrega.
```

**Qué buscaba:** Que el modelo entendiera todo el material antes de escribir una
línea: la consigna oficial del TP final, el contrato del TP2, el script original,
el ensayo real y el mockup. Quería un plan por etapas que reutilizara el código
científico de SPTERO y aplicara lo visto desde la semana 4 donde aportara valor, y
acordar desde el principio cómo se iba a documentar el uso de IA.

**Qué devolvió:** Trabajó en plan mode e invocó la skill de brainstorming de
Superpowers, que clasificó el trabajo como "arquitectónico" (spec escrita + plan).
Lanzó dos subagentes de exploración en paralelo: uno sobre este repositorio (TP1,
TP2, ramas) y otro sobre el repositorio de la materia. Confirmó que pudo leer
`programa.md`, las slides de la semana 4 con la consigna del TP final (§13) y la
semana 5 (§15, recomendaciones para el final), y aclaró que no hay fechas ni rúbrica
formal publicadas y que las semanas 7 y 8 están vacías. Señaló una contradicción en
la consigna (grupos de 2 o 3 en las slides, individual en `programa.md`).

Corrió las funciones del script original sobre `P3_304L_L.raw` y confirmó que
reproducen el mockup (Pm 2372,2 N, dm 2,2709 mm, Rm 578,7 MPa sin corrección), y
calculó también t/10. En el camino tuvo un error propio: ejecutó Python con `-I`,
que ignora `PYTHONIOENCODING`, y la prueba falló por el `print` con emojis del
original en la consola cp1252; lo resolvió reintentando con `-X utf8`.

Detectó que la presentación incluye t/10 en el MVP pero el contrato del TP2 lo
excluye, y planteó cuatro decisiones con opción recomendada. Elegí las cuatro
recomendadas: sumar t/10 con un contrato v1.1, extraer el motor a un módulo
`sptero_core` con tests de caracterización, usar `sqlite3` de la stdlib y mantener
`prompts.md`. Con eso propuso un plan de seis etapas (0 a 5) con gates de revisión.

---

## 2 — Ajustes al plan y ejecución de la etapa 0

Sesión 1 (12/10/2026). Respuesta al rechazar la primera versión del plan.

```
## Ajustes solicitados antes de la implementación

- Persistencia: guardar los archivos .raw originales como BLOB en SQLite, junto con los parámetros y resultados.
- Reprocesamiento: permitir abrir un ensayo guardado, modificar sus parámetros y recalcular resultados sin generar versiones adicionales.
- Gráficos: utilizar Plotly.js para permitir zoom, desplazamiento, consulta de valores y restablecimiento de ejes.
- Comparación: permitir seleccionar dos ensayos del historial y superponer sus curvas carga-desplazamiento, identificadas con colores y leyenda. La comparación no modifica los ensayos.
- Validación: verificar que los cálculos coincidan con SPTERO original, respetando la secuencia de preprocesamiento.
- Datos: no publicar por ahora el archivo .raw experimental en GitHub.

**Primero ejecutar solamente la etapa 0. Detenerse antes del commit para revisar la especificación. No avanzar automáticamente con las demás etapas.**
```

**Qué buscaba:** Ajustar el alcance del plan a lo que necesito del producto
(archivo original en la base, reprocesamiento sin versiones, gráficos interactivos,
comparación de ensayos), asegurar que los cálculos sean los mismos que los de
SPTERO original y no publicar datos experimentales. También quería frenar el
avance: ejecutar solo la etapa 0 y revisar la spec antes de commitear.

**Qué devolvió:** Incorporó los ajustes al plan y marcó que "respetar la secuencia
de preprocesamiento" contradice la decisión 4 del TP2 (cero por precarga siempre):
el original solo lo aplica junto con la corrección de flexibilidad. Comprobó que con
`P3_304L_L.raw` no cambia el resultado, pero lo dejó como decisión pendiente. Para
no publicar el `.raw`, propuso tests de caracterización que leen rutas locales por
variable de entorno y se saltean si no están, más tests con una curva sintética.

En la etapa 0 creó la rama `feature/tp-final-spec`, escribió la spec y la
configuración del agente (`CLAUDE.md`, `settings.json`, dos rules, la skill
`registrar-prompt` y el subagente `verificador-cientifico`). Al escribir la spec
encontró una diferencia que no había visto en el plan: en el original, t/10 usa la
Zona I del ajuste MAO cuando existe, y como MAO queda fuera del MVP, la web
reproduce la rama sin MAO. Usó un subagente de consulta sobre la documentación de
Claude Code y encontró que `settings.json` y los subagentes de una `.claude/`
anidada solo se cargan si la sesión arranca en esa carpeta. Dejó cinco decisiones
pendientes (D1–D5) en la spec y se detuvo antes del commit, como se pidió.

---

## 3 — Cerrar las decisiones D1–D5 y revisar permisos y rutas

Sesión 1 (12/10/2026).

```
Revisé la etapa 0 y está bien. Antes del commit quiero cerrar las decisiones:

D1: seguir la secuencia del SPTERO original.
D2: permitir corregir el espesor de un ensayo guardado y recalcular sus resultados, sin crear versiones.
D3: comparar dos curvas del mismo tipo, ambas crudas o ambas procesadas. Que el usuario pueda elegir.
D4: guardado automático con estado visible, sin un botón Guardar redundante. Eliminar debe requerir confirmación.
D5: mantener la configuración en tp-final/.claude/ y verificar que realmente se cargue.

Revisá también las reglas de permisos de settings.json, especialmente las entradas Write(...), y las rutas relativas de la skill registrar-prompt cuando trabajamos desde tp-final/.

Actualizá la spec, CLAUDE.md y los archivos relacionados. Si D2 requiere modificar el contrato del TP2, hacelo solamente en la futura versión v1.1 del TP final, sin tocar TP2.

No implementes todavía la aplicación. Al terminar, resumime los cambios y las comprobaciones realizadas. Detenete antes del commit.
```

**Qué buscaba:** Cerrar las cinco decisiones pendientes antes de commitear la spec,
que la configuración del agente funcionara de verdad y no solo en el papel
(permisos y rutas), y que el cambio de contrato quedara en el TP final sin tocar el
TP2 entregado.

**Qué devolvió:** Consultó la documentación oficial de permisos y confirmó dos
errores propios en el `settings.json` de la entrada anterior. Las reglas
`Write(...)` con ruta nunca se aplican: Claude Code solo consulta `Edit` y `Read`,
y `Edit` ya cubre todas las herramientas que escriben. Además, `Edit(../TP1/**)` no
protegía nada, porque los patrones no pueden salir de su ancla con `..`. Los
reemplazó por `Edit(//**/TP1/**)` y `Edit(//**/TP2/**)`. La skill
`registrar-prompt` tenía fija la ruta `tp-final/prompts.md`, que falla desde una
sesión en `tp-final/`; la reescribió para ubicar el archivo junto a su `.claude/`.

Para D5 encontró el `claude.exe` de la app de escritorio y lo corrió en modo no
interactivo desde `tp-final/` y desde la raíz, leyendo qué carga al iniciar.
Desde `tp-final/` se leen `settings.json`, el subagente y la skill; desde la raíz,
ninguno de los tres. La CLI no tenía sesión iniciada, así que las reglas `deny`
quedaron verificadas contra la documentación pero sin ejercitar. En el camino tuvo
un tropiezo menor: Python no pudo abrir un archivo en el scratchpad porque la ruta
superaba los 260 caracteres de Windows, y lo repitió con una ruta corta.

Para D2 eligió un `PATCH /tests/{id}` que solo corrige el espesor y recalcula en la
misma transacción, en lugar de mover el espesor a los parámetros de procesamiento,
porque el espesor es una medida de la probeta. Actualizó la spec (D1–D5 cerradas,
contrato v1.1, interfaz, errores, tests), `CLAUDE.md`, la rule de la API, el
subagente y el README, con los porqués marcados para completar. No implementó nada
y se detuvo antes del commit.

---

## 4 — Cerrar la etapa 0 y escribir el plan

Sesión 1 (12/10/2026).

```
Muy bien, damos por aprobada la etapa 0.

Completá los tres "Qué buscaba" de prompts.md con los objetivos que definimos y documentá brevemente la justificación de las nueve decisiones, basándote en los criterios que acordamos: simplicidad, reutilización del SPTERO original, trazabilidad científica y alcance razonable del MVP. No inventes motivaciones adicionales.

Después hacé el commit de la etapa 0.

Avanzá con la etapa 1 usando Superpowers writing-plans. Quiero un plan de implementación concreto, con tareas verificables, tests y criterios de aceptación. Aprovechá las skills y subagentes cuando corresponda.

Recordá que el nuevo PATCH de espesor debe garantizar que, si falla el recálculo, no se modifiquen ni el espesor ni los resultados anteriores.

Al terminar, detenete para que revisemos el plan antes de implementar. No hagas todavía el PR ni avances a la etapa 2.
```

**Qué buscaba:** Cerrar la etapa 0: completar los "Qué buscaba" de 1 a 3 y el
porqué de las nueve decisiones, justificadas solo con los cuatro criterios acordados.
Después, pasar a un plan de implementación concreto con `writing-plans`, con tareas
verificables, tests y criterios de aceptación. Quería que el plan garantizara que,
si falla el recálculo del `PATCH`, no cambian ni el espesor ni el resultado, y
revisarlo antes de implementar.

**Qué devolvió:** Completó los "Qué buscaba" de las entradas 1 a 3, aclarando en el
encabezado que los redactó el modelo a pedido mío, y justificó las nueve decisiones
del README solo con los cuatro criterios. Commiteó la etapa 0 (`fd0a34a`).

Con la skill `writing-plans` escribió el plan en
`docs/superpowers/plans/2026-10-12-sptero-web.md`: 13 tareas en cuatro ramas, cada
una con el test que tiene que fallar primero, el código y el resultado esperado.
Antes de escribirlo comprobó que no hay Node instalado, así que la verificación de
la interfaz usa el navegador integrado de la app (MCP) en lugar de Playwright.
Detectó un hueco en la spec: para marcar Py_t/10 en el gráfico falta su
desplazamiento, y propuso el campo `py_t10_displacement_mm`, marcado como cambio a
confirmar. El requisito del PATCH quedó cubierto en tres niveles: transacción en la
base (Task 6), cálculo antes de escribir (Task 7) y prueba de punta a punta (Task 8).

Al verificar los valores esperados del plan con el script original, encontró un
error propio: la curva sintética aplicaba un piso de 100 N a toda la curva en lugar
de solo a la caída, lo que corría el cruce de t/10 a 2,34 mm y anulaba el cero por
precarga. Varios tests habrían fallado por culpa del plan y no del código. Corrigió
la curva y volvió a verificar todos los valores esperados contra el original. También
corrigió un conteo de tests y un redondeo. Se detuvo sin PR y sin avanzar a la
etapa 2.

---

## 5 — Aprobar el plan y preparar el PR de las etapas 0 y 1

Sesión 1 (12/10/2026).

```
De acuerdo con las tres recomendaciones:

1. Agregá py_t10_displacement_mm al contrato v1.1, nullable si no se encuentra el cruce.
2. Usemos subagent-driven con Superpowers. Priorizá las verificaciones y revisiones que aporten valor, sin generar pasos innecesarios.
3. Te autorizo a hacer commits por tarea dentro de cada etapa, siempre después de verificar los resultados. No hagas push, PR ni merge sin mi aprobación.

Actualizá la spec y el plan, y hacé el commit de cierre de la etapa 1.
Antes de iniciar el desarrollo, quiero integrar las etapas 0 y 1 en main mediante un PR, para que las próximas ramas partan de una base actualizada.
No empieces todavía la etapa 2. Cuando termines, indicame cómo crear y fusionar el PR desde Claude Desktop o GitHub.
```

**Qué buscaba:** Cerrar las tres recomendaciones del plan: sumar
`py_t10_displacement_mm` (null si no hay cruce), ejecutar con subagent-driven sin
verificaciones que no aporten, y commitear por tarea después de verificar, con push,
PR y merge solo con mi aprobación. También quería integrar las etapas 0 y 1 en
`main` con un PR antes de desarrollar, para que las ramas siguientes partieran de una
base actualizada, y saber cómo crear y fusionar ese PR.

**Qué devolvió:** Agregó `py_t10_displacement_mm` a la spec (pipeline, cambios del
contrato y tabla `results`) y alineó los nombres de los archivos de test. En el
plan reemplazó el "cambio a confirmar" por las decisiones tomadas: ejecución
subagent-driven, con un revisor por tarea enfocado en lo que más riesgo tiene en
cada etapa (fidelidad al original, contrato y atomicidad del `PATCH`), la
verificación en el navegador hecha por la sesión principal y una revisión de rama
al cerrar cada etapa. También dejó escrita la autorización de commits por tarea,
sin push, PR ni merge. Commiteó el cierre de la etapa 1 y, sin hacer push, explicó
cómo crear y fusionar el PR.

---

## 6 — Subir la rama de la spec y el plan

Sesión 1 (12/10/2026).

```
Subí la rama feature/tp-final-spec a GitHub. No hagas el PR ni el merge todavía. Avisame cuando esté subida.
```

**Qué buscaba:** Publicar la rama en GitHub para abrir el PR yo, sin que el
agente lo creara ni hiciera el merge.

**Qué devolvió:** Hizo el `git push` de `feature/tp-final-spec` (último commit
`6316594`, cierre de la etapa 1) y dejó la rama local siguiendo a la remota. No
creó el PR ni hizo merge; pasó el enlace para crearlo desde GitHub, porque `gh` no
está instalado.

---

## 7 — Etapa 2: motor científico

Sesión 2 (12/10/2026).

```
Ya fusioné el PR #2 en main. Vamos con la etapa 2 del TP final: implementar SPTERO Core.

Verificá que estemos en tp-final/, que main esté actualizado y que se carguen Superpowers, las skills y el subagente verificador-cientifico. Creá feature/tp-final-core desde main sin afectar TP1 ni TP2.

Ejecutá las tareas 1 a 4 del plan con Superpowers, TDD y subagent-driven. Reutilizá las funciones científicas originales sin modificar las fórmulas.

Antes de implementar, comprobá que tenés acceso local al programa SPTERO original y al ensayo P3_304L_L.raw. Si no los encontrás, pedímelos. Quiero validar los resultados reales, no solamente curvas sintéticas.

Podés trabajar con autonomía y hacer commits por tarea después de verificar los tests. Al terminar, ejecutá el subagente verificador-cientifico y mostrame los resultados.

Detenete antes del push, PR o merge. No avances a la etapa 3.
```

**Qué buscaba:** Implementar el motor científico reutilizando las funciones del
SPTERO original sin cambiar fórmulas, con TDD y subagent-driven, en su propia rama y
sin tocar TP1 ni TP2. Quería validar contra el script original y el `.raw` real, no
solo con curvas sintéticas, y ver el resultado del verificador científico antes de
cualquier push.

**Qué devolvió:** Con `subagent-driven-development`, encontró el script original y
el `.raw` en rutas locales y comprobó la regla `deny` sobre `TP1/` intentando editar
`../TP1/README.md` (la herramienta lo rechazó). Creó `feature/tp-final-core` e hizo
un commit por tarea: `f49e66c` (lectura del `.raw`), `2d0f7c2` (preprocesado y
cálculos), `c7158d3` (pipeline `analizar`) y `bf8388d` (caracterización contra el
original). Suite: 39 passed con los archivos reales; sin ellos, 25 passed y 14
skipped. El verificador científico dio "fiel".

La revisión final encontró que un `.raw` dañado hacía salir `csv.Error` del core, y
el verificador, que el docstring de `analisis.py` decía que todos los valores por
defecto eran los del original cuando `aplicar_correccion=False` no lo es. Dejó las
dos para que decidiera yo. Desvíos que informó: dejó un `cat` sin entrada que colgó
un comando hasta cortarlo, y sumó `encontrar_inicio_tabla` a la comparación por AST
sin consultar (14 tests en vez de 13). Los commits llevan el `Co-Authored-By` de
Haiku 5.5 (tareas 1 a 3) y Sonnet 5.5 (tarea 4), los modelos de los subagentes.

---

## 8 — Cerrar las dos decisiones de la etapa 2

Sesión 2 (12/10/2026).

```
Muy bien, cerramos las dos decisiones pendientes:

1. Capturá csv.Error en sptero_core y convertílo en ValueError, con un test para archivos corruptos. No modifiques los algoritmos científicos.
2. Mantené aplicar_correccion=False por defecto, como en el TP2. Corregí el docstring y documentá la diferencia respecto del programa original.

Conservá el test adicional por AST y las firmas originales de los commits.
También quiero que los hallazgos importantes del ledger que quedaron pendientes estén documentados en archivos versionados, para no perderlos.
Después ejecutá nuevamente toda la suite con el .raw real y el programa original, y pasá el verificador-cientifico. Registrá los cambios y hacé el commit correspondiente.
Si está todo bien, dejá la etapa 2 lista para el PR. No avances a la etapa 3 ni hagas push todavía.
```

**Qué buscaba:** Cerrar las dos decisiones pendientes: que un `.raw` dañado se
informe como error de archivo, sin tocar los algoritmos, y mantener la corrección de
flexibilidad desactivada por defecto, como en el TP2, documentando la diferencia con
el original. También quería que los hallazgos pendientes del ledger quedaran en
archivos versionados y volver a validar todo con el original antes del commit.

**Qué devolvió:** Escribió `test_archivo_corrupto`, lo vio fallar con `_csv.Error`
y después hizo que `leer_raw` lance `ValueError`. Corrigió el docstring, creó
`docs/pendientes.md` con los hallazgos del ledger y actualizó el README. Suite: 40
passed con los archivos reales; sin ellos, 26 passed y 14 skipped. Verificador:
"fiel". Todo fue en un commit, `9ee4acb`. Se equivocó y lo corrigió antes del
commit: en el README me había atribuido un motivo que no di (que C_P depende de la
máquina) y lo sacó. El verificador marcó que la spec §4 no mencionaba la diferencia
del default; no la tocó y me consultó.

---

## 9 — Cerrar la etapa 2 y subir la rama

Sesión 2 (12/10/2026).

```
Perfecto, cerramos la etapa 2.

Actualizá la sección 4 de la spec para aclarar que aplicar_correccion=False es el valor por defecto de la web, a diferencia del programa original. Hacé ese cambio en un commit independiente.

Después subí feature/tp-final-core a GitHub. No hace falta otra revisión completa porque los tests ya pasaron y el verificador científico confirmó los resultados.

El registro de prompts lo terminamos de completar en la etapa de documentación final.

No hagas el merge ni empieces la etapa 3. Pasame el enlace para crear el PR.
```

**Qué buscaba:** Registrar en la spec la diferencia del valor por defecto, en
un commit propio, y subir la rama para el PR. El registro de prompts quedaba para la
documentación final.

**Qué devolvió:** Editó la spec §4 en un commit propio (`aa7d568`), subió la rama y pasó
el enlace del PR. Informó que la rama tenía 7 commits sobre `main`, pero eran 6
(de `f49e66c` a `aa7d568`); el error lo encontró la revisión final de la etapa 5. En ese mismo commit tachó el punto
correspondiente de `docs/pendientes.md`, algo que no le pedí; lo avisó y ofreció
sacarlo.

---

## 10 — Etapa 3: API con FastAPI y SQLite

Sesión 3 (12/10/2026).

```
Ya fusioné el PR de la etapa 2 en main. Vamos con la etapa 3 del TP final: FastAPI + SQLite.

Primero verificá que estamos en tp-final/, que el repositorio está limpio, actualizá main desde origin/main y creá la rama feature/tp-final-api. Comprobá que se carguen las skills y la configuración del agente.

Ejecutá completas las tareas 5 a 8 del plan usando Superpowers, TDD y subagent-driven. Seguí la spec y el contrato OpenAPI v1.1, incluyendo los cambios aprobados.

Quiero que quede funcionando toda la API con persistencia real en SQLite: carga y conservación del .raw original, procesamiento mediante sptero_core, resultados, curvas, historial, reprocesamiento y corrección del espesor.

Prestá especial atención a la atomicidad del PATCH de espesor, la idempotencia de PUT, el manejo de errores y la correspondencia entre FastAPI y OpenAPI.

Tenés autonomía para implementar, corregir errores, ejecutar tests, utilizar subagentes y hacer commits por tarea después de verificarla. No me consultes detalles menores ni me pidas aprobación entre tareas.

Al terminar, ejecutá la suite completa, verificá la integración con el motor científico y realizá una revisión global de la etapa.

Documentá los problemas y decisiones importantes. Mostrame los resultados reales de los tests y dejá la rama lista para PR.

No hagas push, PR ni merge. No avances a la etapa 4.
```

**Qué buscaba:** Tener la API completa con persistencia real en SQLite sobre el
motor ya validado, siguiendo la spec y el contrato v1.1. Me importaban sobre todo la
atomicidad del `PATCH`, la idempotencia del `PUT`, el manejo de errores y que
FastAPI coincidiera con `openapi.yaml`. Le di autonomía entre tareas, pero quería
ver los resultados reales de los tests y una revisión global antes del PR.

**Qué devolvió:** No arrancó. Revisó el estado sin cambiar nada y pidió que
confirmara: el pedido le había llegado entero como texto pegado y le daba una
autonomía que cambiaba la regla del `CLAUDE.md` de proponer antes de tocar
archivos. También avisó que el `main` local estaba atrasado (faltaba el merge del
PR #3).

---

## 11 — Confirmar la autonomía de la etapa 3

Sesión 3 (12/10/2026).

```
Sí, confirmo. Tenés autorización para ejecutar completa la etapa 3 (Tasks 5 a 8) con la autonomía acordada.

Actualizá main mediante fast-forward, creá feature/tp-final-api y trabajá con Superpowers, TDD y subagent-driven.

Podés implementar, corregir errores, ejecutar tests y hacer un commit por tarea verificada, sin consultarme entre tareas. Frená solamente si aparece una decisión importante que cambie el alcance o la arquitectura.

Al terminar, ejecutá la suite completa, el verificador científico y la revisión final. Documentá los hallazgos relevantes.

No hagas push, PR ni merge, y no avances a la etapa 4.
```

**Qué buscaba:** Confirmar la autonomía que el agente me pidió ratificar y fijar
el límite: frenar solo ante una decisión que cambie el alcance o la arquitectura.

**Qué devolvió:** Commits `c1c683f` (contrato v1.1), `454efcf` (repositorio),
`13c2716` (servicio), `4acb45f` (rutas), `60bf039` (ids fuera de int64 y test de
contrato reforzado), `ae29dbb` (correcciones de la revisión final) y `5935508`
(documentación). Suite: 121 passed, con un aviso de deprecación de httpx. El
verificador comparó cuatro casos contra el original con diferencia relativa 0, y
además probó la app con uvicorn y `curl`. Las revisiones encontraron entradas que
terminaban en 500 (ids fuera de int64, espesor 1e-170, nombres con "€"), mensajes de
validación en inglés y `{"thickness_mm": true}` guardado como 1 mm; cada una se
corrigió con su test. Informó 17 decisiones que tomó por mí, entre ellas editar la
descripción del `PATCH` en el contrato y traducir los mensajes de validación porque
el plan contradecía su propia restricción. Sobre la carrera entre `PATCH` y `PUT`
reconoció un error propio: al principio la dio por aceptable creyendo que solo podía
dar un 500, y después vio que se podía perder una actualización sin aviso. Dejó esa
decisión para mí.

---

## 12 — Resolver la concurrencia y cerrar la etapa 3

Sesión 3 (12/10/2026).

```
Muy bien, aprobamos las decisiones de la etapa 3.

Antes del PR quiero resolver la concurrencia entre PATCH y PUT usando transacciones SQLite con BEGIN IMMEDIATE. Asegurate de que ambas operaciones trabajen con datos consistentes y que, si falla el cálculo, se haga rollback sin alterar espesor ni resultados. Agregá tests que reproduzcan la concurrencia.

El resto de las decisiones quedan aprobadas. No hace falta corregir ahora el warning de httpx ni ampliar funcionalidades fuera del MVP.

Validá también openapi.yaml y registrá en la documentación los cambios importantes.

Después ejecutá la suite completa y dejá la etapa lista para el PR. Hacé los commits necesarios, subí la rama a GitHub y pasame el enlace para crear el PR.

No hagas el merge ni avances a la etapa 4.
```

**Qué buscaba:** Resolver la decisión que había dejado abierta la etapa 3: que
`PATCH` y `PUT` no puedan pisarse, con `BEGIN IMMEDIATE`, rollback si falla el
cálculo y tests que reproduzcan la concurrencia. Aprobé el resto de las decisiones y
dejé afuera el warning de httpx y cualquier ampliación del MVP. También quería el
contrato validado y la rama lista para el PR.

**Qué devolvió:** Commits `a808ac0` (`PATCH` y `PUT` serializados con
`BEGIN IMMEDIATE`, más `tests/test_concurrencia.py`), `ac456fe` (no dejar
transacciones abiertas si falla el `COMMIT` o el `ROLLBACK`, pedido por la revisión)
y `bb16cf4` (documentación). Los tests nuevos se corrieron contra el código anterior
y fallaron como debían. Validó `openapi.yaml` con `openapi-spec-validator` 0.9.0
(OpenAPI 3.1.0 válido) y, como contraprueba, rompió un `$ref` a propósito y el
validador lo detectó. Suite: 130 passed. Subió la rama y pasó el enlace. Errores en
el camino: la primera versión del test de concurrencia tiró abajo Python con un
"access violation" por cerrar conexiones con hilos vivos, y la instalación del
validador falló por el límite de longitud de rutas de Windows.

---

## 13 — Etapa 4: interfaz

Sesión 4 (12/10/2026).

```
Ya fusioné la etapa 3 en main. Vamos con la etapa 4: desarrollar la interfaz de SPTERO Web.

Primero verificá que estamos en tp-final/, actualizá main desde origin/main y creá feature/tp-final-ui.

Ejecutá las tareas 9 a 12 del plan usando Superpowers, TDD y subagent-driven, con autonomía para implementar, revisar y corregir sin consultarme entre tareas.

Quiero una web funcional, respetando el mockup y conectada con la API existente. Debe permitir cargar archivos .raw, procesarlos, visualizar las curvas con Plotly.js (zoom, pan y valores interactivos), mostrar resultados, consultar el historial, reabrir ensayos, modificar parámetros y reprocesarlos.

También quiero poder seleccionar dos ensayos y superponer sus curvas, eligiendo entre ambas crudas o ambas procesadas, con leyenda y colores distintos.

Respetá las decisiones de la spec: persistencia automática, corrección de espesor, manejo de errores y sin crear versiones adicionales de un mismo ensayo.

No quiero datos simulados ni resultados hardcodeados en la aplicación. La interfaz debe utilizar los resultados reales del backend.

Al terminar, levantá la aplicación y probá el recorrido completo en el navegador, preferentemente con P3_304L_L.raw. Si no podés usar el navegador automáticamente, avisame para hacer la verificación manual.

Tenés autorización para realizar commits por tarea verificada. Documentá los problemas y decisiones relevantes.

Priorizá una aplicación funcional de punta a punta. No agregues funcionalidades fuera del MVP.

Detenete antes del push, PR o merge. No avances a la etapa 5.
```

**Qué buscaba:** Tener la interfaz funcionando de punta a punta contra la API
existente, respetando el mockup: carga y procesamiento de los `.raw`, gráficos
interactivos con Plotly, historial, reapertura, reprocesamiento y comparación de dos
curvas del mismo tipo. Pedí que no hubiera datos simulados ni resultados fijos, y
que el recorrido se probara en el navegador con `P3_304L_L.raw`, o que me avisara si
no se podía.

**Qué devolvió:** Commits `48b2523` (página de análisis), `c990742` (historial),
`1f1f394` (comparación), `75de2f3` (capturas), `aa2c6e3` (correcciones de la
revisión final: gráfico de comparación desactualizado, aviso viejo al abrir un
ensayo y parámetros heredados) y `3e2155b` (pendientes). Probó el recorrido en el
navegador integrado con `P3_304L_L.raw` y `508-1.raw`, con valores iguales a la
spec. Suite final: 131 passed. No pudo probar el selector de archivos nativo (armó
el archivo con sus bytes desde el navegador) ni ver el diálogo real de `confirm()`
(lo reemplazó desde la automatización). Errores propios que informó: un clic por
coordenadas cayó fuera de "Nuevo análisis" porque la página se había desplazado, y
después de navegar a `#comparacion` usó una referencia de antes de recargar, así que
"Comparar" pareció no andar; en los dos casos lo diagnosticó antes de tocar código.
Informó 7 decisiones que tomó por mí, entre ellas borrar `data/sptero.db` en lugar
de usar `SPTERO_DB` y tomar el HTML/CSS del plan como el mockup, porque
`index_sptero_mockup.html` no está en el repositorio.

---

## 14 — Aprobar la etapa 4 y subir la rama

Sesión 4 (12/10/2026).

```
Doy por aprobada la etapa 4. La interfaz está como quiero y no necesitamos más modificaciones.

Dejá documentados los pendientes menores para futuras versiones, sin seguir ampliando el MVP.

Subí feature/tp-final-ui a GitHub y pasame el enlace para crear el PR hacia main. No hagas el merge ni avances todavía a la etapa 5.
```

**Qué buscaba:** Aprobar la interfaz tal como quedó, dejar documentados los
pendientes menores para otra versión sin ampliar el MVP y subir la rama para el PR.

**Qué devolvió:** Respondió que los pendientes ya estaban en `docs/pendientes.md`
(commit `3e2155b`), así que no hizo otro commit. Subió la rama (6 commits) y pasó el
enlace del PR. No hizo merge.

---

## 15 — Etapa 5: verificación final y entrega

Sesión 5 (12/10/2026).

```
Ya fusioné la etapa 4 en main. Vamos con la etapa 5, la última del TP final de IISAIA.
Primero verificá el estado del repositorio, actualizá main desde origin/main y creá la rama feature/tp-final-entrega.
Ejecutá la Task 13 del plan usando Superpowers y los subagentes que correspondan. Tenés autonomía para completar la etapa sin consultarme por detalles menores.
El objetivo es dejar SPTERO Web listo para entregar y reproducir. Priorizá:

1. Verificar el funcionamiento completo desde una instalación limpia: dependencias, FastAPI, SQLite, frontend y pruebas.
2. Completar el README con instrucciones claras para instalar, ejecutar, utilizar y probar la aplicación, incluyendo Windows.
3. Revisar el cumplimiento del enunciado de IISAIA y documentar cómo se utilizaron Claude Code, skills, subagentes, TDD y GitHub.
4. Revisar prompts.md y proponer los registros que falten usando únicamente prompts reales. No inventes intervenciones ni motivaciones mías.
5. Ejecutar la suite completa y verificar nuevamente los resultados científicos con los archivos originales disponibles.
6. Comprobar que GitHub no incluya archivos .raw experimentales, bases SQLite, datos privados ni archivos temporales.
7. Revisar los pendientes, diferenciando limitaciones conocidas del MVP de problemas que impidan la entrega.

No agregues funcionalidades ni hagas cambios innecesarios en los algoritmos científicos o en la interfaz, que ya están aprobados.
Si aparece un error importante que impida instalar, ejecutar o utilizar la aplicación, corregilo y verificá la solución.
Documentá los resultados reales de las pruebas, las limitaciones y los problemas encontrados. Hacé los commits necesarios y una revisión final.
Al terminar quiero un informe breve: qué quedó listo, qué falta completar por mi parte, cómo ejecutar la aplicación y si considerás que cumple los requisitos de entrega.
No hagas push, PR ni merge hasta que revisemos el resultado.
```

**Qué buscaba:** Dejar SPTERO Web listo para entregar y reproducir: comprobar que
funciona desde una instalación limpia, completar el README como informe con
instrucciones para Windows, revisar el cumplimiento de la consigna, completar
`prompts.md` solo con prompts reales, volver a validar los resultados con los
originales y confirmar que el repositorio no publica datos privados. Todo sin
funcionalidades nuevas ni cambios en lo ya aprobado, y con un informe antes de
cualquier push.

**Qué devolvió:** Trabajó inline con `executing-plans`, retomando el ledger de
las etapas anteriores. Actualizó `main` por fast-forward (el local no tenía el merge
del PR #5) y creó `feature/tp-final-entrega`. Clonó la rama en un directorio vacío,
creó un entorno nuevo e instaló las dependencias: 117 passed y 14 skipped sin los
archivos originales, 131 passed con ellos. Levantó la app desde ese clon y recorrió
la API con `P3_304L_L.raw` y la interfaz en el navegador integrado (abrir,
recalcular con "0,48", cargar `508-1.raw`, comparar, eliminar), con los valores de
la spec y sin errores en la consola. El `verificador-cientifico` comparó el core con
el original en cuatro ensayos reales, sin y con corrección: diferencia relativa 0.
Revisó que el historial del repositorio no tenga `.raw`, bases ni archivos
temporales, releyó la consigna en el repositorio de la materia y un subagente
recuperó de los transcripts los prompts 6 a 15. Completó el README (`4b599c7`),
clasificó los pendientes y una revisión final con un revisor nuevo encontró cuatro
problemas importantes en el informe y varias imprecisiones, que corrigió antes del
último commit. No cambió código.

Errores propios: intentó borrar un directorio temporal con `rm -rf` y la regla
`deny` lo frenó; el clon en el directorio temporal de la sesión falló por la ruta
larga de Windows; pidió `/curve?type=processed` en vez de `?source=processed` y lo
tomó un momento como posible bug; un heredoc para escribir `prompts.md` no llegó a
ejecutarse; y el primer borrador del README tenía las afirmaciones falsas que marcó
la revisión (entre ellas, el pie de una captura y la tabla de endpoints).
