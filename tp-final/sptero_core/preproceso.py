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
