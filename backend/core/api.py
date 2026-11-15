"""API HTTP local de ScriptLens IA.

- Escucha únicamente en 127.0.0.1.
- Cada petición debe incluir el encabezado ``X-ScriptLens-Token`` con un token
  aleatorio generado en cada arranque. Así otras páginas web abiertas en el
  navegador no pueden leer datos del equipo.
- En esta fase todos los endpoints son de solo lectura.
"""

from __future__ import annotations

import secrets
import threading
import time

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.monitoring.diagnosis import summarize
from backend.monitoring.sampler import SystemSampler, system_info
from backend.processes.collector import ProcessMonitor

from .config import APP_NAME, APP_VERSION, AUTHOR, AUTHOR_GITHUB, REPOSITORY_URL, Settings

ALLOWED_ORIGINS = [
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost",
    "http://localhost:1420",
    "http://127.0.0.1:1420",
]


class Engine:
    """Coordina los hilos de muestreo del sistema y de procesos."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.sampler = SystemSampler(settings.history_seconds, settings.sample_interval)
        self.processes = ProcessMonitor(settings.history_seconds)
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []
        self._info_cache: tuple[float, dict] | None = None

    def start(self) -> None:
        self._threads = [
            threading.Thread(target=self._loop, args=(self.sampler.take, self.settings.sample_interval), daemon=True, name="sl-sampler"),
            threading.Thread(target=self._loop, args=(self.processes.sample, self.settings.process_interval), daemon=True, name="sl-procs"),
        ]
        for t in self._threads:
            t.start()

    def stop(self) -> None:
        self._stop.set()

    def _loop(self, fn, interval: float) -> None:
        while not self._stop.is_set():
            started = time.monotonic()
            try:
                fn()
            except Exception:  # noqa: BLE001 — un fallo puntual no debe detener el monitoreo
                pass
            self._stop.wait(max(0.05, interval - (time.monotonic() - started)))

    def info(self) -> dict:
        # El uso de discos cambia lentamente; se cachea 30 s.
        now = time.monotonic()
        if self._info_cache is None or now - self._info_cache[0] > 30:
            self._info_cache = (now, system_info())
        return self._info_cache[1]


def create_app(settings: Settings, engine: Engine | None = None) -> FastAPI:
    token = settings.token or secrets.token_urlsafe(32)
    engine = engine or Engine(settings)

    app = FastAPI(title=APP_NAME, version=APP_VERSION, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.token = token
    app.state.engine = engine
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["X-ScriptLens-Token", "Content-Type"],
    )

    def require_token(x_scriptlens_token: str = Header(default="")) -> None:
        if not secrets.compare_digest(x_scriptlens_token, token):
            raise HTTPException(status_code=401, detail="Token inválido")

    auth = [Depends(require_token)]

    @app.get("/api/health", dependencies=auth)
    def health():
        return {
            "status": "ok",
            "app": APP_NAME,
            "version": APP_VERSION,
            "author": AUTHOR,
            "github": AUTHOR_GITHUB,
            "repository": REPOSITORY_URL,
            "uptime_backend": round(time.time() - engine.sampler.started_at, 1),
        }

    @app.get("/api/system/info", dependencies=auth)
    def info():
        return engine.info()

    @app.get("/api/metrics/current", dependencies=auth)
    def current():
        s = engine.sampler.latest()
        return {"sample": s.to_dict() if s else None, "uptime_seconds": round(time.time() - engine.info()["boot_time"])}

    @app.get("/api/metrics/history", dependencies=auth)
    def history(seconds: int = Query(300, ge=10, le=3600)):
        return {"samples": [s.to_dict() for s in engine.sampler.history(seconds)]}

    @app.get("/api/metrics/summary", dependencies=auth)
    def summary():
        result = summarize(engine.sampler.history(60), engine.sampler.history(), engine.info()["disks"])
        result["scriptlens"] = engine.processes.self_usage()
        return result

    @app.get("/api/processes/top", dependencies=auth)
    def top(by: str = Query("cpu", pattern="^(cpu|memory)$"), limit: int = Query(8, ge=1, le=50)):
        ts, _ = engine.processes.latest()
        return {"measured_at": ts, "by": by, "processes": engine.processes.top(by, limit)}

    @app.get("/api/processes/sustained", dependencies=auth)
    def sustained(seconds: int = Query(60, ge=10, le=600), limit: int = Query(8, ge=1, le=50)):
        return {"seconds": seconds, "processes": engine.processes.sustained(seconds, limit)}

    return app
