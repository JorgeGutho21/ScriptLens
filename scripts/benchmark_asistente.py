"""Medición del asistente: tiempo hasta el primer fragmento, total, tokens/s, carga y memoria.

Uso (PowerShell, raíz del repositorio):
    .\\.venv\\Scripts\\python scripts\\benchmark_asistente.py --etiqueta antes --modelo qwen3:4b-instruct
    .\\.venv\\Scripts\\python scripts\\benchmark_asistente.py --etiqueta despues --modo rapida --modelo qwen3:1.7b

Mide el flujo completo que vive el usuario (recopilar datos → modelo → verificación) con las
diez preguntas de referencia. Los resultados se guardan en docs/pruebas/asistente/<etiqueta>.json.
No inventa cifras: si Ollama no está activo, lo registra así.
"""

from __future__ import annotations

import argparse
import inspect
import json
import platform
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.assistant import llm, service  # noqa: E402
from backend.core.api import Engine  # noqa: E402
from backend.core.config import Settings  # noqa: E402

PREGUNTAS = [
    "¿Por qué mi computador está lento?",
    "¿Qué programa consume más RAM?",
    "¿Qué proceso consume más CPU?",
    "¿Qué tareas se ejecutan en segundo plano?",
    "¿Qué aplicaciones puedo cerrar sin afectar Windows?",
    "¿Qué procesos requieren revisión?",
    "¿Hay programas sospechosos?",
    "¿Qué programas inician con Windows?",
    "¿Cómo puedo mejorar el rendimiento?",
    "¿Qué está ocupando el disco?",
]


def ollama_ps() -> list[dict]:
    try:
        with urllib.request.urlopen(llm.OLLAMA + "/api/ps", timeout=3) as r:
            return [{"modelo": m["name"], "ram_total_mb": round(m["size"] / 2**20), "vram_mb": round(m.get("size_vram", 0) / 2**20)} for m in json.loads(r.read()).get("models", [])]
    except OSError:
        return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--etiqueta", required=True)
    ap.add_argument("--modelo", default=llm.DEFAULT_MODEL, help="vacío = el servicio elige según el modo")
    ap.add_argument("--modo", default=None, help="inmediata | rapida | detallada (solo tras la optimización)")
    ap.add_argument("--descargar", action="store_true", help="descarga el modelo de memoria antes de empezar (mide carga en frío)")
    a = ap.parse_args()

    data_dir = ROOT / "build" / "bench-data"
    engine = Engine(Settings(token="bench", data_dir=data_dir))
    engine.start()
    print("Calentando el motor (15 s de mediciones y revisión de seguridad)…")
    time.sleep(15)
    engine.security.run()  # la primera revisión de seguridad tarda; no se carga al modelo
    if a.descargar:
        body = json.dumps({"model": a.modelo or llm.FAST_MODEL, "keep_alive": 0}).encode()
        try:
            urllib.request.urlopen(urllib.request.Request(llm.OLLAMA + "/api/generate", data=body, headers={"Content-Type": "application/json"}), timeout=30).read()
        except OSError:
            pass

    supports_mode = "modo" in inspect.signature(service.ask).parameters
    rows = []
    for q in PREGUNTAS:
        kwargs = {"modo": a.modo} if supports_mode and a.modo else {}
        t0 = time.perf_counter()
        first = None
        chunks = 0
        done = {}
        for ev in service.ask(engine, q, a.modelo or None, [], True, **kwargs):
            if ev["type"] == "token":
                chunks += 1
                if first is None:
                    first = time.perf_counter() - t0
            elif ev["type"] == "done":
                done = ev
        total = time.perf_counter() - t0
        st = done.get("estadisticas") or {}
        gen = st.get("eval_s")
        row = {
            "pregunta": q,
            "modo": done.get("modo"),
            "modelo": done.get("modelo"),
            "primer_fragmento_s": round(first, 2) if first is not None else None,
            "total_s": round(total, 2),
            "fragmentos": chunks,
            "tokens_generados": st.get("eval_count"),
            "tokens_por_s": round(st["eval_count"] / gen, 1) if st.get("eval_count") and gen else (round(chunks / (total - first), 1) if first and chunks > 1 and total > first else None),
            "carga_modelo_s": st.get("load_s"),
            "tokens_prompt": st.get("prompt_eval_count"),
            "cifras": done.get("verificacion", {}).get("cifras"),
            "no_verificadas": done.get("verificacion", {}).get("no_verificadas"),
            "respuesta": (done.get("answer") or "")[:400],
        }
        rows.append(row)
        print(f"{row['total_s']:6.1f} s · 1.er fragmento {row['primer_fragmento_s']} s · {row['tokens_por_s']} tok/s · {row['modo']} · {q}")
    engine.stop()

    def med(key):
        v = sorted(r[key] for r in rows if r[key] is not None)
        return v[len(v) // 2] if v else None

    out = {
        "etiqueta": a.etiqueta,
        "fecha": time.strftime("%Y-%m-%d %H:%M"),
        "equipo": {"so": f"{platform.system()} {platform.release()} {platform.version()}", "procesador": platform.processor()},
        "ollama": llm.status(),
        "modelo": a.modelo,
        "modo": a.modo,
        "memoria_ollama": ollama_ps(),
        "mediana": {k: med(k) for k in ("primer_fragmento_s", "total_s", "tokens_por_s")},
        "verificadas": sum(1 for r in rows if r["no_verificadas"] == []),
        "resultados": rows,
    }
    dest = ROOT / "docs" / "pruebas" / "asistente"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / f"{a.etiqueta}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Mediana:", out["mediana"], "· memoria:", out["memoria_ollama"], "· verificadas:", out["verificadas"], "/", len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
