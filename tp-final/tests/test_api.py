import pytest
from fastapi.testclient import TestClient

from app import service
from app.main import crear_app


@pytest.fixture
def cliente(tmp_path):
    return TestClient(crear_app(str(tmp_path / "prueba.db")))


@pytest.fixture
def subir(cliente, raw_sintetico):
    def _subir(contenido=None, material="304L", thickness_mm="0.5", nombre="sintetico.raw"):
        return cliente.post(
            "/tests",
            files={"file": (nombre, raw_sintetico if contenido is None else contenido, "application/octet-stream")},
            data={"material": material, "thickness_mm": thickness_mm},
        )
    return _subir


def _codigo(respuesta):
    return respuesta.status_code, respuesta.json()["code"]


def test_post_crea_ensayo(subir):
    r = subir()
    assert r.status_code == 201
    cuerpo = r.json()
    assert r.headers["location"] == f"/tests/{cuerpo['id']}"
    assert cuerpo["point_count"] == 601
    assert cuerpo["result"] is None


@pytest.mark.parametrize("contenido", [b"", b"no es un raw", b"%PDF-1.4\n\x00\xff\xfe binario"])
def test_post_archivo_que_no_es_raw(subir, contenido):
    assert _codigo(subir(contenido=contenido)) == (400, "INVALID_FILE")


@pytest.mark.parametrize("cambios", [{"thickness_mm": "0"}, {"thickness_mm": "abc"}, {"material": ""}])
def test_post_parametros_invalidos(subir, cambios):
    assert _codigo(subir(**cambios)) == (400, "INVALID_PARAMETERS")


def test_post_sin_archivo(cliente):
    r = cliente.post("/tests", data={"material": "304L", "thickness_mm": "0.5"})
    assert _codigo(r) == (400, "INVALID_PARAMETERS")


def test_listado_mas_reciente_primero(cliente, subir):
    primero = subir().json()["id"]
    segundo = subir().json()["id"]
    assert [e["id"] for e in cliente.get("/tests").json()] == [segundo, primero]


def test_get_inexistente_y_id_invalido(cliente):
    assert _codigo(cliente.get("/tests/99")) == (404, "TEST_NOT_FOUND")
    assert _codigo(cliente.get("/tests/0")) == (400, "INVALID_PARAMETERS")


def test_put_procesa(cliente, subir):
    test_id = subir().json()["id"]
    r = cliente.put(f"/tests/{test_id}/result")
    assert r.status_code == 200
    resultado = r.json()
    assert resultado["pm_n"] == pytest.approx(1440.0)
    assert resultado["dm_mm"] == pytest.approx(2.0)
    assert resultado["rm_mpa"] == pytest.approx(398.88)
    assert resultado["py_t10_n"] == pytest.approx(337.5)
    assert resultado["py_t10_displacement_mm"] == pytest.approx(0.1625)
    assert resultado["sigma_y_t10_mpa"] == pytest.approx(467.1)
    assert cliente.get(f"/tests/{test_id}").json()["result"] == resultado


def test_put_idempotente(cliente, subir):
    test_id = subir().json()["id"]
    primero = cliente.put(f"/tests/{test_id}/result", json={"beta": 0.277}).json()
    segundo = cliente.put(f"/tests/{test_id}/result", json={}).json()
    assert segundo == primero
    tercero = cliente.put(f"/tests/{test_id}/result", json={"beta": 0.3}).json()
    assert tercero["rm_mpa"] == pytest.approx(0.3 * 1440 / (2.0 * 0.5))


@pytest.mark.parametrize("cuerpo", [{"beta": 0}, {"compliance_mm_per_n": -1}, {"apply_compliance_correction": "quizás"}])
def test_put_parametros_invalidos(cliente, subir, cuerpo):
    test_id = subir().json()["id"]
    assert _codigo(cliente.put(f"/tests/{test_id}/result", json=cuerpo)) == (400, "INVALID_PARAMETERS")


def test_put_inexistente(cliente):
    assert _codigo(cliente.put("/tests/99/result")) == (404, "TEST_NOT_FOUND")


def test_put_422_y_queda_sin_resultado(cliente, subir, construir_raw, curva_decreciente):
    test_id = subir(contenido=construir_raw(*curva_decreciente)).json()["id"]
    assert _codigo(cliente.put(f"/tests/{test_id}/result")) == (422, "PROCESSING_FAILED")
    assert _codigo(cliente.get(f"/tests/{test_id}/result")) == (404, "RESULT_NOT_FOUND")


def test_curvas(cliente, subir):
    test_id = subir().json()["id"]
    cruda = cliente.get(f"/tests/{test_id}/curve").json()
    assert cruda["source"] == "raw" and len(cruda["displacement_mm"]) == 601
    assert _codigo(cliente.get(f"/tests/{test_id}/curve?source=processed")) == (404, "RESULT_NOT_FOUND")
    assert _codigo(cliente.get(f"/tests/{test_id}/curve?source=otra")) == (400, "INVALID_PARAMETERS")
    cliente.put(f"/tests/{test_id}/result", json={"apply_compliance_correction": True})
    procesada = cliente.get(f"/tests/{test_id}/curve?source=processed").json()
    assert len(procesada["displacement_mm"]) == 600
    assert procesada["displacement_mm"][0] == 0.0


def test_archivo_original(cliente, subir, raw_sintetico):
    test_id = subir(nombre="P_prueba.raw").json()["id"]
    r = cliente.get(f"/tests/{test_id}/file")
    assert r.status_code == 200
    assert r.content == raw_sintetico
    assert r.headers["content-disposition"] == 'attachment; filename="P_prueba.raw"'


def test_delete(cliente, subir):
    test_id = subir().json()["id"]
    assert cliente.delete(f"/tests/{test_id}").status_code == 204
    assert _codigo(cliente.get(f"/tests/{test_id}")) == (404, "TEST_NOT_FOUND")
    assert _codigo(cliente.delete(f"/tests/{test_id}")) == (404, "TEST_NOT_FOUND")


def test_patch_recalcula(cliente, subir):
    test_id = subir().json()["id"]
    cliente.put(f"/tests/{test_id}/result")
    r = cliente.patch(f"/tests/{test_id}", json={"thickness_mm": 0.25})
    assert r.status_code == 200
    assert r.json()["thickness_mm"] == 0.25
    assert r.json()["result"]["rm_mpa"] == pytest.approx(797.76)


def test_patch_mismo_espesor_no_cambia(cliente, subir):
    test_id = subir().json()["id"]
    cliente.put(f"/tests/{test_id}/result")
    antes = cliente.get(f"/tests/{test_id}").json()
    assert cliente.patch(f"/tests/{test_id}", json={"thickness_mm": 0.5}).json() == antes


@pytest.mark.parametrize("cuerpo", [{"thickness_mm": 0}, {"thickness_mm": "abc"}, {}])
def test_patch_invalido(cliente, subir, cuerpo):
    test_id = subir().json()["id"]
    assert _codigo(cliente.patch(f"/tests/{test_id}", json=cuerpo)) == (400, "INVALID_PARAMETERS")


def test_patch_inexistente(cliente):
    assert _codigo(cliente.patch("/tests/99", json={"thickness_mm": 0.4})) == (404, "TEST_NOT_FOUND")


def test_patch_si_falla_el_recalculo_no_cambia_nada(cliente, subir, monkeypatch):
    test_id = subir().json()["id"]
    cliente.put(f"/tests/{test_id}/result")
    antes = cliente.get(f"/tests/{test_id}").json()

    def falla(*args, **kwargs):
        raise ValueError("falla simulada del recálculo")

    monkeypatch.setattr(service, "analizar", falla)
    assert _codigo(cliente.patch(f"/tests/{test_id}", json={"thickness_mm": 0.25})) == (422, "PROCESSING_FAILED")
    assert cliente.get(f"/tests/{test_id}").json() == antes


def test_post_espesor_no_finito(subir):
    assert _codigo(subir(thickness_mm="inf")) == (400, "INVALID_PARAMETERS")


def test_patch_espesor_infinito(cliente, subir):
    test_id = subir().json()["id"]
    r = cliente.patch(f"/tests/{test_id}", content=b'{"thickness_mm": Infinity}', headers={"content-type": "application/json"})
    assert _codigo(r) == (400, "INVALID_PARAMETERS")


def test_put_beta_infinito(cliente, subir):
    test_id = subir().json()["id"]
    r = cliente.put(f"/tests/{test_id}/result", content=b'{"beta": Infinity}', headers={"content-type": "application/json"})
    assert _codigo(r) == (400, "INVALID_PARAMETERS")


def test_archivo_con_nombre_no_ascii(cliente, subir, raw_sintetico):
    test_id = subir(nombre="ensayo_€ñ.raw").json()["id"]
    r = cliente.get(f"/tests/{test_id}/file")
    assert r.status_code == 200
    assert r.content == raw_sintetico
    assert r.headers["content-disposition"] == "attachment; filename*=utf-8''ensayo_%E2%82%AC%C3%B1.raw"
