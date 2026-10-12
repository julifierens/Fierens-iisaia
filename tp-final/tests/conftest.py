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
