"""Rutas de acciones supervisadas: preparar (resumen + token) y ejecutar (con token)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .operations import ActionError, ActionManager


class ProcessReq(BaseModel):
    accion: str = Field(pattern="^(cerrar|finalizar)$")
    pid: int = Field(gt=4)
    create_time: float
    nombre: str = Field(max_length=260)


class StartupReq(BaseModel):
    id: str = Field(max_length=400)
    habilitar: bool


class UninstallReq(BaseModel):
    id: str = Field(max_length=400)


class ExecuteReq(BaseModel):
    token: str = Field(min_length=10, max_length=100)


def router(engine) -> APIRouter:
    r = APIRouter(prefix="/api/actions")
    mgr: ActionManager = engine.actions

    def wrap(fn, *args):
        try:
            return fn(*args)
        except ActionError as e:
            raise HTTPException(409, str(e)) from e

    @r.post("/process/prepare")
    def prepare_process(req: ProcessReq):
        return wrap(mgr.prepare_process, req.accion, req.pid, req.create_time, req.nombre)

    @r.post("/startup/prepare")
    def prepare_startup(req: StartupReq):
        return wrap(mgr.prepare_startup, req.id, req.habilitar)

    @r.get("/temp/preview")
    def temp_preview():
        return wrap(mgr.temp_preview)

    @r.post("/temp/prepare")
    def prepare_temp():
        return wrap(mgr.prepare_temp)

    @r.get("/programs")
    def programs():
        return {"programas": [{k: v for k, v in p.items() if not k.startswith("_")} for p in mgr.installed_programs()]}

    @r.post("/programs/prepare")
    def prepare_uninstall(req: UninstallReq):
        return wrap(mgr.prepare_uninstall, req.id)

    @r.post("/execute")
    def execute(req: ExecuteReq):
        return wrap(mgr.execute, req.token)

    return r
