from pathlib import Path

import yaml

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


from app.main import crear_app

SCHEMAS_COMPARTIDOS = ["Test", "TestUpdate", "ProcessingRequest", "ProcessingParameters", "Result", "Curve"]


def test_la_app_implementa_las_operaciones_del_contrato():
    assert operaciones(crear_app(":memory:").openapi()) == operaciones(cargar_contrato())


def test_los_campos_de_la_app_coinciden_con_el_contrato():
    app_schemas = crear_app(":memory:").openapi()["components"]["schemas"]
    contrato_schemas = cargar_contrato()["components"]["schemas"]
    for nombre in SCHEMAS_COMPARTIDOS:
        assert set(app_schemas[nombre]["properties"]) == set(contrato_schemas[nombre]["properties"]), nombre
