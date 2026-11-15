"""Enrutador de intenciones: decide qué herramientas de solo lectura consultar.

Es determinista (reglas sobre la pregunta normalizada), de modo que el modelo de
lenguaje nunca elige ni parametriza herramientas por sí mismo.
"""

from __future__ import annotations

import re
import unicodedata


def norm(text: str) -> str:
    t = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


# (intención, patrones, herramientas)
INTENTS: list[tuple[str, list[str], list[str]]] = [
    ("script", [r"\bscript", r"linea por linea", r"\.bat\b", r"\.ps1\b", r"powershell", r"\bcmd\b"], ["ultimo_script"]),
    ("cambios", [r"cambi", r"desde el ultimo", r"antes que", r"mas (ram|memoria|cpu) que antes", r"compar"], ["cambios", "resumen_rendimiento"]),
    ("desactivar_inicio", [r"desactiv\w* .*inicio", r"si desactivo", r"programa de inicio"], ["inicio_automatico"]),
    ("inicio", [r"inicia\w* con windows", r"inicio automatico", r"arranque", r"al encender", r"startup"], ["inicio_automatico"]),
    ("tareas", [r"tarea[s]? programada", r"programador de tareas", r"por que aparecio .*tarea"], ["tareas"]),
    ("amenazas", [r"amenaza", r"virus", r"malware", r"sospechos", r"defender", r"segur", r"hackead", r"infectad"], ["seguridad", "en_revision"]),
    ("alerta", [r"\balerta", r"\baviso", r"hallazgo", r"advertencia", r"notificacion"], ["en_revision", "seguridad", "resumen_rendimiento"]),
    ("revision", [r"revision", r"revisar", r"raro", r"extrano", r"peligros", r"investiga", r"desconocid", r"no (lo |la )?conozco"], ["en_revision", "seguridad"]),
    ("cerrar", [r"puedo cerrar", r"cerrar sin", r"que (programas|aplicaciones) (puedo )?cerrar", r"liberar"], ["cerrables", "resumen_rendimiento"]),
    ("segundo_plano", [r"segundo plano", r"fondo", r"background", r"servicio"], ["segundo_plano"]),
    ("ram", [r"\bram\b", r"memoria"], ["procesos_top_memoria", "resumen_rendimiento"]),
    ("cpu", [r"\bcpu\b", r"procesador"], ["procesos_top_cpu", "resumen_rendimiento"]),
    ("disco", [r"disco", r"almacenamiento", r"espacio", r"ocupando", r"lleno"], ["disco"]),
    ("lento", [r"lent", r"rendimiento", r"mejorar", r"acelerar", r"rapido", r"optimiz", r"se traba", r"congel"], ["resumen_rendimiento", "procesos_top_memoria", "procesos_top_cpu", "disco"]),
]

_PROC_NAME = re.compile(r"([\w.\-]+\.exe)\b", re.I)
_QUE_ES = re.compile(r"(?:que (?:es|significa|hace)|para que sirve)\s+(?:el proceso\s+|este proceso\s+|el programa\s+)?[«\"']?([\w.\-]+)", re.I)


# Palabras que pueden seguir a «qué significa…» sin ser el nombre de un proceso.
_NOT_A_PROCESS = {
    "la", "el", "lo", "los", "las", "un", "una", "esto", "eso", "este", "esta", "ese", "esa", "estos", "estas",
    "aquel", "aquella", "mi", "su", "que", "ram", "cpu", "memoria", "procesador", "disco", "alerta", "aviso",
}


def route(question: str) -> dict:
    q = norm(question)
    tools: list[str] = []
    intents: list[str] = []
    for name, patterns, t in INTENTS:
        if any(re.search(p, q) for p in patterns):
            intents.append(name)
            for x in t:
                if x not in tools:
                    tools.append(x)
    proceso = None
    m = _PROC_NAME.search(question)
    if m:
        proceso = m.group(1).strip()
    else:
        m2 = _QUE_ES.search(q)
        if m2 and m2.group(1) not in _NOT_A_PROCESS:
            proceso = m2.group(1)
    if proceso:
        intents.insert(0, "proceso")
    if not tools and not proceso:
        intents.append("general")
        tools = ["resumen_rendimiento"]
    return {"intenciones": intents, "herramientas": tools[:5], "proceso": proceso}
