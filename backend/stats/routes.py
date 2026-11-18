"""Rutas locales de «Estadísticas de mi PC»."""

from __future__ import annotations

import socket
import time

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from . import report


class SettingsReq(BaseModel):
    activadas: bool
    retencion_dias: int = Field(ge=7, le=365)
    aplicaciones: bool


class ExportReq(BaseModel):
    formato: str = Field(pattern="^(csv|html)$")
    periodo: str = Field(default="semana", pattern="^(dia|semana|mes)$")


def router(engine) -> APIRouter:
    r = APIRouter(prefix="/api/stats")
    st = engine.stats

    @r.get("/summary")
    def summary(period: str = Query("dia", pattern="^(dia|semana|mes)$")):
        st.load_boot_events()  # consulta de solo lectura al registro de eventos, como mucho cada hora
        return st.summary(period)

    @r.post("/settings")
    def settings(req: SettingsReq):
        return st.set_settings(req.activadas, req.retencion_dias, req.aplicaciones)

    @r.delete("/data/{what}")
    def delete(what: str):
        if what not in ("aplicaciones", "alertas", "todo"):
            raise HTTPException(400, "Elemento no válido")
        return st.delete(what)

    @r.post("/export")
    def export(req: ExportReq):
        from backend.reports.routes import reports_dir

        name = f"ScriptLens_Informe_Estadisticas_{req.periodo}_{time.strftime('%Y%m%d_%H%M%S')}.{req.formato}"
        path = reports_dir() / name
        if req.formato == "csv":
            path.write_text("﻿" + st.export_csv(req.periodo), encoding="utf-8")  # BOM: Excel lo abre con tildes
        else:
            path.write_text(report.render(st.summary(req.periodo), socket.gethostname()), encoding="utf-8")
        engine.db.log_action("informe", name, "completada", f"Estadísticas {req.formato.upper()} generadas", None)
        return {"archivo": name, "ruta": str(path), "bytes": path.stat().st_size}

    return r
