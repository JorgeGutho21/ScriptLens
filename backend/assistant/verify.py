"""Verificación de cifras de la respuesta generada.

Concepto heredado del proyecto «BitácoraIA» del autor (IA generativa local
verificada cifra por cifra): cada número que menciona el modelo debe existir en
los datos medidos que recibió. Los números que no se encuentran se informan al
usuario como «no verificados» en lugar de presentarse como hechos.
"""

from __future__ import annotations

import json
import re

_NUM = re.compile(r"(?<![\w.])(\d{1,3}(?:[.\s]\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)(?![\w])")
_IGNORE = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 60, 100}  # cifras triviales (enumeraciones, «1 minuto», «100 %»)


def _to_float(token: str) -> float | None:
    t = token.replace(" ", "")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", t):
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def data_numbers(data) -> list[float]:
    nums: list[float] = []

    def walk(x):
        if isinstance(x, bool):
            return
        if isinstance(x, (int, float)):
            nums.append(float(x))
        elif isinstance(x, str):
            nums.extend(v for v in (_to_float(m) for m in _NUM.findall(x)) if v is not None)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                walk(v)

    walk(data)
    return nums


def _matches(value: float, known: list[float]) -> bool:
    for k in known:
        if abs(value - k) <= max(0.06, abs(k) * 0.02):  # redondeo: 51,8 ≈ 52
            return True
        for scale in (1024, 1024**2, 1024**3, 1000):  # MB↔GB y similares
            if abs(value - k / scale) <= max(0.06, abs(k / scale) * 0.03) or abs(value - k * scale) <= max(0.06, abs(k * scale) * 0.03):
                return True
        if abs(value - round(k)) < 0.51 and abs(value - k) < 0.6:
            return True
    return False


def verify(answer: str, data) -> dict:
    known = data_numbers(json.loads(json.dumps(data, default=str)))
    found, unverified = [], []
    for tok in _NUM.findall(answer):
        v = _to_float(tok)
        if v is None or v in _IGNORE:
            continue
        found.append(tok)
        if not _matches(v, known):
            unverified.append(tok)
    return {"cifras": len(found), "no_verificadas": sorted(set(unverified)), "verificada": not unverified}
