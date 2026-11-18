"""Cliente mínimo de Ollama (http://127.0.0.1:11434). Solo localhost: nada sale del equipo.

Optimizaciones de la versión 0.2 (medidas en docs/pruebas/asistente):
- El estado de Ollama se guarda 15 s en caché: antes se consultaba dos veces por pregunta.
- Opciones por modo: «rápida» usa menos contexto y respuestas más cortas que «detallada».
- ``keep_alive`` de 30 min para reutilizar el modelo ya cargado entre preguntas.
- Cancelación real: al cancelar se cierra la conexión y Ollama deja de generar.
- Estadísticas reales de Ollama (tokens, duración, carga) y detección de GPU/CPU (``/api/ps``).
"""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from typing import Iterator

OLLAMA = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3:4b-instruct"
FAST_MODEL = "qwen3:1.7b"
KEEP_ALIVE = "30m"
# Modelos sugeridos (tamaño aproximado de descarga, Q4_K_M)
MODELS = [
    {"id": "qwen3:4b-instruct", "nombre": "Qwen3 4B Instruct", "descarga_gb": 2.5, "ram_gb": 4.5, "nota": "Modo detallado. Respuestas directas, sin razonamiento extenso.", "modo": "detallada"},
    {"id": "qwen3:1.7b", "nombre": "Qwen3 1.7B", "descarga_gb": 1.4, "ram_gb": 2.5, "nota": "Modo rápido y equipos con 8 GB de RAM o menos. Menos preciso.", "modo": "rapida"},
    {"id": "qwen3:4b", "nombre": "Qwen3 4B (razonamiento)", "descarga_gb": 2.5, "ram_gb": 4.5, "nota": "Razona antes de responder: mucho más lento.", "modo": "detallada"},
]

# Contexto y longitud máxima por modo. Los datos que se envían caben de sobra en 4096 tokens.
OPTIONS = {
    "rapida": {"temperature": 0.2, "num_ctx": 4096, "num_predict": 320},
    "detallada": {"temperature": 0.2, "num_ctx": 8192, "num_predict": 700},
}

_cache: dict = {"t": 0.0, "v": None}
_cache_lock = threading.Lock()
STATUS_TTL = 15.0


def _get(path: str, timeout: float = 3.0):
    with urllib.request.urlopen(OLLAMA + path, timeout=timeout) as r:
        return json.loads(r.read())


def _status() -> dict:
    try:
        version = _get("/api/version", 1.5)["version"]
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        return {"instalado_o_activo": False, "version": None, "modelos": []}
    try:
        models = [m["name"] for m in _get("/api/tags").get("models", [])]
    except (urllib.error.URLError, OSError, ValueError):
        models = []
    return {"instalado_o_activo": True, "version": version, "modelos": models}


def status(cached: bool = True) -> dict:
    with _cache_lock:
        if cached and _cache["v"] is not None and time.monotonic() - _cache["t"] < STATUS_TTL:
            return _cache["v"]
    v = _status()
    with _cache_lock:
        _cache.update(t=time.monotonic(), v=v)
    return v


def invalidate_status() -> None:
    with _cache_lock:
        _cache["v"] = None


def has_model(model: str, st: dict | None = None) -> bool:
    st = st or status()
    return st["instalado_o_activo"] and any(m == model or m == model + ":latest" for m in st["modelos"])


def loaded() -> list[dict]:
    """Modelos cargados en memoria y si usan GPU (``size_vram``) o solo CPU."""
    try:
        models = _get("/api/ps", 2).get("models", [])
    except (urllib.error.URLError, OSError, ValueError):
        return []
    out = []
    for m in models:
        size, vram = m.get("size") or 0, m.get("size_vram") or 0
        pct = round(100 * vram / size) if size else 0
        out.append({"modelo": m["name"], "ram_mb": round(size / 2**20), "vram_mb": round(vram / 2**20), "procesador": "GPU" if pct >= 90 else "CPU" if pct == 0 else f"{pct} % GPU / {100 - pct} % CPU", "expira": m.get("expires_at")})
    return out


def warmup(model: str) -> bool:
    """Carga el modelo en memoria sin generar texto, para que la primera pregunta no espere la carga."""
    body = json.dumps({"model": model, "keep_alive": KEEP_ALIVE}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(OLLAMA + "/api/generate", data=body, headers={"Content-Type": "application/json"}), timeout=120).read()
        return True
    except OSError:
        return False


def chat_stream(model: str, messages: list[dict], modo: str = "detallada", stats: dict | None = None, cancel: threading.Event | None = None, num_predict: int | None = None) -> Iterator[str]:
    """Genera fragmentos de texto. Omite cualquier bloque de razonamiento <think>.

    ``stats`` recibe los contadores reales de Ollama al terminar. Si ``cancel`` se activa,
    se cierra la conexión (Ollama detiene la generación) y el generador termina.
    """
    opts = dict(OPTIONS.get(modo, OPTIONS["detallada"]))
    if num_predict:
        opts["num_predict"] = num_predict
    body = json.dumps({"model": model, "messages": messages, "stream": True, "think": False, "keep_alive": KEEP_ALIVE, "options": opts}).encode("utf-8")
    req = urllib.request.Request(OLLAMA + "/api/chat", data=body, headers={"Content-Type": "application/json"})
    in_think = False
    r = urllib.request.urlopen(req, timeout=300)
    try:
        for raw in r:
            if cancel is not None and cancel.is_set():
                if stats is not None:
                    stats["cancelada"] = True
                return
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
                if stats is not None:
                    ns = 1e9
                    stats.update(
                        eval_count=chunk.get("eval_count"),
                        eval_s=round((chunk.get("eval_duration") or 0) / ns, 2),
                        prompt_eval_count=chunk.get("prompt_eval_count"),
                        prompt_eval_s=round((chunk.get("prompt_eval_duration") or 0) / ns, 2),
                        load_s=round((chunk.get("load_duration") or 0) / ns, 2),
                        total_s=round((chunk.get("total_duration") or 0) / ns, 2),
                    )
                break
    finally:
        r.close()  # cerrar la conexión también detiene la generación en Ollama


def pull_stream(model: str) -> Iterator[dict]:
    req = urllib.request.Request(OLLAMA + "/api/pull", data=json.dumps({"model": model, "stream": True}).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3600) as r:
        for raw in r:
            if raw.strip():
                yield json.loads(raw)
    invalidate_status()
