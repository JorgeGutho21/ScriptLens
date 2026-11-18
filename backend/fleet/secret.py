"""Protección de las credenciales de los equipos vinculados con DPAPI de Windows.

``CryptProtectData`` cifra con una clave ligada a la cuenta de Windows del usuario: otra cuenta
o una copia de la base de datos en otro equipo no puede leer los tokens. Fuera de Windows (solo
en pruebas) se guarda tal cual con un prefijo que lo indica.
"""

from __future__ import annotations

import sys

_PLAIN = b"plain:"


if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class _Blob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    _crypt32 = ctypes.windll.crypt32
    _kernel32 = ctypes.windll.kernel32
    _ENTROPY = b"ScriptLens IA fleet v1"

    def _blob(data: bytes) -> _Blob:
        buf = ctypes.create_string_buffer(data, len(data))
        return _Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))

    def _call(name: str, data: bytes) -> bytes:
        out = _Blob()
        src, ent = _blob(data), _blob(_ENTROPY)
        fn = getattr(_crypt32, name)  # CryptProtectData / CryptUnprotectData (misma firma)
        if not fn(ctypes.byref(src), None, ctypes.byref(ent), None, None, 0x1, ctypes.byref(out)):  # CRYPTPROTECT_UI_FORBIDDEN
            raise OSError("DPAPI no pudo procesar la credencial")
        try:
            return ctypes.string_at(out.pbData, out.cbData)
        finally:
            _kernel32.LocalFree(out.pbData)

    def protect(token: str) -> bytes:
        return _call("CryptProtectData", token.encode("utf-8"))

    def unprotect(blob: bytes) -> str:
        if blob.startswith(_PLAIN):
            return blob[len(_PLAIN) :].decode("utf-8")
        return _call("CryptUnprotectData", blob).decode("utf-8")

else:  # pragma: no cover — ScriptLens solo se distribuye para Windows

    def protect(token: str) -> bytes:
        return _PLAIN + token.encode("utf-8")

    def unprotect(blob: bytes) -> str:
        return blob[len(_PLAIN) :].decode("utf-8")
