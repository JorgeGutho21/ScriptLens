"""Carpetas conocidas del usuario según Windows (SHGetKnownFolderPath).

Con la copia de seguridad de OneDrive, Windows redirige Documentos, Escritorio o
Imágenes a ``OneDrive\\...``: las rutas ``%USERPROFILE%\\Documents`` dejan de ser
las carpetas que el usuario ve. Este módulo pregunta a Windows y, si falla, usa
la ruta clásica dentro del perfil.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

FOLDER_IDS = {
    "Documents": "{FDD39AD0-238F-46AF-ADB4-6C85480369C7}",
    "Desktop": "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}",
    "Downloads": "{374DE290-123F-4565-9164-39C4925E467B}",
    "Pictures": "{33E28130-4E1E-4676-835A-98395C3BC3BB}",
    "Music": "{4BD8D571-6D19-48D3-BE97-422220080E43}",
    "Videos": "{18989B1D-99B5-455B-841C-AB7C74E4DDFC}",
}


def known_folder(name: str) -> Path:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class GUID(ctypes.Structure):
            _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]

        u = uuid.UUID(FOLDER_IDS[name])
        guid = GUID(u.fields[0], u.fields[1], u.fields[2], (ctypes.c_ubyte * 8)(*u.bytes[8:]))
        out = ctypes.c_wchar_p()
        fn = ctypes.windll.shell32.SHGetKnownFolderPath
        fn.argtypes = [ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE, ctypes.POINTER(ctypes.c_wchar_p)]
        fn.restype = ctypes.c_long
        try:
            if fn(ctypes.byref(guid), 0, None, ctypes.byref(out)) == 0 and out.value:
                return Path(out.value)
        except OSError:
            pass
        finally:
            if out:
                ctypes.windll.ole32.CoTaskMemFree(out)
    return Path.home() / name


def personal_folders() -> list[Path]:
    """Carpetas personales que ninguna limpieza debe tocar (rutas reales y clásicas)."""
    home = Path.home()
    paths = {known_folder(n) for n in FOLDER_IDS} | {home / n for n in FOLDER_IDS}
    for var in ("OneDrive", "OneDriveCommercial", "OneDriveConsumer"):
        if os.environ.get(var):
            paths.add(Path(os.environ[var]))
    return sorted(paths)
