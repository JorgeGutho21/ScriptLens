"""Lectura segura de scripts: SOLO como texto.

Basado en leer.py del proyecto original (guía 03B, §10.2). Regla de oro conservada:
este módulo nunca llama a cmd.exe, powershell.exe, subprocess ni os.system sobre
el archivo analizado. Las pruebas automatizadas verifican esa propiedad.
"""

from __future__ import annotations

LIMITE = 1_000_000  # 1 MB, como en el original
CODIFICACIONES = ("utf-8-sig", "utf-16", "cp1252", "cp850")


def decode(datos: bytes) -> tuple[str, str]:
    """Devuelve (texto, codificación detectada)."""
    datos = datos[:LIMITE]
    # UTF-16 sin BOM es frecuente en scripts guardados por PowerShell 5.1:
    # se detecta por la proporción de bytes nulos.
    if datos[:2] in (b"\xff\xfe", b"\xfe\xff") or (len(datos) > 8 and datos[1::2].count(0) > len(datos) // 4):
        try:
            enc = "utf-16" if datos[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-16-le"
            return datos.decode(enc), enc
        except UnicodeDecodeError:
            pass
    for cod in CODIFICACIONES:
        if cod == "utf-16":
            continue
        try:
            return datos.decode(cod), cod
        except UnicodeDecodeError:
            continue
    return datos.decode("latin-1", errors="replace"), "latin-1"


def tipo_por_nombre(nombre: str, texto: str) -> str:
    n = (nombre or "").lower()
    for ext, tipo in ((".ps1", "powershell"), (".psm1", "powershell"), (".bat", "bat"), (".cmd", "cmd")):
        if n.endswith(ext) or n.endswith(ext + ".txt"):
            return tipo
    # Sin extensión reconocible: se infiere por el contenido.
    low = texto.lower()
    ps_marks = sum(low.count(m) for m in ("$", "get-", "set-", "write-host", "param(", "function "))
    bat_marks = sum(low.count(m) for m in ("@echo off", "goto ", "%~", "set /a", "rem "))
    return "powershell" if ps_marks > bat_marks else "bat"
