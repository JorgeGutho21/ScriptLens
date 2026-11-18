"""Respuesta inmediata: preguntas sencillas contestadas con los datos medidos, sin modelo.

Solo se usa cuando la pregunta pide un dato concreto (CPU, RAM, disco, tiempo encendido o los
programas que más consumen) y no pide explicación, causa ni recomendación. En ese caso el
modelo no aporta información nueva y solo añadiría espera.
"""

from __future__ import annotations

from .router import norm

SIMPLE_INTENTS = {"cpu", "ram", "disco", "uptime"}
# Palabras que indican que la persona quiere una explicación, no solo el dato.
NEEDS_REASONING = ("por que", "porque", "como puedo", "como hago", "mejorar", "deberia", "recomienda", "explica", "que significa", "es normal", "es peligroso", "conviene", "solucion", "arreglar", "lento")


def can_answer(route: dict, question: str) -> bool:
    intents = set(route["intenciones"])
    if not intents or not intents <= SIMPLE_INTENTS or route.get("proceso"):
        return False
    q = norm(question)
    return not any(w in q for w in NEEDS_REASONING)


def _list(progs: list[dict], field: str, unit: str, n: int = 3) -> str:
    return ", ".join(f"{p['nombre']} ({p[field]}{unit})" for p in progs[:n])


def answer(route: dict, data: dict) -> str:
    intents = route["intenciones"]
    r = data.get("resumen_rendimiento") or {}
    parts: list[str] = []
    if "cpu" in intents:
        parts.append(f"El procesador está ahora al {r.get('cpu_ahora_pct')} % (promedio del último minuto: {r.get('cpu_prom_1min_pct')} %).")
        top = (data.get("procesos_top_cpu") or {}).get("programas") or []
        if top:
            parts.append(f"Los programas que más procesador usan son: {_list(top, 'cpu_prom_1min_pct', ' %')}.")
    if "ram" in intents:
        parts.append(f"La memoria RAM está al {r.get('ram_ahora_pct')} %: {r.get('ram_usada_gb')} GB en uso de {r.get('ram_total_gb')} GB.")
        top = (data.get("procesos_top_memoria") or {}).get("programas") or []
        if top:
            parts.append(f"Los programas que más memoria usan son: {_list(top, 'ram_mb', ' MB')}.")
    if "disco" in intents:
        d = data.get("disco") or {}
        units = d.get("unidades") or []
        if units:
            parts.append("Almacenamiento: " + "; ".join(f"unidad {u['unidad']} con {u['usado_pct']} % usado y {u['libre_gb']} GB libres" for u in units) + ".")
    if "uptime" in intents and r:
        parts.append(f"La PC lleva {r['tiempo_encendido_h']} horas encendida desde el último arranque de Windows ({r['ultimo_arranque']}). Si usa suspensión o el Inicio rápido, ese tiempo puede incluir periodos en reposo.")
    parts.append("Respuesta inmediata con los datos medidos ahora. Si quiere una explicación o recomendaciones, pregunte por ejemplo «¿por qué?» o «¿cómo lo mejoro?».")
    return " ".join(parts)
