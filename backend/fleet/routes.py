"""Rutas locales de «Mis computadoras» (exigen el token interno de la aplicación)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from .service import FleetError


class PairReq(BaseModel):
    direccion: str = Field(min_length=3, max_length=64)
    puerto: int = Field(default=8765, ge=1024, le=65535)
    codigo: str = Field(pattern=r"^\d{6}$")
    nombre: str | None = Field(default=None, max_length=60)


def router(engine) -> APIRouter:
    r = APIRouter(prefix="/api/fleet")
    fleet = engine.fleet

    def guarded(fn, *args):
        try:
            return fn(*args)
        except FleetError as e:
            raise HTTPException(e.status, e.message) from e

    @r.get("/devices")
    def devices():
        return {"equipos": fleet.devices(), "esta_pc": {"device_id": engine.remote.device_id, "nombre": __import__("socket").gethostname()}}

    @r.post("/pair")
    def pair(req: PairReq):
        return guarded(fleet.start_pair, req.direccion, req.puerto, req.codigo, req.nombre)

    @r.get("/pair/{pid}")
    def pair_status(pid: str):
        return guarded(fleet.poll_pair, pid)

    @r.get("/devices/{did}")
    def device(did: str):
        return guarded(fleet.device, did)

    @r.get("/devices/{did}/history")
    def history(did: str, hours: int = Query(24, ge=1, le=168)):
        return fleet.history(did, hours)

    @r.get("/devices/{did}/processes")
    def processes(did: str, by: str = Query("cpu", pattern="^(cpu|memory)$")):
        return guarded(fleet.live, did, "procesos", f"?by={by}&limit=10")

    @r.get("/devices/{did}/findings")
    def findings(did: str):
        return guarded(fleet.live, did, "hallazgos")

    @r.get("/devices/{did}/stats")
    def stats(did: str):
        return guarded(fleet.live, did, "estadisticas", "?period=dia")

    @r.delete("/devices/{did}")
    def unlink(did: str):
        return guarded(fleet.unlink, did)

    return r
