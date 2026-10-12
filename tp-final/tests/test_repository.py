import sqlite3

import pytest

from app import repository

RESULTADO = {
    "apply_compliance_correction": False,
    "compliance_mm_per_n": None,
    "beta": 0.277,
    "pm_n": 1440.0,
    "dm_mm": 2.0,
    "rm_mpa": 398.88,
    "py_t10_n": 337.5,
    "py_t10_displacement_mm": 0.1625,
    "sigma_y_t10_mpa": 467.1,
    "processed_at": "2026-10-12T15:00:00+00:00",
}


@pytest.fixture
def con(tmp_path):
    conexion = repository.conectar(str(tmp_path / "prueba.db"))
    yield conexion
    conexion.close()


def _crear(con, nombre="a.raw", uploaded_at="2026-10-12T10:00:00+00:00"):
    return repository.crear_ensayo(con, nombre, "304L", 0.5, 601, b"contenido", uploaded_at)


def test_crear_y_obtener_sin_resultado(con):
    test_id = _crear(con)
    ensayo = repository.obtener_ensayo(con, test_id)
    assert ensayo == {
        "id": test_id, "filename": "a.raw", "material": "304L", "thickness_mm": 0.5,
        "uploaded_at": "2026-10-12T10:00:00+00:00", "point_count": 601, "result": None,
    }


def test_obtener_inexistente(con):
    assert repository.obtener_ensayo(con, 99) is None
    assert repository.obtener_archivo(con, 99) is None


def test_archivo_original_intacto(con):
    test_id = repository.crear_ensayo(con, "b.raw", "304L", 0.5, 601, b"\x00\xffbytes", "2026-10-12T10:00:00+00:00")
    assert repository.obtener_archivo(con, test_id) == ("b.raw", b"\x00\xffbytes")


def test_listar_mas_reciente_primero_y_sin_blob(con):
    primero = _crear(con, "a.raw", "2026-10-12T10:00:00+00:00")
    segundo = _crear(con, "b.raw", "2026-10-12T11:00:00+00:00")
    ensayos = repository.listar_ensayos(con)
    assert [e["id"] for e in ensayos] == [segundo, primero]
    assert "raw_file" not in ensayos[0]


def test_guardar_y_reemplazar_resultado(con):
    test_id = _crear(con)
    repository.guardar_resultado(con, test_id, RESULTADO)
    repository.guardar_resultado(con, test_id, {**RESULTADO, "beta": 0.3, "rm_mpa": 432.0})
    resultado = repository.obtener_ensayo(con, test_id)["result"]
    assert resultado["rm_mpa"] == 432.0
    assert resultado["parameters"] == {"apply_compliance_correction": False, "compliance_mm_per_n": None, "beta": 0.3}
    assert con.execute("SELECT COUNT(*) FROM results").fetchone()[0] == 1


def test_actualizar_espesor_con_resultado(con):
    test_id = _crear(con)
    repository.guardar_resultado(con, test_id, RESULTADO)
    repository.actualizar_espesor(con, test_id, 0.25, {**RESULTADO, "rm_mpa": 797.76})
    ensayo = repository.obtener_ensayo(con, test_id)
    assert ensayo["thickness_mm"] == 0.25
    assert ensayo["result"]["rm_mpa"] == 797.76


def test_actualizar_espesor_es_atomico(con):
    # Si falla la escritura del resultado, el espesor tampoco cambia.
    test_id = _crear(con)
    repository.guardar_resultado(con, test_id, RESULTADO)
    with pytest.raises(sqlite3.IntegrityError):
        repository.actualizar_espesor(con, test_id, 0.25, {**RESULTADO, "pm_n": None})
    ensayo = repository.obtener_ensayo(con, test_id)
    assert ensayo["thickness_mm"] == 0.5
    assert ensayo["result"]["rm_mpa"] == 398.88


def test_borrar_en_cascada(con):
    test_id = _crear(con)
    repository.guardar_resultado(con, test_id, RESULTADO)
    assert repository.borrar_ensayo(con, test_id) is True
    assert repository.obtener_ensayo(con, test_id) is None
    assert con.execute("SELECT COUNT(*) FROM results").fetchone()[0] == 0
    assert repository.borrar_ensayo(con, test_id) is False
