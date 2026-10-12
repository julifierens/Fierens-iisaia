# Prompts — TP final

Prompts relevantes del desarrollo de SPTERO Web con Claude Code, copiados textuales
y en orden. "Qué buscaba" lo escribe el autor; "Qué devolvió" resume lo que hizo el
modelo, errores incluidos. A diferencia del TP1 y el TP2, el trabajo final se hace
en varias sesiones; cada entrada indica a cuál pertenece.

Los "Qué buscaba" de las entradas 1 a 3 los redactó el modelo a pedido mío (prompt
4), a partir de los objetivos que habíamos acordado en la conversación, y los revisé.

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

**Qué buscaba:** _(completa Julián)_

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

**Qué buscaba:** _(completa Julián)_

**Qué devolvió:** Agregó `py_t10_displacement_mm` a la spec (pipeline, cambios del
contrato y tabla `results`) y alineó los nombres de los archivos de test. En el
plan reemplazó el "cambio a confirmar" por las decisiones tomadas: ejecución
subagent-driven, con un revisor por tarea enfocado en lo que más riesgo tiene en
cada etapa (fidelidad al original, contrato y atomicidad del `PATCH`), la
verificación en el navegador hecha por la sesión principal y una revisión de rama
al cerrar cada etapa. También dejó escrita la autorización de commits por tarea,
sin push, PR ni merge. Commiteó el cierre de la etapa 1 y, sin hacer push, explicó
cómo crear y fusionar el PR.
