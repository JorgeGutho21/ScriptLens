"""Punto de entrada del backend: ``python -m backend``.

Al estar listo imprime en stdout una sola línea JSON:
``{"event": "ready", "port": <int>, "token": "<str>"}``
que la aplicación Tauri lee para conectarse. El token nunca se escribe en disco.
"""

from __future__ import annotations

import json
import os
import socket
import sys

import uvicorn

from backend.core.api import Engine, create_app
from backend.core.config import Settings


def _watch_parent(parent_pid: int, on_exit) -> None:
    """Termina el motor si la aplicación que lo inició deja de existir.

    Evita procesos huérfanos aunque la aplicación se cierre de forma inesperada.
    """
    import threading
    import time

    import psutil

    def loop() -> None:
        while psutil.pid_exists(parent_pid):
            time.sleep(1.0)
        on_exit()

    threading.Thread(target=loop, daemon=True, name="sl-parent-watch").start()


def main() -> int:
    settings = Settings.from_env()
    engine = Engine(settings)
    app = create_app(settings, engine)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((settings.host, settings.port))
    # Escuchar antes de anunciar "ready": las conexiones tempranas quedan en cola
    # en lugar de ser rechazadas mientras uvicorn termina de arrancar.
    sock.listen(64)
    port = sock.getsockname()[1]

    engine.start()
    print(json.dumps({"event": "ready", "port": port, "token": app.state.token}), flush=True)

    config = uvicorn.Config(app, log_level="warning", access_log=False, lifespan="off")
    server = uvicorn.Server(config)
    parent = os.environ.get("SCRIPTLENS_PARENT_PID")
    if parent and parent.isdigit():
        _watch_parent(int(parent), lambda: setattr(server, "should_exit", True))
    try:
        server.run(sockets=[sock])
    finally:
        engine.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
