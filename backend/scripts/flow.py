"""Análisis de flujo y estructuras de control.

``flujo_bat`` conserva el comportamiento del original (guía 03B, §10.3):
etiquetas, saltos goto/call y ciclos (goto hacia una etiqueta anterior).
Mejora: el «posible ciclo infinito» se evalúa por ciclo, buscando una condición
(if) o una salida (exit, goto :eof) entre la etiqueta y el salto, en lugar de
buscar un «if» en todo el script como hacía la versión original.
"""

from __future__ import annotations

import re

ETIQ = re.compile(r"^\s*:(\w+)")
SALTO = re.compile(r"\b(goto|call)\s+:?(\w+)", re.IGNORECASE)
SALIDA = re.compile(r"(?i)\b(if|exit)\b|goto\s+:?eof\b")


def flujo_bat(texto: str) -> dict:
    lineas = texto.splitlines()
    etiquetas: dict[str, int] = {}
    saltos = []
    for n, linea in enumerate(lineas, start=1):
        m = ETIQ.match(linea)
        if m and not linea.strip().startswith("::"):
            etiquetas[m.group(1).lower()] = n
        if linea.strip().lower().startswith(("rem ", "::")):
            continue
        for tipo, destino in SALTO.findall(linea):
            saltos.append({"linea": n, "tipo": tipo.lower(), "destino": destino.lower(), "existe": destino.lower() in etiquetas or destino.lower() == "eof"})
    # Segunda pasada: un salto puede apuntar a una etiqueta definida más abajo.
    for s in saltos:
        s["existe"] = s["destino"] in etiquetas or s["destino"] == "eof"
    ciclos = []
    for s in saltos:
        inicio = etiquetas.get(s["destino"])
        if s["tipo"] == "goto" and inicio is not None and inicio < s["linea"]:
            cuerpo = "\n".join(lineas[inicio : s["linea"] - 1])
            ciclos.append({**s, "desde": inicio, "con_salida": bool(SALIDA.search(cuerpo))})
    return {
        "etiquetas": etiquetas,
        "saltos": saltos,
        "ciclos": ciclos,
        "posible_ciclo_infinito": any(not c["con_salida"] for c in ciclos),
        "saltos_rotos": [s for s in saltos if not s["existe"]],
    }


_STRUCT = {
    "powershell": [
        ("funcion", re.compile(r"(?i)^\s*function\s+([\w-]+)")),
        ("bucle", re.compile(r"(?i)^\s*(while|for|foreach|do)\b|\|\s*(foreach-object|%)\s*\{")),
        ("condicion", re.compile(r"(?i)^\s*(if|elseif|switch)\b")),
        ("manejo_errores", re.compile(r"(?i)^\s*(try|catch|finally|trap)\b")),
        ("parametros", re.compile(r"(?i)^\s*param\s*\(")),
    ],
    "bat": [
        ("bucle", re.compile(r"(?i)^\s*for\b")),
        ("condicion", re.compile(r"(?i)^\s*if\b|\|\||&&")),
        ("salida", re.compile(r"(?i)^\s*exit\b")),
        ("variables", re.compile(r"(?i)^\s*set\b")),
        ("pausa", re.compile(r"(?i)^\s*(pause|timeout)\b")),
    ],
}


def estructuras(texto: str, tipo: str) -> dict:
    reglas = _STRUCT["powershell" if tipo == "powershell" else "bat"]
    found: dict[str, list[int]] = {}
    funciones = []
    for n, linea in enumerate(texto.splitlines(), start=1):
        for nombre, rx in reglas:
            m = rx.search(linea)
            if m:
                found.setdefault(nombre, []).append(n)
                if nombre == "funcion":
                    funciones.append({"nombre": m.group(1), "linea": n})
    return {"conteo": {k: len(v) for k, v in found.items()}, "lineas": found, "funciones": funciones}
