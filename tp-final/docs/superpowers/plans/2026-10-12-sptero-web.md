# SPTERO Web — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir SPTERO Web: una app FastAPI + SQLite + JS/Plotly que reproduce el análisis SPT del script original (Pm, dm, Rm, t/10) con persistencia, reprocesamiento, corrección de espesor y comparación de curvas.

**Architecture:** `sptero_core/` es la lógica científica copiada del script original, pura y testeada contra él. `app/` expone el contrato `openapi.yaml` v1.1 con FastAPI. `service.py` orquesta y `repository.py` guarda en SQLite con `sqlite3`. `static/` es una página única en JS vanilla con Plotly.js, servida por la misma app.

**Tech Stack:** Python 3.12 · numpy 2.4.1 · FastAPI 0.143.0 · uvicorn 0.54.0 · python-multipart 0.0.32 · pytest 9.1.1 · httpx 0.28.1 · PyYAML 6.0.3 · Plotly.js 2.35.2 (CDN) · SQLite (stdlib).

**Spec:** `tp-final/docs/superpowers/specs/2026-10-12-sptero-web-design.md`

## Decisiones tomadas al revisar el plan (12/10/2026)

- **`py_t10_displacement_mm`** se agrega al `Result` v1.1 y a la tabla `results`
  (`number | null`, `null` si no hay cruce). Es el `x_py` que ya devuelve
  `estimar_py_t10`, y permite marcar Py_t/10 en el gráfico. La spec ya está
  actualizada (secciones 4, 5 y 6).
- **Ejecución subagent-driven** (`superpowers:subagent-driven-development`), con
  las verificaciones que aportan valor y sin pasos de más:
  - Un subagente implementa cada tarea y un revisor la controla contra la spec y
    esta tarea antes de pasar a la siguiente.
  - El revisor de las Tasks 1–4 mira sobre todo la fidelidad al original. El de
    las Tasks 5–8, el contrato y la atomicidad del `PATCH`.
  - Las Tasks 9–12 (interfaz) las implementa un subagente, pero la verificación
    en el navegador la hace la sesión principal, que es la que tiene el navegador
    integrado.
  - Al cerrar cada etapa hay una revisión de toda la rama
    (`superpowers:requesting-code-review`) antes de pedir el PR.
- **Commits:** autorizados uno por tarea dentro de cada etapa, siempre después de
  verificar los resultados (tests en verde con la salida a la vista). **Push, PR y
  merge solo con aprobación explícita de Julián.**

## Global Constraints

- Todo vive en `tp-final/`. Los comandos se corren con el directorio de trabajo en `tp-final/`. `TP1/` y `TP2/` no se tocan.
- **Sesión:** la ejecución se hace en una sesión de Claude Code abierta en `tp-final/` (D5), para que carguen `settings.json`, las rules y el subagente.
- Python del entorno: `.venv/Scripts/python` (Windows). Tests: `.venv/Scripts/python -m pytest`.
- Las fórmulas del core no se modifican. Los únicos cambios permitidos son de entrada/salida (bytes en vez de ruta, sin `print`). Cada función copiada se compara con la original (tolerancia relativa 1e-9).
- El script original y los `.raw` reales no se versionan. Variables locales: `SPTERO_ORIGINAL`, `SPTERO_RAW_SAMPLE`; base: `SPTERO_DB` (por defecto `data/sptero.db`).
- Pipeline (D1): leer → invertir signo/ordenar → [solo con corrección: v = vref − F·C_P → reordenar → cero por precarga F0 = 5 N] → Pm/dm → Rm = β·Pm/(dm·t) → t/10 por la rama sin MAO.
- Valores por defecto: C_P = 2.281e-4 mm/N, β = 0.277, F0 = 5 N.
- Errores: siempre `{"code", "message"}` con `message` en español. 400 `INVALID_FILE` / `INVALID_PARAMETERS`, 404 `TEST_NOT_FOUND` / `RESULT_NOT_FOUND`, 422 `PROCESSING_FAILED`. La validación de FastAPI responde 400, nunca 422.
- `PUT /result` es idempotente, y si no cambian los parámetros tampoco cambia `processed_at`. `PATCH /tests/{id}` corrige solo `thickness_mm`, recalcula en una transacción y, **si el recálculo falla, no cambia ni el espesor ni el resultado**.
- Nombres de la API en inglés; código interno, comentarios, mensajes y commits en español (`tipo: descripción en minúscula`, con la línea `Co-Authored-By` del agente).
- Ramas: `feature/tp-final-core` (Tasks 1–4), `feature/tp-final-api` (Tasks 5–8), `feature/tp-final-ui` (Tasks 9–12), y cierre (Task 13) en `feature/tp-final-cierre`. Cada rama sale de `main` actualizado después de que Julián mergea el PR anterior. Commit por tarea autorizado después de verificar; **push, PR y merge solo con aprobación de Julián**.
- Interfaz: datos del usuario (nombre de archivo, material) siempre con `textContent`, nunca con `innerHTML`.

## Review Focus

1. **Archivo que no es un `.raw`** (vacío, PDF, binario): `POST /tests` responde 400 `INVALID_FILE` y nunca 500. Test en la Task 8 (`test_post_archivo_que_no_es_raw`).
2. **Encabezado con caracteres que no son UTF-8** (cp1252, típico de los exports de Windows, por ejemplo una nota con "é"): el archivo se lee igual. Test en la Task 1 (`test_encabezado_cp1252`); además, todos los `.raw` sintéticos se generan en cp1252.
3. **Con corrección, una curva que nunca llega a 5 N**: el cero no recorta nada y el análisis termina. Test en la Task 3 (`test_precarga_nunca_alcanzada`).
4. **`PATCH` con un recálculo que falla**: no cambia ni el espesor ni el resultado anterior. Tests en la Task 6 (rollback de la base), la Task 7 (falla del cálculo) y la Task 8 (de punta a punta).
5. **Números con coma decimal en el formulario** ("0,5"): la interfaz los acepta. Verificación en el navegador en la Task 9 (paso de coma decimal).

---

# Etapa 2 — Motor científico (`feature/tp-final-core`)

### Task 1: Entorno y lectura del `.raw`

**Files:**
- Create: `tp-final/requirements.txt`, `tp-final/pytest.ini`
- Create: `tp-final/sptero_core/__init__.py`, `tp-final/sptero_core/raw.py`
- Test: `tp-final/tests/conftest.py`, `tp-final/tests/test_raw.py`

**Interfaces:**
- Produces: `sptero_core.raw.CurvaRaw(x: np.ndarray, y: np.ndarray, invertida: bool)`, `sptero_core.raw.leer_raw(contenido: bytes, xcol="Extension mm", ycol="Load N") -> CurvaRaw` (lanza `ValueError` con mensaje en español), `sptero_core.raw.encontrar_inicio_tabla(lines) -> int | None`.
- Produces (tests): fixtures `construir_raw(x, y, decimal=".", nota=..., encabezado=...) -> bytes`, `curva_sintetica() -> (x, y)`, `curva_lineal() -> (x, y)`, `curva_decreciente() -> (x, y)`.

- [ ] **Step 0: Comprobar la configuración del agente (pendiente de la etapa 0)**

En la sesión abierta en `tp-final/`, pedirle al agente que agregue una línea vacía al final de `../TP1/README.md`. Resultado esperado: la herramienta `Edit` lo rechaza por la regla `deny` `Edit(//**/TP1/**)`. Anotar el resultado (rechazado o no) para el README, en "Cómo gestioné el contexto". Si **no** se rechaza, frenar y avisarle a Julián antes de seguir.

- [ ] **Step 1: Crear el entorno**

`tp-final/requirements.txt`:
```text
numpy==2.4.1
fastapi==0.143.0
uvicorn==0.54.0
python-multipart==0.0.32
httpx==0.28.1
pytest==9.1.1
PyYAML==6.0.3
```

`tp-final/pytest.ini`:
```ini
[pytest]
testpaths = tests
pythonpath = .
```

Run:
```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```
Expected: instala sin errores.

- [ ] **Step 2: Escribir los datos sintéticos de prueba**

`tp-final/tests/conftest.py`:
```python
"""Curvas y archivos .raw sintéticos para los tests.

Los .raw reales no se publican: estos archivos imitan el export de la Instron
(encabezado de metadatos + tabla separada por ';') con curvas conocidas, y se
codifican en cp1252 como los exports de Windows.
"""
import numpy as np
import pytest

ENCABEZADO_TABLA = '"Time sec";"Extension mm";"Load N";"Stress MPa"'


def _construir_raw(x, y, decimal=".", nota="Ensayo sintético", encabezado=ENCABEZADO_TABLA):
    lineas = [
        '"Test Type";"Manual"',
        f'"Note 1:";"{nota}"',
        '"Specimen";1',
        encabezado,
    ]
    for i, (xi, yi) in enumerate(zip(x, y)):
        fila = f"{i * 0.5};{float(xi)!r};{float(yi)!r};0"
        if decimal == ",":
            fila = fila.replace(".", ",")
        lineas.append(fila)
    return ("\r\n".join(lineas) + "\r\n").encode("cp1252")


def _curva_sintetica():
    """Curva SPT idealizada con resultados conocidos (t = 0,5 mm, β = 0,277).

    Elástica 3000 N/mm hasta 0,1 mm, plástica 600 N/mm hasta el pico (2,0 mm;
    1440 N) y caída hasta 1000 N. La caída no baja del 10 % de Pm para que no
    entre en el ajuste elástico de t/10. Valores esperados sin corrección:
    Pm = 1440 N, dm = 2,0 mm, Rm = 398,88 MPa, Py_t/10 = 337,5 N en x = 0,1625 mm,
    σy_t/10 = 467,1 MPa.
    """
    x = np.linspace(0.0, 2.5, 601)
    y = np.where(x <= 0.1, 3000.0 * x, 300.0 + 600.0 * (x - 0.1))
    caida = np.maximum(1440.0 - 4000.0 * (x - 2.0), 1000.0)
    return x, np.where(x <= 2.0, y, caida)


def _curva_lineal():
    """Recta 3000 N/mm: la línea offset t/10 es paralela y nunca la cruza."""
    x = np.linspace(0.0, 1.0, 101)
    return x, 3000.0 * x


def _curva_decreciente():
    """El máximo está en el primer punto: dm = 0 y Rm no se puede calcular."""
    x = np.linspace(0.0, 2.0, 101)
    return x, 1000.0 - 100.0 * x


@pytest.fixture
def construir_raw():
    return _construir_raw


@pytest.fixture
def curva_sintetica():
    return _curva_sintetica()


@pytest.fixture
def curva_lineal():
    return _curva_lineal()


@pytest.fixture
def curva_decreciente():
    return _curva_decreciente()


@pytest.fixture
def raw_sintetico(construir_raw, curva_sintetica):
    """El .raw sintético tal como lo exporta la Instron: compresión con signo negativo."""
    x, y = curva_sintetica
    return construir_raw(-x, -y)
```

- [ ] **Step 3: Escribir los tests que fallan**

`tp-final/tests/test_raw.py`:
```python
import numpy as np
import pytest

from sptero_core.raw import leer_raw


def test_lee_e_invierte_signo(raw_sintetico, curva_sintetica):
    x, y = curva_sintetica
    curva = leer_raw(raw_sintetico)
    assert curva.invertida is True
    np.testing.assert_array_equal(curva.x, x)
    np.testing.assert_array_equal(curva.y, y)


def test_sin_inversion_si_ya_es_positiva(construir_raw, curva_sintetica):
    x, y = curva_sintetica
    curva = leer_raw(construir_raw(x, y))
    assert curva.invertida is False
    np.testing.assert_array_equal(curva.x, x)


def test_ordena_por_desplazamiento(construir_raw, curva_sintetica):
    x, y = curva_sintetica
    curva = leer_raw(construir_raw(x[::-1], y[::-1]))
    assert np.all(np.diff(curva.x) >= 0)


def test_coma_decimal(construir_raw, curva_sintetica):
    x, y = curva_sintetica
    curva = leer_raw(construir_raw(x, y, decimal=","))
    np.testing.assert_array_equal(curva.x, x)
    np.testing.assert_array_equal(curva.y, y)


def test_encabezado_cp1252(construir_raw, curva_sintetica):
    x, y = curva_sintetica
    contenido = construir_raw(x, y, nota="Probeta 304L — ensayo a 20 °C, operador José")
    assert len(leer_raw(contenido).x) == len(x)


def test_sin_encabezado_de_tabla():
    with pytest.raises(ValueError, match="encabezado"):
        leer_raw(b"esto no es un archivo de la Instron\r\n1;2;3\r\n")


def test_archivo_vacio():
    with pytest.raises(ValueError, match="encabezado"):
        leer_raw(b"")


def test_faltan_columnas(construir_raw, curva_sintetica):
    x, y = curva_sintetica
    contenido = construir_raw(x, y, encabezado='"Time sec";"Displacement mm";"Load N";"Stress MPa"')
    with pytest.raises(ValueError, match="columnas"):
        leer_raw(contenido)


def test_menos_de_20_puntos(construir_raw, curva_sintetica):
    x, y = curva_sintetica
    with pytest.raises(ValueError, match="pocos puntos"):
        leer_raw(construir_raw(x[:19], y[:19]))
```

- [ ] **Step 4: Correr y ver que fallan**

Run: `.venv/Scripts/python -m pytest tests/test_raw.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'sptero_core'`.

- [ ] **Step 5: Implementar `raw.py`**

`tp-final/sptero_core/__init__.py`:
```python
"""Motor científico de SPTERO: funciones copiadas del script original, sin interfaz de usuario."""
```

`tp-final/sptero_core/raw.py`:
```python
"""Lectura del archivo .raw exportado por la Instron.

Copia de `encontrar_inicio_tabla` y `cargar_raw_a_listas` de Programa SPTERO.py.
Cambios de entrada/salida respecto del original (las reglas de lectura no cambian):
- recibe el contenido del archivo en bytes, no una ruta;
- no imprime: devuelve `invertida` para indicar si se invirtió el signo.
"""
import csv
import io
import math
from dataclasses import dataclass

import numpy as np

COLUMNA_X = "Extension mm"
COLUMNA_Y = "Load N"


@dataclass(frozen=True)
class CurvaRaw:
    x: np.ndarray
    y: np.ndarray
    invertida: bool


def encontrar_inicio_tabla(lines):
    for i, l in enumerate(lines):
        s = l.strip()
        if s.startswith('"Time') and ("Load" in s) and (";" in s):
            return i
    return None


def leer_raw(contenido: bytes, xcol=COLUMNA_X, ycol=COLUMNA_Y) -> CurvaRaw:
    # El original abre el archivo en modo texto con errors="replace"; un
    # TextIOWrapper reproduce la misma lectura por líneas desde bytes.
    texto = io.TextIOWrapper(io.BytesIO(contenido), encoding="utf-8", errors="replace")
    lines = texto.readlines()

    header_idx = encontrar_inicio_tabla(lines)
    if header_idx is None:
        raise ValueError('No encontré el encabezado de la tabla (fila tipo "Time ...;...Load...").')

    data_str = "".join(lines[header_idx:])
    reader = csv.DictReader(io.StringIO(data_str), delimiter=';', quotechar='"')

    fieldnames = [c.strip() for c in (reader.fieldnames or [])]
    if reader.fieldnames:
        reader.fieldnames = fieldnames

    if xcol not in fieldnames or ycol not in fieldnames:
        raise ValueError(
            f"No encuentro columnas esperadas.\n"
            f"Busco: {xcol!r} y {ycol!r}\n"
            f"Disponibles: {fieldnames}"
        )

    x, y = [], []
    for row in reader:
        try:
            xv = float(str(row[xcol]).strip().replace(",", "."))
            yv = float(str(row[ycol]).strip().replace(",", "."))
        except Exception:
            continue
        if math.isfinite(xv) and math.isfinite(yv):
            x.append(xv)
            y.append(yv)

    if len(x) < 20:
        raise ValueError("Muy pocos puntos leídos. ¿Seguro es el .raw correcto?")

    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)

    # invertir signo si vienen mayormente negativos
    flipped = False
    if np.median(y) < 0:
        y = -y
        flipped = True
    if np.median(x) < 0:
        x = -x
        flipped = True

    # ordenar por x creciente
    idx = np.argsort(x)
    return CurvaRaw(x=x[idx], y=y[idx], invertida=flipped)
```

Nota: el mensaje "No encuentro columnas esperadas" contiene "columnas", y "Muy pocos puntos" contiene "pocos puntos" (los `match` de los tests).

- [ ] **Step 6: Correr y ver que pasan**

Run: `.venv/Scripts/python -m pytest tests/test_raw.py -v`
Expected: 9 passed.

Nota: los valores esperados de las curvas sintéticas (`conftest.py`) se verificaron con las funciones del script original al escribir este plan.

- [ ] **Step 7: Commit** (con pedido explícito de Julián)

```bash
git add requirements.txt pytest.ini sptero_core tests/conftest.py tests/test_raw.py
git commit -m "feat: agregar lectura de archivos raw al motor científico"
```

### Task 2: Preprocesado y cálculos

**Files:**
- Create: `tp-final/sptero_core/preproceso.py`, `tp-final/sptero_core/calculos.py`
- Test: `tp-final/tests/test_calculos.py`

**Interfaces:**
- Produces (`preproceso`): `corregir_desplazamiento_por_flexibilidad_A1(x_mm, y_N, CP_mm_por_N) -> np.ndarray`, `cero_automatico_por_precarga(x, y, F0_N=5.0, shift_force=False) -> (x2, y2, i0, x0, y0)`.
- Produces (`calculos`): `linear_regression_and_r2(x, y) -> (m, b, r2)`, `interp_x_at_sign_change(x, diff) -> float | None`, `estimar_py_t10(x, y, t_mm, mask_zonaI_used=None) -> dict | None` (claves `x_py`, `py`, `m`, `b`, `offset`), `sigma_y_from_py(py, t_mm, metodo) -> float | None`, `max_load_and_dm(x, y) -> (Pm, dm, i)`, `rm_from_beta(Pm, dm, t_mm, beta) -> float | None`.

- [ ] **Step 1: Escribir los tests que fallan**

`tp-final/tests/test_calculos.py`:
```python
import numpy as np
import pytest

from sptero_core.calculos import (
    estimar_py_t10,
    linear_regression_and_r2,
    max_load_and_dm,
    rm_from_beta,
    sigma_y_from_py,
)
from sptero_core.preproceso import (
    cero_automatico_por_precarga,
    corregir_desplazamiento_por_flexibilidad_A1,
)


def test_regresion_exacta_sobre_una_recta():
    x = np.linspace(0, 1, 11)
    m, b, r2 = linear_regression_and_r2(x, 2.0 * x + 1.0)
    assert m == pytest.approx(2.0)
    assert b == pytest.approx(1.0)
    assert r2 == pytest.approx(1.0)


def test_pm_dm_y_rm(curva_sintetica):
    x, y = curva_sintetica
    pm, dm, _ = max_load_and_dm(x, y)
    assert pm == pytest.approx(1440.0, rel=1e-9)
    assert dm == pytest.approx(2.0, rel=1e-9)
    assert rm_from_beta(pm, dm, 0.5, 0.277) == pytest.approx(398.88, rel=1e-9)


def test_rm_no_calculable_con_dm_cero():
    assert rm_from_beta(1000.0, 0.0, 0.5, 0.277) is None


def test_py_t10_con_cruce(curva_sintetica):
    x, y = curva_sintetica
    t10 = estimar_py_t10(x, y, t_mm=0.5)
    assert t10["x_py"] == pytest.approx(0.1625, rel=1e-9)
    assert t10["py"] == pytest.approx(337.5, rel=1e-9)
    assert sigma_y_from_py(t10["py"], 0.5, metodo="t10") == pytest.approx(467.1, rel=1e-9)


def test_py_t10_sin_cruce(curva_lineal):
    x, y = curva_lineal
    assert estimar_py_t10(x, y, t_mm=0.5) is None


def test_correccion_de_flexibilidad():
    x = np.array([1.0, 2.0])
    f = np.array([100.0, 200.0])
    np.testing.assert_allclose(corregir_desplazamiento_por_flexibilidad_A1(x, f, 1e-3), [0.9, 1.8])


def test_cero_por_precarga_recorta_y_pone_cero():
    x = np.array([0.0, 0.1, 0.2, 0.3])
    y = np.array([1.0, 4.0, 6.0, 9.0])
    x2, y2, i0, x0, y0 = cero_automatico_por_precarga(x, y, F0_N=5.0)
    assert (i0, x0, y0) == (2, 0.2, 6.0)
    np.testing.assert_allclose(x2, [0.0, 0.1])
    np.testing.assert_allclose(y2, [6.0, 9.0])


def test_cero_por_precarga_sin_llegar_a_f0_no_cambia():
    x = np.array([0.0, 0.1, 0.2])
    y = np.array([1.0, 2.0, 3.0])
    x2, y2, i0, _, _ = cero_automatico_por_precarga(x, y, F0_N=5.0)
    assert i0 == 0
    np.testing.assert_array_equal(x2, x)
    np.testing.assert_array_equal(y2, y)
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `.venv/Scripts/python -m pytest tests/test_calculos.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'sptero_core.calculos'`.

- [ ] **Step 3: Implementar copiando del original**

`tp-final/sptero_core/preproceso.py` (copia textual de `Programa SPTERO.py`, líneas 242–284):
```python
"""Preprocesado de la curva: corrección de flexibilidad y cero por precarga.

Copia textual de Programa SPTERO.py. No se modifica ninguna línea.
"""
import numpy as np


def corregir_desplazamiento_por_flexibilidad_A1(x_mm, y_N, CP_mm_por_N):
    """
    UNE Anexo A (A.1): v = vref - F*C_P
    En tu script: x = Extension(mm)=vref (cruceta), y = Load(N)=F
    Devuelve x_corr (mm).
    """
    x = np.asarray(x_mm, float)
    F = np.asarray(y_N, float)
    x_corr = x - F * float(CP_mm_por_N)
    return x_corr

def cero_automatico_por_precarga(x, y, F0_N=5.0, shift_force=False):
    """
    Cero automático por precarga:
    - Busca el primer índice i0 tal que y[i0] >= F0_N.
    - Recorta la curva desde i0.
    - Resta x[i0] a todo x para que x=0 en el contacto.
    - Opcional: shift_force=True para restar y[i0] y dejar F=0 en contacto.

    Devuelve: (x2, y2, i0, x0, y0)
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)

    if len(x) < 3:
        return x, y, 0, float(x[0]) if len(x) else 0.0, float(y[0]) if len(y) else 0.0

    # primer punto que supera la precarga
    idx = np.where(y >= float(F0_N))[0]
    if idx.size == 0:
        # si nunca supera F0, no hacemos nada
        return x, y, 0, float(x[0]), float(y[0])

    i0 = int(idx[0])
    x0 = float(x[i0])
    y0 = float(y[i0])

    x2 = x[i0:] - x0
    y2 = y[i0:]
    if shift_force:
        y2 = y2 - y0

    return x2, y2, i0, x0, y0
```

`tp-final/sptero_core/calculos.py` (copia textual de `Programa SPTERO.py`, líneas 307–317, 493–533, 553–573):
```python
"""Cálculos SPT: regresión, fluencia por t/10, Pm/dm y Rm.

Copia textual de Programa SPTERO.py. No se modifica ninguna línea.
"""
import numpy as np


def linear_regression_and_r2(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if len(x) < 2:
        raise ValueError("Regresión: pocos puntos.")
    m, b = np.polyfit(x, y, 1)
    yhat = m * x + b
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
    r2 = 0.0 if ss_tot <= 1e-30 else (1.0 - ss_res / ss_tot)
    return float(m), float(b), float(r2)


def interp_x_at_sign_change(x, diff):
    for i in range(1, len(diff)):
        d0, d1 = diff[i - 1], diff[i]
        if d0 == 0:
            return float(x[i - 1])
        if d0 * d1 < 0:
            t = -d0 / (d1 - d0)
            return float(x[i - 1] + (x[i] - x[i - 1]) * t)
    return None


def estimar_py_t10(x, y, t_mm, mask_zonaI_used=None):
    pmax = float(np.max(y))
    if pmax <= 0:
        return None

    off = float(t_mm) / 10.0

    if mask_zonaI_used is not None and np.sum(mask_zonaI_used) >= 6:
        x_el = x[mask_zonaI_used]
        y_el = y[mask_zonaI_used]
    else:
        mask_el = y <= 0.10 * pmax
        if np.sum(mask_el) < 8:
            mask_el[:max(10, int(0.05 * len(x)))] = True
        x_el = x[mask_el]
        y_el = y[mask_el]

    m, b, _ = linear_regression_and_r2(x_el, y_el)

    valid = x >= off
    xx = x[valid]
    yy = y[valid]
    diff = yy - (m * (xx - off) + b)

    x_int = interp_x_at_sign_change(xx, diff)
    if x_int is None:
        return None

    py = m * (x_int - off) + b
    return {"x_py": float(x_int), "py": float(py), "m": m, "b": b, "offset": off}


def sigma_y_from_py(py, t_mm, metodo):
    if py is None or t_mm <= 0:
        return None
    if metodo.lower() == "mao":
        a = 0.442
    elif metodo.lower() == "t10":
        a = 0.346
    else:
        raise ValueError("metodo debe ser 'mao' o 't10'")
    return a * float(py) / (float(t_mm) ** 2)


def max_load_and_dm(x, y):
    i = int(np.argmax(y))
    return float(y[i]), float(x[i]), i


def rm_from_beta(Pm, dm, t_mm, beta):
    if dm <= 0 or t_mm <= 0:
        return None
    return float(beta) * float(Pm) / (float(dm) * float(t_mm))
```

- [ ] **Step 4: Correr y ver que pasan**

Run: `.venv/Scripts/python -m pytest tests/test_calculos.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add sptero_core/preproceso.py sptero_core/calculos.py tests/test_calculos.py
git commit -m "feat: copiar preprocesado y cálculos de sptero al motor"
```

### Task 3: Pipeline de análisis (D1)

**Files:**
- Create: `tp-final/sptero_core/analisis.py`
- Test: `tp-final/tests/test_analisis.py`

**Interfaces:**
- Consumes: `leer_raw`, `CurvaRaw` (Task 1); funciones de `preproceso` y `calculos` (Task 2).
- Produces: `F0_PRECARGA_N = 5.0`; `ParametrosProcesamiento(aplicar_correccion: bool = False, cp_mm_por_n: float = 2.281e-4, beta: float = 0.277)`; `ResultadoAnalisis(x_mm, y_n, pm_n, dm_mm, rm_mpa, py_t10_n, py_t10_displacement_mm, sigma_y_t10_mpa)` (los tres últimos `float | None`); `preprocesar(curva: CurvaRaw, parametros) -> (x, y)`; `analizar(contenido: bytes, espesor_mm: float, parametros) -> ResultadoAnalisis` (lanza `ValueError` si el archivo es inválido o Rm no se puede calcular).

- [ ] **Step 1: Escribir los tests que fallan**

`tp-final/tests/test_analisis.py`:
```python
import numpy as np
import pytest

from sptero_core.analisis import ParametrosProcesamiento, analizar, preprocesar
from sptero_core.raw import leer_raw

SIN_CORRECCION = ParametrosProcesamiento()
CON_CORRECCION = ParametrosProcesamiento(aplicar_correccion=True)


def test_analisis_completo_sin_correccion(raw_sintetico):
    r = analizar(raw_sintetico, 0.5, SIN_CORRECCION)
    assert r.pm_n == pytest.approx(1440.0, rel=1e-9)
    assert r.dm_mm == pytest.approx(2.0, rel=1e-9)
    assert r.rm_mpa == pytest.approx(398.88, rel=1e-9)
    assert r.py_t10_n == pytest.approx(337.5, rel=1e-9)
    assert r.py_t10_displacement_mm == pytest.approx(0.1625, rel=1e-9)
    assert r.sigma_y_t10_mpa == pytest.approx(467.1, rel=1e-9)


def test_sin_correccion_no_aplica_cero_por_precarga(raw_sintetico):
    # D1: como el original, el cero solo se aplica junto con la corrección.
    x, y = preprocesar(leer_raw(raw_sintetico), SIN_CORRECCION)
    assert len(x) == 601
    assert y[0] == 0.0  # el primer punto, por debajo de 5 N, se conserva


def test_con_correccion_aplica_cero_por_precarga(raw_sintetico):
    x, y = preprocesar(leer_raw(raw_sintetico), CON_CORRECCION)
    assert len(x) == 600
    assert x[0] == 0.0
    assert y[0] >= 5.0


def test_correccion_reduce_dm(raw_sintetico):
    sin = analizar(raw_sintetico, 0.5, SIN_CORRECCION)
    con = analizar(raw_sintetico, 0.5, CON_CORRECCION)
    assert con.dm_mm < sin.dm_mm
    assert con.pm_n == pytest.approx(sin.pm_n)


def test_precarga_nunca_alcanzada(construir_raw):
    x = np.linspace(0.0, 1.0, 50)
    y = 4.0 * x  # nunca llega a 5 N
    contenido = construir_raw(x, y)
    xp, _ = preprocesar(leer_raw(contenido), CON_CORRECCION)
    assert len(xp) == 50
    r = analizar(contenido, 0.5, CON_CORRECCION)
    assert r.pm_n == pytest.approx(4.0)


def test_sin_cruce_t10_devuelve_none(construir_raw, curva_lineal):
    r = analizar(construir_raw(*curva_lineal), 0.5, SIN_CORRECCION)
    assert r.py_t10_n is None
    assert r.py_t10_displacement_mm is None
    assert r.sigma_y_t10_mpa is None
    assert r.rm_mpa == pytest.approx(1662.0, rel=1e-9)


def test_dm_cero_falla(construir_raw, curva_decreciente):
    with pytest.raises(ValueError, match="Rm"):
        analizar(construir_raw(*curva_decreciente), 0.5, SIN_CORRECCION)


def test_archivo_invalido_falla():
    with pytest.raises(ValueError):
        analizar(b"basura", 0.5, SIN_CORRECCION)
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `.venv/Scripts/python -m pytest tests/test_analisis.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'sptero_core.analisis'`.

- [ ] **Step 3: Implementar**

`tp-final/sptero_core/analisis.py`:
```python
"""Pipeline de análisis: reemplaza al main() interactivo del script original.

Sigue la secuencia de main() (Programa SPTERO.py, líneas 979–1058 y 1203–1209)
con los valores por defecto que el original ofrece en cada pregunta:
leer → invertir signo/ordenar → [con corrección: v = vref − F·C_P → reordenar →
cero por precarga con F0 = 5 N] → Pm/dm → Rm → t/10.

t/10 usa la rama sin MAO (mask_zonaI_used=None) porque MAO está fuera del MVP.
"""
from dataclasses import dataclass

import numpy as np

from sptero_core.calculos import estimar_py_t10, max_load_and_dm, rm_from_beta, sigma_y_from_py
from sptero_core.preproceso import cero_automatico_por_precarga, corregir_desplazamiento_por_flexibilidad_A1
from sptero_core.raw import CurvaRaw, leer_raw

F0_PRECARGA_N = 5.0


@dataclass(frozen=True)
class ParametrosProcesamiento:
    aplicar_correccion: bool = False
    cp_mm_por_n: float = 2.281e-4
    beta: float = 0.277


@dataclass(frozen=True)
class ResultadoAnalisis:
    x_mm: np.ndarray
    y_n: np.ndarray
    pm_n: float
    dm_mm: float
    rm_mpa: float
    py_t10_n: float | None
    py_t10_displacement_mm: float | None
    sigma_y_t10_mpa: float | None


def preprocesar(curva: CurvaRaw, parametros: ParametrosProcesamiento):
    x, y = curva.x, curva.y
    if parametros.aplicar_correccion:
        x = corregir_desplazamiento_por_flexibilidad_A1(x, y, parametros.cp_mm_por_n)
        # Re-ordenar por x por si la corrección genera pequeños desórdenes
        idx = np.argsort(x)
        x = x[idx]
        y = y[idx]
        x, y, _i0, _x0, _y0 = cero_automatico_por_precarga(x, y, F0_N=F0_PRECARGA_N, shift_force=False)
    return x, y


def analizar(contenido: bytes, espesor_mm: float, parametros: ParametrosProcesamiento) -> ResultadoAnalisis:
    x, y = preprocesar(leer_raw(contenido), parametros)

    pm, dm, _ = max_load_and_dm(x, y)
    rm = rm_from_beta(pm, dm, espesor_mm, parametros.beta)
    if rm is None:
        raise ValueError(f"No se puede calcular Rm: dm = {dm:.4f} mm, tiene que ser mayor que cero.")

    t10 = estimar_py_t10(x, y, t_mm=espesor_mm, mask_zonaI_used=None)
    py = t10["py"] if t10 else None
    return ResultadoAnalisis(
        x_mm=x,
        y_n=y,
        pm_n=pm,
        dm_mm=dm,
        rm_mpa=rm,
        py_t10_n=py,
        py_t10_displacement_mm=t10["x_py"] if t10 else None,
        sigma_y_t10_mpa=sigma_y_from_py(py, espesor_mm, metodo="t10"),
    )
```

- [ ] **Step 4: Correr toda la suite**

Run: `.venv/Scripts/python -m pytest -v`
Expected: 25 passed (9 + 8 + 8).

- [ ] **Step 5: Commit**

```bash
git add sptero_core/analisis.py tests/test_analisis.py
git commit -m "feat: agregar pipeline de análisis con la secuencia del original"
```

### Task 4: Caracterización contra el SPTERO original

**Files:**
- Test: `tp-final/tests/test_caracterizacion.py`

**Interfaces:**
- Consumes: `leer_raw` (Task 1), `preproceso`/`calculos` (Task 2), `analizar`/`ParametrosProcesamiento` (Task 3).
- Variables de entorno: `SPTERO_ORIGINAL`, `SPTERO_RAW_SAMPLE`.

- [ ] **Step 1: Escribir el test**

`tp-final/tests/test_caracterizacion.py`:
```python
"""Compara sptero_core con el script original de SPTERO.

El script y el .raw real no se publican: se leen de rutas locales y, si las
variables de entorno no están definidas, estos tests se saltean.
"""
import ast
import contextlib
import importlib.util
import inspect
import io
import os
import sys
import textwrap
from unittest import mock

import numpy as np
import pytest

from sptero_core import calculos, preproceso
from sptero_core.analisis import ParametrosProcesamiento, analizar
from sptero_core.raw import leer_raw

RUTA_ORIGINAL = os.environ.get("SPTERO_ORIGINAL")
RUTA_RAW = os.environ.get("SPTERO_RAW_SAMPLE")

pytestmark = pytest.mark.skipif(
    not (RUTA_ORIGINAL and RUTA_RAW),
    reason="Definir SPTERO_ORIGINAL y SPTERO_RAW_SAMPLE para comparar con el SPTERO original",
)

# El original importa su interfaz de consola al cargarse. Las funciones de cálculo
# no la usan, así que se reemplaza por módulos falsos solo durante la importación.
MODULOS_DE_INTERFAZ = [
    "tkinter", "matplotlib", "matplotlib.pyplot", "reportlab", "reportlab.platypus",
    "reportlab.lib", "reportlab.lib.colors", "reportlab.lib.units",
    "reportlab.lib.pagesizes", "reportlab.lib.styles",
]

COPIADAS = {
    preproceso: ["corregir_desplazamiento_por_flexibilidad_A1", "cero_automatico_por_precarga"],
    calculos: ["linear_regression_and_r2", "interp_x_at_sign_change", "estimar_py_t10",
               "sigma_y_from_py", "max_load_and_dm", "rm_from_beta"],
}

RTOL = 1e-9
T_MM = 0.5
BETA = 0.277
CP = 2.281e-4


@pytest.fixture(scope="module")
def original():
    falsos = {nombre: mock.MagicMock() for nombre in MODULOS_DE_INTERFAZ}
    with mock.patch.dict(sys.modules, falsos):
        spec = importlib.util.spec_from_file_location("sptero_original", RUTA_ORIGINAL)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def contenido():
    with open(RUTA_RAW, "rb") as f:
        return f.read()


def _silencioso(funcion, *args, **kwargs):
    # El original imprime emojis, que fallan en una consola cp1252.
    with contextlib.redirect_stdout(io.StringIO()):
        return funcion(*args, **kwargs)


def _arbol(funcion):
    return ast.dump(ast.parse(textwrap.dedent(inspect.getsource(funcion))))


def _pipeline_original(original, cp):
    """Reproduce main() del original con los valores por defecto (sin MAO)."""
    x, y = _silencioso(original.cargar_raw_a_listas, RUTA_RAW)
    if cp is not None:
        x = original.corregir_desplazamiento_por_flexibilidad_A1(x, y, cp)
        idx = np.argsort(x)
        x, y = x[idx], y[idx]
        x, y, *_ = original.cero_automatico_por_precarga(x, y, F0_N=5.0, shift_force=False)
    pm, dm, _ = original.max_load_and_dm(x, y)
    rm = original.rm_from_beta(pm, dm, T_MM, BETA)
    t10 = original.estimar_py_t10(x, y, t_mm=T_MM, mask_zonaI_used=None)
    sigma = original.sigma_y_from_py(t10["py"], T_MM, metodo="t10") if t10 else None
    return x, y, pm, dm, rm, t10, sigma


@pytest.mark.parametrize("modulo,nombre", [(m, n) for m, ns in COPIADAS.items() for n in ns])
def test_funcion_copiada_es_identica(original, modulo, nombre):
    assert _arbol(getattr(modulo, nombre)) == _arbol(getattr(original, nombre))


def test_lectura_igual_al_original(original, contenido):
    x0, y0 = _silencioso(original.cargar_raw_a_listas, RUTA_RAW)
    curva = leer_raw(contenido)
    np.testing.assert_allclose(curva.x, x0, rtol=RTOL)
    np.testing.assert_allclose(curva.y, y0, rtol=RTOL)


@pytest.mark.parametrize("cp", [None, CP], ids=["sin_correccion", "con_correccion"])
def test_pipeline_igual_al_original(original, contenido, cp):
    x0, y0, pm0, dm0, rm0, t10_0, sigma0 = _pipeline_original(original, cp)
    parametros = ParametrosProcesamiento(aplicar_correccion=cp is not None, beta=BETA)
    r = analizar(contenido, T_MM, parametros)
    np.testing.assert_allclose(r.x_mm, x0, rtol=RTOL)
    np.testing.assert_allclose(r.y_n, y0, rtol=RTOL)
    assert r.pm_n == pytest.approx(pm0, rel=RTOL)
    assert r.dm_mm == pytest.approx(dm0, rel=RTOL)
    assert r.rm_mpa == pytest.approx(rm0, rel=RTOL)
    assert r.py_t10_n == pytest.approx(t10_0["py"], rel=RTOL)
    assert r.py_t10_displacement_mm == pytest.approx(t10_0["x_py"], rel=RTOL)
    assert r.sigma_y_t10_mpa == pytest.approx(sigma0, rel=RTOL)


@pytest.mark.parametrize(
    "cp,pm,dm,rm,py,sigma",
    [
        (None, 2372.2, 2.2709, 578.7, 274.9, 380.5),
        (CP, 2372.2, 1.7319, 758.8, 281.8, 390.1),
    ],
    ids=["sin_correccion", "con_correccion"],
)
def test_valores_de_referencia_de_la_spec(contenido, cp, pm, dm, rm, py, sigma):
    """Tabla de la spec, sección 4 (P3_304L_L.raw, t = 0,5 mm, β = 0,277)."""
    if os.path.basename(RUTA_RAW) != "P3_304L_L.raw":
        pytest.skip("Los valores de referencia son de P3_304L_L.raw")
    r = analizar(contenido, T_MM, ParametrosProcesamiento(aplicar_correccion=cp is not None, beta=BETA))
    assert round(r.pm_n, 1) == pm
    assert round(r.dm_mm, 4) == dm
    assert round(r.rm_mpa, 1) == rm
    assert round(r.py_t10_n, 1) == py
    assert round(r.sigma_y_t10_mpa, 1) == sigma
```

- [ ] **Step 2: Ver que se saltea sin las variables**

Run: `.venv/Scripts/python -m pytest tests/test_caracterizacion.py -v`
Expected: todos `SKIPPED` con el motivo "Definir SPTERO_ORIGINAL y SPTERO_RAW_SAMPLE…".

- [ ] **Step 3: Ver que falla si el core se aparta del original (rojo)**

Cambiar temporalmente en `sptero_core/calculos.py` `a = 0.346` por `a = 0.347`, y correr con las variables definidas:
```bash
SPTERO_ORIGINAL="C:/Users/julif/Documents/Maestría/Programa SPETERO/Programa SPTERO.py" SPTERO_RAW_SAMPLE="C:/Users/julif/Documents/Maestría/Ensayos - SPT/A Julian Fierens/P3_304L_L.raw" .venv/Scripts/python -m pytest tests/test_caracterizacion.py -v
```
Expected: FAIL en `test_funcion_copiada_es_identica[...sigma_y_from_py]`, `test_pipeline_igual_al_original` y `test_valores_de_referencia_de_la_spec`. **Revertir el cambio.**

- [ ] **Step 4: Correr en verde con las variables**

Mismo comando del Step 3, con el core restaurado.
Expected: 13 passed (8 funciones copiadas + 1 lectura + 2 pipeline + 2 valores de referencia).

- [ ] **Step 5: Verificación con el subagente**

Despachar el subagente `verificador-cientifico` (definido en `.claude/agents/verificador-cientifico.md`), con las dos variables de entorno disponibles. Pegar su veredicto en la descripción del PR de la etapa.
Expected: "fiel", con la salida real de pytest.

- [ ] **Step 6: Suite completa y commit** (con pedido explícito)

Run: `.venv/Scripts/python -m pytest -v` (sin variables: los de caracterización aparecen `SKIPPED`).
```bash
git add tests/test_caracterizacion.py
git commit -m "test: comparar el motor científico con el sptero original"
```
Fin de la etapa 2: Julián abre el PR `feature/tp-final-core` → `main`.

---

# Etapa 3 — Persistencia y API (`feature/tp-final-api`)

### Task 5: Contrato v1.1

**Files:**
- Create: `tp-final/openapi.yaml` (copia de `TP2/openapi.yaml` con las ediciones de abajo)
- Test: `tp-final/tests/test_contrato.py`

**Interfaces:**
- Produces: `openapi.yaml` con 9 operaciones y los schemas `TestUpload`, `Test`, `TestUpdate`, `ProcessingRequest`, `ProcessingParameters`, `Result`, `Curve`, `Error`. `Result` tiene `pm_n`, `dm_mm`, `rm_mpa`, `py_t10_n`, `py_t10_displacement_mm`, `sigma_y_t10_mpa`, `parameters`, `processed_at`.

- [ ] **Step 1: Escribir el test que falla**

`tp-final/tests/test_contrato.py`:
```python
from pathlib import Path

import yaml

CONTRATO = Path(__file__).resolve().parent.parent / "openapi.yaml"

OPERACIONES_ESPERADAS = {
    ("/tests", "get"), ("/tests", "post"),
    ("/tests/{testId}", "get"), ("/tests/{testId}", "patch"), ("/tests/{testId}", "delete"),
    ("/tests/{testId}/file", "get"),
    ("/tests/{testId}/curve", "get"),
    ("/tests/{testId}/result", "get"), ("/tests/{testId}/result", "put"),
}
METODOS_HTTP = {"get", "post", "put", "patch", "delete"}


def cargar_contrato():
    return yaml.safe_load(CONTRATO.read_text(encoding="utf-8"))


def operaciones(contrato):
    return {
        (ruta, metodo)
        for ruta, item in contrato["paths"].items()
        for metodo in item
        if metodo in METODOS_HTTP
    }


def test_version_1_1():
    assert cargar_contrato()["info"]["version"] == "1.1.0"


def test_operaciones_del_contrato():
    assert operaciones(cargar_contrato()) == OPERACIONES_ESPERADAS


def test_result_incluye_t10():
    result = cargar_contrato()["components"]["schemas"]["Result"]
    for campo in ("py_t10_n", "py_t10_displacement_mm", "sigma_y_t10_mpa"):
        assert campo in result["properties"]
        assert campo in result["required"]
        assert result["properties"][campo]["type"] == ["number", "null"]


def test_test_update_solo_espesor():
    test_update = cargar_contrato()["components"]["schemas"]["TestUpdate"]
    assert test_update["required"] == ["thickness_mm"]
    assert set(test_update["properties"]) == {"thickness_mm"}
```

- [ ] **Step 2: Correr y ver que falla**

Run: `.venv/Scripts/python -m pytest tests/test_contrato.py -v`
Expected: FAIL con `FileNotFoundError` (no existe `openapi.yaml`).

- [ ] **Step 3: Copiar el contrato del TP2 y aplicar las ediciones**

Copiar `../TP2/openapi.yaml` a `openapi.yaml` (copia; `TP2/` no se modifica) y editar la copia:

1. `info.version: 1.0.0` → `info.version: 1.1.0`. Al final de `info.description` agregar:
```yaml
    **Cambios en v1.1 (TP final).** Se suma la fluencia por t/10 al resultado; el
    cero por precarga se aplica solo con la corrección de flexibilidad, como en el
    SPTERO original; y se puede corregir el espesor de un ensayo
    (`PATCH /tests/{testId}`).
```
También, en la primera oración de la descripción, reemplazar "resultado (Pm, dm, Rm)" por "resultado (Pm, dm, Rm y fluencia por t/10)".

2. En `/tests` → `get.description`, reemplazar el texto por:
```yaml
      description: Cada ensayo incluye su resultado vigente, o `null` si todavía no se procesó. Ordenados del más reciente al más antiguo.
```

3. En `/tests` → `post.responses.'400'.description`, reemplazar el texto por:
```yaml
          description: |
            Falta un campo o `thickness_mm` no es mayor que cero
            (`INVALID_PARAMETERS`), o el archivo no respeta el formato descrito
            arriba: no tiene la fila de encabezado de la tabla, le faltan las
            columnas `"Extension mm"` o `"Load N"`, o tiene menos de 20 puntos
            válidos (`INVALID_FILE`).
```

4. En `/tests/{testId}`, entre `get` y `delete`, agregar:
```yaml
    patch:
      tags: [Ensayos]
      summary: Corrige el espesor de un ensayo y recalcula su resultado
      description: |
        Solo se puede corregir `thickness_mm`. Si el ensayo tiene resultado, se
        recalcula con los mismos parámetros de procesamiento y se reemplaza (no
        se guardan versiones). El cambio de espesor y el nuevo resultado se
        guardan juntos: si el recálculo falla, no cambia ni el espesor ni el
        resultado anterior. Si el espesor es igual al actual, no cambia nada.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TestUpdate'
      responses:
        '200':
          description: Ensayo actualizado, con su resultado recalculado
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Test'
        '400':
          description: Falta `thickness_mm` o no es un número mayor que cero (`INVALID_PARAMETERS`)
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '404':
          $ref: '#/components/responses/TestNotFound'
        '422':
          description: |
            El recálculo con el nuevo espesor no se pudo hacer
            (`PROCESSING_FAILED`). No se guardó ningún cambio.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
```

5. En `/tests/{testId}/file` → `200.content`, reemplazar `text/csv:` por `application/octet-stream:` y el schema por:
```yaml
            application/octet-stream:
              schema:
                type: string
                format: binary
```

6. En `/tests/{testId}/curve`: en la descripción, reemplazar "(con el cero por precarga y, si se pidió, la corrección por compliance)" por "(si se pidió la corrección por compliance, corregida, reordenada y con el cero por precarga)". En `'400'.description`, poner "El valor de `source` no es `raw` ni `processed` (`INVALID_PARAMETERS`)".

7. En `/tests/{testId}/result` → `put.description`: reemplazar la primera oración por "Calcula Pm, dm, Rm y la fluencia por t/10 a partir del archivo original y reemplaza el resultado anterior, si existía. No se guardan versiones.", y reemplazar los pasos 2 a 4 por:
```yaml
        2. Si `apply_compliance_correction` es `true`: corrige el
           desplazamiento con v = vref − F·C_P, reordena por desplazamiento y
           aplica el cero por precarga con F0 = 5 N (toma como contacto el
           primer punto con carga mayor o igual a 5 N, descarta los anteriores
           y pone el desplazamiento en 0 ahí; si ningún punto llega a 5 N, la
           curva sigue sin cambios). Sin corrección no se aplica el cero, igual
           que en el SPTERO original.
        3. Pm es la carga máxima y dm su desplazamiento; Rm = β·Pm / (dm·t),
           con t = `thickness_mm` del ensayo.
        4. Fluencia por t/10: recta elástica ajustada con los puntos de carga
           hasta el 10 % de Pm, desplazada t/10; Py es su cruce con la curva y
           σy = 0,346·Py/t². Si no hay cruce, los tres campos de t/10 son `null`.
```
En `put.responses.'400'.description` poner "Algún parámetro tiene un tipo inválido o no es mayor que cero (`INVALID_PARAMETERS`)".

8. En `components.schemas`, después de `TestUpload`, agregar:
```yaml
    TestUpdate:
      type: object
      description: Corrección del espesor de un ensayo
      required: [thickness_mm]
      properties:
        thickness_mm:
          type: number
          format: double
          exclusiveMinimum: 0
          description: Espesor inicial corregido, en mm
          examples: [0.48]
```

9. En `Result`, cambiar `required` a `[pm_n, dm_mm, rm_mpa, py_t10_n, py_t10_displacement_mm, sigma_y_t10_mpa, parameters, processed_at]` y agregar después de `rm_mpa`:
```yaml
        py_t10_n:
          type: ['number', 'null']
          format: double
          description: Carga de fluencia Py por el método t/10, en N, o `null` si no hubo cruce
          examples: [274.9]
        py_t10_displacement_mm:
          type: ['number', 'null']
          format: double
          description: Desplazamiento de Py t/10 sobre la curva procesada, en mm, o `null`
          examples: [0.2581]
        sigma_y_t10_mpa:
          type: ['number', 'null']
          format: double
          description: Límite elástico estimado σy = 0,346·Py/t², en MPa, o `null`
          examples: [380.5]
```
(0,2581 mm es el `x_py` real de `P3_304L_L.raw` sin corrección, calculado con el script original al escribir este plan.)

- [ ] **Step 4: Correr y ver que pasa, y validar el YAML**

Run: `.venv/Scripts/python -m pytest tests/test_contrato.py -v`
Expected: 4 passed.
Además, pegar `openapi.yaml` en https://editor-next.swagger.io (lo hace Julián) y confirmar que no hay errores.

- [ ] **Step 5: Commit**

```bash
git add openapi.yaml tests/test_contrato.py
git commit -m "docs: agregar contrato openapi v1.1 del tp final"
```

### Task 6: Repositorio SQLite

**Files:**
- Create: `tp-final/app/__init__.py`, `tp-final/app/repository.py`
- Test: `tp-final/tests/test_repository.py`

**Interfaces:**
- Produces: `conectar(ruta: str) -> sqlite3.Connection`; `crear_ensayo(con, filename, material, thickness_mm, point_count, raw_file: bytes, uploaded_at: str) -> int`; `listar_ensayos(con) -> list[dict]`; `obtener_ensayo(con, test_id) -> dict | None`; `obtener_archivo(con, test_id) -> tuple[str, bytes] | None`; `guardar_resultado(con, test_id, resultado: dict) -> None`; `actualizar_espesor(con, test_id, thickness_mm, resultado: dict | None) -> None`; `borrar_ensayo(con, test_id) -> bool`.
- Forma del ensayo devuelto: `{"id", "filename", "material", "thickness_mm", "uploaded_at", "point_count", "result"}`, con `result` `None` o `{"pm_n", "dm_mm", "rm_mpa", "py_t10_n", "py_t10_displacement_mm", "sigma_y_t10_mpa", "parameters": {"apply_compliance_correction", "compliance_mm_per_n", "beta"}, "processed_at"}` (forma del contrato).
- Forma del `resultado` que se guarda (plana): claves de `CAMPOS_RESULTADO`.

- [ ] **Step 1: Escribir los tests que fallan**

`tp-final/tests/test_repository.py`:
```python
import sqlite3

import pytest

from app import repository

RESULTADO = {
    "apply_compliance_correction": False,
    "compliance_mm_per_n": None,
    "beta": 0.277,
    "pm_n": 1440.0,
    "dm_mm": 2.0,
    "rm_mpa": 398.88,
    "py_t10_n": 337.5,
    "py_t10_displacement_mm": 0.1625,
    "sigma_y_t10_mpa": 467.1,
    "processed_at": "2026-10-12T15:00:00+00:00",
}


@pytest.fixture
def con(tmp_path):
    conexion = repository.conectar(str(tmp_path / "prueba.db"))
    yield conexion
    conexion.close()


def _crear(con, nombre="a.raw", uploaded_at="2026-10-12T10:00:00+00:00"):
    return repository.crear_ensayo(con, nombre, "304L", 0.5, 601, b"contenido", uploaded_at)


def test_crear_y_obtener_sin_resultado(con):
    test_id = _crear(con)
    ensayo = repository.obtener_ensayo(con, test_id)
    assert ensayo == {
        "id": test_id, "filename": "a.raw", "material": "304L", "thickness_mm": 0.5,
        "uploaded_at": "2026-10-12T10:00:00+00:00", "point_count": 601, "result": None,
    }


def test_obtener_inexistente(con):
    assert repository.obtener_ensayo(con, 99) is None
    assert repository.obtener_archivo(con, 99) is None


def test_archivo_original_intacto(con):
    test_id = repository.crear_ensayo(con, "b.raw", "304L", 0.5, 601, b"\x00\xffbytes", "2026-10-12T10:00:00+00:00")
    assert repository.obtener_archivo(con, test_id) == ("b.raw", b"\x00\xffbytes")


def test_listar_mas_reciente_primero_y_sin_blob(con):
    primero = _crear(con, "a.raw", "2026-10-12T10:00:00+00:00")
    segundo = _crear(con, "b.raw", "2026-10-12T11:00:00+00:00")
    ensayos = repository.listar_ensayos(con)
    assert [e["id"] for e in ensayos] == [segundo, primero]
    assert "raw_file" not in ensayos[0]


def test_guardar_y_reemplazar_resultado(con):
    test_id = _crear(con)
    repository.guardar_resultado(con, test_id, RESULTADO)
    repository.guardar_resultado(con, test_id, {**RESULTADO, "beta": 0.3, "rm_mpa": 432.0})
    resultado = repository.obtener_ensayo(con, test_id)["result"]
    assert resultado["rm_mpa"] == 432.0
    assert resultado["parameters"] == {"apply_compliance_correction": False, "compliance_mm_per_n": None, "beta": 0.3}
    assert con.execute("SELECT COUNT(*) FROM results").fetchone()[0] == 1


def test_actualizar_espesor_con_resultado(con):
    test_id = _crear(con)
    repository.guardar_resultado(con, test_id, RESULTADO)
    repository.actualizar_espesor(con, test_id, 0.25, {**RESULTADO, "rm_mpa": 797.76})
    ensayo = repository.obtener_ensayo(con, test_id)
    assert ensayo["thickness_mm"] == 0.25
    assert ensayo["result"]["rm_mpa"] == 797.76


def test_actualizar_espesor_es_atomico(con):
    # Si falla la escritura del resultado, el espesor tampoco cambia.
    test_id = _crear(con)
    repository.guardar_resultado(con, test_id, RESULTADO)
    with pytest.raises(sqlite3.IntegrityError):
        repository.actualizar_espesor(con, test_id, 0.25, {**RESULTADO, "pm_n": None})
    ensayo = repository.obtener_ensayo(con, test_id)
    assert ensayo["thickness_mm"] == 0.5
    assert ensayo["result"]["rm_mpa"] == 398.88


def test_borrar_en_cascada(con):
    test_id = _crear(con)
    repository.guardar_resultado(con, test_id, RESULTADO)
    assert repository.borrar_ensayo(con, test_id) is True
    assert repository.obtener_ensayo(con, test_id) is None
    assert con.execute("SELECT COUNT(*) FROM results").fetchone()[0] == 0
    assert repository.borrar_ensayo(con, test_id) is False
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `.venv/Scripts/python -m pytest tests/test_repository.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 3: Implementar**

`tp-final/app/__init__.py`:
```python
"""API de SPTERO Web."""
```

`tp-final/app/repository.py`:
```python
"""Acceso a SQLite con SQL explícito (sqlite3 de la biblioteca estándar).

Las escrituras usan `with con:`, que confirma la transacción si todo sale bien
y la deshace si hay una excepción.
"""
import sqlite3
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS tests (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    filename      TEXT    NOT NULL,
    material      TEXT    NOT NULL,
    thickness_mm  REAL    NOT NULL CHECK (thickness_mm > 0),
    uploaded_at   TEXT    NOT NULL,
    point_count   INTEGER NOT NULL,
    raw_file      BLOB    NOT NULL
);

CREATE TABLE IF NOT EXISTS results (
    test_id                      INTEGER PRIMARY KEY
                                 REFERENCES tests(id) ON DELETE CASCADE,
    apply_compliance_correction  INTEGER NOT NULL,
    compliance_mm_per_n          REAL,
    beta                         REAL    NOT NULL,
    pm_n                         REAL    NOT NULL,
    dm_mm                        REAL    NOT NULL,
    rm_mpa                       REAL    NOT NULL,
    py_t10_n                     REAL,
    py_t10_displacement_mm       REAL,
    sigma_y_t10_mpa              REAL,
    processed_at                 TEXT    NOT NULL
);
"""

CAMPOS_RESULTADO = (
    "apply_compliance_correction", "compliance_mm_per_n", "beta", "pm_n", "dm_mm", "rm_mpa",
    "py_t10_n", "py_t10_displacement_mm", "sigma_y_t10_mpa", "processed_at",
)

_SELECT_ENSAYOS = """
SELECT t.id, t.filename, t.material, t.thickness_mm, t.uploaded_at, t.point_count,
       r.test_id AS r_test_id, r.apply_compliance_correction, r.compliance_mm_per_n, r.beta,
       r.pm_n, r.dm_mm, r.rm_mpa, r.py_t10_n, r.py_t10_displacement_mm, r.sigma_y_t10_mpa,
       r.processed_at
FROM tests t
LEFT JOIN results r ON r.test_id = t.id
"""

_UPSERT_RESULTADO = f"""
INSERT INTO results (test_id, {", ".join(CAMPOS_RESULTADO)})
VALUES (?, {", ".join("?" for _ in CAMPOS_RESULTADO)})
ON CONFLICT(test_id) DO UPDATE SET
{", ".join(f"{campo} = excluded.{campo}" for campo in CAMPOS_RESULTADO)}
"""


def conectar(ruta: str) -> sqlite3.Connection:
    if ruta != ":memory:":
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ruta, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(ESQUEMA)
    return con


def _a_dict(fila) -> dict:
    ensayo = {
        "id": fila["id"],
        "filename": fila["filename"],
        "material": fila["material"],
        "thickness_mm": fila["thickness_mm"],
        "uploaded_at": fila["uploaded_at"],
        "point_count": fila["point_count"],
        "result": None,
    }
    if fila["r_test_id"] is not None:
        ensayo["result"] = {
            "pm_n": fila["pm_n"],
            "dm_mm": fila["dm_mm"],
            "rm_mpa": fila["rm_mpa"],
            "py_t10_n": fila["py_t10_n"],
            "py_t10_displacement_mm": fila["py_t10_displacement_mm"],
            "sigma_y_t10_mpa": fila["sigma_y_t10_mpa"],
            "parameters": {
                "apply_compliance_correction": bool(fila["apply_compliance_correction"]),
                "compliance_mm_per_n": fila["compliance_mm_per_n"],
                "beta": fila["beta"],
            },
            "processed_at": fila["processed_at"],
        }
    return ensayo


def crear_ensayo(con, filename, material, thickness_mm, point_count, raw_file: bytes, uploaded_at: str) -> int:
    with con:
        cursor = con.execute(
            "INSERT INTO tests (filename, material, thickness_mm, uploaded_at, point_count, raw_file) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (filename, material, thickness_mm, uploaded_at, point_count, raw_file),
        )
    return cursor.lastrowid


def listar_ensayos(con) -> list[dict]:
    filas = con.execute(_SELECT_ENSAYOS + "ORDER BY t.uploaded_at DESC, t.id DESC").fetchall()
    return [_a_dict(fila) for fila in filas]


def obtener_ensayo(con, test_id: int) -> dict | None:
    fila = con.execute(_SELECT_ENSAYOS + "WHERE t.id = ?", (test_id,)).fetchone()
    return _a_dict(fila) if fila else None


def obtener_archivo(con, test_id: int) -> tuple[str, bytes] | None:
    fila = con.execute("SELECT filename, raw_file FROM tests WHERE id = ?", (test_id,)).fetchone()
    return (fila["filename"], bytes(fila["raw_file"])) if fila else None


def _upsert_resultado(con, test_id: int, resultado: dict) -> None:
    con.execute(_UPSERT_RESULTADO, (test_id, *(resultado[campo] for campo in CAMPOS_RESULTADO)))


def guardar_resultado(con, test_id: int, resultado: dict) -> None:
    with con:
        _upsert_resultado(con, test_id, resultado)


def actualizar_espesor(con, test_id: int, thickness_mm: float, resultado: dict | None) -> None:
    """Cambia el espesor y, si se pasa, reemplaza el resultado en la misma transacción."""
    with con:
        con.execute("UPDATE tests SET thickness_mm = ? WHERE id = ?", (thickness_mm, test_id))
        if resultado is not None:
            _upsert_resultado(con, test_id, resultado)


def borrar_ensayo(con, test_id: int) -> bool:
    with con:
        cursor = con.execute("DELETE FROM tests WHERE id = ?", (test_id,))
    return cursor.rowcount > 0
```

- [ ] **Step 4: Correr y ver que pasan**

Run: `.venv/Scripts/python -m pytest tests/test_repository.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add app/__init__.py app/repository.py tests/test_repository.py
git commit -m "feat: agregar repositorio sqlite de ensayos y resultados"
```

### Task 7: Servicio (casos de uso)

**Files:**
- Create: `tp-final/app/service.py`
- Test: `tp-final/tests/test_service.py`

**Interfaces:**
- Consumes: `repository` (Task 6); `leer_raw` (Task 1); `ParametrosProcesamiento`, `analizar`, `preprocesar` (Task 3).
- Produces: `ErrorApi(status: int, code: str, message: str)`; `listar(con)`, `obtener(con, test_id)`, `subir(con, filename, contenido, material, thickness_mm) -> dict`, `procesar(con, test_id, parametros) -> dict` (resultado), `corregir_espesor(con, test_id, thickness_mm) -> dict` (ensayo), `resultado(con, test_id) -> dict`, `curva(con, test_id, source) -> dict`, `archivo(con, test_id) -> tuple[str, bytes]`, `borrar(con, test_id) -> None`. `service.analizar` es el nombre importado que los tests reemplazan con `monkeypatch`.

- [ ] **Step 1: Escribir los tests que fallan**

`tp-final/tests/test_service.py`:
```python
import pytest

from app import repository, service
from sptero_core.analisis import ParametrosProcesamiento


@pytest.fixture
def con(tmp_path):
    conexion = repository.conectar(str(tmp_path / "prueba.db"))
    yield conexion
    conexion.close()


@pytest.fixture
def ensayo(con, raw_sintetico):
    return service.subir(con, "sintetico.raw", raw_sintetico, "304L", 0.5)


def _error(excinfo):
    return excinfo.value.status, excinfo.value.code


def test_subir_guarda_y_cuenta_puntos(ensayo):
    assert ensayo["point_count"] == 601
    assert ensayo["result"] is None


def test_subir_archivo_invalido(con):
    with pytest.raises(service.ErrorApi) as excinfo:
        service.subir(con, "x.raw", b"no es un raw", "304L", 0.5)
    assert _error(excinfo) == (400, "INVALID_FILE")


def test_procesar_y_resultado(con, ensayo):
    resultado = service.procesar(con, ensayo["id"], ParametrosProcesamiento())
    assert resultado["rm_mpa"] == pytest.approx(398.88)
    assert resultado["parameters"] == {"apply_compliance_correction": False, "compliance_mm_per_n": None, "beta": 0.277}
    assert service.resultado(con, ensayo["id"]) == resultado


def test_procesar_idempotente_no_toca_processed_at(con, ensayo, monkeypatch):
    primero = service.procesar(con, ensayo["id"], ParametrosProcesamiento())
    monkeypatch.setattr(service, "_ahora", lambda: "2099-01-01T00:00:00+00:00")
    segundo = service.procesar(con, ensayo["id"], ParametrosProcesamiento())
    assert segundo["processed_at"] == primero["processed_at"]


def test_procesar_guarda_cp_solo_si_se_aplica(con, ensayo):
    resultado = service.procesar(con, ensayo["id"], ParametrosProcesamiento(aplicar_correccion=True))
    assert resultado["parameters"]["compliance_mm_per_n"] == 2.281e-4


def test_procesar_falla_422(con, construir_raw, curva_decreciente):
    test_id = service.subir(con, "d.raw", construir_raw(*curva_decreciente), "304L", 0.5)["id"]
    with pytest.raises(service.ErrorApi) as excinfo:
        service.procesar(con, test_id, ParametrosProcesamiento())
    assert _error(excinfo) == (422, "PROCESSING_FAILED")


def test_inexistente_404(con):
    for llamada in (
        lambda: service.obtener(con, 99),
        lambda: service.procesar(con, 99, ParametrosProcesamiento()),
        lambda: service.corregir_espesor(con, 99, 0.4),
        lambda: service.curva(con, 99, "raw"),
        lambda: service.archivo(con, 99),
        lambda: service.borrar(con, 99),
    ):
        with pytest.raises(service.ErrorApi) as excinfo:
            llamada()
        assert _error(excinfo) == (404, "TEST_NOT_FOUND")


def test_sin_procesar_404_result_not_found(con, ensayo):
    for llamada in (lambda: service.resultado(con, ensayo["id"]), lambda: service.curva(con, ensayo["id"], "processed")):
        with pytest.raises(service.ErrorApi) as excinfo:
            llamada()
        assert _error(excinfo) == (404, "RESULT_NOT_FOUND")


def test_curva_procesada_en_coordenadas_del_resultado(con, ensayo):
    resultado = service.procesar(con, ensayo["id"], ParametrosProcesamiento(aplicar_correccion=True))
    curva = service.curva(con, ensayo["id"], "processed")
    assert curva["displacement_mm"][0] == 0.0
    i = curva["load_n"].index(max(curva["load_n"]))
    assert curva["displacement_mm"][i] == pytest.approx(resultado["dm_mm"])


def test_corregir_espesor_recalcula(con, ensayo):
    service.procesar(con, ensayo["id"], ParametrosProcesamiento())
    actualizado = service.corregir_espesor(con, ensayo["id"], 0.25)
    assert actualizado["thickness_mm"] == 0.25
    assert actualizado["result"]["rm_mpa"] == pytest.approx(797.76)
    assert actualizado["result"]["py_t10_n"] == pytest.approx(318.75)
    assert actualizado["result"]["parameters"]["beta"] == 0.277


def test_corregir_espesor_igual_no_cambia(con, ensayo):
    antes = {**ensayo, "result": service.procesar(con, ensayo["id"], ParametrosProcesamiento())}
    assert service.corregir_espesor(con, ensayo["id"], 0.5) == antes


def test_corregir_espesor_sin_resultado(con, ensayo):
    actualizado = service.corregir_espesor(con, ensayo["id"], 0.4)
    assert actualizado["thickness_mm"] == 0.4
    assert actualizado["result"] is None


def test_corregir_espesor_si_falla_el_recalculo_no_cambia_nada(con, ensayo, monkeypatch):
    service.procesar(con, ensayo["id"], ParametrosProcesamiento())
    antes = service.obtener(con, ensayo["id"])

    def falla(*args, **kwargs):
        raise ValueError("falla simulada del recálculo")

    monkeypatch.setattr(service, "analizar", falla)
    with pytest.raises(service.ErrorApi) as excinfo:
        service.corregir_espesor(con, ensayo["id"], 0.25)
    assert _error(excinfo) == (422, "PROCESSING_FAILED")
    assert service.obtener(con, ensayo["id"]) == antes


def test_borrar(con, ensayo):
    service.borrar(con, ensayo["id"])
    with pytest.raises(service.ErrorApi):
        service.obtener(con, ensayo["id"])
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `.venv/Scripts/python -m pytest tests/test_service.py -v`
Expected: FAIL con `ImportError: cannot import name 'service'`.

- [ ] **Step 3: Implementar**

`tp-final/app/service.py`:
```python
"""Casos de uso de SPTERO Web: orquestan el motor científico y el repositorio.

Traducen los ValueError del core a errores de la API (`ErrorApi`); el core no
conoce HTTP.
"""
from datetime import datetime, timezone

from app import repository
from sptero_core.analisis import ParametrosProcesamiento, analizar, preprocesar
from sptero_core.raw import leer_raw


class ErrorApi(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ensayo_o_404(con, test_id: int) -> dict:
    ensayo = repository.obtener_ensayo(con, test_id)
    if ensayo is None:
        raise ErrorApi(404, "TEST_NOT_FOUND", f"El ensayo {test_id} no existe")
    return ensayo


def _contenido(con, test_id: int) -> bytes:
    return repository.obtener_archivo(con, test_id)[1]


def _parametros_de(resultado: dict) -> ParametrosProcesamiento:
    p = resultado["parameters"]
    if p["apply_compliance_correction"]:
        return ParametrosProcesamiento(True, p["compliance_mm_per_n"], p["beta"])
    return ParametrosProcesamiento(aplicar_correccion=False, beta=p["beta"])


def _mismos_parametros(resultado: dict, parametros: ParametrosProcesamiento) -> bool:
    return resultado["parameters"] == _parametros_contrato(parametros)


def _parametros_contrato(parametros: ParametrosProcesamiento) -> dict:
    return {
        "apply_compliance_correction": parametros.aplicar_correccion,
        "compliance_mm_per_n": parametros.cp_mm_por_n if parametros.aplicar_correccion else None,
        "beta": parametros.beta,
    }


def _calcular(contenido: bytes, thickness_mm: float, parametros: ParametrosProcesamiento) -> dict:
    """Corre el análisis y arma el resultado plano para el repositorio. No escribe nada."""
    try:
        r = analizar(contenido, thickness_mm, parametros)
    except ValueError as error:
        raise ErrorApi(422, "PROCESSING_FAILED", str(error)) from error
    return {
        **_parametros_contrato(parametros),
        "pm_n": r.pm_n,
        "dm_mm": r.dm_mm,
        "rm_mpa": r.rm_mpa,
        "py_t10_n": r.py_t10_n,
        "py_t10_displacement_mm": r.py_t10_displacement_mm,
        "sigma_y_t10_mpa": r.sigma_y_t10_mpa,
        "processed_at": _ahora(),
    }


def listar(con) -> list[dict]:
    return repository.listar_ensayos(con)


def obtener(con, test_id: int) -> dict:
    return _ensayo_o_404(con, test_id)


def subir(con, filename: str, contenido: bytes, material: str, thickness_mm: float) -> dict:
    try:
        curva = leer_raw(contenido)
    except ValueError as error:
        raise ErrorApi(400, "INVALID_FILE", str(error)) from error
    test_id = repository.crear_ensayo(con, filename, material, thickness_mm, len(curva.x), contenido, _ahora())
    return repository.obtener_ensayo(con, test_id)


def procesar(con, test_id: int, parametros: ParametrosProcesamiento) -> dict:
    ensayo = _ensayo_o_404(con, test_id)
    if ensayo["result"] is not None and _mismos_parametros(ensayo["result"], parametros):
        return ensayo["result"]
    nuevo = _calcular(_contenido(con, test_id), ensayo["thickness_mm"], parametros)
    repository.guardar_resultado(con, test_id, nuevo)
    return repository.obtener_ensayo(con, test_id)["result"]


def corregir_espesor(con, test_id: int, thickness_mm: float) -> dict:
    ensayo = _ensayo_o_404(con, test_id)
    if ensayo["thickness_mm"] == thickness_mm:
        return ensayo
    nuevo = None
    if ensayo["result"] is not None:
        # Se calcula antes de escribir: si falla, no se tocó la base.
        nuevo = _calcular(_contenido(con, test_id), thickness_mm, _parametros_de(ensayo["result"]))
    # Espesor y resultado se guardan en una sola transacción.
    repository.actualizar_espesor(con, test_id, thickness_mm, nuevo)
    return repository.obtener_ensayo(con, test_id)


def resultado(con, test_id: int) -> dict:
    ensayo = _ensayo_o_404(con, test_id)
    if ensayo["result"] is None:
        raise ErrorApi(404, "RESULT_NOT_FOUND", f"El ensayo {test_id} todavía no se procesó")
    return ensayo["result"]


def curva(con, test_id: int, source: str) -> dict:
    _ensayo_o_404(con, test_id)
    if source == "processed":
        parametros = _parametros_de(resultado(con, test_id))
        x, y = preprocesar(leer_raw(_contenido(con, test_id)), parametros)
    else:
        cruda = leer_raw(_contenido(con, test_id))
        x, y = cruda.x, cruda.y
    return {"test_id": test_id, "source": source, "displacement_mm": x.tolist(), "load_n": y.tolist()}


def archivo(con, test_id: int) -> tuple[str, bytes]:
    _ensayo_o_404(con, test_id)
    return repository.obtener_archivo(con, test_id)


def borrar(con, test_id: int) -> None:
    if not repository.borrar_ensayo(con, test_id):
        raise ErrorApi(404, "TEST_NOT_FOUND", f"El ensayo {test_id} no existe")
```

- [ ] **Step 4: Correr y ver que pasan**

Run: `.venv/Scripts/python -m pytest tests/test_service.py -v`
Expected: 14 passed.

- [ ] **Step 5: Commit**

```bash
git add app/service.py tests/test_service.py
git commit -m "feat: agregar casos de uso con recálculo atómico del espesor"
```

### Task 8: Rutas FastAPI

**Files:**
- Create: `tp-final/app/schemas.py`, `tp-final/app/main.py`
- Modify: `tp-final/tests/test_contrato.py` (agrega la comparación app ↔ contrato)
- Test: `tp-final/tests/test_api.py`

**Interfaces:**
- Consumes: `service` (Task 7), `repository.conectar` (Task 6), `ParametrosProcesamiento` (Task 3).
- Produces: `app.main.crear_app(ruta_db: str | None = None) -> FastAPI` y `app.main.app` (para uvicorn). La Task 9 agrega a `crear_app` la página y los estáticos.

- [ ] **Step 1: Escribir los tests que fallan**

`tp-final/tests/test_api.py`:
```python
import pytest
from fastapi.testclient import TestClient

from app import service
from app.main import crear_app


@pytest.fixture
def cliente(tmp_path):
    return TestClient(crear_app(str(tmp_path / "prueba.db")))


@pytest.fixture
def subir(cliente, raw_sintetico):
    def _subir(contenido=None, material="304L", thickness_mm="0.5", nombre="sintetico.raw"):
        return cliente.post(
            "/tests",
            files={"file": (nombre, raw_sintetico if contenido is None else contenido, "application/octet-stream")},
            data={"material": material, "thickness_mm": thickness_mm},
        )
    return _subir


def _codigo(respuesta):
    return respuesta.status_code, respuesta.json()["code"]


def test_post_crea_ensayo(subir):
    r = subir()
    assert r.status_code == 201
    cuerpo = r.json()
    assert r.headers["location"] == f"/tests/{cuerpo['id']}"
    assert cuerpo["point_count"] == 601
    assert cuerpo["result"] is None


@pytest.mark.parametrize("contenido", [b"", b"no es un raw", b"%PDF-1.4\n\x00\xff\xfe binario"])
def test_post_archivo_que_no_es_raw(subir, contenido):
    assert _codigo(subir(contenido=contenido)) == (400, "INVALID_FILE")


@pytest.mark.parametrize("cambios", [{"thickness_mm": "0"}, {"thickness_mm": "abc"}, {"material": ""}])
def test_post_parametros_invalidos(subir, cambios):
    assert _codigo(subir(**cambios)) == (400, "INVALID_PARAMETERS")


def test_post_sin_archivo(cliente):
    r = cliente.post("/tests", data={"material": "304L", "thickness_mm": "0.5"})
    assert _codigo(r) == (400, "INVALID_PARAMETERS")


def test_listado_mas_reciente_primero(cliente, subir):
    primero = subir().json()["id"]
    segundo = subir().json()["id"]
    assert [e["id"] for e in cliente.get("/tests").json()] == [segundo, primero]


def test_get_inexistente_y_id_invalido(cliente):
    assert _codigo(cliente.get("/tests/99")) == (404, "TEST_NOT_FOUND")
    assert _codigo(cliente.get("/tests/0")) == (400, "INVALID_PARAMETERS")


def test_put_procesa(cliente, subir):
    test_id = subir().json()["id"]
    r = cliente.put(f"/tests/{test_id}/result")
    assert r.status_code == 200
    resultado = r.json()
    assert resultado["pm_n"] == pytest.approx(1440.0)
    assert resultado["dm_mm"] == pytest.approx(2.0)
    assert resultado["rm_mpa"] == pytest.approx(398.88)
    assert resultado["py_t10_n"] == pytest.approx(337.5)
    assert resultado["py_t10_displacement_mm"] == pytest.approx(0.1625)
    assert resultado["sigma_y_t10_mpa"] == pytest.approx(467.1)
    assert cliente.get(f"/tests/{test_id}").json()["result"] == resultado


def test_put_idempotente(cliente, subir):
    test_id = subir().json()["id"]
    primero = cliente.put(f"/tests/{test_id}/result", json={"beta": 0.277}).json()
    segundo = cliente.put(f"/tests/{test_id}/result", json={}).json()
    assert segundo == primero
    tercero = cliente.put(f"/tests/{test_id}/result", json={"beta": 0.3}).json()
    assert tercero["rm_mpa"] == pytest.approx(0.3 * 1440 / (2.0 * 0.5))


@pytest.mark.parametrize("cuerpo", [{"beta": 0}, {"compliance_mm_per_n": -1}, {"apply_compliance_correction": "quizás"}])
def test_put_parametros_invalidos(cliente, subir, cuerpo):
    test_id = subir().json()["id"]
    assert _codigo(cliente.put(f"/tests/{test_id}/result", json=cuerpo)) == (400, "INVALID_PARAMETERS")


def test_put_inexistente(cliente):
    assert _codigo(cliente.put("/tests/99/result")) == (404, "TEST_NOT_FOUND")


def test_put_422_y_queda_sin_resultado(cliente, subir, construir_raw, curva_decreciente):
    test_id = subir(contenido=construir_raw(*curva_decreciente)).json()["id"]
    assert _codigo(cliente.put(f"/tests/{test_id}/result")) == (422, "PROCESSING_FAILED")
    assert _codigo(cliente.get(f"/tests/{test_id}/result")) == (404, "RESULT_NOT_FOUND")


def test_curvas(cliente, subir):
    test_id = subir().json()["id"]
    cruda = cliente.get(f"/tests/{test_id}/curve").json()
    assert cruda["source"] == "raw" and len(cruda["displacement_mm"]) == 601
    assert _codigo(cliente.get(f"/tests/{test_id}/curve?source=processed")) == (404, "RESULT_NOT_FOUND")
    assert _codigo(cliente.get(f"/tests/{test_id}/curve?source=otra")) == (400, "INVALID_PARAMETERS")
    cliente.put(f"/tests/{test_id}/result", json={"apply_compliance_correction": True})
    procesada = cliente.get(f"/tests/{test_id}/curve?source=processed").json()
    assert len(procesada["displacement_mm"]) == 600
    assert procesada["displacement_mm"][0] == 0.0


def test_archivo_original(cliente, subir, raw_sintetico):
    test_id = subir(nombre="P_prueba.raw").json()["id"]
    r = cliente.get(f"/tests/{test_id}/file")
    assert r.status_code == 200
    assert r.content == raw_sintetico
    assert r.headers["content-disposition"] == 'attachment; filename="P_prueba.raw"'


def test_delete(cliente, subir):
    test_id = subir().json()["id"]
    assert cliente.delete(f"/tests/{test_id}").status_code == 204
    assert _codigo(cliente.get(f"/tests/{test_id}")) == (404, "TEST_NOT_FOUND")
    assert _codigo(cliente.delete(f"/tests/{test_id}")) == (404, "TEST_NOT_FOUND")


def test_patch_recalcula(cliente, subir):
    test_id = subir().json()["id"]
    cliente.put(f"/tests/{test_id}/result")
    r = cliente.patch(f"/tests/{test_id}", json={"thickness_mm": 0.25})
    assert r.status_code == 200
    assert r.json()["thickness_mm"] == 0.25
    assert r.json()["result"]["rm_mpa"] == pytest.approx(797.76)


def test_patch_mismo_espesor_no_cambia(cliente, subir):
    test_id = subir().json()["id"]
    cliente.put(f"/tests/{test_id}/result")
    antes = cliente.get(f"/tests/{test_id}").json()
    assert cliente.patch(f"/tests/{test_id}", json={"thickness_mm": 0.5}).json() == antes


@pytest.mark.parametrize("cuerpo", [{"thickness_mm": 0}, {"thickness_mm": "abc"}, {}])
def test_patch_invalido(cliente, subir, cuerpo):
    test_id = subir().json()["id"]
    assert _codigo(cliente.patch(f"/tests/{test_id}", json=cuerpo)) == (400, "INVALID_PARAMETERS")


def test_patch_inexistente(cliente):
    assert _codigo(cliente.patch("/tests/99", json={"thickness_mm": 0.4})) == (404, "TEST_NOT_FOUND")


def test_patch_si_falla_el_recalculo_no_cambia_nada(cliente, subir, monkeypatch):
    test_id = subir().json()["id"]
    cliente.put(f"/tests/{test_id}/result")
    antes = cliente.get(f"/tests/{test_id}").json()

    def falla(*args, **kwargs):
        raise ValueError("falla simulada del recálculo")

    monkeypatch.setattr(service, "analizar", falla)
    assert _codigo(cliente.patch(f"/tests/{test_id}", json={"thickness_mm": 0.25})) == (422, "PROCESSING_FAILED")
    assert cliente.get(f"/tests/{test_id}").json() == antes
```

Agregar al final de `tp-final/tests/test_contrato.py`:
```python
from app.main import crear_app

SCHEMAS_COMPARTIDOS = ["Test", "TestUpdate", "ProcessingRequest", "ProcessingParameters", "Result", "Curve"]


def test_la_app_implementa_las_operaciones_del_contrato():
    assert operaciones(crear_app(":memory:").openapi()) == operaciones(cargar_contrato())


def test_los_campos_de_la_app_coinciden_con_el_contrato():
    app_schemas = crear_app(":memory:").openapi()["components"]["schemas"]
    contrato_schemas = cargar_contrato()["components"]["schemas"]
    for nombre in SCHEMAS_COMPARTIDOS:
        assert set(app_schemas[nombre]["properties"]) == set(contrato_schemas[nombre]["properties"]), nombre
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `.venv/Scripts/python -m pytest tests/test_api.py tests/test_contrato.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.main'`.

- [ ] **Step 3: Implementar los schemas**

`tp-final/app/schemas.py`:
```python
"""Modelos Pydantic: reflejan los schemas de openapi.yaml v1.1."""
from typing import Literal

from pydantic import BaseModel, Field


class ProcessingParameters(BaseModel):
    apply_compliance_correction: bool
    compliance_mm_per_n: float | None
    beta: float


class Result(BaseModel):
    pm_n: float
    dm_mm: float
    rm_mpa: float
    py_t10_n: float | None
    py_t10_displacement_mm: float | None
    sigma_y_t10_mpa: float | None
    parameters: ProcessingParameters
    processed_at: str


class Test(BaseModel):
    id: int
    filename: str
    material: str
    thickness_mm: float
    uploaded_at: str
    point_count: int
    result: Result | None


class TestUpdate(BaseModel):
    thickness_mm: float = Field(gt=0)


class ProcessingRequest(BaseModel):
    apply_compliance_correction: bool = False
    compliance_mm_per_n: float = Field(default=2.281e-4, gt=0)
    beta: float = Field(default=0.277, gt=0)


class Curve(BaseModel):
    test_id: int
    source: Literal["raw", "processed"]
    displacement_mm: list[float]
    load_n: list[float]
```

- [ ] **Step 4: Implementar las rutas**

`tp-final/app/main.py`:
```python
"""Rutas de la API de SPTERO Web (contrato openapi.yaml v1.1).

Las rutas no calculan ni escriben SQL: validan la entrada y delegan en service.
"""
import os
import sqlite3
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Body, Depends, FastAPI, File, Form, Path as PathParam, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import repository, service
from app.schemas import Curve, ProcessingRequest, Result, Test, TestUpdate
from sptero_core.analisis import ParametrosProcesamiento

RAIZ = Path(__file__).resolve().parent.parent
RUTA_DB_POR_DEFECTO = RAIZ / "data" / "sptero.db"


def crear_app(ruta_db: str | None = None) -> FastAPI:
    ruta = ruta_db or os.environ.get("SPTERO_DB") or str(RUTA_DB_POR_DEFECTO)
    app = FastAPI(title="API de SPTERO Web", version="1.1.0")

    def conexion():
        con = repository.conectar(ruta)
        try:
            yield con
        finally:
            con.close()

    Conexion = Annotated[sqlite3.Connection, Depends(conexion)]
    TestId = Annotated[int, PathParam(ge=1, description="Identificador del ensayo")]

    @app.exception_handler(service.ErrorApi)
    def error_api(_request, error: service.ErrorApi):
        return JSONResponse(status_code=error.status, content={"code": error.code, "message": error.message})

    @app.exception_handler(RequestValidationError)
    def error_validacion(_request, error: RequestValidationError):
        detalle = "; ".join(f"{'.'.join(str(p) for p in e['loc'][1:])}: {e['msg']}" for e in error.errors())
        return JSONResponse(status_code=400, content={"code": "INVALID_PARAMETERS", "message": f"Parámetros inválidos: {detalle}"})

    @app.get("/tests", response_model=list[Test], tags=["Ensayos"])
    def listar(con: Conexion):
        return service.listar(con)

    @app.post("/tests", status_code=201, response_model=Test, tags=["Ensayos"])
    def subir(
        con: Conexion,
        response: Response,
        file: Annotated[UploadFile, File()],
        material: Annotated[str, Form(min_length=1, max_length=50)],
        thickness_mm: Annotated[float, Form(gt=0)],
    ):
        ensayo = service.subir(con, file.filename or "ensayo.raw", file.file.read(), material, thickness_mm)
        response.headers["Location"] = f"/tests/{ensayo['id']}"
        return ensayo

    @app.get("/tests/{testId}", response_model=Test, tags=["Ensayos"])
    def obtener(con: Conexion, testId: TestId):
        return service.obtener(con, testId)

    @app.patch("/tests/{testId}", response_model=Test, tags=["Ensayos"])
    def corregir_espesor(con: Conexion, testId: TestId, cuerpo: TestUpdate):
        return service.corregir_espesor(con, testId, cuerpo.thickness_mm)

    @app.delete("/tests/{testId}", status_code=204, tags=["Ensayos"])
    def borrar(con: Conexion, testId: TestId):
        service.borrar(con, testId)
        return Response(status_code=204)

    @app.get("/tests/{testId}/file", tags=["Ensayos"], response_class=Response)
    def archivo(con: Conexion, testId: TestId):
        nombre, contenido = service.archivo(con, testId)
        return Response(
            content=contenido,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
        )

    @app.get("/tests/{testId}/curve", response_model=Curve, tags=["Ensayos"])
    def curva(con: Conexion, testId: TestId, source: Literal["raw", "processed"] = "raw"):
        return service.curva(con, testId, source)

    @app.get("/tests/{testId}/result", response_model=Result, tags=["Resultados"])
    def resultado(con: Conexion, testId: TestId):
        return service.resultado(con, testId)

    @app.put("/tests/{testId}/result", response_model=Result, tags=["Resultados"])
    def procesar(con: Conexion, testId: TestId, cuerpo: Annotated[ProcessingRequest | None, Body()] = None):
        cuerpo = cuerpo or ProcessingRequest()
        parametros = ParametrosProcesamiento(
            aplicar_correccion=cuerpo.apply_compliance_correction,
            cp_mm_por_n=cuerpo.compliance_mm_per_n,
            beta=cuerpo.beta,
        )
        return service.procesar(con, testId, parametros)

    return app


app = crear_app()
```

- [ ] **Step 5: Correr toda la suite**

Run: `.venv/Scripts/python -m pytest -v`
Expected: todo en verde (caracterización `SKIPPED` sin variables). Si un test de `test_api.py` da 422 en lugar de 400, el handler de `RequestValidationError` no se registró: revisar que esté dentro de `crear_app`.

- [ ] **Step 6: Probar a mano el servidor**

Run: `.venv/Scripts/python -m uvicorn app.main:app --port 8000` y abrir `http://localhost:8000/docs`.
Expected: Swagger lista las 9 operaciones. Subir `P3_304L_L.raw` desde `/docs` (POST con t = 0.5) y procesar con `PUT` sin cuerpo: Pm 2372,2 · dm 2,2709 · Rm 578,7 · Py 274,9 (en 0,2581 mm) · σy 380,5.

- [ ] **Step 7: Commit**

```bash
git add app/schemas.py app/main.py tests/test_api.py tests/test_contrato.py openapi.yaml
git commit -m "feat: agregar rutas fastapi del contrato v1.1"
```
Fin de la etapa 3: `superpowers:requesting-code-review` sobre la rama, correcciones, y Julián abre el PR `feature/tp-final-api` → `main`.

---

# Etapa 4 — Interfaz (`feature/tp-final-ui`)

Verificación en navegador: no hay Node instalado, así que no se usa Playwright MCP. Se usa el navegador integrado de la app (MCP `Claude_Browser`), que ya está disponible: la "pregunta cero" de la semana 6 (¿el host ya lo hace?). El servidor se levanta con `preview_start` desde `.claude/launch.json`.

### Task 9: Página de análisis (carga, procesamiento, estado, gráfico, eliminar)

**Files:**
- Create: `tp-final/static/index.html`, `tp-final/static/styles.css`, `tp-final/static/app.js`, `tp-final/.claude/launch.json`
- Modify: `tp-final/app/main.py` (servir la página y los estáticos)
- Test: `tp-final/tests/test_api.py` (la página se sirve)

**Interfaces:**
- Consumes: la API de la Task 8.
- Produces (en `app.js`, para las Tasks 10 y 11): `estado` (`{ensayo, archivo, ensayos, seleccion}`), `pedir(metodo, url, cuerpo)`, `leerNumero(id, nombre)`, `graficar(divId, trazas)`, `layoutBase()`, `COLORES`, `abrirEnsayo(id)`, `cargarHistorial()` (la Task 9 la deja como función vacía y la Task 10 la completa), `eliminarEnsayo(ensayo)`, `nuevoAnalisis()`, `actualizarComparacion()` (vacía hasta la Task 11).

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tp-final/tests/test_api.py`:
```python
def test_sirve_la_interfaz(cliente):
    r = cliente.get("/")
    assert r.status_code == 200
    assert "SPTERO" in r.text
    assert cliente.get("/static/app.js").status_code == 200
```

Run: `.venv/Scripts/python -m pytest tests/test_api.py::test_sirve_la_interfaz -v`
Expected: FAIL (404).

- [ ] **Step 2: Servir los estáticos**

En `tp-final/app/main.py` agregar los imports:
```python
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
```
la constante:
```python
CARPETA_STATIC = RAIZ / "static"
```
y, dentro de `crear_app`, justo antes de `return app`:
```python
    @app.get("/", include_in_schema=False)
    def inicio():
        return FileResponse(CARPETA_STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=CARPETA_STATIC), name="static")
```

`tp-final/.claude/launch.json`:
```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "sptero-web",
      "runtimeExecutable": ".venv/Scripts/python",
      "runtimeArgs": ["-m", "uvicorn", "app.main:app", "--port", "8000"],
      "port": 8000
    }
  ]
}
```

- [ ] **Step 3: Escribir la página**

`tp-final/static/index.html`:
```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SPTERO Web</title>
<link rel="stylesheet" href="/static/styles.css">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
</head>
<body>
<header>
  <div class="brand">SPTERO <span>Web</span></div>
  <nav class="nav">
    <a href="#analisis">Análisis</a>
    <a href="#historial">Historial</a>
    <a href="#comparacion">Comparación</a>
  </nav>
</header>

<main>
  <section class="hero" id="analisis">
    <div>
      <h1 id="titulo">Nuevo análisis SPT</h1>
      <p class="subtitle">Cargá un archivo .raw, revisá la curva y obtené los parámetros principales del ensayo.</p>
    </div>
    <div class="badge" id="estado" data-estado="vacio" role="status">Sin ensayo abierto</div>
  </section>

  <section class="grid-main">
    <aside class="card">
      <div class="card-header">
        <h2>Datos del ensayo</h2>
        <p>Cada análisis se guarda automáticamente.</p>
      </div>
      <form class="card-body" id="formulario" novalidate>
        <label class="upload" id="zona-carga">
          <input type="file" id="archivo" accept=".raw,.csv" hidden>
          <div class="upload-icon">↑</div>
          <strong>Arrastrar archivo .raw</strong>
          <span>o hacer clic para elegirlo</span>
          <div class="file-chip" id="chip-archivo" hidden>
            <div class="dot"></div>
            <div><b id="nombre-archivo"></b><small id="detalle-archivo"></small></div>
          </div>
        </label>

        <div class="field">
          <label for="material">Material</label>
          <input class="input" id="material" maxlength="50" autocomplete="off">
        </div>
        <div class="two">
          <div class="field">
            <label for="espesor">Espesor t [mm]</label>
            <input class="input" id="espesor" inputmode="decimal" value="0.5">
          </div>
          <div class="field">
            <label for="beta">β para Rm</label>
            <input class="input" id="beta" inputmode="decimal" value="0.277">
          </div>
        </div>
        <div class="field">
          <label for="cp">C<sub>P</sub> [mm/N]</label>
          <input class="input" id="cp" inputmode="decimal" value="2.281e-4">
          <div class="help">Flexibilidad conocida del sistema.</div>
        </div>
        <label class="check">
          <input type="checkbox" id="corregir">
          <span>Aplicar corrección de flexibilidad al desplazamiento antes del análisis.</span>
        </label>

        <p class="aviso" id="aviso-formulario" role="alert" hidden></p>
        <button class="primary" type="submit" id="boton-analizar">Analizar ensayo</button>
        <div class="acciones">
          <button class="secondary" type="button" id="boton-nuevo">Nuevo análisis</button>
          <button class="danger" type="button" id="boton-eliminar" hidden>Eliminar ensayo</button>
        </div>
      </form>
    </aside>

    <div class="right-column">
      <section class="card">
        <div class="chart-title-row">
          <div>
            <h2>Curva carga–desplazamiento</h2>
            <p id="subtitulo-grafico">Todavía no hay un ensayo analizado.</p>
          </div>
        </div>
        <div class="chart-wrap" id="grafico"></div>
      </section>

      <section class="card">
        <div class="card-header">
          <h2>Resultados principales</h2>
          <p id="parametros-usados">—</p>
        </div>
        <div class="card-body">
          <div class="results-grid">
            <div class="metric"><small>Carga máxima Pm</small><strong id="m-pm">—</strong><span>N</span></div>
            <div class="metric"><small>Desplazamiento a Pm · dm</small><strong id="m-dm">—</strong><span>mm</span></div>
            <div class="metric"><small>Resistencia estimada Rm</small><strong id="m-rm">—</strong><span>MPa</span></div>
            <div class="metric"><small>Fluencia Py · t/10</small><strong id="m-py">—</strong><span>N</span></div>
            <div class="metric"><small>Límite elástico σy · t/10</small><strong id="m-sigma">—</strong><span>MPa</span></div>
          </div>
          <p class="note">Py t/10 se calcula con la rama de SPTERO que no usa MAO (MAO no está en esta versión): puede diferir de un análisis por consola que haya usado zonas MAO.</p>
        </div>
      </section>
    </div>
  </section>

  <section class="card history" id="historial">
    <div class="card-header">
      <h2>Historial</h2>
      <p>Abrí un ensayo para reprocesarlo o marcá dos para comparar sus curvas.</p>
    </div>
    <div class="card-body tabla-scroll">
      <table class="table">
        <thead>
          <tr><th>COMPARAR</th><th>ENSAYO</th><th>MATERIAL</th><th>T [MM]</th><th>PM</th><th>RM</th><th>FECHA</th><th>ESTADO</th><th></th></tr>
        </thead>
        <tbody id="filas-historial"></tbody>
      </table>
    </div>
  </section>

  <section class="card history" id="comparacion">
    <div class="chart-title-row">
      <div>
        <h2>Comparación</h2>
        <p id="ayuda-comparacion">Marcá dos ensayos en el historial.</p>
      </div>
      <div class="controles">
        <select class="input" id="tipo-curva" aria-label="Tipo de curva">
          <option value="raw">Curvas crudas</option>
          <option value="processed">Curvas procesadas</option>
        </select>
        <button class="save" type="button" id="boton-comparar" disabled>Comparar</button>
      </div>
    </div>
    <div class="chart-wrap" id="grafico-comparacion"></div>
  </section>
</main>
<script src="/static/app.js"></script>
</body>
</html>
```

`tp-final/static/styles.css`:
```css
:root {
  --bg: #f5f7fa;
  --panel: #ffffff;
  --ink: #14212b;
  --muted: #667784;
  --line: #dfe6eb;
  --navy: #17384d;
  --teal: #187e77;
  --teal-soft: #e9f5f3;
  --red: #b53e47;
  --red-soft: #fbecee;
  --amber-soft: #fdf4e3;
  --shadow: 0 10px 30px rgba(20, 33, 43, .07);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  background: var(--bg);
  color: var(--ink);
}
header {
  height: 68px; background: var(--navy); color: white;
  display: flex; align-items: center; gap: 22px; padding: 0 34px;
  box-shadow: 0 2px 8px rgba(0,0,0,.12);
}
.brand { font-weight: 750; font-size: 21px; letter-spacing: .2px; }
.brand span { color: #7fe1d7; }
.nav { display: flex; gap: 6px; margin-left: 22px; }
.nav a { color: #d8e6ec; text-decoration: none; font-size: 14px; padding: 9px 12px; border-radius: 8px; }
.nav a:hover { background: rgba(255,255,255,.12); color: white; }
main { max-width: 1220px; margin: 28px auto 46px; padding: 0 24px; }
.hero { display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; margin-bottom: 20px; }
h1 { margin: 0 0 6px; font-size: 30px; line-height: 1.15; }
.subtitle { margin: 0; color: var(--muted); font-size: 15px; }
.badge {
  padding: 8px 12px; border-radius: 999px; font-size: 13px; white-space: nowrap;
  background: #eef2f5; color: var(--muted); border: 1px solid var(--line);
}
.badge[data-estado="procesado"] { background: var(--teal-soft); color: #116a64; border-color: #cce8e5; }
.badge[data-estado="sin-procesar"], .badge[data-estado="guardando"] { background: var(--amber-soft); color: #8a5a12; border-color: #f0dcb4; }
.badge[data-estado="error"] { background: var(--red-soft); color: var(--red); border-color: #f0c9cd; }
.grid-main { display: grid; grid-template-columns: 360px minmax(0, 1fr); gap: 20px; align-items: start; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; box-shadow: var(--shadow); }
.card-header { padding: 18px 20px 14px; border-bottom: 1px solid var(--line); }
.card-header h2 { font-size: 16px; margin: 0 0 4px; }
.card-header p { margin: 0; color: var(--muted); font-size: 13px; }
.card-body { padding: 20px; }
.upload {
  display: block; cursor: pointer; text-align: center; margin-bottom: 18px; padding: 22px 16px;
  border: 1.5px dashed #a9bcc6; border-radius: 12px; background: #fbfcfd;
}
.upload.arrastrando { border-color: var(--teal); background: var(--teal-soft); }
.upload.bloqueada { cursor: default; opacity: .75; }
.upload-icon {
  width: 42px; height: 42px; margin: 0 auto 10px; border-radius: 12px; display: grid; place-items: center;
  background: var(--teal-soft); color: var(--teal); font-weight: 800; font-size: 20px;
}
.upload strong { display: block; font-size: 14px; margin-bottom: 4px; }
.upload span { color: var(--muted); font-size: 12px; }
.file-chip {
  display: flex; align-items: center; gap: 10px; margin-top: 12px; padding: 10px 12px; text-align: left;
  border: 1px solid var(--line); border-radius: 10px; background: white;
}
.file-chip[hidden] { display: none; }
.file-chip b { display: block; font-size: 13px; word-break: break-all; }
.file-chip small { color: var(--muted); }
.dot { width: 9px; height: 9px; border-radius: 50%; background: #2ea56f; flex: none; }
label { font-size: 12px; font-weight: 650; display: block; margin-bottom: 6px; }
.field { margin-bottom: 14px; }
.input {
  width: 100%; border: 1px solid #cfd9df; background: #fff; border-radius: 9px;
  padding: 11px 12px; font-size: 14px; color: var(--ink); font-family: inherit;
}
.input[readonly] { background: #f3f6f8; color: var(--muted); }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.help { color: var(--muted); font-size: 11px; margin-top: 5px; }
.check {
  display: flex; gap: 9px; align-items: flex-start; padding: 12px; margin: 3px 0 16px;
  background: #f7fafb; border: 1px solid var(--line); border-radius: 9px;
  font-size: 12px; font-weight: 400; color: #425562;
}
.aviso { margin: 0 0 12px; padding: 10px 12px; border-radius: 9px; background: var(--red-soft); color: var(--red); font-size: 13px; }
button { font-family: inherit; cursor: pointer; }
button:disabled { cursor: not-allowed; opacity: .55; }
.primary { width: 100%; padding: 12px 14px; border: 0; border-radius: 9px; background: var(--teal); color: white; font-weight: 700; font-size: 14px; }
.acciones { display: flex; gap: 10px; margin-top: 10px; }
.acciones button { flex: 1; }
.secondary, .save, .danger, .boton-fila { padding: 10px 14px; border-radius: 9px; font-size: 13px; font-weight: 700; }
.secondary { background: white; border: 1px solid #ccd8de; color: #3b4f5b; }
.save { background: var(--navy); border: 1px solid var(--navy); color: white; }
.danger { background: white; border: 1px solid #e3b4b9; color: var(--red); }
.right-column { display: grid; gap: 20px; }
.chart-title-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; padding: 16px 18px 0; }
.chart-title-row h2 { font-size: 16px; margin: 0 0 4px; }
.chart-title-row p { margin: 0; color: var(--muted); font-size: 12px; }
.chart-wrap { padding: 12px 12px 4px; min-height: 380px; }
.sin-grafico { color: var(--muted); font-size: 13px; padding: 24px; }
.results-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.metric { border: 1px solid var(--line); border-radius: 11px; padding: 14px; background: #fbfcfd; }
.metric small { color: var(--muted); display: block; font-size: 11px; margin-bottom: 5px; }
.metric strong { font-size: 22px; letter-spacing: -.2px; }
.metric span { color: var(--muted); font-size: 12px; margin-left: 3px; }
.note { margin-top: 16px; color: var(--muted); font-size: 12px; }
.history { margin-top: 20px; }
.tabla-scroll { padding: 0; overflow-x: auto; }
.table { width: 100%; border-collapse: collapse; font-size: 13px; }
.table th { text-align: left; color: var(--muted); font-size: 11px; font-weight: 700; padding: 10px 14px; border-bottom: 1px solid var(--line); }
.table td { padding: 12px 14px; border-bottom: 1px solid #edf1f3; }
.table tr:last-child td { border-bottom: 0; }
.status { display: inline-block; padding: 5px 8px; border-radius: 999px; font-size: 11px; font-weight: 700; background: var(--teal-soft); color: #116a64; }
.status.pendiente { background: var(--amber-soft); color: #8a5a12; }
.boton-fila { padding: 6px 10px; font-size: 12px; margin-left: 6px; background: white; border: 1px solid #ccd8de; color: #3b4f5b; }
.boton-fila.danger { border-color: #e3b4b9; color: var(--red); }
.controles { display: flex; gap: 10px; }
.controles .input { width: auto; padding: 9px 10px; }
@media (max-width: 900px) {
  header { padding: 0 16px; }
  main { padding: 0 16px; }
  .grid-main { grid-template-columns: 1fr; }
  .results-grid { grid-template-columns: 1fr 1fr; }
  .nav { display: none; }
  .hero, .chart-title-row { flex-direction: column; align-items: flex-start; }
}
```

`tp-final/static/app.js`:
```javascript
"use strict";

// SPTERO Web: interfaz en JS sin frameworks. Habla solo con la API del contrato v1.1.
// Los datos del usuario (archivo, material) se insertan siempre con textContent.

const PLOTLY_CONFIG = { responsive: true, displaylogo: false };
const COLORES = ["#187e77", "#b5643e"];
const estado = { ensayo: null, archivo: null, ensayos: [], seleccion: [] };
const $ = (id) => document.getElementById(id);

async function pedir(metodo, url, cuerpo) {
  const opciones = { method: metodo, headers: {} };
  if (cuerpo instanceof FormData) {
    opciones.body = cuerpo;
  } else if (cuerpo !== undefined) {
    opciones.body = JSON.stringify(cuerpo);
    opciones.headers["Content-Type"] = "application/json";
  }
  const respuesta = await fetch(url, opciones);
  if (respuesta.status === 204) return null;
  const datos = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    const error = new Error(datos && datos.message ? datos.message : `Error ${respuesta.status}`);
    error.code = datos && datos.code;
    throw error;
  }
  return datos;
}

function leerNumero(id, nombre) {
  const texto = $(id).value.trim().replace(",", ".");
  const valor = Number(texto);
  if (texto === "" || !Number.isFinite(valor) || valor <= 0) {
    throw new Error(`${nombre} tiene que ser un número mayor que cero.`);
  }
  return valor;
}

function formato(valor, decimales) {
  if (valor === null || valor === undefined) return "—";
  return valor.toLocaleString("es-AR", { minimumFractionDigits: decimales, maximumFractionDigits: decimales });
}

function mostrarEstado(clave, texto) {
  const insignia = $("estado");
  insignia.dataset.estado = clave;
  insignia.textContent = texto;
}

function mostrarAviso(texto) {
  const aviso = $("aviso-formulario");
  aviso.textContent = texto || "";
  aviso.hidden = !texto;
}

function mostrarChip(nombre, detalle) {
  $("nombre-archivo").textContent = nombre;
  $("detalle-archivo").textContent = detalle;
  $("chip-archivo").hidden = false;
}

function layoutBase() {
  return {
    margin: { l: 64, r: 20, t: 10, b: 50 },
    xaxis: { title: { text: "Desplazamiento [mm]" }, zeroline: false },
    yaxis: { title: { text: "Carga [N]" }, zeroline: false },
    hovermode: "closest",
    legend: { orientation: "h", y: -0.22 },
  };
}

function graficar(divId, trazas) {
  const div = $(divId);
  if (typeof Plotly === "undefined") {
    div.textContent = "No se pudo cargar Plotly.js (hace falta conexión a internet para el gráfico).";
    div.className = "chart-wrap sin-grafico";
    return;
  }
  Plotly.react(div, trazas, layoutBase(), PLOTLY_CONFIG);
}

function leerParametros() {
  return {
    apply_compliance_correction: $("corregir").checked,
    compliance_mm_per_n: leerNumero("cp", "C_P"),
    beta: leerNumero("beta", "β"),
  };
}

async function alEnviar(evento) {
  evento.preventDefault();
  mostrarAviso("");
  let espesor;
  let parametros;
  try {
    espesor = leerNumero("espesor", "El espesor");
    parametros = leerParametros();
  } catch (error) {
    mostrarAviso(error.message);
    return;
  }
  if (estado.ensayo) {
    await recalcular(espesor, parametros);
  } else {
    await analizarNuevo(espesor, parametros);
  }
}

async function analizarNuevo(espesor, parametros) {
  const material = $("material").value.trim();
  if (!estado.archivo) { mostrarAviso("Elegí un archivo .raw."); return; }
  if (!material) { mostrarAviso("Indicá el material."); return; }
  const datos = new FormData();
  datos.append("file", estado.archivo);
  datos.append("material", material);
  datos.append("thickness_mm", String(espesor));
  mostrarEstado("guardando", "Guardando…");
  let creado;
  try {
    creado = await pedir("POST", "/tests", datos);
  } catch (error) {
    mostrarEstado("error", "Error al guardar");
    mostrarAviso(error.message);
    return;
  }
  try {
    await pedir("PUT", `/tests/${creado.id}/result`, parametros);
  } catch (error) {
    mostrarAviso(`El ensayo se guardó, pero no se pudo procesar: ${error.message}`);
  }
  await abrirEnsayo(creado.id);
  await cargarHistorial();
}

async function recalcular(espesor, parametros) {
  const id = estado.ensayo.id;
  mostrarEstado("guardando", "Guardando…");
  try {
    if (espesor !== estado.ensayo.thickness_mm) {
      await pedir("PATCH", `/tests/${id}`, { thickness_mm: espesor });
    }
    const actual = estado.ensayo.result && estado.ensayo.result.parameters;
    const cambiaron = !actual
      || actual.apply_compliance_correction !== parametros.apply_compliance_correction
      || actual.beta !== parametros.beta
      || (parametros.apply_compliance_correction && actual.compliance_mm_per_n !== parametros.compliance_mm_per_n);
    if (cambiaron) await pedir("PUT", `/tests/${id}/result`, parametros);
  } catch (error) {
    mostrarAviso(error.message);
  }
  await abrirEnsayo(id);
  await cargarHistorial();
}

async function abrirEnsayo(id) {
  let ensayo;
  try {
    ensayo = await pedir("GET", `/tests/${id}`);
  } catch (error) {
    mostrarAviso(error.message);
    return;
  }
  estado.ensayo = ensayo;
  estado.archivo = null;
  $("titulo").textContent = `Ensayo ${ensayo.filename}`;
  $("material").value = ensayo.material;
  $("material").readOnly = true;
  $("espesor").value = String(ensayo.thickness_mm);
  $("archivo").disabled = true;
  $("zona-carga").classList.add("bloqueada");
  mostrarChip(ensayo.filename, `${ensayo.point_count} puntos · guardado`);
  $("boton-analizar").textContent = "Recalcular";
  $("boton-eliminar").hidden = false;
  if (ensayo.result) {
    const p = ensayo.result.parameters;
    $("beta").value = String(p.beta);
    $("corregir").checked = p.apply_compliance_correction;
    if (p.compliance_mm_per_n !== null) $("cp").value = String(p.compliance_mm_per_n);
    mostrarEstado("procesado", "Guardado · procesado");
  } else {
    mostrarEstado("sin-procesar", "Guardado · sin procesar");
  }
  mostrarResultado(ensayo.result);
  await graficarEnsayo(ensayo);
}

function mostrarResultado(resultado) {
  $("m-pm").textContent = resultado ? formato(resultado.pm_n, 1) : "—";
  $("m-dm").textContent = resultado ? formato(resultado.dm_mm, 4) : "—";
  $("m-rm").textContent = resultado ? formato(resultado.rm_mpa, 1) : "—";
  $("m-py").textContent = resultado ? formato(resultado.py_t10_n, 1) : "—";
  $("m-sigma").textContent = resultado ? formato(resultado.sigma_y_t10_mpa, 1) : "—";
  if (!resultado) {
    $("parametros-usados").textContent = "—";
    return;
  }
  const p = resultado.parameters;
  const correccion = p.apply_compliance_correction ? `con corrección C_P = ${p.compliance_mm_per_n} mm/N` : "sin corrección de flexibilidad";
  $("parametros-usados").textContent = `t = ${estado.ensayo.thickness_mm} mm · β = ${p.beta} · ${correccion}`;
}

async function graficarEnsayo(ensayo) {
  const fuente = ensayo.result ? "processed" : "raw";
  let curva;
  try {
    curva = await pedir("GET", `/tests/${ensayo.id}/curve?source=${fuente}`);
  } catch (error) {
    mostrarAviso(error.message);
    return;
  }
  const trazas = [{
    x: curva.displacement_mm, y: curva.load_n, mode: "lines", name: "Curva SPT",
    line: { color: COLORES[0], width: 2 },
    hovertemplate: "%{x:.4f} mm<br>%{y:.1f} N<extra></extra>",
  }];
  const r = ensayo.result;
  if (r) {
    trazas.push({
      x: [r.dm_mm], y: [r.pm_n], mode: "markers", name: "Pm",
      marker: { size: 12, color: "white", line: { color: "#b53e47", width: 3 } },
      hovertemplate: "Pm = %{y:.1f} N<br>dm = %{x:.4f} mm<extra></extra>",
    });
    if (r.py_t10_n !== null) {
      trazas.push({
        x: [r.py_t10_displacement_mm], y: [r.py_t10_n], mode: "markers", name: "Py t/10",
        marker: { size: 10, symbol: "square", color: "#17384d" },
        hovertemplate: "Py t/10 = %{y:.1f} N<br>%{x:.4f} mm<extra></extra>",
      });
    }
  }
  $("subtitulo-grafico").textContent = fuente === "processed"
    ? "Curva procesada: la que se usó para calcular los resultados."
    : "Curva cruda: el ensayo todavía no se procesó.";
  graficar("grafico", trazas);
}

async function eliminarEnsayo(ensayo) {
  const confirmado = window.confirm(`¿Eliminar ${ensayo.filename} y su resultado? No se puede deshacer.`);
  if (!confirmado) return;
  try {
    await pedir("DELETE", `/tests/${ensayo.id}`);
  } catch (error) {
    mostrarAviso(error.message);
    return;
  }
  estado.seleccion = estado.seleccion.filter((id) => id !== ensayo.id);
  if (estado.ensayo && estado.ensayo.id === ensayo.id) nuevoAnalisis();
  await cargarHistorial();
}

function nuevoAnalisis() {
  estado.ensayo = null;
  estado.archivo = null;
  $("formulario").reset();
  $("material").readOnly = false;
  $("archivo").disabled = false;
  $("zona-carga").classList.remove("bloqueada");
  $("chip-archivo").hidden = true;
  $("titulo").textContent = "Nuevo análisis SPT";
  $("boton-analizar").textContent = "Analizar ensayo";
  $("boton-eliminar").hidden = true;
  $("subtitulo-grafico").textContent = "Todavía no hay un ensayo analizado.";
  mostrarAviso("");
  mostrarEstado("vacio", "Sin ensayo abierto");
  mostrarResultado(null);
  if (typeof Plotly !== "undefined") Plotly.purge("grafico");
}

function elegirArchivo(archivo) {
  if (!archivo || estado.ensayo) return;
  estado.archivo = archivo;
  mostrarChip(archivo.name, "Listo para analizar");
  mostrarAviso("");
}

async function cargarHistorial() {
  // Se completa en la Task 10.
}

function actualizarComparacion() {
  // Se completa en la Task 11.
}

function iniciar() {
  $("formulario").addEventListener("submit", alEnviar);
  $("boton-nuevo").addEventListener("click", nuevoAnalisis);
  $("boton-eliminar").addEventListener("click", () => estado.ensayo && eliminarEnsayo(estado.ensayo));
  $("archivo").addEventListener("change", (e) => elegirArchivo(e.target.files[0]));
  const zona = $("zona-carga");
  zona.addEventListener("dragover", (e) => { e.preventDefault(); if (!estado.ensayo) zona.classList.add("arrastrando"); });
  zona.addEventListener("dragleave", () => zona.classList.remove("arrastrando"));
  zona.addEventListener("drop", (e) => {
    e.preventDefault();
    zona.classList.remove("arrastrando");
    elegirArchivo(e.dataTransfer.files[0]);
  });
  cargarHistorial();
}

iniciar();
```

- [ ] **Step 4: Correr la suite**

Run: `.venv/Scripts/python -m pytest -v`
Expected: todo en verde, incluido `test_sirve_la_interfaz`.

- [ ] **Step 5: Verificar en el navegador integrado**

Levantar `sptero-web` con `preview_start` (usa `.claude/launch.json`). Con las herramientas `Claude_Browser`:
1. Cargar el `.raw` real por la API (el navegador integrado no puede elegir archivos locales):
   ```bash
   .venv/Scripts/python -c "import httpx,sys; r=httpx.post('http://localhost:8000/tests', files={'file': ('P3_304L_L.raw', open(sys.argv[1],'rb'))}, data={'material':'304L','thickness_mm':'0.5'}); print(r.status_code, r.json()['id'])" "C:/Users/julif/Documents/Maestría/Ensayos - SPT/A Julian Fierens/P3_304L_L.raw"
   ```
   y abrirlo desde la consola del navegador con `abrirEnsayo(<id>)` (la Task 10 agrega el botón "Abrir"). Expected: "Guardado · sin procesar" y la curva cruda.
2. Clic en **Recalcular** sin corrección. Expected: Pm 2.372,2 · dm 2,2709 · Rm 578,7 · Py 274,9 · σy 380,5; marcadores de Pm y Py sobre la curva; "Guardado · procesado".
3. Marcar la corrección y **Recalcular**. Expected: dm 1,7319 · Rm 758,8 · Py 281,8 · σy 390,1; la curva empieza en 0.
4. **Flujo de carga por la interfaz:** clic en **Nuevo análisis** (con un ensayo abierto, la zona de carga ignora archivos). Después, con `javascript_tool`, crear un `File` con un `.raw` sintético y disparar `drop` sobre `#zona-carga`:
   ```javascript
   const filas = Array.from({length: 120}, (_, i) => { const x = i * 0.02; const y = x <= 0.1 ? 3000 * x : 300 + 600 * (x - 0.1); return `${i * 0.5};-${x};-${y};0`; });
   const texto = ['"Test Type";"Manual"', '"Time sec";"Extension mm";"Load N";"Stress MPa"', ...filas].join("\r\n");
   const dt = new DataTransfer(); dt.items.add(new File([texto], "sintetico_ui.raw"));
   document.getElementById("zona-carga").dispatchEvent(new DragEvent("drop", { dataTransfer: dt, bubbles: true }));
   ```
   Expected: el chip muestra `sintetico_ui.raw`. Completar material "Prueba", espesor **"0,5" con coma** (Review Focus 5) y **Analizar ensayo**. Expected: se guarda y se procesa, "Guardado · procesado".
5. **Errores:** espesor "abc" → aviso "El espesor tiene que ser un número mayor que cero." y nada se envía (revisar con `read_network_requests`).
6. **Eliminar:** clic en **Eliminar ensayo** y cancelar → no pasa nada; repetir y aceptar → el formulario vuelve a "Nuevo análisis". (Para aceptar el `confirm` desde la automatización, reemplazarlo antes con `window.confirm = () => true` en `javascript_tool`, y anotar que así se probó.)
7. Plotly: probar zoom con arrastre, doble clic para restablecer ejes, y el hover con valores en mm y N.
8. Sacar una captura del estado final y revisar `read_console_messages` (sin errores).

- [ ] **Step 6: Commit**

```bash
git add static app/main.py tests/test_api.py .claude/launch.json
git commit -m "feat: agregar página de análisis con guardado automático"
```

### Task 10: Historial, reabrir y reprocesar

**Files:**
- Modify: `tp-final/static/app.js` (reemplaza `cargarHistorial` y agrega funciones auxiliares)

**Interfaces:**
- Consumes: `estado`, `pedir`, `formato`, `abrirEnsayo`, `eliminarEnsayo`, `mostrarAviso`, `actualizarComparacion` (Task 9).
- Produces: `cargarHistorial()` completo y `alternarSeleccion(id, casilla)`, que usa la Task 11.

- [ ] **Step 1: Reemplazar `cargarHistorial` en `app.js`**

Reemplazar la función vacía `cargarHistorial` por:
```javascript
function celda(contenido) {
  const td = document.createElement("td");
  if (contenido instanceof Node) td.append(contenido);
  else td.textContent = contenido;
  return td;
}

function boton(texto, clase, alHacerClic) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = clase;
  b.textContent = texto;
  b.addEventListener("click", alHacerClic);
  return b;
}

function alternarSeleccion(id, casilla) {
  if (casilla.checked) {
    if (estado.seleccion.length >= 2) {
      casilla.checked = false;
      $("ayuda-comparacion").textContent = "Solo se pueden comparar dos ensayos a la vez.";
      return;
    }
    estado.seleccion.push(id);
  } else {
    estado.seleccion = estado.seleccion.filter((otro) => otro !== id);
  }
  actualizarComparacion();
}

async function cargarHistorial() {
  let ensayos;
  try {
    ensayos = await pedir("GET", "/tests");
  } catch (error) {
    mostrarAviso(error.message);
    return;
  }
  estado.ensayos = ensayos;
  estado.seleccion = estado.seleccion.filter((id) => ensayos.some((e) => e.id === id));
  const cuerpo = $("filas-historial");
  cuerpo.replaceChildren();
  if (ensayos.length === 0) {
    const fila = document.createElement("tr");
    const vacia = celda("Todavía no hay ensayos guardados.");
    vacia.colSpan = 9;
    fila.append(vacia);
    cuerpo.append(fila);
  }
  for (const ensayo of ensayos) {
    const casilla = document.createElement("input");
    casilla.type = "checkbox";
    casilla.checked = estado.seleccion.includes(ensayo.id);
    casilla.setAttribute("aria-label", `Comparar ${ensayo.filename}`);
    casilla.addEventListener("change", () => alternarSeleccion(ensayo.id, casilla));

    const nombre = document.createElement("b");
    nombre.textContent = ensayo.filename;
    const insignia = document.createElement("span");
    insignia.className = ensayo.result ? "status" : "status pendiente";
    insignia.textContent = ensayo.result ? "Procesado" : "Sin procesar";
    const acciones = document.createElement("span");
    acciones.append(
      boton("Abrir", "boton-fila", () => { abrirEnsayo(ensayo.id); $("analisis").scrollIntoView({ behavior: "smooth" }); }),
      boton("Eliminar", "boton-fila danger", () => eliminarEnsayo(ensayo)),
    );

    const fila = document.createElement("tr");
    fila.append(
      celda(casilla),
      celda(nombre),
      celda(ensayo.material),
      celda(formato(ensayo.thickness_mm, 3)),
      celda(ensayo.result ? `${formato(ensayo.result.pm_n, 0)} N` : "—"),
      celda(ensayo.result ? `${formato(ensayo.result.rm_mpa, 0)} MPa` : "—"),
      celda(new Date(ensayo.uploaded_at).toLocaleDateString("es-AR")),
      celda(insignia),
      celda(acciones),
    );
    cuerpo.append(fila);
  }
  actualizarComparacion();
}
```

- [ ] **Step 2: Verificar en el navegador integrado**

Recargar la página (servidor de la Task 9).
1. El historial muestra los ensayos del más reciente al más antiguo, con Pm/Rm y su estado.
2. **Abrir** sobre `P3_304L_L.raw` → el panel carga material (solo lectura), t, β, C_P y la casilla de corrección con los valores guardados; el botón dice "Recalcular".
3. **Corrección de espesor (D2):** cambiar t a 0,48 y **Recalcular**. Expected: con β = 0,277 y sin corrección, Rm = 0,277·2372,2/(2,2709·0,48) ≈ 602,8 MPa, y la fila del historial se actualiza. Volver a 0,5 → Rm 578,7.
4. **Reprocesar sin versiones:** cambiar β a 0,3 y **Recalcular** → el historial sigue mostrando un solo `P3_304L_L.raw`, ahora con Rm ≈ 626,8 (0,3·2372,2/(2,2709·0,5)).
5. **Nombre con HTML:** subir por la API un archivo `<img src=x onerror=alert(1)>.raw` con el contenido del `.raw` sintético. Expected: el historial muestra el texto literal y no ejecuta nada (sin diálogo de alerta y sin errores en la consola).
6. **Eliminar desde la fila:** cancelar no borra; aceptar lo saca del historial.

- [ ] **Step 3: Commit**

```bash
git add static/app.js
git commit -m "feat: agregar historial con reapertura y reprocesamiento"
```

### Task 11: Comparación de dos curvas (D3)

**Files:**
- Modify: `tp-final/static/app.js` (reemplaza `actualizarComparacion` y agrega `comparar`)

**Interfaces:**
- Consumes: `estado.seleccion`, `estado.ensayos` (Task 10), `pedir`, `graficar`, `COLORES` (Task 9).

- [ ] **Step 1: Reemplazar `actualizarComparacion` y agregar `comparar`**

Reemplazar la función vacía `actualizarComparacion` por:
```javascript
function ensayosSeleccionados() {
  return estado.seleccion.map((id) => estado.ensayos.find((e) => e.id === id)).filter(Boolean);
}

function actualizarComparacion() {
  const seleccionados = ensayosSeleccionados();
  const opcionProcesadas = $("tipo-curva").querySelector('option[value="processed"]');
  const todosProcesados = seleccionados.length === 2 && seleccionados.every((e) => e.result);
  opcionProcesadas.disabled = !todosProcesados;
  if (!todosProcesados && $("tipo-curva").value === "processed") $("tipo-curva").value = "raw";
  $("boton-comparar").disabled = seleccionados.length !== 2;

  const ayuda = $("ayuda-comparacion");
  if (seleccionados.length < 2) {
    ayuda.textContent = `Marcá dos ensayos en el historial (${seleccionados.length} de 2).`;
  } else if (!todosProcesados) {
    ayuda.textContent = "Curvas procesadas no disponible: algún ensayo todavía no se procesó.";
  } else {
    ayuda.textContent = "Elegí el tipo de curva y compará.";
  }
}

async function comparar() {
  const seleccionados = ensayosSeleccionados();
  if (seleccionados.length !== 2) return;
  const fuente = $("tipo-curva").value;
  const tipo = fuente === "processed" ? "procesada" : "cruda";
  try {
    const curvas = await Promise.all(seleccionados.map((e) => pedir("GET", `/tests/${e.id}/curve?source=${fuente}`)));
    const trazas = curvas.map((curva, i) => ({
      x: curva.displacement_mm,
      y: curva.load_n,
      mode: "lines",
      name: `${seleccionados[i].filename} · ${seleccionados[i].material} · ${tipo}`,
      line: { color: COLORES[i], width: 2 },
      hovertemplate: "%{x:.4f} mm<br>%{y:.1f} N<extra>%{fullData.name}</extra>",
    }));
    graficar("grafico-comparacion", trazas);
  } catch (error) {
    $("ayuda-comparacion").textContent = error.message;
  }
}
```
y en `iniciar()` agregar:
```javascript
  $("boton-comparar").addEventListener("click", comparar);
  $("tipo-curva").addEventListener("change", actualizarComparacion);
```

- [ ] **Step 2: Verificar en el navegador integrado**

1. Con un solo ensayo marcado: "Comparar" deshabilitado y la ayuda dice "(1 de 2)". No deja marcar un tercero.
2. Marcar `P3_304L_L.raw` (procesado) y uno sin procesar: "Curvas procesadas" aparece deshabilitada con el motivo. **Comparar** muestra dos curvas crudas, de colores distintos, con leyenda "archivo · material · cruda".
3. Procesar el segundo y comparar con "Curvas procesadas": las dos curvas empiezan donde corresponde a su preprocesado y la leyenda dice "procesada".
4. Comparar no modifica nada: `GET /tests` antes y después da lo mismo (con `read_network_requests`: solo hay `GET`).
5. Eliminar uno de los dos marcados: sale de la selección y "Comparar" se deshabilita.

- [ ] **Step 3: Commit**

```bash
git add static/app.js
git commit -m "feat: agregar comparación de dos curvas del mismo tipo"
```

### Task 12: Verificación de punta a punta y cierre de la etapa

**Files:**
- Ninguno nuevo (la evidencia va al PR y al README en la Task 13).

- [ ] **Step 1: Recorrido completo con base limpia**

Con `SPTERO_DB` apuntando a un archivo nuevo en `data/` (por ejemplo `data/verificacion.db`), levantar el servidor y repetir en orden: cargar `P3_304L_L.raw`, procesar sin corrección, procesar con corrección, corregir t a 0,48 y volver a 0,5, cargar un segundo ensayo, comparar crudas y procesadas, eliminar con confirmación. Comprobar que cada valor coincide con la tabla de la spec, sección 4.

- [ ] **Step 2: Capturas**

Guardar capturas de: análisis procesado con marcadores, historial y comparación. Van a `docs/capturas/` (`analisis.png`, `historial.png`, `comparacion.png`) para el README, sin datos sensibles.

- [ ] **Step 3: Suite y review**

Run: `.venv/Scripts/python -m pytest -v` (y con las variables de caracterización). Después, `superpowers:requesting-code-review` sobre la rama; corregir lo que corresponda.

- [ ] **Step 4: Commit**

```bash
git add docs/capturas
git commit -m "docs: agregar capturas de la verificación de la interfaz"
```
Fin de la etapa 4: Julián abre el PR `feature/tp-final-ui` → `main`.

---

# Etapa 5 — Cierre (`feature/tp-final-cierre`)

### Task 13: Informe y verificación final

**Files:**
- Modify: `tp-final/README.md`, `tp-final/prompts.md`, `README.md` (raíz: quitar "en curso"), `CLAUDE.md` (raíz: estado del TP final)

- [ ] **Step 1: Verificación final con evidencia**

`superpowers:verification-before-completion`: correr
```bash
.venv/Scripts/python -m pytest -v
```
sin y con `SPTERO_ORIGINAL`/`SPTERO_RAW_SAMPLE`, y pegar las dos salidas reales (resumen de pasados y salteados) en el README, sección "Validación".

- [ ] **Step 2: Completar el README-informe**

Secciones, con este contenido:
- **Cómo se ejecuta:** venv, `pip install -r requirements.txt`, `uvicorn app.main:app`, abrir `http://localhost:8000`; variables `SPTERO_DB`, `SPTERO_ORIGINAL`, `SPTERO_RAW_SAMPLE`; que Plotly necesita internet.
- **Qué me propuse construir:** objetivo y alcance de la spec, sección 1–2.
- **Arquitectura:** árbol de `tp-final/`, tabla de los 9 endpoints con status codes, esquema de datos, contrato UI ↔ servidor (qué llamadas hace cada acción de la interfaz) y la regla de dependencias core ← service ← rutas.
- **Fragmentos clave de código:** `analizar` (pipeline D1), `corregir_espesor` + `actualizar_espesor` (atomicidad del PATCH), el handler 400 de validación.
- **Decisiones que tomé yo:** las nueve ya escritas, más `py_t10_displacement_mm` si se aprobó.
- **Cómo gestioné el contexto:** spec y plan en disco; `CLAUDE.md` + rules por carpeta; sesiones desde `tp-final/` (y la prueba de carga de la etapa 0); el subagente `verificador-cientifico` aislando la lectura del original; un commit por tarea; plan mode al inicio; el navegador integrado como MCP.
- **Qué salió mal y cómo lo corregí:** cada desvío registrado en `prompts.md` (por ejemplo, las reglas `Write(...)` que no se aplicaban, la ruta de la skill, el `-I` que ignoraba `PYTHONIOENCODING`, la diferencia t/10 sin MAO, el campo de desplazamiento de Py que faltaba en la spec) y los que aparezcan al ejecutar este plan.
- **Validación:** salidas de pytest, tabla de valores de referencia contra la web y capturas.
- **Prompts:** enlace a `prompts.md` y los prompts clave.

- [ ] **Step 3: Índices de la raíz**

`README.md` raíz: quitar "(en curso)" de la entrada del TP final. `CLAUDE.md` raíz: estado del TP final → "Entregado".

- [ ] **Step 4: Commit y cierre**

```bash
git add README.md prompts.md ../README.md ../CLAUDE.md
git commit -m "docs: completar el informe del tp final"
```
`superpowers:finishing-a-development-branch`: Julián abre el PR final.
