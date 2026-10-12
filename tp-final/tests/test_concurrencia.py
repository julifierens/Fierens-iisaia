"""Pedidos concurrentes sobre el mismo ensayo (dos conexiones, dos hilos).

PATCH /tests/{id} y PUT /tests/{id}/result leen, calculan y escriben. Si la
lectura queda fuera de la transacción de escritura, el segundo pedido pisa en
silencio lo que confirmó el primero. Estos tests frenan al primer pedido en
medio del cálculo y lanzan el segundo.

Ningún test puede colgar la suite: todas las esperas tienen timeout, el hilo
frenado se libera siempre en `finally` y los hilos son daemon.
"""
import sqlite3
import threading

import pytest

from app import repository, service
from sptero_core.analisis import ParametrosProcesamiento

ESPERA_S = 10.0   # tope de cualquier espera sobre un Event o un join
PAUSA_S = 0.3     # cuánto se espera para comprobar que el segundo pedido sigue bloqueado


@pytest.fixture
def ruta(tmp_path):
    return str(tmp_path / "concurrencia.db")


@pytest.fixture
def conexiones(ruta):
    con1 = repository.conectar(ruta)
    con2 = repository.conectar(ruta)
    yield con1, con2
    con1.close()
    con2.close()


@pytest.fixture
def ensayo_procesado(conexiones, raw_sintetico):
    """Ensayo de 0,5 mm ya procesado con los parámetros por defecto (β = 0,277)."""
    con1, _ = conexiones
    ensayo = service.subir(con1, "sintetico.raw", raw_sintetico, "304L", 0.5)
    service.procesar(con1, ensayo["id"], ParametrosProcesamiento())
    return ensayo["id"]


class _Frenado:
    """Envoltorio de `service.analizar`: la primera llamada se frena a mitad del cálculo."""

    def __init__(self, real):
        self.real = real
        self.dentro = threading.Event()
        self.liberar = threading.Event()
        self.llamadas = 0

    def __call__(self, *args, **kwargs):
        self.llamadas += 1
        if self.llamadas == 1:
            self.dentro.set()
            self.liberar.wait(ESPERA_S)
        return self.real(*args, **kwargs)


def _hilo(funcion, *args):
    """Hilo que guarda su resultado o su excepción para revisarlos desde el principal."""
    salida = {}

    def correr():
        try:
            salida["valor"] = funcion(*args)
        except BaseException as error:  # se re-lanza en el hilo principal
            salida["error"] = error

    hilo = threading.Thread(target=correr, daemon=True)
    return hilo, salida


def _terminar(hilo, salida):
    hilo.join(ESPERA_S)
    assert not hilo.is_alive(), "el hilo no terminó"
    if "error" in salida:
        raise salida["error"]
    return salida["valor"]


def _correr_en_carrera(monkeypatch, primero, segundo):
    """Frena `primero` en el cálculo, lanza `segundo`, comprueba que espera y libera todo."""
    frenado = _Frenado(service.analizar)
    monkeypatch.setattr(service, "analizar", frenado)
    hilo1, salida1 = _hilo(*primero)
    hilo2, salida2 = _hilo(*segundo)
    try:
        hilo1.start()
        assert frenado.dentro.wait(ESPERA_S), "el primer pedido no llegó al cálculo"
        hilo2.start()
        hilo2.join(PAUSA_S)
        espero = hilo2.is_alive()
    finally:
        # Se libera y se espera a los dos hilos antes de cualquier assert: si un
        # hilo siguiera usando su conexión al cerrarla, el proceso podría caerse.
        frenado.liberar.set()
        for hilo in (hilo1, hilo2):
            if hilo.ident is not None:
                hilo.join(ESPERA_S)
    assert espero, "el segundo pedido no esperó al primero"
    _terminar(hilo1, salida1)
    _terminar(hilo2, salida2)


def _verificar_estado_final(ruta, test_id):
    """Estado esperado: espesor 0,25 y β = 0,4, con Rm calculado con ese espesor."""
    con = repository.conectar(ruta)
    try:
        final = repository.obtener_ensayo(con, test_id)
    finally:
        con.close()
    assert final["thickness_mm"] == 0.25
    assert final["result"]["parameters"]["beta"] == 0.4
    assert final["result"]["rm_mpa"] == pytest.approx(0.4 * 1440.0 / (2.0 * 0.25))


def test_put_durante_un_patch_no_se_pierde(monkeypatch, ruta, conexiones, ensayo_procesado):
    con1, con2 = conexiones
    _correr_en_carrera(
        monkeypatch,
        (service.corregir_espesor, con1, ensayo_procesado, 0.25),
        (service.procesar, con2, ensayo_procesado, ParametrosProcesamiento(beta=0.4)),
    )
    _verificar_estado_final(ruta, ensayo_procesado)


def test_patch_durante_un_put_no_se_pierde(monkeypatch, ruta, conexiones, ensayo_procesado):
    con1, con2 = conexiones
    _correr_en_carrera(
        monkeypatch,
        (service.procesar, con1, ensayo_procesado, ParametrosProcesamiento(beta=0.4)),
        (service.corregir_espesor, con2, ensayo_procesado, 0.25),
    )
    _verificar_estado_final(ruta, ensayo_procesado)


def test_patch_que_falla_en_el_calculo_hace_rollback(monkeypatch, conexiones, ensayo_procesado):
    con, _ = conexiones
    antes = repository.obtener_ensayo(con, ensayo_procesado)

    def falla(*args, **kwargs):
        raise ValueError("falla simulada")

    monkeypatch.setattr(service, "analizar", falla)
    with pytest.raises(service.ErrorApi) as excinfo:
        service.corregir_espesor(con, ensayo_procesado, 0.25)
    assert excinfo.value.status == 422

    assert not con.in_transaction
    assert repository.obtener_ensayo(con, ensayo_procesado) == antes
    # La conexión sigue usable: una escritura posterior funciona.
    repository.actualizar_espesor(con, ensayo_procesado, 0.3, None)
    assert repository.obtener_ensayo(con, ensayo_procesado)["thickness_mm"] == 0.3


def test_excepcion_cualquiera_en_el_calculo_hace_rollback(monkeypatch, conexiones, ensayo_procesado):
    con, _ = conexiones
    antes = repository.obtener_ensayo(con, ensayo_procesado)
    def falla(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(service, "analizar", falla)
    with pytest.raises(RuntimeError):
        service.procesar(con, ensayo_procesado, ParametrosProcesamiento(beta=0.4))
    assert not con.in_transaction
    assert repository.obtener_ensayo(con, ensayo_procesado) == antes


def test_lock_no_liberado_termina_en_operational_error(ruta, raw_sintetico, monkeypatch):
    """Si el lock no se libera dentro del timeout, el pedido falla con OperationalError."""
    monkeypatch.setattr(repository, "ESPERA_LOCK_S", 0.2)
    con1 = repository.conectar(ruta)
    con2 = repository.conectar(ruta)
    try:
        ensayo = service.subir(con1, "s.raw", raw_sintetico, "304L", 0.5)
        with repository.transaccion(con1):
            with pytest.raises(sqlite3.OperationalError):
                service.corregir_espesor(con2, ensayo["id"], 0.25)
        assert not con2.in_transaction
    finally:
        con1.close()
        con2.close()
