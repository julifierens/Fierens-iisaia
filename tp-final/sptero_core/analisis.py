"""Pipeline de análisis: reemplaza al main() interactivo del script original.

Sigue la secuencia de main() (Programa SPTERO.py, líneas 979–1058 y 1203–1209):
leer → invertir signo/ordenar → [con corrección: v = vref − F·C_P → reordenar →
cero por precarga con F0 = 5 N] → Pm/dm → Rm → t/10.

Valores por defecto:
- C_P = 2,281e-4 mm/N, β = 0,277 y F0 = 5 N (sin desplazar F) son los que el
  original ofrece al apretar Enter.
- aplicar_correccion = False NO coincide con el original: en la consola, Enter
  aplica la corrección (pregunta de la línea 988, default "s"). Se mantiene False
  porque es el default del contrato heredado del TP2 (ProcessingRequest).
  Con el mismo .raw, los valores por defecto de la web dan el caso sin corrección
  y Enter en la consola da el caso con corrección.

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
