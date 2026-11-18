"""Aplicación HTTP remota, independiente de la API local y de SOLO LECTURA.

Defensas (en este orden):
1. Solo clientes con IP privada (LAN, hotspot). Cualquier otra → 403.
2. Límite de peticiones por IP.
3. Lista explícita de rutas: un método o ruta no incluido aquí no existe (404/405). No se
   registra ninguna ruta de acciones, comandos, ajustes, archivos ni del asistente.
4. Sesión obligatoria para los datos (cookie HttpOnly del navegador o ``Authorization: Bearer``
   de la consola). El token interno de Tauri no se acepta aquí ni se expone.
5. Encabezados de seguridad: CSP estricta, sin caché, sin incrustación en marcos.
"""

from __future__ import annotations

import time
from collections import deque
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from . import views
from .auth import PairingError
from .netinfo import is_allowed_client

WEB_DIR = Path(__file__).with_name("web")
COOKIE = "sl_remote"
RATE_LIMIT = 240  # peticiones por minuto y por IP (la vista remota hace ~1 por segundo)

# Única lista de rutas que existen en el servidor remoto (se comprueba en las pruebas).
ALLOWED_ROUTES = {
    ("GET", "/"),
    ("GET", "/remote.js"),
    ("GET", "/remote.css"),
    ("GET", "/icon.svg"),
    ("POST", "/remote/api/pair/request"),
    ("GET", "/remote/api/pair/status"),
    ("POST", "/remote/api/logout"),
    ("GET", "/remote/api/whoami"),
    ("GET", "/remote/api/overview"),
    ("GET", "/remote/api/history"),
    ("GET", "/remote/api/processes"),
    ("GET", "/remote/api/findings"),
    ("GET", "/remote/api/stats"),
}

SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


class PairBody(BaseModel):
    codigo: str = Field(pattern=r"^\d{6}$")
    nombre: str = Field(min_length=1, max_length=60)
    tipo: str = Field(default="navegador", pattern=r"^(navegador|consola)$")


def create_remote_app(service) -> FastAPI:
    engine = service.engine
    auth = service.auth
    hits: dict[str, deque] = {}

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def guard(request: Request, call_next):
        ip = request.client.host if request.client else None
        if not is_allowed_client(ip, service.allow_loopback):
            return JSONResponse({"detail": "Solo se permiten dispositivos de la red local."}, status_code=403, headers=SECURITY_HEADERS)
        now = time.monotonic()
        q = hits.setdefault(ip, deque())
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= RATE_LIMIT:
            return JSONResponse({"detail": "Demasiadas peticiones. Espere un momento."}, status_code=429, headers=SECURITY_HEADERS)
        q.append(now)
        if (request.method, request.url.path) not in ALLOWED_ROUTES:
            # Cualquier otra operación (POST de acciones, DELETE, rutas locales…) no existe aquí.
            status = 405 if any(p == request.url.path for _, p in ALLOWED_ROUTES) else 404
            return JSONResponse({"detail": "Operación no disponible en la vista remota de solo lectura."}, status_code=status, headers=SECURITY_HEADERS)
        response = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            response.headers.setdefault(k, v)
        return response

    def session(request: Request) -> dict:
        token = request.cookies.get(COOKIE)
        header = request.headers.get("authorization", "")
        if header.lower().startswith("bearer "):
            token = header[7:].strip()
        s = auth.validate(token, request.client.host)
        if s is None or not service.serving:
            raise HTTPException(401, "Sesión no válida o revocada. Vuelva a vincular este dispositivo.")
        return s

    # --- Página web remota (archivos estáticos propios) -------------------
    def static(name: str, media: str):
        return FileResponse(WEB_DIR / name, media_type=media)

    app.get("/")(lambda: static("index.html", "text/html; charset=utf-8"))
    app.get("/remote.js")(lambda: static("remote.js", "text/javascript; charset=utf-8"))
    app.get("/remote.css")(lambda: static("remote.css", "text/css; charset=utf-8"))
    app.get("/icon.svg")(lambda: static("icon.svg", "image/svg+xml"))

    # --- Vinculación -----------------------------------------------------
    @app.post("/remote/api/pair/request")
    def pair_request(body: PairBody, request: Request):
        try:
            req = auth.request(body.codigo, body.nombre, body.tipo, request.client.host)
        except PairingError as e:
            raise HTTPException(e.status, e.message) from e
        return {"solicitud": req.id, "frase": req.frase, "equipo": views.device_name(), "huella": service.fingerprint, "device_id": service.device_id}

    @app.get("/remote/api/pair/status")
    def pair_status(solicitud: str = Query(min_length=10, max_length=64)):
        estado, token, tipo = auth.poll(solicitud)
        if estado != "autorizada":
            return {"estado": estado}
        if tipo == "consola":
            return {"estado": "autorizada", "token": token, "device_id": service.device_id, "huella": service.fingerprint}
        resp = JSONResponse({"estado": "autorizada"})
        resp.set_cookie(COOKIE, token, max_age=12 * 3600, httponly=True, secure=True, samesite="strict", path="/")
        return resp

    @app.post("/remote/api/logout")
    def logout(s: dict = Depends(session)):
        auth.revoke(s["id"])
        resp = JSONResponse({"cerrada": True})
        resp.delete_cookie(COOKIE, path="/")
        return resp

    # --- Consulta de datos ----------------------------------------------
    @app.get("/remote/api/whoami")
    def whoami(s: dict = Depends(session)):
        return {"equipo": views.device_name(), "device_id": service.device_id, "sesion": {"nombre": s["nombre"], "tipo": s["tipo"], "caduca": s["expires_at"]}, "comparte": service.sharing(), "solo_lectura": True}

    @app.get("/remote/api/overview")
    def overview(_: dict = Depends(session)):
        return views.overview(engine, service.device_id)

    @app.get("/remote/api/history")
    def history(seconds: int = Query(300, ge=10, le=600), _: dict = Depends(session)):
        return views.history(engine, seconds)

    @app.get("/remote/api/processes")
    def processes(by: str = Query("cpu", pattern="^(cpu|memory)$"), limit: int = Query(8, ge=1, le=10), _: dict = Depends(session)):
        if not service.sharing()["procesos"]:
            raise HTTPException(403, "El propietario de la PC no comparte la lista de procesos.")
        return views.processes(engine, by, limit)

    @app.get("/remote/api/findings")
    def findings(_: dict = Depends(session)):
        return views.findings(engine, service.sharing()["seguridad"])

    @app.get("/remote/api/stats")
    def stats(period: str = Query("dia", pattern="^(dia|semana)$"), _: dict = Depends(session)):
        if not service.sharing()["estadisticas"]:
            raise HTTPException(403, "El propietario de la PC no comparte las estadísticas.")
        st = getattr(engine, "stats", None)
        if st is None:
            return {"disponible": False}
        return st.remote_summary(period)

    @app.exception_handler(404)
    async def not_found(request: Request, exc):
        return JSONResponse({"detail": "No encontrado"}, status_code=404, headers=SECURITY_HEADERS)

    app.state.allowed = ALLOWED_ROUTES
    return app
