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
