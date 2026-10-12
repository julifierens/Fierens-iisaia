"""Rutas de la API de SPTERO Web (contrato openapi.yaml v1.1).

Las rutas no calculan ni escriben SQL: validan la entrada y delegan en service.
"""
import os
import sqlite3
from urllib.parse import quote
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Body, Depends, FastAPI, File, Form, Path as PathParam, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import repository, service
from app.schemas import Curve, Error, ProcessingRequest, Result, Test, TestUpdate
from sptero_core.analisis import ParametrosProcesamiento

RAIZ = Path(__file__).resolve().parent.parent
RUTA_DB_POR_DEFECTO = RAIZ / "data" / "sptero.db"
CARPETA_STATIC = RAIZ / "static"
# El contrato declara el id como int64; SQLite no acepta enteros mayores.
MAX_ID = 2**63 - 1

NO_ENCONTRADO = {404: {"model": Error, "description": "El ensayo no existe (TEST_NOT_FOUND)"}}
PARAMETROS_INVALIDOS = {400: {"model": Error, "description": "Parámetros inválidos (INVALID_PARAMETERS)"}}
NO_PROCESABLE = {422: {"model": Error, "description": "No se pudo calcular el resultado (PROCESSING_FAILED)"}}


# Mensajes de validación en español, por tipo de error de Pydantic.
MENSAJES_VALIDACION = {
    "missing": lambda ctx: "es obligatorio",
    "greater_than": lambda ctx: f"debe ser mayor que {ctx.get('gt'):g}",
    "less_than_equal": lambda ctx: f"debe ser menor o igual que {ctx.get('le'):g}",
    "float_parsing": lambda ctx: "debe ser un número",
    "float_type": lambda ctx: "debe ser un número",
    "finite_number": lambda ctx: "debe ser un número finito",
    "int_parsing": lambda ctx: "debe ser un entero",
    "int_type": lambda ctx: "debe ser un entero",
    "literal_error": lambda ctx: f"debe ser uno de: {ctx.get('expected')}",
    "string_too_short": lambda ctx: f"debe tener al menos {ctx.get('min_length')} caracteres",
    "string_too_long": lambda ctx: f"debe tener como máximo {ctx.get('max_length')} caracteres",
    "bool_parsing": lambda ctx: "debe ser verdadero o falso",
    "bool_type": lambda ctx: "debe ser verdadero o falso",
    "json_invalid": lambda ctx: "JSON mal formado",
    "model_attributes_type": lambda ctx: "debe ser un objeto JSON",
    "dict_type": lambda ctx: "debe ser un objeto JSON",
}


def _mensaje_validacion(e: dict) -> str:
    # En un JSON roto Pydantic pone la posición del error en la ubicación: no sirve al usuario.
    ubicacion = "" if e["type"] == "json_invalid" else ".".join(str(p) for p in e["loc"][1:])
    texto = MENSAJES_VALIDACION.get(e["type"], lambda ctx: "valor inválido")(e.get("ctx") or {})
    return f"{ubicacion or 'el cuerpo'}: {texto}"


def _content_disposition(nombre: str) -> str:
    """Cabecera de descarga; los nombres no ASCII van codificados (RFC 6266), como en FileResponse."""
    citado = quote(nombre)
    if citado != nombre:
        return f"attachment; filename*=utf-8''{citado}"
    return f'attachment; filename="{nombre}"'


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
    TestId = Annotated[int, PathParam(ge=1, le=MAX_ID, description="Identificador del ensayo")]

    @app.exception_handler(service.ErrorApi)
    def error_api(_request, error: service.ErrorApi):
        return JSONResponse(status_code=error.status, content={"code": error.code, "message": error.message})

    @app.exception_handler(RequestValidationError)
    def error_validacion(_request, error: RequestValidationError):
        detalle = "; ".join(_mensaje_validacion(e) for e in error.errors())
        return JSONResponse(status_code=400, content={"code": "INVALID_PARAMETERS", "message": f"Parámetros inválidos: {detalle}"})

    @app.get("/tests", response_model=list[Test], tags=["Ensayos"])
    def listar(con: Conexion):
        return service.listar(con)

    @app.post(
        "/tests", status_code=201, response_model=Test, tags=["Ensayos"],
        responses={400: {"model": Error, "description": "Parámetros inválidos o archivo inválido (INVALID_PARAMETERS, INVALID_FILE)"}},
    )
    def subir(
        con: Conexion,
        response: Response,
        file: Annotated[UploadFile, File()],
        material: Annotated[str, Form(min_length=1, max_length=50)],
        thickness_mm: Annotated[float, Form(gt=0, allow_inf_nan=False)],
    ):
        ensayo = service.subir(con, file.filename or "ensayo.raw", file.file.read(), material, thickness_mm)
        response.headers["Location"] = f"/tests/{ensayo['id']}"
        return ensayo

    @app.get("/tests/{testId}", response_model=Test, tags=["Ensayos"], responses=NO_ENCONTRADO)
    def obtener(con: Conexion, testId: TestId):
        return service.obtener(con, testId)

    @app.patch("/tests/{testId}", response_model=Test, tags=["Ensayos"], responses=NO_ENCONTRADO | PARAMETROS_INVALIDOS | NO_PROCESABLE)
    def corregir_espesor(con: Conexion, testId: TestId, cuerpo: TestUpdate):
        return service.corregir_espesor(con, testId, cuerpo.thickness_mm)

    @app.delete("/tests/{testId}", status_code=204, tags=["Ensayos"], responses=NO_ENCONTRADO)
    def borrar(con: Conexion, testId: TestId):
        service.borrar(con, testId)
        return Response(status_code=204)

    @app.get("/tests/{testId}/file", tags=["Ensayos"], response_class=Response, responses=NO_ENCONTRADO)
    def archivo(con: Conexion, testId: TestId):
        nombre, contenido = service.archivo(con, testId)
        return Response(
            content=contenido,
            media_type="application/octet-stream",
            headers={"Content-Disposition": _content_disposition(nombre)},
        )

    @app.get(
        "/tests/{testId}/curve", response_model=Curve, tags=["Ensayos"],
        responses=NO_ENCONTRADO | PARAMETROS_INVALIDOS,
    )
    def curva(con: Conexion, testId: TestId, source: Literal["raw", "processed"] = "raw"):
        return service.curva(con, testId, source)

    @app.get("/tests/{testId}/result", response_model=Result, tags=["Resultados"], responses=NO_ENCONTRADO)
    def resultado(con: Conexion, testId: TestId):
        return service.resultado(con, testId)

    @app.put(
        "/tests/{testId}/result", response_model=Result, tags=["Resultados"],
        responses=NO_ENCONTRADO | PARAMETROS_INVALIDOS | NO_PROCESABLE,
    )
    def procesar(con: Conexion, testId: TestId, cuerpo: Annotated[ProcessingRequest | None, Body()] = None):
        cuerpo = cuerpo or ProcessingRequest()
        parametros = ParametrosProcesamiento(
            aplicar_correccion=cuerpo.apply_compliance_correction,
            cp_mm_por_n=cuerpo.compliance_mm_per_n,
            beta=cuerpo.beta,
        )
        return service.procesar(con, testId, parametros)

    @app.get("/", include_in_schema=False)
    def inicio():
        return FileResponse(CARPETA_STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=CARPETA_STATIC), name="static")

    return app


app = crear_app()
