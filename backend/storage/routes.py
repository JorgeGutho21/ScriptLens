"""Rutas de historial, comparación y privacidad."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from . import diagnostics as dg


class SaveRequest(BaseModel):
    label: str = Field(default="", max_length=120)


class SettingRequest(BaseModel):
    key: str = Field(pattern="^(history_enabled|conversations_enabled)$")
    value: bool


def router(engine) -> APIRouter:
    r = APIRouter(prefix="/api")
    db = engine.db

    @r.get("/history/diagnostics")
    def list_diagnostics():
        return {"diagnostics": dg.listing(db), "history_enabled": db.settings()["history_enabled"]}

    @r.post("/history/diagnostics")
    def save_diagnostic(req: SaveRequest):
        if not db.settings()["history_enabled"]:
            raise HTTPException(409, "El historial está desactivado en Ajustes.")
        try:
            diag = dg.capture(engine)
        except ValueError as e:
            raise HTTPException(409, str(e)) from e
        label = req.label.strip() or "Diagnóstico"
        did = dg.save(db, diag, label)
        return dg.load(db, did)

    @r.get("/history/diagnostics/{did}")
    def get_diagnostic(did: int):
        d = dg.load(db, did)
        if d is None:
            raise HTTPException(404, "Diagnóstico no encontrado")
        return d

    @r.delete("/history/diagnostics/{did}")
    def delete_diagnostic(did: int):
        if not dg.delete(db, did):
            raise HTTPException(404, "Diagnóstico no encontrado")
        return {"deleted": did}

    @r.get("/history/compare")
    def compare(a: int, b: str = Query("actual", pattern=r"^(actual|\d+)$")):
        da = dg.load(db, a)
        if da is None:
            raise HTTPException(404, "Diagnóstico A no encontrado")
        if b == "actual":
            try:
                dbb = dg.capture(engine)
            except ValueError as e:
                raise HTTPException(409, str(e)) from e
            dbb["label"], dbb["id"] = "Ahora", None
        else:
            dbb = dg.load(db, int(b))
            if dbb is None:
                raise HTTPException(404, "Diagnóstico B no encontrado")
        if da.get("created_at", 0) > dbb.get("created_at", 0):
            da, dbb = dbb, da  # siempre de más antiguo a más reciente
        return dg.compare(da, dbb)

    @r.get("/settings")
    def get_settings():
        return db.settings()

    @r.post("/settings")
    def set_setting(req: SettingRequest):
        db.set_setting(req.key, req.value)
        return db.settings()

    @r.delete("/privacy/{what}")
    def clear(what: str):
        if what not in ("diagnostics", "conversations", "actions"):
            raise HTTPException(400, "Elemento no válido")
        return {"deleted": db.clear(what), "what": what}

    @r.get("/actions/log")
    def action_log(limit: int = Query(100, ge=1, le=500)):
        return {"actions": db.actions(limit)}

    return r
