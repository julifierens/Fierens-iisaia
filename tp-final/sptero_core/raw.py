"""Lectura del archivo .raw exportado por la Instron.

Copia de `encontrar_inicio_tabla` y `cargar_raw_a_listas` de Programa SPTERO.py.
Cambios de entrada/salida respecto del original (las reglas de lectura no cambian):
- recibe el contenido del archivo en bytes, no una ruta;
- no imprime: devuelve `invertida` para indicar si se invirtió el signo;
- un `csv.Error` (archivo dañado) se convierte en `ValueError`, como el resto de
  los errores de lectura.
"""
import csv
import io
import math
from dataclasses import dataclass

import numpy as np

COLUMNA_X = "Extension mm"
COLUMNA_Y = "Load N"


@dataclass(frozen=True)
class CurvaRaw:
    x: np.ndarray
    y: np.ndarray
    invertida: bool


def encontrar_inicio_tabla(lines):
    for i, l in enumerate(lines):
        s = l.strip()
        if s.startswith('"Time') and ("Load" in s) and (";" in s):
            return i
    return None


def leer_raw(contenido: bytes, xcol=COLUMNA_X, ycol=COLUMNA_Y) -> CurvaRaw:
    # El original abre el archivo en modo texto con errors="replace"; un
    # TextIOWrapper reproduce la misma lectura por líneas desde bytes.
    texto = io.TextIOWrapper(io.BytesIO(contenido), encoding="utf-8", errors="replace")
    lines = texto.readlines()

    header_idx = encontrar_inicio_tabla(lines)
    if header_idx is None:
        raise ValueError('No encontré el encabezado de la tabla (fila tipo "Time ...;...Load...").')

    data_str = "".join(lines[header_idx:])
    reader = csv.DictReader(io.StringIO(data_str), delimiter=';', quotechar='"')

    # El original deja escapar csv.Error (por ejemplo, una comilla sin cerrar en
    # un archivo truncado). Se traduce a ValueError; las reglas de lectura no cambian.
    try:
        fieldnames = [c.strip() for c in (reader.fieldnames or [])]
        if reader.fieldnames:
            reader.fieldnames = fieldnames

        if xcol not in fieldnames or ycol not in fieldnames:
            raise ValueError(
                f"No encuentro columnas esperadas.\n"
                f"Busco: {xcol!r} y {ycol!r}\n"
                f"Disponibles: {fieldnames}"
            )

        x, y = [], []
        for row in reader:
            try:
                xv = float(str(row[xcol]).strip().replace(",", "."))
                yv = float(str(row[ycol]).strip().replace(",", "."))
            except Exception:
                continue
            if math.isfinite(xv) and math.isfinite(yv):
                x.append(xv)
                y.append(yv)
    except csv.Error as e:
        raise ValueError("El archivo está dañado: no se pudo leer la tabla de datos.") from e

    if len(x) < 20:
        raise ValueError("Muy pocos puntos leídos. ¿Seguro es el .raw correcto?")

    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)

    # invertir signo si vienen mayormente negativos
    flipped = False
    if np.median(y) < 0:
        y = -y
        flipped = True
    if np.median(x) < 0:
        x = -x
        flipped = True

    # ordenar por x creciente
    idx = np.argsort(x)
    return CurvaRaw(x=x[idx], y=y[idx], invertida=flipped)
