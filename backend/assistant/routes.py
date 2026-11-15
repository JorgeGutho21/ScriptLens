"""Rutas del asistente. Todas de lectura salvo guardar/borrar conversaciones propias."""

from __future__ import annotations

import json
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import llm, service


class AskReq(BaseModel):
    pregunta: str = Field(min_length=1, max_length=1000)
    conversacion_id: int | None = None
    modelo: str | None = Field(default=None, pattern=r"^[\w.:\-]{1,60}$")
    usar_ia: bool = True


class PullReq(BaseModel):
    modelo: str = Field(pattern=r"^[\w.:\-]{1,60}$")
    acepto_descarga: bool


def router(engine) -> APIRouter:
    r = APIRouter(prefix="/api/assistant")
    db = engine.db

    @r.get("/status")
    def status():
        s = llm.status()
        return {**s, "modelo_predeterminado": llm.DEFAULT_MODEL, "modelos_sugeridos": llm.MODELS}

    @r.post("/ask")
    def ask(req: AskReq):
        save = db.settings()["conversations_enabled"]
        cid = req.conversacion_id
        history: list[dict] = []
        if cid is not None:
            if not db.query("SELECT id FROM conversations WHERE id = ?", (cid,)):
                raise HTTPException(404, "Conversación no encontrada")
            history = db.query("SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id", (cid,))
        elif save:
            cid = db.execute("INSERT INTO conversations(created_at, title) VALUES (?, ?)", (time.time(), req.pregunta[:80])).lastrowid

        def events():
            if cid is not None and save:
                db.execute("INSERT INTO messages(conversation_id, created_at, role, content) VALUES (?,?,?,?)", (cid, time.time(), "user", req.pregunta))
            yield json.dumps({"type": "conversation", "id": cid if save else None}) + "\n"
            for ev in service.ask(engine, req.pregunta, req.modelo, history, req.usar_ia):
                if ev["type"] == "done" and cid is not None and save:
                    db.execute(
                        "INSERT INTO messages(conversation_id, created_at, role, content, evidence_json) VALUES (?,?,?,?,?)",
                        (cid, time.time(), "assistant", ev["answer"], json.dumps({k: ev[k] for k in ("modo", "modelo", "verificacion")}, default=str)),
                    )
                yield json.dumps(ev, ensure_ascii=False, default=str) + "\n"

        return StreamingResponse(events(), media_type="application/x-ndjson")

    @r.get("/conversations")
    def conversations():
        return {"conversaciones": db.query("SELECT id, created_at, title FROM conversations ORDER BY id DESC LIMIT 50")}

    @r.get("/conversations/{cid}")
    def conversation(cid: int):
        msgs = db.query("SELECT role, content, created_at, evidence_json FROM messages WHERE conversation_id = ? ORDER BY id", (cid,))
        for m in msgs:
            m["meta"] = json.loads(m.pop("evidence_json") or "null")
        return {"id": cid, "mensajes": msgs}

    @r.delete("/conversations/{cid}")
    def delete_conversation(cid: int):
        return {"deleted": db.execute("DELETE FROM conversations WHERE id = ?", (cid,)).rowcount}

    @r.post("/pull")
    def pull(req: PullReq):
        """Descarga un modelo con Ollama SOLO tras la autorización explícita del usuario."""
        if not req.acepto_descarga:
            raise HTTPException(400, "Se requiere autorización explícita para descargar el modelo.")
        if req.modelo not in {m["id"] for m in llm.MODELS}:
            raise HTTPException(400, "Modelo no admitido.")

        def events():
            try:
                for ev in llm.pull_stream(req.modelo):
                    yield json.dumps(ev) + "\n"
            except Exception as e:  # noqa: BLE001
                yield json.dumps({"error": str(e)}) + "\n"

        return StreamingResponse(events(), media_type="application/x-ndjson")

    return r
