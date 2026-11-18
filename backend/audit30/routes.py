"""Rutas locales de la auditoría de 30 controles (se ejecuta solo cuando el usuario lo pide)."""

from __future__ import annotations

import socket
import threading
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from . import collect, evaluate, report


class Audit30State:
    def __init__(self) -> None:
        self.result: dict | None = None
        self.running = False
        self.error: str | None = None
        self._lock = threading.Lock()

    def start(self) -> bool:
        with self._lock:
            if self.running:
                return False
            self.running = True
        threading.Thread(target=self._run, daemon=True, name="sl-audit30").start()
        return True

    def _run(self) -> None:
        try:
            t0 = time.time()
            res = evaluate.evaluate(collect.collect())
            res["medido_en"], res["duracion_s"] = time.time(), round(time.time() - t0, 1)
            self.result, self.error = res, None
        except Exception as e:  # noqa: BLE001
            self.error = str(e)
        finally:
            self.running = False


class ReportReq(BaseModel):
    formato: str = Field(pattern="^(pdf|html)$")


def router(engine) -> APIRouter:
    r = APIRouter(prefix="/api/audit30")
    state: Audit30State = engine.audit30

    @r.get("")
    def get():
        return {"ejecutando": state.running, "error": state.error, "resultado": state.result}

    @r.post("/run")
    def run():
        return {"iniciada": state.start()}

    @r.post("/report")
    def make_report(req: ReportReq):
        from backend.reports.routes import reports_dir

        if state.result is None:
            raise HTTPException(409, "Ejecute primero la auditoría.")
        name = f"ScriptLens_Informe_Auditoria30_{time.strftime('%Y%m%d_%H%M%S')}.{req.formato}"
        path = reports_dir() / name
        if req.formato == "html":
            path.write_text(report.render_html(state.result, socket.gethostname()), encoding="utf-8")
        else:
            report.render_pdf(state.result, socket.gethostname(), path)
        engine.db.log_action("informe", name, "completada", f"Auditoría de 30 controles {req.formato.upper()}", None)
        return {"archivo": name, "ruta": str(path), "bytes": path.stat().st_size}

    return r
