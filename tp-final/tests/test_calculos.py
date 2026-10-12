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
