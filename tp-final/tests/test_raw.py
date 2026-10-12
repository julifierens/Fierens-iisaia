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
