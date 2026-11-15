import os
import sys
from pathlib import Path

import pytest

from backend.core.known_folders import known_folder, personal_folders

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Solo Windows")


def test_documents_matches_windows_shell_folder():
    """La carpeta Documentos coincide con la que Windows registra para el usuario."""
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as k:
        registered = Path(os.path.expandvars(winreg.QueryValueEx(k, "Personal")[0]))
    assert known_folder("Documents").resolve() == registered.resolve()


def test_personal_folders_include_real_and_classic_paths():
    folders = personal_folders()
    assert known_folder("Downloads") in folders
    assert Path.home() / "Documents" in folders
