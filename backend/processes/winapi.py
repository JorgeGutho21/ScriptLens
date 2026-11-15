"""Consultas puntuales a la API de Windows (solo lectura)."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

IS_WINDOWS = sys.platform == "win32"


def visible_window_pids() -> set[int]:
    """PID de los procesos que tienen al menos una ventana visible con título.

    Sirve para distinguir «aplicaciones abiertas» de procesos en segundo plano.
    """
    if not IS_WINDOWS:
        return set()
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    pids: set[int] = set()
    proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd) and user32.GetWindowTextLengthW(hwnd) > 0 and not user32.GetWindow(hwnd, 4):  # GW_OWNER
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            pids.add(pid.value)
        return True

    user32.EnumWindows(proto(cb), 0)
    return pids


def window_handles(pid: int) -> list[int]:
    """Ventanas principales visibles de un proceso (para solicitar un cierre normal)."""
    if not IS_WINDOWS:
        return []
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    handles: list[int] = []
    proto = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd) and not user32.GetWindow(hwnd, 4):
            handles.append(hwnd)
        return True

    user32.EnumWindows(proto(cb), 0)
    return handles


def post_close(hwnd: int) -> bool:
    """Envía WM_CLOSE: equivale a pulsar la X de la ventana (el programa puede pedir guardar)."""
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    return bool(user32.PostMessageW(hwnd, 0x0010, 0, 0))
