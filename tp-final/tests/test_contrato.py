from pathlib import Path

import yaml

from app.main import crear_app

CONTRATO = Path(__file__).resolve().parent.parent / "openapi.yaml"

OPERACIONES_ESPERADAS = {
    ("/tests", "get"), ("/tests", "post"),
    ("/tests/{testId}", "get"), ("/tests/{testId}", "patch"), ("/tests/{testId}", "delete"),
    ("/tests/{testId}/file", "get"),
    ("/tests/{testId}/curve", "get"),
    ("/tests/{testId}/result", "get"), ("/tests/{testId}/result", "put"),
}
METODOS_HTTP = {"get", "post", "put", "patch", "delete"}


def cargar_contrato():
    return yaml.safe_load(CONTRATO.read_text(encoding="utf-8"))


def operaciones(contrato):
    return {
        (ruta, metodo)
        for ruta, item in contrato["paths"].items()
        for metodo in item
        if metodo in METODOS_HTTP
    }


def test_version_1_1():
    assert cargar_contrato()["info"]["version"] == "1.1.0"


def test_operaciones_del_contrato():
    assert operaciones(cargar_contrato()) == OPERACIONES_ESPERADAS


def test_result_incluye_t10():
    result = cargar_contrato()["components"]["schemas"]["Result"]
    for campo in ("py_t10_n", "py_t10_displacement_mm", "sigma_y_t10_mpa"):
        assert campo in result["properties"]
        assert campo in result["required"]
        assert result["properties"][campo]["type"] == ["number", "null"]


def test_test_update_solo_espesor():
    test_update = cargar_contrato()["components"]["schemas"]["TestUpdate"]
    assert test_update["required"] == ["thickness_mm"]
    assert set(test_update["properties"]) == {"thickness_mm"}


SCHEMAS_COMPARTIDOS = ["Test", "TestUpdate", "ProcessingRequest", "ProcessingParameters", "Result", "Curve", "Error"]


def test_la_app_implementa_las_operaciones_del_contrato():
    assert operaciones(crear_app(":memory:").openapi()) == operaciones(cargar_contrato())


def test_los_campos_de_la_app_coinciden_con_el_contrato():
    app_schemas = crear_app(":memory:").openapi()["components"]["schemas"]
    contrato_schemas = cargar_contrato()["components"]["schemas"]
    for nombre in SCHEMAS_COMPARTIDOS:
        assert set(app_schemas[nombre]["properties"]) == set(contrato_schemas[nombre]["properties"]), nombre


def test_los_campos_requeridos_coinciden_con_el_contrato():
    app_schemas = crear_app(":memory:").openapi()["components"]["schemas"]
    contrato_schemas = cargar_contrato()["components"]["schemas"]
    for nombre in SCHEMAS_COMPARTIDOS:
        de_la_app = set(app_schemas[nombre].get("required", []))
        del_contrato = set(contrato_schemas[nombre].get("required", []))
        assert de_la_app == del_contrato, f"required de {nombre}"


def codigos_por_operacion(spec, es_app=False):
    """{(ruta, metodo): {codigos de respuesta}}. En la app se ignora el 422 automatico de FastAPI."""
    resultado = {}
    for ruta, item in spec["paths"].items():
        for metodo, operacion in item.items():
            if metodo not in METODOS_HTTP:
                continue
            codigos = set()
            for codigo, respuesta in operacion["responses"].items():
                esquema = respuesta.get("content", {}).get("application/json", {}).get("schema", {})
                if es_app and codigo == "422" and esquema.get("$ref", "").endswith("/HTTPValidationError"):
                    continue
                codigos.add(codigo)
            resultado[(ruta, metodo)] = codigos
    return resultado


def test_las_respuestas_de_cada_operacion_coinciden_con_el_contrato():
    de_la_app = codigos_por_operacion(crear_app(":memory:").openapi(), es_app=True)
    del_contrato = codigos_por_operacion(cargar_contrato())
    for operacion, codigos in del_contrato.items():
        assert de_la_app[operacion] == codigos, f"codigos de respuesta de {operacion}"
