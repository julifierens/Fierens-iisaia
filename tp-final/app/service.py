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
