"""Comprobación de actualizaciones: SOLO bajo demanda del usuario y sin instalar nada.

Consulta la última versión publicada en GitHub Releases del repositorio oficial.
La petición no incluye datos del equipo (solo un agente de usuario genérico).
Si hay una versión nueva, la aplicación muestra el enlace a la página oficial;
la descarga y la instalación las decide y realiza el usuario.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from .config import APP_VERSION

LATEST_URL = "https://api.github.com/repos/JorgeGutho21/ScriptLens/releases/latest"


def _parse(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3]) or (0,)


def check() -> dict:
    req = urllib.request.Request(LATEST_URL, headers={"User-Agent": "ScriptLens-IA", "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"actual": APP_VERSION, "ultima": None, "hay_nueva": False, "mensaje": "Aún no hay versiones publicadas en GitHub Releases."}
        return {"actual": APP_VERSION, "ultima": None, "hay_nueva": False, "mensaje": f"No se pudo consultar GitHub (HTTP {e.code})."}
    except (urllib.error.URLError, OSError, ValueError):
        return {"actual": APP_VERSION, "ultima": None, "hay_nueva": False, "mensaje": "Sin conexión a Internet o GitHub no responde."}
    tag = data.get("tag_name") or ""
    newer = _parse(tag) > _parse(APP_VERSION)
    return {
        "actual": APP_VERSION,
        "ultima": tag,
        "hay_nueva": newer,
        "url": data.get("html_url"),
        "publicada": data.get("published_at"),
        "notas": (data.get("body") or "")[:2000],
        "mensaje": "Hay una versión nueva disponible. Descárguela desde la página oficial y verifique su hash SHA-256." if newer else "Tiene la versión más reciente.",
    }
