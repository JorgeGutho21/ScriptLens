"""Desofuscación estática (sin ejecutar nada).

Se normalizan técnicas simples de ofuscación para que las reglas puedan
reconocer los comandos. Si el script construye código en tiempo de ejecución
de formas más complejas, el análisis lo indica como limitación.
"""

from __future__ import annotations

import base64
import re

_ENC = re.compile(r"(?i)-e(?:nc(?:odedcommand)?|c)?\s+([A-Za-z0-9+/=]{16,})")
_B64_CALL = re.compile(r"(?i)FromBase64String\(\s*['\"]([A-Za-z0-9+/=]{16,})['\"]\s*\)")
_CONCAT = re.compile(r"""(['"])([^'"]*)\1\s*\+\s*(['"])([^'"]*)\3""")


def normalize_line(line: str, tipo: str) -> str:
    """Elimina ofuscación superficial: ^ en CMD, ` y concatenaciones en PowerShell."""
    s = line
    if tipo in ("bat", "cmd"):
        s = re.sub(r"\^(.)", r"\1", s)  # c^m^d → cmd
        s = s.replace('""', "")
    else:
        s = re.sub(r"`([^nrt0abfv`])", r"\1", s)  # I`nv`oke → Invoke (conserva `n, `t…)
        for _ in range(5):
            new = _CONCAT.sub(lambda m: m.group(1) + m.group(2) + m.group(4) + m.group(1), s)
            if new == s:
                break
            s = new
    return s


def _decode_b64(data: str, utf16: bool) -> str | None:
    try:
        raw = base64.b64decode(data + "=" * (-len(data) % 4), validate=False)
    except (ValueError, base64.binascii.Error):
        return None
    for enc in (("utf-16-le", "utf-8") if utf16 else ("utf-8", "utf-16-le")):
        try:
            text = raw.decode(enc)
        except UnicodeDecodeError:
            continue
        printable = sum(ch.isprintable() or ch in "\r\n\t" for ch in text)
        if text and printable / len(text) > 0.9:
            return text
    return None


def decoded_payloads(texto: str) -> list[dict]:
    """Decodifica -EncodedCommand y FromBase64String literales para analizarlos como texto."""
    out = []
    for n, line in enumerate(texto.splitlines(), start=1):
        for m in _ENC.finditer(line):
            dec = _decode_b64(m.group(1), utf16=True)
            if dec:
                out.append({"linea": n, "origen": "-EncodedCommand", "texto": dec[:4000]})
        for m in _B64_CALL.finditer(line):
            dec = _decode_b64(m.group(1), utf16=False)
            if dec:
                out.append({"linea": n, "origen": "FromBase64String", "texto": dec[:4000]})
    return out


def obfuscation_signals(texto: str) -> list[str]:
    signals = []
    if re.search(r"\^[a-z]", texto, re.I) and re.search(r"(?i)c\^?m\^?d|p\^?o\^?w\^?e\^?r", texto):
        signals.append("Uso de ^ para fragmentar nombres de comandos en CMD")
    if re.search(r"`[a-zA-Z]", texto) and re.search(r"(?i)i`?n`?v`?o`?k`?e|i`?e`?x", texto):
        signals.append("Uso de comillas invertidas (`) para fragmentar comandos de PowerShell")
    if _CONCAT.search(texto) and re.search(r"(?i)(invoke|iex|download|expression)", texto.replace("'", "").replace('"', "").replace("+", "")):
        signals.append("Concatenación de cadenas para construir comandos")
    if _ENC.search(texto) or _B64_CALL.search(texto):
        signals.append("Contenido codificado en Base64")
    if re.search(r"(?i)\[char\]\s*\d+", texto) and texto.lower().count("[char]") > 4:
        signals.append("Construcción de texto con códigos de caracteres ([char])")
    if re.search(r"(?i)-join\s*\(|\.replace\(|-replace\b", texto) and re.search(r"(?i)(iex|invoke-expression)", texto):
        signals.append("Transformación de texto antes de ejecutarlo dinámicamente")
    return signals
