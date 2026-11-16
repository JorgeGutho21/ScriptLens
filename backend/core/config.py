"""Configuración central de ScriptLens IA.

Todas las rutas de datos son locales al usuario. La aplicación instalada fija SCRIPTLENS_DATA_DIR en
%LOCALAPPDATA%\\io.github.jorgegutho21.scriptlens; sin esa variable (desarrollo) se usa %LOCALAPPDATA%\\ScriptLens.
Nada de lo que se configura aquí envía información fuera del equipo.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

APP_NAME = "ScriptLens IA"
APP_VERSION = "0.1.1"
AUTHOR = "Jorge Gutiérrez"
AUTHOR_GITHUB = "@JorgeGutho21"
REPOSITORY_URL = "https://github.com/JorgeGutho21/ScriptLens"


def default_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".local" / "share")
    return Path(base) / "ScriptLens"


@dataclass(frozen=True)
class Settings:
    """Parámetros de ejecución del backend local."""

    host: str = "127.0.0.1"
    port: int = 0  # 0 = puerto libre asignado por el sistema
    token: str = ""
    data_dir: Path = field(default_factory=lambda: default_data_dir())
    # Muestreo del sistema
    sample_interval: float = 1.0  # segundos entre mediciones globales
    process_interval: float = 2.0  # segundos entre mediciones de procesos
    history_seconds: int = 600  # ventana de historial en memoria (10 min)

    @classmethod
    def from_env(cls) -> "Settings":
        port = int(os.environ.get("SCRIPTLENS_PORT", "0"))
        token = os.environ.get("SCRIPTLENS_TOKEN", "")
        data_dir = os.environ.get("SCRIPTLENS_DATA_DIR")
        kwargs = {"port": port, "token": token}
        if data_dir:
            kwargs["data_dir"] = Path(data_dir)
        return cls(**kwargs)
