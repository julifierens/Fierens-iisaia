import pytest

from app import repository, service
from sptero_core.analisis import ParametrosProcesamiento


@pytest.fixture
def con(tmp_path):
    conexion = repository.conectar(str(tmp_path / "prueba.db"))
    yield conexion
    conexion.close()


@pytest.fixture
def ensayo(con, raw_sintetico):
    return service.subir(con, "sintetico.raw", raw_sintetico, "304L", 0.5)


def _error(excinfo):
    return excinfo.value.status, excinfo.value.code


def test_subir_guarda_y_cuenta_puntos(ensayo):
    assert ensayo["point_count"] == 601
    assert ensayo["result"] is None


def test_subir_archivo_invalido(con):
    with pytest.raises(service.ErrorApi) as excinfo:
        service.subir(con, "x.raw", b"no es un raw", "304L", 0.5)
    assert _error(excinfo) == (400, "INVALID_FILE")


def test_procesar_y_resultado(con, ensayo):
    resultado = service.procesar(con, ensayo["id"], ParametrosProcesamiento())
    assert resultado["rm_mpa"] == pytest.approx(398.88)
    assert resultado["parameters"] == {"apply_compliance_correction": False, "compliance_mm_per_n": None, "beta": 0.277}
    assert service.resultado(con, ensayo["id"]) == resultado


def test_procesar_idempotente_no_toca_processed_at(con, ensayo, monkeypatch):
    primero = service.procesar(con, ensayo["id"], ParametrosProcesamiento())
    monkeypatch.setattr(service, "_ahora", lambda: "2099-01-01T00:00:00+00:00")
    segundo = service.procesar(con, ensayo["id"], ParametrosProcesamiento())
    assert segundo["processed_at"] == primero["processed_at"]


def test_procesar_guarda_cp_solo_si_se_aplica(con, ensayo):
    resultado = service.procesar(con, ensayo["id"], ParametrosProcesamiento(aplicar_correccion=True))
    assert resultado["parameters"]["compliance_mm_per_n"] == 2.281e-4


def test_procesar_falla_422(con, construir_raw, curva_decreciente):
    test_id = service.subir(con, "d.raw", construir_raw(*curva_decreciente), "304L", 0.5)["id"]
    with pytest.raises(service.ErrorApi) as excinfo:
        service.procesar(con, test_id, ParametrosProcesamiento())
    assert _error(excinfo) == (422, "PROCESSING_FAILED")


def test_inexistente_404(con):
    for llamada in (
        lambda: service.obtener(con, 99),
        lambda: service.procesar(con, 99, ParametrosProcesamiento()),
        lambda: service.corregir_espesor(con, 99, 0.4),
        lambda: service.curva(con, 99, "raw"),
        lambda: service.archivo(con, 99),
        lambda: service.borrar(con, 99),
    ):
        with pytest.raises(service.ErrorApi) as excinfo:
            llamada()
        assert _error(excinfo) == (404, "TEST_NOT_FOUND")


def test_sin_procesar_404_result_not_found(con, ensayo):
    for llamada in (lambda: service.resultado(con, ensayo["id"]), lambda: service.curva(con, ensayo["id"], "processed")):
        with pytest.raises(service.ErrorApi) as excinfo:
            llamada()
        assert _error(excinfo) == (404, "RESULT_NOT_FOUND")


def test_curva_procesada_en_coordenadas_del_resultado(con, ensayo):
    resultado = service.procesar(con, ensayo["id"], ParametrosProcesamiento(aplicar_correccion=True))
    curva = service.curva(con, ensayo["id"], "processed")
    assert curva["displacement_mm"][0] == 0.0
    i = curva["load_n"].index(max(curva["load_n"]))
    assert curva["displacement_mm"][i] == pytest.approx(resultado["dm_mm"])


def test_corregir_espesor_recalcula(con, ensayo):
    service.procesar(con, ensayo["id"], ParametrosProcesamiento())
    actualizado = service.corregir_espesor(con, ensayo["id"], 0.25)
    assert actualizado["thickness_mm"] == 0.25
    assert actualizado["result"]["rm_mpa"] == pytest.approx(797.76)
    assert actualizado["result"]["py_t10_n"] == pytest.approx(318.75)
    assert actualizado["result"]["parameters"]["beta"] == 0.277


def test_corregir_espesor_igual_no_cambia(con, ensayo):
    antes = {**ensayo, "result": service.procesar(con, ensayo["id"], ParametrosProcesamiento())}
    assert service.corregir_espesor(con, ensayo["id"], 0.5) == antes


def test_corregir_espesor_sin_resultado(con, ensayo):
    actualizado = service.corregir_espesor(con, ensayo["id"], 0.4)
    assert actualizado["thickness_mm"] == 0.4
    assert actualizado["result"] is None


def test_corregir_espesor_si_falla_el_recalculo_no_cambia_nada(con, ensayo, monkeypatch):
    service.procesar(con, ensayo["id"], ParametrosProcesamiento())
    antes = service.obtener(con, ensayo["id"])

    def falla(*args, **kwargs):
        raise ValueError("falla simulada del recálculo")

    monkeypatch.setattr(service, "analizar", falla)
    with pytest.raises(service.ErrorApi) as excinfo:
        service.corregir_espesor(con, ensayo["id"], 0.25)
    assert _error(excinfo) == (422, "PROCESSING_FAILED")
    assert service.obtener(con, ensayo["id"]) == antes


def test_borrar(con, ensayo):
    service.borrar(con, ensayo["id"])
    with pytest.raises(service.ErrorApi):
        service.obtener(con, ensayo["id"])
