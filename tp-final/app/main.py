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
from fastapi.responses import JSONResponse

from app import repository, service
from app.schemas import Curve, ProcessingRequest, Result, Test, TestUpdate
from sptero_core.analisis import ParametrosProcesamiento

RAIZ = Path(__file__).resolve().parent.parent
RUTA_DB_POR_DEFECTO = RAIZ / "data" / "sptero.db"


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
    TestId = Annotated[int, PathParam(ge=1, description="Identificador del ensayo")]

    @app.exception_handler(service.ErrorApi)
    def error_api(_request, error: service.ErrorApi):
        return JSONResponse(status_code=error.status, content={"code": error.code, "message": error.message})

    @app.exception_handler(RequestValidationError)
    def error_validacion(_request, error: RequestValidationError):
        detalle = "; ".join(f"{'.'.join(str(p) for p in e['loc'][1:])}: {e['msg']}" for e in error.errors())
        return JSONResponse(status_code=400, content={"code": "INVALID_PARAMETERS", "message": f"Parámetros inválidos: {detalle}"})

    @app.get("/tests", response_model=list[Test], tags=["Ensayos"])
    def listar(con: Conexion):
        return service.listar(con)

    @app.post("/tests", status_code=201, response_model=Test, tags=["Ensayos"])
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

    @app.get("/tests/{testId}", response_model=Test, tags=["Ensayos"])
    def obtener(con: Conexion, testId: TestId):
        return service.obtener(con, testId)

    @app.patch("/tests/{testId}", response_model=Test, tags=["Ensayos"])
    def corregir_espesor(con: Conexion, testId: TestId, cuerpo: TestUpdate):
        return service.corregir_espesor(con, testId, cuerpo.thickness_mm)

    @app.delete("/tests/{testId}", status_code=204, tags=["Ensayos"])
    def borrar(con: Conexion, testId: TestId):
        service.borrar(con, testId)
        return Response(status_code=204)

    @app.get("/tests/{testId}/file", tags=["Ensayos"], response_class=Response)
    def archivo(con: Conexion, testId: TestId):
        nombre, contenido = service.archivo(con, testId)
        return Response(
            content=contenido,
            media_type="application/octet-stream",
            headers={"Content-Disposition": _content_disposition(nombre)},
        )

    @app.get("/tests/{testId}/curve", response_model=Curve, tags=["Ensayos"])
    def curva(con: Conexion, testId: TestId, source: Literal["raw", "processed"] = "raw"):
        return service.curva(con, testId, source)

    @app.get("/tests/{testId}/result", response_model=Result, tags=["Resultados"])
    def resultado(con: Conexion, testId: TestId):
        return service.resultado(con, testId)

    @app.put("/tests/{testId}/result", response_model=Result, tags=["Resultados"])
    def procesar(con: Conexion, testId: TestId, cuerpo: Annotated[ProcessingRequest | None, Body()] = None):
        cuerpo = cuerpo or ProcessingRequest()
        parametros = ParametrosProcesamiento(
            aplicar_correccion=cuerpo.apply_compliance_correction,
            cp_mm_por_n=cuerpo.compliance_mm_per_n,
            beta=cuerpo.beta,
        )
        return service.procesar(con, testId, parametros)

    return app


app = crear_app()
