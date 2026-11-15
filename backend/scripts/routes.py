"""Rutas del analizador de scripts. El contenido se recibe como texto; nunca se ejecuta."""

from __future__ import annotations

import base64

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .analyzer import analyze, model_metrics
from .reading import LIMITE


class AnalyzeRequest(BaseModel):
    nombre: str = Field(default="", max_length=260)
    # Base64 para conservar la codificación original (UTF-16, CP1252…)
    contenido_b64: str = Field(max_length=int(LIMITE * 1.4) + 16)


def router(engine) -> APIRouter:
    r = APIRouter(prefix="/api/scripts")

    @r.post("/analyze")
    def analyze_script(req: AnalyzeRequest):
        try:
            data = base64.b64decode(req.contenido_b64, validate=True)
        except (ValueError, base64.binascii.Error) as e:
            raise HTTPException(422, "Contenido no válido") from e
        result = analyze(data, req.nombre)
        engine.last_script_analysis = result  # disponible para el asistente (solo lectura)
        return result

    @r.get("/model")
    def model_info():
        m = model_metrics()
        if m is None:
            raise HTTPException(404, "Modelo no entrenado")
        return m

    return r
