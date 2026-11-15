"""API HTTP local de ScriptLens IA.

- Escucha únicamente en 127.0.0.1.
- Cada petición debe incluir el encabezado ``X-ScriptLens-Token`` con un token
  aleatorio generado en cada arranque. Así otras páginas web abiertas en el
  navegador no pueden leer datos del equipo.
- Las rutas de cada módulo viven en su propio archivo ``routes.py``.
"""

from __future__ import annotations

import secrets
import time

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.monitoring.diagnosis import summarize

from .config import APP_NAME, APP_VERSION, AUTHOR, AUTHOR_GITHUB, REPOSITORY_URL, Settings
from .engine import Engine

ALLOWED_ORIGINS = [
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost",
    "http://localhost:1420",
    "http://127.0.0.1:1420",
]


def monitoring_router(engine: Engine) -> APIRouter:
    r = APIRouter()

    @r.get("/api/health")
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

    @r.get("/api/system/info")
    def info():
        return engine.info()

    @r.get("/api/metrics/current")
    def current():
        s = engine.sampler.latest()
        return {"sample": s.to_dict() if s else None, "uptime_seconds": round(time.time() - engine.info()["boot_time"])}

    @r.get("/api/metrics/history")
    def history(seconds: int = Query(300, ge=10, le=3600)):
        return {"samples": [s.to_dict() for s in engine.sampler.history(seconds)]}

    @r.get("/api/metrics/summary")
    def summary():
        result = summarize(engine.sampler.history(60), engine.sampler.history(), engine.info()["disks"])
        result["scriptlens"] = engine.processes.self_usage()
        return result

    @r.get("/api/processes/top")
    def top(by: str = Query("cpu", pattern="^(cpu|memory)$"), limit: int = Query(8, ge=1, le=50)):
        ts, _ = engine.processes.latest()
        return {"measured_at": ts, "by": by, "processes": engine.processes.top(by, limit)}

    @r.get("/api/processes/sustained")
    def sustained(seconds: int = Query(60, ge=10, le=600), limit: int = Query(8, ge=1, le=50)):
        return {"seconds": seconds, "processes": engine.processes.sustained(seconds, limit)}

    return r


def create_app(settings: Settings, engine: Engine | None = None) -> FastAPI:
    token = settings.token or secrets.token_urlsafe(32)
    engine = engine or Engine(settings)

    def require_token(x_scriptlens_token: str = Header(default="")) -> None:
        if not secrets.compare_digest(x_scriptlens_token, token):
            raise HTTPException(status_code=401, detail="Token inválido")

    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        dependencies=[Depends(require_token)],
    )
    app.state.token = token
    app.state.engine = engine
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["X-ScriptLens-Token", "Content-Type"],
    )

    from backend.processes.routes import router as processes_router
    from backend.actions.routes import router as actions_router
    from backend.assistant.routes import router as assistant_router
    from backend.scripts.routes import router as scripts_router
    from backend.security.routes import router as security_router
    from backend.storage.routes import router as storage_router

    app.include_router(monitoring_router(engine))
    app.include_router(processes_router(engine))
    app.include_router(storage_router(engine))
    app.include_router(security_router(engine))
    app.include_router(scripts_router(engine))
    app.include_router(actions_router(engine))
    app.include_router(assistant_router(engine))
    return app
