"""Acceso a SQLite con SQL explícito (sqlite3 de la biblioteca estándar).

Las escrituras usan `with con:`, que confirma la transacción si todo sale bien
y la deshace si hay una excepción.
"""
import sqlite3
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS tests (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    filename      TEXT    NOT NULL,
    material      TEXT    NOT NULL,
    thickness_mm  REAL    NOT NULL CHECK (thickness_mm > 0),
    uploaded_at   TEXT    NOT NULL,
    point_count   INTEGER NOT NULL,
    raw_file      BLOB    NOT NULL
);

CREATE TABLE IF NOT EXISTS results (
    test_id                      INTEGER PRIMARY KEY
                                 REFERENCES tests(id) ON DELETE CASCADE,
    apply_compliance_correction  INTEGER NOT NULL,
    compliance_mm_per_n          REAL,
    beta                         REAL    NOT NULL,
    pm_n                         REAL    NOT NULL,
    dm_mm                        REAL    NOT NULL,
    rm_mpa                       REAL    NOT NULL,
    py_t10_n                     REAL,
    py_t10_displacement_mm       REAL,
    sigma_y_t10_mpa              REAL,
    processed_at                 TEXT    NOT NULL
);
"""

# Orden de los parámetros de `_upsert_resultado`. El SQL de `_UPSERT_RESULTADO`
# lista las mismas columnas en el mismo orden.
CAMPOS_RESULTADO = (
    "apply_compliance_correction", "compliance_mm_per_n", "beta", "pm_n", "dm_mm", "rm_mpa",
    "py_t10_n", "py_t10_displacement_mm", "sigma_y_t10_mpa", "processed_at",
)

_SELECT_ENSAYOS = """
SELECT t.id, t.filename, t.material, t.thickness_mm, t.uploaded_at, t.point_count,
       r.test_id AS r_test_id, r.apply_compliance_correction, r.compliance_mm_per_n, r.beta,
       r.pm_n, r.dm_mm, r.rm_mpa, r.py_t10_n, r.py_t10_displacement_mm, r.sigma_y_t10_mpa,
       r.processed_at
FROM tests t
LEFT JOIN results r ON r.test_id = t.id
"""

# SQL literal: el upsert no se arma con f-strings (ver .claude/rules/api.md).
# Si se cambia CAMPOS_RESULTADO, cambiar también esta consulta.
_UPSERT_RESULTADO = """
INSERT INTO results (test_id, apply_compliance_correction, compliance_mm_per_n, beta, pm_n, dm_mm,
                     rm_mpa, py_t10_n, py_t10_displacement_mm, sigma_y_t10_mpa, processed_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(test_id) DO UPDATE SET
    apply_compliance_correction = excluded.apply_compliance_correction,
    compliance_mm_per_n         = excluded.compliance_mm_per_n,
    beta                        = excluded.beta,
    pm_n                        = excluded.pm_n,
    dm_mm                       = excluded.dm_mm,
    rm_mpa                      = excluded.rm_mpa,
    py_t10_n                    = excluded.py_t10_n,
    py_t10_displacement_mm      = excluded.py_t10_displacement_mm,
    sigma_y_t10_mpa             = excluded.sigma_y_t10_mpa,
    processed_at                = excluded.processed_at
"""


def conectar(ruta: str) -> sqlite3.Connection:
    if ruta != ":memory:":
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ruta, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(ESQUEMA)
    return con


def _a_dict(fila) -> dict:
    ensayo = {
        "id": fila["id"],
        "filename": fila["filename"],
        "material": fila["material"],
        "thickness_mm": fila["thickness_mm"],
        "uploaded_at": fila["uploaded_at"],
        "point_count": fila["point_count"],
        "result": None,
    }
    if fila["r_test_id"] is not None:
        ensayo["result"] = {
            "pm_n": fila["pm_n"],
            "dm_mm": fila["dm_mm"],
            "rm_mpa": fila["rm_mpa"],
            "py_t10_n": fila["py_t10_n"],
            "py_t10_displacement_mm": fila["py_t10_displacement_mm"],
            "sigma_y_t10_mpa": fila["sigma_y_t10_mpa"],
            "parameters": {
                "apply_compliance_correction": bool(fila["apply_compliance_correction"]),
                "compliance_mm_per_n": fila["compliance_mm_per_n"],
                "beta": fila["beta"],
            },
            "processed_at": fila["processed_at"],
        }
    return ensayo


def crear_ensayo(con, filename, material, thickness_mm, point_count, raw_file: bytes, uploaded_at: str) -> int:
    with con:
        cursor = con.execute(
            "INSERT INTO tests (filename, material, thickness_mm, uploaded_at, point_count, raw_file) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (filename, material, thickness_mm, uploaded_at, point_count, raw_file),
        )
    return cursor.lastrowid


def listar_ensayos(con) -> list[dict]:
    filas = con.execute(_SELECT_ENSAYOS + "ORDER BY t.uploaded_at DESC, t.id DESC").fetchall()
    return [_a_dict(fila) for fila in filas]


def obtener_ensayo(con, test_id: int) -> dict | None:
    fila = con.execute(_SELECT_ENSAYOS + "WHERE t.id = ?", (test_id,)).fetchone()
    return _a_dict(fila) if fila else None


def obtener_archivo(con, test_id: int) -> tuple[str, bytes] | None:
    fila = con.execute("SELECT filename, raw_file FROM tests WHERE id = ?", (test_id,)).fetchone()
    return (fila["filename"], bytes(fila["raw_file"])) if fila else None


def _upsert_resultado(con, test_id: int, resultado: dict) -> None:
    con.execute(_UPSERT_RESULTADO, (test_id, *(resultado[campo] for campo in CAMPOS_RESULTADO)))


def guardar_resultado(con, test_id: int, resultado: dict) -> None:
    with con:
        _upsert_resultado(con, test_id, resultado)


def actualizar_espesor(con, test_id: int, thickness_mm: float, resultado: dict | None) -> None:
    """Cambia el espesor y, si se pasa, reemplaza el resultado en la misma transacción."""
    with con:
        con.execute("UPDATE tests SET thickness_mm = ? WHERE id = ?", (thickness_mm, test_id))
        if resultado is not None:
            _upsert_resultado(con, test_id, resultado)


def borrar_ensayo(con, test_id: int) -> bool:
    with con:
        cursor = con.execute("DELETE FROM tests WHERE id = ?", (test_id,))
    return cursor.rowcount > 0
