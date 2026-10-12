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

from sptero_core import calculos, preproceso, raw
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
    raw: ["encontrar_inicio_tabla"],
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
