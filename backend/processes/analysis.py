"""Clasificación, evaluación de señales y explicaciones de procesos.

Principio central (requisito del proyecto): ningún proceso se califica como
malicioso solo por ser desconocido, no tener firma o consumir muchos recursos.
Las señales se combinan y cada conclusión indica si es un dato COMPROBADO
(medido o verificado) o una conclusión ESTIMADA (inferida a partir de reglas).
"""

from __future__ import annotations

import os
import re
import threading

import psutil

from .knowledge import PROTECTED, lookup

# Estados de hallazgo del proyecto (§12 del documento de requisitos)
INFORMATIVO = "informativo"
NORMAL = "normal"
CONSUMO = "consumo_elevado"
REVISION = "requiere_revision"
SOSPECHOSA = "actividad_sospechosa"
AMENAZA = "amenaza_detectada"
INSUFICIENTE = "info_insuficiente"

SEVERITY = [NORMAL, INFORMATIVO, INSUFICIENTE, CONSUMO, REVISION, SOSPECHOSA, AMENAZA]

CPU_HIGH_AVG = 25.0  # % del equipo, promedio de 60 s
MEM_HIGH_SHARE = 15.0  # % de la RAM total

_TEMP_PARTS = ("\\appdata\\local\\temp\\", "\\windows\\temp\\", "\\$recycle.bin\\", "\\users\\public\\")
_SECRET = re.compile(r"(?i)((?:password|passwd|pwd|token|secret|apikey|api_key|key)\s*[=:]\s*)(\S+)")


class PathCache:
    """Ruta del ejecutable por (PID, hora de creación); solo se consulta una vez por proceso."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._paths: dict[tuple, str | None] = {}

    def update(self, snaps) -> None:
        alive = set()
        for s in snaps:
            key = (s.pid, s.create_time)
            alive.add(key)
            if key in self._paths:
                continue
            try:
                exe = psutil.Process(s.pid).exe() or None
            except (psutil.Error, OSError):
                exe = None
            # Procesos del núcleo devuelven nombres sin ruta ("Registry", "MemCompression").
            if exe and not os.path.isabs(exe):
                exe = None
            with self._lock:
                self._paths[key] = exe
        with self._lock:
            for k in list(self._paths):
                if k not in alive:
                    del self._paths[k]

    def get(self, pid: int, create_time: float | None) -> str | None:
        with self._lock:
            return self._paths.get((pid, create_time))


def category(snap, window_pids: set[int]) -> str:
    known = lookup(snap.name)
    if snap.pid in (0, 4) or (known and known["rol"] == "critico" and known["carpeta"] is None):
        return "sistema"
    if snap.pid in window_pids:
        return "aplicacion"
    if snap.session_id == 0:
        return "servicio"
    return "segundo_plano"


CATEGORY_ES = {
    "sistema": "Núcleo de Windows",
    "servicio": "Servicio (segundo plano del sistema)",
    "aplicacion": "Aplicación abierta",
    "segundo_plano": "En segundo plano",
}


def redact(cmdline: str) -> str:
    """Oculta posibles contraseñas o tokens en la línea de comandos."""
    return _SECRET.sub(lambda m: m.group(1) + "•••", cmdline)


def signals(snap, path: str | None, sig: dict | None, stats: dict | None, mem_total: int | None, detections: list | None = None) -> list[dict]:
    """Señales observadas en un proceso, cada una con su evidencia y su tipo."""
    out: list[dict] = []
    name = (snap.name or "").lower()
    known = lookup(name)
    low_path = (path or "").lower()
    if snap.pid == 0:
        return out  # «System Idle Process» representa tiempo libre del procesador
    kernel = known is not None and known["rol"] == "critico" and known["carpeta"] is None

    if detections:
        for d in detections:
            out.append(
                {
                    "code": "defender",
                    "estado": AMENAZA,
                    "titulo": "Microsoft Defender registró una detección para este archivo",
                    "evidencia": f"{d.get('amenaza', 'Amenaza')} · {d.get('fecha', '')}",
                    "fuente": "Microsoft Defender",
                    "tipo": "comprobado",
                }
            )

    if path is None and not kernel:
        out.append(
            {
                "code": "sin_ruta",
                "estado": INSUFICIENTE,
                "titulo": "No se pudo leer la ubicación del programa",
                "evidencia": "Windows no permite consultar este proceso sin permisos de administrador.",
                "fuente": "ScriptLens",
                "tipo": "comprobado",
            }
        )

    if path and known and known.get("carpeta"):
        folder = os.path.dirname(low_path)
        if folder != known["carpeta"]:
            out.append(
                {
                    "code": "ubicacion_inesperada",
                    "estado": REVISION,
                    "titulo": "El nombre coincide con un componente de Windows, pero está en otra carpeta",
                    "evidencia": f"Ubicación real: {path}. Ubicación esperada: {known['carpeta']}",
                    "fuente": "Base de conocimiento de ScriptLens",
                    "tipo": "estimado",
                }
            )

    if path and any(p in low_path for p in _TEMP_PARTS):
        out.append(
            {
                "code": "ubicacion_temporal",
                "estado": REVISION,
                "titulo": "Se ejecuta desde una carpeta temporal o pública",
                "evidencia": path,
                "fuente": "ScriptLens",
                "tipo": "comprobado",
            }
        )
    elif path and "\\downloads\\" in low_path:
        out.append(
            {
                "code": "ubicacion_descargas",
                "estado": INFORMATIVO,
                "titulo": "Se ejecuta desde la carpeta Descargas",
                "evidencia": path,
                "fuente": "ScriptLens",
                "tipo": "comprobado",
            }
        )

    if sig:
        if sig["estado"] in ("alterada", "no_confiable"):
            out.append(
                {
                    "code": "firma_invalida",
                    "estado": REVISION,
                    "titulo": sig["descripcion_estado"],
                    "evidencia": f"Firmante: {sig.get('firmante') or 'desconocido'}",
                    "fuente": "Windows (Authenticode)",
                    "tipo": "comprobado",
                }
            )
        elif sig["estado"] == "sin_firma":
            out.append(
                {
                    "code": "sin_firma",
                    "estado": INFORMATIVO,
                    "titulo": "El programa no tiene firma digital",
                    "evidencia": "Muchos programas legítimos (scripts, herramientas pequeñas) no se firman. Por sí solo no indica peligro.",
                    "fuente": "Windows (Authenticode)",
                    "tipo": "comprobado",
                }
            )

    if stats and stats.get("cpu_avg") is not None and stats["cpu_avg"] >= CPU_HIGH_AVG and stats["samples"] >= 10:
        out.append(
            {
                "code": "cpu_sostenida",
                "estado": CONSUMO,
                "titulo": "Usa mucho procesador de forma continua",
                "evidencia": f"Promedio {stats['cpu_avg']} % del equipo en {stats['seconds']} s (máximo {stats['cpu_max']} %).",
                "fuente": "Mediciones de ScriptLens",
                "tipo": "comprobado",
            }
        )
    if mem_total and snap.memory_rss and snap.memory_rss / mem_total * 100 >= MEM_HIGH_SHARE:
        out.append(
            {
                "code": "memoria_alta",
                "estado": CONSUMO,
                "titulo": "Ocupa una parte importante de la memoria RAM",
                "evidencia": f"{snap.memory_rss / mem_total * 100:.1f} % de la RAM total.",
                "fuente": "Mediciones de ScriptLens",
                "tipo": "comprobado",
            }
        )

    # Combinación de señales: suplantación de nombre + sin firma válida → actividad sospechosa.
    codes = {s["code"] for s in out}
    if "ubicacion_inesperada" in codes and (sig is None or sig["estado"] != "valida"):
        out.append(
            {
                "code": "posible_suplantacion",
                "estado": SOSPECHOSA,
                "titulo": "Posible suplantación de un componente de Windows",
                "evidencia": "Usa el nombre de un proceso del sistema, está fuera de su carpeta y no tiene una firma válida verificada.",
                "fuente": "Reglas de ScriptLens",
                "tipo": "estimado",
            }
        )
    return out


def overall(signal_list: list[dict]) -> str:
    """Estado global: el más severo, pero solo informativo si no hay nada relevante."""
    if not signal_list:
        return NORMAL
    worst = max(signal_list, key=lambda s: SEVERITY.index(s["estado"]))["estado"]
    return worst if worst != INFORMATIVO else NORMAL


def can_terminate(name: str, pid: int, own_pids: set[int]) -> tuple[bool, str]:
    n = (name or "").lower()
    if pid in (0, 4) or n in PROTECTED:
        return False, "Es un componente esencial o de seguridad de Windows; ScriptLens no permite finalizarlo."
    if pid in own_pids:
        return False, "Es parte de ScriptLens."
    return True, ""


def explain(detail: dict) -> list[dict]:
    """Respuestas a las preguntas frecuentes sobre un proceso, en lenguaje sencillo."""
    name = detail["name"] or "Este proceso"
    known = lookup(detail["name"])
    sig = detail.get("signature") or {}
    stats = detail.get("stats") or {}
    sigs = detail.get("signals") or []
    qa: list[dict] = []

    if known:
        que, tipo = known["que"], "estimado"
    elif sig.get("descripcion"):
        que, tipo = f"Según la información del archivo: «{sig['descripcion']}»" + (f" de {sig['editor']}." if sig.get("editor") else "."), "comprobado"
    else:
        que, tipo = "ScriptLens no tiene información sobre este programa y el archivo no incluye una descripción.", "estimado"
    qa.append({"pregunta": "¿Qué hace este proceso?", "respuesta": que, "tipo": tipo})

    parent = detail.get("parent")
    cat = detail.get("category")
    if cat == "servicio":
        why = "Es un servicio: Windows o un programa instalado lo inicia en segundo plano, normalmente al encender el equipo."
    elif cat == "aplicacion":
        why = "Es una aplicación con una ventana abierta."
    elif cat == "sistema":
        why = "Forma parte del funcionamiento interno de Windows."
    else:
        why = "Funciona en segundo plano dentro de su sesión."
    if parent:
        why += f" Lo inició «{parent['name']}» (PID {parent['pid']})."
    qa.append({"pregunta": "¿Por qué está ejecutándose?", "respuesta": why, "tipo": "comprobado" if parent else "estimado"})

    mem = detail.get("memory_rss")
    cpu_txt = f"{stats['cpu_avg']} % de CPU en promedio durante el último minuto" if stats.get("cpu_avg") is not None else "CPU aún sin suficientes mediciones"
    mem_txt = f"{mem / 1024**2:.0f} MB de RAM" if mem else "memoria no disponible"
    qa.append({"pregunta": "¿Cuánto consume?", "respuesta": f"{mem_txt}; {cpu_txt}.", "tipo": "comprobado"})

    rol = known["rol"] if known else None
    if rol in ("critico", "seguridad"):
        need, close = "Sí. Es necesario para que Windows funcione o esté protegido.", "No. ScriptLens no permite cerrarlo."
        after = "Windows podría bloquearse, cerrar la sesión, reiniciarse o quedar desprotegido."
    elif rol == "sistema":
        need = "Es un componente de Windows. Puede no ser imprescindible, pero alguna función del sistema depende de él."
        close = "No se recomienda. Si lo cierra, Windows normalmente lo vuelve a iniciar."
        after = "La función asociada (por ejemplo, búsqueda o impresión) podría dejar de responder temporalmente."
    elif cat == "aplicacion":
        need = "No. Es un programa abierto por el usuario."
        close = "Sí, preferiblemente desde su propia ventana o con «Solicitar cierre», que le permite guardar su trabajo."
        after = "Se cerrará el programa. Si tenía trabajo sin guardar, podría perderse si se finaliza a la fuerza."
    else:
        need = "No parece ser un componente de Windows." if sig.get("binario_windows") is False else "No hay información suficiente para afirmarlo."
        close = "Posiblemente, pero investigue primero qué programa lo instaló. Use «Finalizar» solo si sabe qué es."
        after = "El programa que depende de él podría dejar de funcionar o volver a iniciarlo."
    qa.append({"pregunta": "¿Es necesario para Windows?", "respuesta": need, "tipo": "estimado"})
    qa.append({"pregunta": "¿Puedo cerrarlo?", "respuesta": close, "tipo": "estimado"})
    qa.append({"pregunta": "¿Qué sucede si lo cierro?", "respuesta": after, "tipo": "estimado"})

    autostart = detail.get("autostart")
    if autostart is None:
        qa.append({"pregunta": "¿Se inicia automáticamente?", "respuesta": "Consulte la sección Seguridad → Inicio automático para ver los programas que arrancan con Windows.", "tipo": "estimado"})
    elif autostart:
        qa.append({"pregunta": "¿Se inicia automáticamente?", "respuesta": "Sí: " + "; ".join(a["origen"] for a in autostart), "tipo": "comprobado"})
    else:
        qa.append({"pregunta": "¿Se inicia automáticamente?", "respuesta": "No aparece en las entradas de inicio automático revisadas (Registro Run y carpeta Inicio).", "tipo": "comprobado"})

    relevant = [s for s in sigs if s["estado"] in (REVISION, SOSPECHOSA, AMENAZA)]
    if relevant:
        susp = " ".join(f"• {s['titulo']}." for s in relevant)
        qa.append({"pregunta": "¿Tiene características sospechosas?", "respuesta": susp + " Esto indica que conviene revisarlo, no que sea necesariamente malicioso.", "tipo": "estimado"})
    else:
        qa.append({"pregunta": "¿Tiene características sospechosas?", "respuesta": "No se observaron señales de riesgo con la evidencia disponible.", "tipo": "estimado"})

    if any(s["code"] == "defender" for s in sigs):
        qa.append({"pregunta": "¿Ha sido detectado por Microsoft Defender?", "respuesta": "Sí. Revise la detección en Seguridad de Windows y siga sus recomendaciones.", "tipo": "comprobado"})
    else:
        qa.append({"pregunta": "¿Ha sido detectado por Microsoft Defender?", "respuesta": "No hay detecciones registradas de Defender para este archivo en el historial accesible.", "tipo": "comprobado" if detail.get("defender_checked") else "estimado"})
    return qa
