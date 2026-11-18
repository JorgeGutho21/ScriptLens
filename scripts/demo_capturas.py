"""Entorno de DEMOSTRACIÓN para tomar capturas del acceso remoto y de «Mis computadoras».

Todo ocurre en este mismo equipo y solo en 127.0.0.1: no se abre ningún puerto en la red local,
no se toca el firewall y no se usan los datos de la instalación real (cada instancia tiene su
propia carpeta temporal). Las capturas obtenidas así deben rotularse como demostración: los
«equipos» son instancias aisladas del motor que miden el mismo PC.

Uso (PowerShell, desde la raíz del repositorio):
    .\\.venv\\Scripts\\python scripts\\demo_capturas.py consola  CARPETA
    .\\.venv\\Scripts\\python scripts\\demo_capturas.py agente   CARPETA PC-LAB-01 8771

- ``consola``: motor de la interfaz en 127.0.0.1:47811 (el de ``frontend/.env.development.local``).
  Su acceso remoto, al activarse, escucha solo en 127.0.0.1:8770, y además se sirve una copia
  HTTP de la vista remota en http://localhost:8790/ para verla en un navegador de escritorio
  con tamaño de celular (los navegadores integrados rechazan certificados propios).
- ``agente``: otra instancia con el acceso remoto activo en 127.0.0.1:PUERTO. Escribe su código
  temporal y su huella en CARPETA/NOMBRE.json y autoriza sola las solicitudes tras 15 s.
"""

from __future__ import annotations

import json
import os
import platform
import socket
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEMO_IFACE = [{"interfaz": "Solo este equipo (demostración)", "ip": "127.0.0.1", "virtual": False, "enlace_local": False}]


def _patch(name: str) -> None:
    """Nombre de equipo neutro y solo la interfaz de bucle local."""
    import backend.fleet.service as fs
    import backend.remote.netinfo as ni
    import backend.remote.service as rs
    import backend.remote.views as rv

    for mod in (ni, rs, rv, fs):
        mod.device_name = lambda: name
    socket.gethostname = lambda: name  # nunca mostrar el nombre real del equipo en las capturas
    platform.node = lambda: name
    rs.local_addresses = lambda: list(DEMO_IFACE)


def _engine(folder: Path):
    from backend.core.api import Engine
    from backend.core.config import Settings

    folder.mkdir(parents=True, exist_ok=True)
    os.environ["SCRIPTLENS_DATA_DIR"] = str(folder)
    os.environ.setdefault("SCRIPTLENS_REPORTS_DIR", str(folder / "Informes"))
    settings = Settings.from_env()
    engine = Engine(settings)
    engine.remote.allow_loopback = True
    engine.fleet.allow_loopback = True
    original = engine.remote.enable
    engine.remote.enable = lambda port=None, addresses=None: original(port, ["127.0.0.1"])
    return settings, engine


def consola(root: Path) -> None:
    import uvicorn

    from backend.core.api import create_app
    from backend.remote.app import create_remote_app

    _patch("PC-PRINCIPAL")
    os.environ["SCRIPTLENS_PORT"] = "47811"
    os.environ["SCRIPTLENS_TOKEN"] = "dev-local-token-123"
    settings, engine = _engine(root / "consola")
    engine.db.set_setting("remote_port", 8770)
    app = create_app(settings, engine)
    engine.start()

    mirror = uvicorn.Server(uvicorn.Config(create_remote_app(engine.remote), host="127.0.0.1", port=8790, log_level="warning", lifespan="off"))
    threading.Thread(target=mirror.run, daemon=True).start()
    print("Consola de demostración: interfaz en 127.0.0.1:47811, vista remota en http://localhost:8790/", flush=True)
    try:
        uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=47811, log_level="warning", lifespan="off")).run()
    finally:
        engine.stop()


def agente(root: Path, name: str, port: int) -> None:
    _patch(name)
    _, engine = _engine(root / name)
    engine.start()
    st = engine.remote.enable(port)
    out = root / f"{name}.json"
    seen: dict[str, float] = {}
    print(f"Agente {name} en https://127.0.0.1:{port}/ (solo este equipo)", flush=True)
    try:
        while True:
            st = engine.remote.status()
            if not st["codigo"]["codigo"]:
                engine.remote.new_code()
                st = engine.remote.status()
            out.write_text(json.dumps({"puerto": port, "codigo": st["codigo"]["codigo"], "huella_corta": st["huella_corta"]}), encoding="utf-8")
            for req in st["solicitudes"]:
                first = seen.setdefault(req["id"], time.time())
                if time.time() - first > 15:
                    engine.remote.auth.decide(req["id"], True)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        engine.stop()


if __name__ == "__main__":
    socket.setdefaulttimeout(None)
    role, root = sys.argv[1], Path(sys.argv[2])
    if role == "consola":
        consola(root)
    else:
        agente(root, sys.argv[3], int(sys.argv[4]))
