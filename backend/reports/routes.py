"""Generación de informes. Los archivos se guardan en Documentos\\ScriptLens IA\\Informes."""

from __future__ import annotations

import os
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import data, html_report, pdf_report


def reports_dir() -> Path:
    base = Path(os.environ.get("SCRIPTLENS_REPORTS_DIR") or (Path.home() / "Documents" / "ScriptLens IA" / "Informes"))
    base.mkdir(parents=True, exist_ok=True)
    return base


class ReportReq(BaseModel):
    formato: str = "pdf"
    incluir_seguridad: bool = True
    comparar_con: int | None = None


def router(engine) -> APIRouter:
    r = APIRouter(prefix="/api/reports")

    @r.post("")
    def generate(req: ReportReq):
        if req.formato not in ("pdf", "html"):
            raise HTTPException(422, "Formato no válido")
        d = data.collect(engine, req.incluir_seguridad, req.comparar_con)
        name = f"ScriptLens_Informe_{time.strftime('%Y%m%d_%H%M%S')}.{req.formato}"
        path = reports_dir() / name
        if req.formato == "html":
            path.write_text(html_report.render(d), encoding="utf-8")
        else:
            pdf_report.render(d, path)
        engine.db.log_action("informe", name, "completada", f"Informe {req.formato.upper()} generado", None)
        return {"archivo": name, "ruta": str(path), "bytes": path.stat().st_size}

    @r.get("")
    def listing():
        files = sorted(reports_dir().glob("ScriptLens_Informe_*.*"), key=lambda p: p.stat().st_mtime, reverse=True)
        return {"carpeta": str(reports_dir()), "informes": [{"archivo": p.name, "bytes": p.stat().st_size, "fecha": p.stat().st_mtime} for p in files[:50]]}

    @r.post("/open/{name}")
    def open_report(name: str):
        """Abre un informe generado por ScriptLens con el programa predeterminado."""
        folder = reports_dir().resolve()
        path = (folder / name).resolve()
        if path.parent != folder or not path.name.startswith("ScriptLens_Informe_") or path.suffix not in (".pdf", ".html") or not path.exists():
            raise HTTPException(404, "Informe no encontrado")
        os.startfile(path)  # noqa: S606 — archivo propio y validado
        return {"abierto": path.name}

    @r.post("/open-folder")
    def open_folder():
        os.startfile(reports_dir())  # noqa: S606
        return {"abierto": str(reports_dir())}

    return r
