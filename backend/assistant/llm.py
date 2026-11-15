"""Cliente mínimo de Ollama (http://127.0.0.1:11434). Solo localhost: nada sale del equipo."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Iterator

OLLAMA = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3:4b-instruct"
# Modelos sugeridos (tamaño aproximado de descarga, Q4_K_M)
MODELS = [
    {"id": "qwen3:4b-instruct", "nombre": "Qwen3 4B Instruct", "descarga_gb": 2.5, "ram_gb": 4.5, "nota": "Recomendado. Respuestas directas, sin razonamiento extenso."},
    {"id": "qwen3:1.7b", "nombre": "Qwen3 1.7B", "descarga_gb": 1.4, "ram_gb": 2.5, "nota": "Para equipos con 8 GB de RAM o menos. Menos preciso."},
    {"id": "qwen3:4b", "nombre": "Qwen3 4B (razonamiento)", "descarga_gb": 2.5, "ram_gb": 4.5, "nota": "Razona antes de responder: mucho más lento."},
]


def _get(path: str, timeout: float = 3.0):
    with urllib.request.urlopen(OLLAMA + path, timeout=timeout) as r:
        return json.loads(r.read())


def status() -> dict:
    try:
        version = _get("/api/version")["version"]
    except (urllib.error.URLError, OSError, ValueError):
        return {"instalado_o_activo": False, "version": None, "modelos": []}
    try:
        models = [m["name"] for m in _get("/api/tags").get("models", [])]
    except (urllib.error.URLError, OSError, ValueError):
        models = []
    return {"instalado_o_activo": True, "version": version, "modelos": models}


_THINK = re.compile(r"<think>.*?</think>", re.S)


def chat_stream(model: str, messages: list[dict], num_predict: int = 700) -> Iterator[str]:
    """Genera fragmentos de texto. Omite cualquier bloque de razonamiento <think>."""
    body = json.dumps(
        {
            "model": model,
            "messages": messages,
            "stream": True,
            "think": False,
            "keep_alive": "10m",
            "options": {"temperature": 0.2, "num_ctx": 8192, "num_predict": num_predict},
        }
    ).encode("utf-8")
    req = urllib.request.Request(OLLAMA + "/api/chat", data=body, headers={"Content-Type": "application/json"})
    in_think = False
    with urllib.request.urlopen(req, timeout=300) as r:
        for raw in r:
            if not raw.strip():
                continue
            chunk = json.loads(raw)
            if chunk.get("error"):
                raise RuntimeError(chunk["error"])
            text = (chunk.get("message") or {}).get("content", "")
            if "<think>" in text:
                in_think = True
                text = text.split("<think>", 1)[0]
            if in_think:
                if "</think>" in text:
                    in_think = False
                    text = text.split("</think>", 1)[1]
                else:
                    continue
            if text:
                yield text
            if chunk.get("done"):
                break


def pull_stream(model: str) -> Iterator[dict]:
    req = urllib.request.Request(OLLAMA + "/api/pull", data=json.dumps({"model": model, "stream": True}).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3600) as r:
        for raw in r:
            if raw.strip():
                yield json.loads(raw)
