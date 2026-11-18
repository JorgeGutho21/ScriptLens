"""Señales de actividad del usuario, sin capturar contenido.

- ``idle_seconds``: segundos desde la última entrada de teclado o ratón (``GetLastInputInfo``).
  Solo es un contador de tiempo: no registra qué teclas se pulsan ni dónde se hace clic.
- ``foreground_app``: nombre del ejecutable de la ventana en primer plano. Se usa SOLO si la
  persona activa «Aplicaciones más utilizadas»; no se lee el título de la ventana.
"""

from __future__ import annotations

import sys

import psutil

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class _LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

    _user32 = ctypes.windll.user32
    _kernel32 = ctypes.windll.kernel32
    _kernel32.GetTickCount64.restype = ctypes.c_ulonglong

    def idle_seconds() -> float | None:
        info = _LASTINPUTINFO(ctypes.sizeof(_LASTINPUTINFO), 0)
        if not _user32.GetLastInputInfo(ctypes.byref(info)):
            return None
        now = _kernel32.GetTickCount64() & 0xFFFFFFFF  # dwTime es de 32 bits
        return ((now - info.dwTime) & 0xFFFFFFFF) / 1000.0

    def foreground_app() -> str | None:
        hwnd = _user32.GetForegroundWindow()
        if not hwnd:
            return None
        pid = wintypes.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        try:
            return psutil.Process(pid.value).name()
        except psutil.Error:
            return None

else:  # pragma: no cover

    def idle_seconds() -> float | None:
        return None

    def foreground_app() -> str | None:
        return None


def user_session_open() -> bool:
    try:
        return bool(psutil.users())
    except Exception:  # noqa: BLE001
        return False
