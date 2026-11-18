"""Control del acceso remoto desde la aplicación local (exige el token interno de Tauri).

Ninguna de estas rutas existe en el servidor remoto: un dispositivo vinculado no puede
activar, autorizar, revocar ni cambiar lo que se comparte.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .auth import PairingError
from .service import RemoteError


class EnableReq(BaseModel):
    puerto: int | None = Field(default=None, ge=1024, le=65535)


class DecideReq(BaseModel):
    autorizar: bool


class SharingReq(BaseModel):
    procesos: bool
    seguridad: bool
    estadisticas: bool


def router(engine) -> APIRouter:
    r = APIRouter(prefix="/api/remote")
    svc = engine.remote

    def guarded(fn, *args):
        try:
            return fn(*args)
        except RemoteError as e:
            raise HTTPException(409, str(e)) from e
        except PairingError as e:
            raise HTTPException(e.status, e.message) from e

    @r.get("/status")
    def status():
        return svc.status()

    @r.post("/enable")
    def enable(req: EnableReq):
        return guarded(svc.enable, req.puerto)

    @r.post("/pause")
    def pause():
        return svc.pause()

    @r.post("/disable")
    def disable():
        return svc.disable()

    @r.post("/code")
    def code():
        return guarded(svc.new_code)

    @r.post("/requests/{short_id}")
    def decide(short_id: str, req: DecideReq):
        return guarded(svc.auth.decide, short_id, req.autorizar)

    @r.delete("/sessions/{sid}")
    def revoke(sid: str):
        if not svc.auth.revoke(sid):
            raise HTTPException(404, "Dispositivo no encontrado")
        return {"revocada": sid}

    @r.post("/sharing")
    def sharing(req: SharingReq):
        return svc.set_sharing(req.procesos, req.seguridad, req.estadisticas)

    return r
