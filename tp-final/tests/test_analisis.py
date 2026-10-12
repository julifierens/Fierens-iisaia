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
