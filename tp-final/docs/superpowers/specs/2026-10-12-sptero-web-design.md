# SPTERO Web — Especificación de diseño

Fecha: 2026-10-12 · Autor: Julián Alejandro Fierens · Estado: **revisada; decisiones D1–D5 cerradas el 12/10/2026**

Esta spec sale de la sesión de brainstorming del 12/10/2026 y es la referencia de
qué se construye en el trabajo final. Si algo cambia durante la implementación,
se edita este archivo en un commit propio y se explica el porqué en el README.

## 1. Problema, usuarios y objetivo

SPTERO es un script de Python que analiza ensayos Small Punch Test (SPT) a partir
de los archivos `.raw` que exporta la máquina Instron. Hoy se usa por consola:
pide los parámetros con `input()`, abre diálogos de tkinter, muestra gráficos de
matplotlib y deja los resultados en un PDF suelto. No hay historial ni forma de
volver a un análisis.

**Usuarios:** quien ensaya probetas SPT en el laboratorio (hoy, Julián) y necesita
obtener los parámetros de un ensayo, guardarlos y volver a ellos.

**Objetivo del MVP:** el mismo análisis científico, en un flujo web completo y
persistente: cargar `.raw` → procesar → ver la curva → calcular Pm · dm · Rm ·
fluencia t/10 → guardar → consultar el historial, reprocesar y comparar.

**Criterio de éxito:** sobre el ensayo de referencia `P3_304L_L.raw`, la web da los
mismos valores que SPTERO original (tolerancia relativa 1e-9) y el recorrido de
punta a punta funciona en el navegador.

## 2. Alcance

**Entra (MVP):**
- Carga y validación de `.raw` por contenido.
- Preprocesado con la misma secuencia que el original (sección 4).
- Corrección de flexibilidad opcional con C_P manual.
- Pm, dm, Rm (β configurable) y fluencia por t/10 (Py_t/10 y σy_t/10).
- Persistencia en SQLite del archivo original (BLOB), parámetros y resultado.
- Guardado automático: cada ensayo queda persistido al analizarlo, con su estado visible.
- Historial: listar, reabrir, reprocesar con otros parámetros o con el espesor
  corregido (siempre sin versiones) y eliminar con confirmación.
- Gráfico interactivo con Plotly.js: zoom, desplazamiento, valores al pasar el
  mouse y restablecimiento de ejes.
- Comparación de dos ensayos del historial con curvas superpuestas del mismo tipo
  (las dos crudas o las dos procesadas, a elección), solo lectura.

**Queda para después (roadmap de la presentación):** probetas entalladas, cálculo
automático de C_P (A.2 / A.3), MAO y Fe bilineal, ductilidad (ESP, εf, pop-in),
reportes PDF, autenticación, procesamiento en lote y dashboards. La comparación de
dos ensayos se adelanta del roadmap al MVP por pedido explícito, acotada a dos
curvas y sin métricas comparativas.

## 3. Arquitectura

```
Navegador (HTML + CSS + JS vanilla + Plotly.js)
        │  HTTP/JSON (contrato openapi.yaml v1.1)
        ▼
app/        FastAPI: rutas, validación de entrada, mapeo de errores
        │
        ├──► app/service.py     orquesta: lee el BLOB, llama al core, guarda el resultado
        │         │
        │         ├──► sptero_core/   lógica científica pura (numpy), sin I/O de usuario
        │         └──► app/repository.py   SQL explícito con sqlite3 (stdlib)
        ▼
SQLite (data/sptero.db)
```

Regla de dependencias: `sptero_core` no importa nada de `app` ni de FastAPI y no
imprime ni lee archivos del disco: recibe bytes o arrays y devuelve datos. Así se
puede testear solo y compararlo directamente contra el script original. `app/`
depende del core y del repositorio, nunca al revés.

### Módulos

| Módulo | Responsabilidad | Origen |
|---|---|---|
| `sptero_core/raw.py` | Encontrar el encabezado de la tabla, parsear `Extension mm` / `Load N`, invertir signo si la mediana es negativa y ordenar por x. Entra `bytes`, sale `(x, y, invertida)`. | `encontrar_inicio_tabla`, `cargar_raw_a_listas` (sin `print`, desde bytes) |
| `sptero_core/preproceso.py` | Corrección de flexibilidad y cero por precarga, en la secuencia del original. | `corregir_desplazamiento_por_flexibilidad_A1`, `cero_automatico_por_precarga` |
| `sptero_core/calculos.py` | Pm/dm, Rm, regresión lineal, Py_t/10 y σy. | `max_load_and_dm`, `rm_from_beta`, `linear_regression_and_r2`, `interp_x_at_sign_change`, `estimar_py_t10`, `sigma_y_from_py` |
| `sptero_core/analisis.py` | Función única `analizar(contenido, espesor, parametros)` que encadena todo y devuelve curva procesada + resultados. Es lo que llama el servicio. | nuevo (reemplaza el `main()` de consola) |
| `app/schemas.py` | Modelos Pydantic que reflejan `openapi.yaml`. | nuevo |
| `app/repository.py` | CRUD de ensayos y resultados con SQL explícito. | nuevo |
| `app/service.py` | Casos de uso: subir, procesar, obtener curva, borrar. | nuevo |
| `app/main.py` | Rutas FastAPI, handlers de error, servir `static/`. | nuevo |
| `static/` | `index.html`, `styles.css`, `app.js`. Estilo del mockup. | mockup de la entrega parcial |

Las funciones científicas se **copian sin cambiar las fórmulas**. Los únicos
cambios permitidos son de entrada/salida: leer desde `bytes` en lugar de una ruta,
quitar `print`, devolver un indicador en lugar de avisar por consola. Cada cambio
de este tipo queda cubierto por un test de caracterización (sección 9).

## 4. Pipeline de procesamiento

Secuencia del original (`main()` de `Programa SPTERO.py`, líneas 979–1058), que la
web respeta:

1. **Leer** el `.raw`: tabla desde la primera fila que empieza con `"Time` y
   contiene `Load` y `;`; columnas `Extension mm` (x) y `Load N` (y); separador
   decimal `.` o `,`; filas no numéricas se descartan; mínimo 20 puntos.
2. **Invertir signo** de x y/o y si su mediana es negativa (la Instron exporta
   compresión en negativo) y **ordenar** por x creciente.
3. Si `apply_compliance_correction` es verdadero:
   1. `v = vref − F·C_P`.
   2. Reordenar por x.
   3. **Cero por precarga** con F0 = 5 N: se toma el primer punto con F ≥ 5 N como
      contacto, se descartan los anteriores y se resta su x (F no se desplaza).
4. **Pm** = máximo de F; **dm** = x en ese punto.
5. **Rm** = β·Pm / (dm·t). Si dm ≤ 0 o t ≤ 0 → error `PROCESSING_FAILED`.
6. **Py_t/10**: recta elástica ajustada sobre los puntos con F ≤ 0,10·Pm (o los
   primeros max(10, 5 %) si son menos de 8), desplazada t/10; Py es el cruce con la
   curva, y su desplazamiento queda como `py_t10_displacement_mm`. **σy_t/10** =
   0,346·Py/t². Si no hay cruce, los tres son `null` (no es error).

Los parámetros que se usan en el original con su valor por defecto son los mismos:
C_P = 2,281e-4 mm/N, β = 0,277, F0 = 5 N.

> **Decisión D1 (cerrada) — cero por precarga: se sigue la secuencia del original.**
> El cero se aplica solo dentro de la rama con corrección de flexibilidad (paso
> 3.3). Esto revierte la decisión 4 del TP2, que lo aplicaba siempre; el cambio
> queda en el contrato v1.1 del TP final y `TP2/` no se modifica. Con
> `P3_304L_L.raw` no hay diferencia (el primer punto ya supera 5 N, i0 = 0), pero
> con otros ensayos sí puede haberla. Un test sintético con una curva que arranca
> por debajo de 5 N fija este comportamiento.

> **Diferencia conocida con el original — t/10 sin MAO.** En el script,
> `estimar_py_t10` usa los puntos de Zona I del ajuste MAO cuando MAO se calculó, y
> solo si no, cae al criterio F ≤ 0,10·Pm. MAO queda fuera del MVP, así que la web
> reproduce **la rama sin MAO**. Un análisis hecho por consola con zonas MAO
> cargadas puede dar otro Py_t/10. Se documenta en la interfaz (texto de ayuda) y
> en el README.

**Valores de referencia** (`P3_304L_L.raw`, 582 puntos, t = 0,5 mm, β = 0,277,
calculados con el script original el 12/10/2026):

| Caso | Pm [N] | dm [mm] | Rm [MPa] | Py_t/10 [N] | σy_t/10 [MPa] |
|---|---|---|---|---|---|
| Sin corrección | 2372,2 | 2,2709 | 578,7 | 274,9 | 380,5 |
| C_P = 2,281e-4 mm/N | 2372,2 | 1,7319 | 758,8 | 281,8 | 390,1 |

## 5. Contrato de la API (v1.1)

Base: `TP2/openapi.yaml` v1.0.0. Se copia a `tp-final/openapi.yaml` y evoluciona
ahí; la carpeta `TP2/` no se toca. Se mantienen los 8 endpoints y se agrega uno
(`PATCH /tests/{testId}`, por D2):

| Método | Ruta | Uso | Códigos |
|---|---|---|---|
| POST | `/tests` | subir ensayo (multipart: `file`, `material`, `thickness_mm`) | 201 · 400 |
| GET | `/tests` | historial | 200 |
| GET | `/tests/{testId}` | detalle (incluye `result` o `null`) | 200 · 404 |
| PATCH | `/tests/{testId}` | **nuevo:** corregir el espesor y recalcular el resultado | 200 · 400 · 404 · 422 |
| DELETE | `/tests/{testId}` | borrar ensayo, archivo y resultado | 204 · 404 |
| GET | `/tests/{testId}/file` | descargar el `.raw` original | 200 · 404 |
| GET | `/tests/{testId}/curve?source=raw\|processed` | curva | 200 · 400 · 404 |
| PUT | `/tests/{testId}/result` | procesar / reprocesar (idempotente) | 200 · 400 · 404 · 422 |
| GET | `/tests/{testId}/result` | consultar resultado | 200 · 404 |

**Cambios v1.0 → v1.1:**
1. `Result` suma `py_t10_n`, `py_t10_displacement_mm` y `sigma_y_t10_mpa`
   (`number | null`: `null` si no se encuentra el cruce). El desplazamiento de Py
   es el `x_py` de `estimar_py_t10` y permite marcar el punto en el gráfico
   (agregado al revisar el plan, 12/10/2026).
2. La descripción del pipeline pasa a la secuencia de la sección 4: el cero por
   precarga se aplica solo con corrección de flexibilidad (D1; revierte la
   decisión 4 del TP2).
3. Nuevo `PATCH /tests/{testId}` con cuerpo `TestUpdate {thickness_mm}` (D2;
   revierte la parte de la decisión 3 del TP2 que impedía editar el espesor). Ver
   "Corrección del espesor" más abajo.
4. Las respuestas 400 de `POST /tests` (falta un campo o `thickness_mm` ≤ 0), de
   `PATCH /tests/{testId}`, de `PUT /result` y de `/curve` documentan el código
   `INVALID_PARAMETERS`, que estaba en el enum pero no se usaba (observación
   pendiente del TP2). `INVALID_FILE` queda solo para problemas del archivo.
5. `GET /tests/{testId}/file` se declara `application/octet-stream` (antes solo
   `text/csv`, aunque se aceptan `.raw`).
6. `GET /tests` documenta el orden: más reciente primero.

Se mantienen las reglas del TP2: un único resultado por ensayo que se reemplaza al
reprocesar; en `PUT` los campos no enviados toman su valor por defecto; si los
parámetros son iguales a los actuales no cambia nada, ni siquiera `processed_at`.

**Corrección del espesor (D2).** El espesor sigue siendo un dato del ensayo (es una
medida de la probeta, no un parámetro de cálculo), por eso se corrige sobre el
recurso ensayo y no en `ProcessingRequest`. Reglas de `PATCH /tests/{testId}`:
- Cuerpo `{"thickness_mm": <número > 0>}`, obligatorio. El material no se edita.
- Si el espesor es igual al actual, no cambia nada (idempotente).
- Si el ensayo tiene resultado, se recalcula en la misma transacción con los
  parámetros guardados (corrección, C_P, β) y se actualiza `processed_at`. El
  espesor cambia Rm, el offset t/10, Py_t/10 y σy_t/10. No se guardan versiones:
  el resultado anterior se reemplaza.
- Si el recálculo falla (`PROCESSING_FAILED`), no se guarda nada: el ensayo queda
  con su espesor y su resultado anteriores.
- Si el ensayo no tiene resultado, solo se actualiza el espesor.
- Responde 200 con el `Test` actualizado (resultado incluido).

FastAPI responde 422 por defecto ante un cuerpo inválido. El contrato pide 400
`INVALID_PARAMETERS`, así que se registra un handler propio para
`RequestValidationError`.

## 6. Datos

SQLite en `tp-final/data/sptero.db` (ruta configurable con `SPTERO_DB`; la carpeta
`data/` no se versiona). Acceso con `sqlite3` de la stdlib y `PRAGMA foreign_keys = ON`.

```sql
CREATE TABLE IF NOT EXISTS tests (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    filename      TEXT    NOT NULL,
    material      TEXT    NOT NULL,
    thickness_mm  REAL    NOT NULL CHECK (thickness_mm > 0),
    uploaded_at   TEXT    NOT NULL,          -- ISO 8601 UTC
    point_count   INTEGER NOT NULL,
    raw_file      BLOB    NOT NULL           -- archivo original, sin modificar
);

CREATE TABLE IF NOT EXISTS results (
    test_id                      INTEGER PRIMARY KEY
                                 REFERENCES tests(id) ON DELETE CASCADE,
    apply_compliance_correction  INTEGER NOT NULL,   -- 0/1
    compliance_mm_per_n          REAL,               -- NULL si no hubo corrección
    beta                         REAL    NOT NULL,
    pm_n                         REAL    NOT NULL,
    dm_mm                        REAL    NOT NULL,
    rm_mpa                       REAL    NOT NULL,
    py_t10_n                     REAL,               -- NULL si no hubo cruce
    py_t10_displacement_mm       REAL,               -- NULL si no hubo cruce
    sigma_y_t10_mpa              REAL,
    processed_at                 TEXT    NOT NULL
);
```

- `results.test_id` es a la vez PK y FK: garantiza un resultado por ensayo. Reprocesar
  es un `INSERT ... ON CONFLICT(test_id) DO UPDATE`.
- Las curvas **no se guardan**: se recalculan desde el BLOB cuando se piden. Son
  ~600 puntos y el cálculo es determinista; guardarlas duplicaría datos que pueden
  quedar desincronizados con los parámetros.
- `GET /tests` selecciona columnas explícitas para no traer el BLOB al listar.

## 7. Interfaz

Una sola página servida por FastAPI desde `static/`, con el estilo del mockup
(`index_sptero_mockup.html`: barra navy, tarjetas blancas, acento teal).

**Panel izquierdo — Datos del ensayo:** zona de carga (arrastrar o elegir `.raw`),
material, espesor t, β, C_P y casilla "Aplicar corrección de flexibilidad". Botón
**Analizar ensayo**, que guarda y procesa en un solo paso (`POST /tests` +
`PUT /result`). Cuando se reabre un ensayo guardado, el material queda solo lectura,
t, β, C_P y la corrección son editables, y el botón pasa a **Recalcular**: si
cambió t llama a `PATCH /tests/{id}`, si cambiaron los parámetros llama a
`PUT /result` (en ese orden, y solo lo que cambió).

**Estado de guardado (D4):** no hay botón Guardar. Un indicador visible en el
panel muestra el estado del ensayo abierto: *Guardando…*, *Guardado · procesado*,
*Guardado · sin procesar* (con el mensaje de error si el procesamiento falló) o
*Error al guardar*. Si `POST /tests` funciona pero `PUT /result` falla, el ensayo
queda guardado sin procesar y se puede corregir y recalcular, o eliminar.

**Eliminar (D4):** botón **Eliminar ensayo** en el panel y en cada fila del
historial. Siempre pide confirmación en un diálogo que nombra el archivo
("¿Eliminar P3_304L_L.raw y su resultado? No se puede deshacer."); recién al
confirmar llama a `DELETE /tests/{id}`.

**Gráfico — Curva carga–desplazamiento (Plotly.js):** curva procesada, marcador de
Pm (círculo rojo, como el mockup) y punto Py_t/10. Barra de Plotly con zoom,
desplazamiento, restablecer ejes y valores al pasar el mouse
(`desplazamiento [mm]`, `carga [N]`).

**Resultados:** tarjetas con Pm, dm, Rm, Py_t/10 y σy_t/10, y debajo los parámetros
con que se calcularon. Texto de ayuda sobre la diferencia t/10 sin MAO.

**Historial:** tabla con ensayo, material, Pm, Rm, fecha y estado (procesado / sin
procesar). Cada fila se puede **abrir** (carga el ensayo en el panel para
reprocesar), **eliminar** (con confirmación) o **marcar para comparar**.

**Comparación (D3):** con exactamente dos ensayos marcados se habilita
**Comparar**. Un selector elige el tipo de curva, igual para las dos: **crudas** o
**procesadas**. "Procesadas" solo está disponible si los dos ensayos tienen
resultado; si no, la opción aparece deshabilitada con el motivo. El gráfico Plotly
muestra las dos curvas superpuestas, cada una de un color, con una leyenda que
indica archivo, material y tipo de curva. Usa solo `GET /tests/{id}/curve?source=…`
y no escribe nada en el servidor.

Plotly.js se carga desde CDN con versión fija (sin `latest`). Sin conexión a
internet el gráfico no carga; se acepta para el MVP y se anota en el README.

**Decisiones de interfaz cerradas (12/10/2026):**
- **D2:** el espesor de un ensayo guardado se puede corregir y el resultado se
  recalcula sin crear versiones (`PATCH /tests/{id}`, sección 5).
- **D3:** se comparan dos curvas del mismo tipo, crudas o procesadas, a elección
  del usuario.
- **D4:** guardado automático con estado visible y sin botón Guardar. Eliminar
  siempre pide confirmación.

## 8. Errores

Todas las respuestas de error usan `Error {code, message}` con mensaje en español.

| Situación | HTTP | `code` |
|---|---|---|
| Archivo sin encabezado, sin columnas esperadas o con < 20 puntos | 400 | `INVALID_FILE` |
| Falta `material` o `thickness_mm`, o `thickness_mm` ≤ 0 (en `POST` o `PATCH`) | 400 | `INVALID_PARAMETERS` |
| Cuerpo de `PUT` con tipos inválidos o valores ≤ 0 | 400 | `INVALID_PARAMETERS` |
| `source` distinto de `raw`/`processed` | 400 | `INVALID_PARAMETERS` |
| El ensayo no existe | 404 | `TEST_NOT_FOUND` |
| Se pide resultado o curva procesada de un ensayo sin procesar | 404 | `RESULT_NOT_FOUND` |
| Rm no calculable (dm ≤ 0), al procesar o al recalcular por `PATCH` | 422 | `PROCESSING_FAILED` |

Los `ValueError` del core se traducen en el servicio; el core no conoce HTTP. En la
interfaz, cada error se muestra en un aviso dentro de la tarjeta correspondiente,
con el `message` del servidor.

## 9. Estrategia de pruebas

TDD: cada test se ve fallar antes de escribir el código que lo hace pasar.

1. **Caracterización del core contra el original** (`tests/test_caracterizacion.py`).
   Importa `Programa SPTERO.py` desde la ruta de `SPTERO_ORIGINAL` y lee el ensayo
   de `SPTERO_RAW_SAMPLE`; compara cada función copiada y el pipeline completo
   (con y sin corrección) con tolerancia relativa 1e-9, y verifica los valores de
   referencia de la sección 4. Si las variables no están definidas, se saltean
   (`pytest.skip`) con un mensaje claro: ni el script original ni el `.raw` se
   publican en el repositorio.
2. **Core con curva sintética** (`tests/test_raw.py`, `tests/test_calculos.py` y
   `tests/test_analisis.py`, uno por módulo del core). Se genera en el test un
   `.raw` mínimo (encabezado + tabla) con una curva conocida: detección de
   encabezado, coma decimal, inversión de signo, orden, error con < 20 puntos y sin
   encabezado, Pm/dm, Rm, t/10 con y sin cruce, y cero por precarga aplicado solo
   con corrección (D1), con una curva que arranca por debajo de 5 N.
3. **Repositorio** (`tests/test_repository.py`) sobre una base temporal: alta,
   listado sin BLOB, reemplazo de resultado, borrado en cascada.
4. **Servicio y API** (`tests/test_service.py` para los casos de uso;
   `tests/test_api.py` con `TestClient` y base temporal): cada endpoint y
   cada código de error de la sección 8, idempotencia de `PUT` y de `PATCH`, y
   que un `PATCH` que falla al recalcular no deja cambios a medias.
5. **Contrato** (`tests/test_contrato.py`): las rutas y métodos de `app.openapi()`
   coinciden con los de `openapi.yaml`.
6. **Interfaz**: verificación de punta a punta en el navegador, guiada por MCP
   (sección 10), con el ensayo de referencia cargado localmente. No se automatiza
   con un framework de tests de UI (fuera de alcance).

"En verde" significa la suite completa, con su salida pegada en el PR.

## 10. Configuración del agente

La consigna pide la configuración del agente versionada dentro de `tp-final/`. Cada
pieza tiene un motivo concreto:

| Pieza | Para qué |
|---|---|
| `tp-final/CLAUDE.md` | Mapa de carpetas, comandos, convenciones y reglas de trabajo del TP final. Remite a esta spec y al plan. |
| `.claude/settings.json` | Permisos pensados para el proyecto: correr tests y servidor sin preguntar; preguntar antes de commit, push, merge, rebase, reset o instalar paquetes; prohibido editar `TP1/` (congelado) y `TP2/` (entregado), `rm -rf` y push forzado. |
| `.claude/rules/core.md` (`paths: sptero_core/**`) | Las fórmulas no se tocan; todo cambio en el core va con test de caracterización. |
| `.claude/rules/api.md` (`paths: app/**`, `openapi.yaml`) | El contrato manda: códigos y `Error` de la sección 8; si cambia la API, primero cambia `openapi.yaml`. |
| `.claude/skills/registrar-prompt/` | Skill propia: agrega una entrada a `prompts.md` con el formato acordado y deja "Qué buscaba" para Julián. Se invoca a mano (`/registrar-prompt`) porque qué prompt es relevante lo decide él. |
| `.claude/agents/verificador-cientifico.md` | Subagente de solo lectura: compara el core con el script original (código y resultados) y reporta diferencias. Se justifica porque esa comparación es lo que más contexto consume (leer 1.500 líneas del original) y conviene aislarla de la sesión principal. |
| MCP (etapa 4) | Navegador controlado por el agente para la verificación de punta a punta de la interfaz. |

> **Decisión D5 (cerrada) — la configuración vive en `tp-final/.claude/`** y las
> sesiones de desarrollo arrancan con el directorio de trabajo en `tp-final/`.

**Qué dice la documentación** (consultada el 12/10/2026 con un subagente):
- `tp-final/CLAUDE.md`, las skills y las rules se cargan aunque la sesión arranque en
  la raíz del repo, a demanda, cuando el agente trabaja con archivos de `tp-final/`.
- `settings.json`, los subagentes y `.mcp.json` **solo** se leen desde el directorio
  de trabajo de la sesión, no desde subcarpetas.
- No está documentado contra qué raíz se resuelven los `paths:` de una rule anidada;
  las rules declaran los dos patrones (`sptero_core/**` y `tp-final/sptero_core/**`).
- Permisos: solo se consultan reglas `Edit(...)` y `Read(...)` para archivos; una
  regla `Write(...)` con ruta se acepta pero **nunca se aplica**. Las rutas siguen
  la sintaxis de gitignore y no pueden salir de su ancla con `..`; para alcanzar
  `TP1/` desde `tp-final/` hace falta una ruta absoluta `//…`. Por eso las reglas
  quedaron como `Edit(//**/TP1/**)` y `Edit(//**/TP2/**)`, que cubren cualquier
  carpeta `TP1`/`TP2` (son nombres que solo existen en este repositorio).

**Qué se comprobó en la práctica** (12/10/2026, `claude.exe` 2.1.295 en modo no
interactivo, leyendo el evento `init` que lista agentes y skills):

| Sesión iniciada en | `settings.json` | subagente `verificador-cientifico` | skill `registrar-prompt` |
|---|---|---|---|
| `tp-final/` | se lee | cargado | cargada (`/registrar-prompt`) |
| raíz del repo | no se lee | no aparece | no aparece al inicio |

Con la sesión en `tp-final/`, la CLI avisó que ignoraba las 9 reglas `allow` porque
el workspace todavía no está marcado como confiable; las reglas `deny` y `ask`
aplican igual. Las `allow` se activan cuando Julián acepta el diálogo de confianza
en la primera sesión interactiva. Las reglas `deny` sobre `TP1/` y `TP2/` se
verificaron contra la documentación, pero **no se ejercitaron**: la CLI no tenía
sesión iniciada y no se pudo pedirle al modelo que intentara una edición. Queda
como chequeo al empezar la etapa 2 (pedir una edición en `TP1/` y ver que se
rechaza).

## 11. Proceso y registro del uso de IA

- Superpowers: brainstorming (esta spec) → writing-plans (plan en
  `docs/superpowers/plans/`) → ejecución con review por tarea →
  requesting-code-review → verification-before-completion →
  finishing-a-development-branch.
- GitHub Flow: una rama `feature/tp-final-<etapa>` por etapa, commits chicos con
  `tipo: descripción`, un PR por etapa.
- `tp-final/prompts.md`: prompts relevantes textuales, con "Qué buscaba" (lo escribe
  Julián) y "Qué devolvió".
- Las desviaciones del modelo se registran en el momento para "Qué salió mal".
- Las decisiones D1–D5 se cerraron en la revisión de esta spec y están registradas
  en el README.

## 12. Riesgos

- **El script original no está en el repo.** La caracterización depende de una ruta
  local; en otra máquina esos tests se saltean. Mitigación: tests sintéticos que
  cubren el pipeline y valores de referencia fijados en la spec.
- **Plotly por CDN.** Sin internet no hay gráfico. Aceptado para el MVP.
- **Codificación del `.raw`.** El original abre el archivo con la codificación del
  sistema (`errors="replace"`). La web decodifica los bytes como UTF-8 con
  `errors="replace"`; el encabezado y los números son ASCII, así que no cambia el
  resultado. Se cubre con un test.
