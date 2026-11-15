"""Diagnóstico de rendimiento en lenguaje sencillo.

Reglas deterministas sobre métricas medidas. Se distingue entre consumo
sostenido (promedio en una ventana) y picos instantáneos, para no alarmar al
usuario por un salto momentáneo.
"""

from __future__ import annotations

from dataclasses import dataclass

from .sampler import Sample, average

# Umbrales documentados en docs/arquitectura/diagnostico.md
CPU_SUSTAINED = 80.0
CPU_ELEVATED = 60.0
RAM_HIGH = 85.0
RAM_ELEVATED = 75.0
DISK_FULL = 90.0
MIN_WINDOW_SAMPLES = 20  # ~20 s de datos antes de hablar de "sostenido"


@dataclass
class Finding:
    code: str
    estado: str  # informativo | normal | consumo_elevado | requiere_revision | info_insuficiente
    titulo: str
    explicacion: str
    evidencia: str
    recomendacion: str

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def summarize(window: list[Sample], long_window: list[Sample], disks: list[dict]) -> dict:
    current = window[-1] if window else None
    findings: list[Finding] = []

    if len(window) < MIN_WINDOW_SAMPLES:
        findings.append(
            Finding(
                "datos_insuficientes",
                "info_insuficiente",
                "Recopilando mediciones",
                "ScriptLens necesita unos segundos de mediciones para distinguir un consumo sostenido de un pico momentáneo.",
                f"{len(window)} de {MIN_WINDOW_SAMPLES} mediciones necesarias.",
                "Espere unos segundos con la aplicación abierta.",
            )
        )

    cpu_avg = average(window, "cpu_percent")
    ram_avg = average(window, "mem_percent")

    if cpu_avg is not None and len(window) >= MIN_WINDOW_SAMPLES:
        if cpu_avg >= CPU_SUSTAINED:
            findings.append(
                Finding(
                    "cpu_sostenida",
                    "consumo_elevado",
                    "El procesador está muy ocupado de forma continua",
                    "Durante el último minuto el procesador ha trabajado casi al máximo. Los programas pueden responder más lento.",
                    f"Promedio de CPU en el último minuto: {cpu_avg} %.",
                    "Revise en «Procesos» qué programa consume más CPU de forma sostenida y ciérrelo si no lo necesita.",
                )
            )
        elif cpu_avg >= CPU_ELEVATED:
            findings.append(
                Finding(
                    "cpu_elevada",
                    "informativo",
                    "El procesador tiene una carga moderada",
                    "Hay programas trabajando activamente. Es normal mientras usa aplicaciones exigentes.",
                    f"Promedio de CPU en el último minuto: {cpu_avg} %.",
                    "No requiere acción si el equipo responde bien.",
                )
            )

    if ram_avg is not None and len(window) >= MIN_WINDOW_SAMPLES:
        if ram_avg >= RAM_HIGH:
            findings.append(
                Finding(
                    "ram_alta",
                    "consumo_elevado",
                    "La memoria RAM está casi llena",
                    "La memoria RAM almacena temporalmente los datos que utilizan los programas abiertos. Si está muy ocupada, el computador puede responder más lentamente.",
                    f"Uso promedio de RAM en el último minuto: {ram_avg} %.",
                    "Cierre pestañas o programas que no esté usando. En «Procesos» verá cuáles ocupan más memoria.",
                )
            )
        elif ram_avg >= RAM_ELEVATED:
            findings.append(
                Finding(
                    "ram_elevada",
                    "informativo",
                    "La memoria RAM tiene un uso considerable",
                    "Todavía hay margen, pero abrir muchos más programas podría hacer el equipo más lento.",
                    f"Uso promedio de RAM en el último minuto: {ram_avg} %.",
                    "No requiere acción inmediata.",
                )
            )

    for d in disks:
        if d.get("percent", 0) >= DISK_FULL:
            findings.append(
                Finding(
                    f"disco_lleno_{d['mountpoint']}",
                    "requiere_revision",
                    f"La unidad {d['mountpoint']} tiene poco espacio libre",
                    "Con poco espacio, Windows puede tener dificultades para actualizarse y algunos programas pueden fallar.",
                    f"Ocupado: {d['percent']} %.",
                    "Revise qué archivos grandes puede mover o eliminar usted mismo. ScriptLens no borra archivos automáticamente.",
                )
            )

    has_issue = any(f.estado in ("consumo_elevado", "requiere_revision") for f in findings)
    enough = len(window) >= MIN_WINDOW_SAMPLES
    if enough and not has_issue:
        findings.insert(
            0,
            Finding(
                "estado_normal",
                "normal",
                "Su computador funciona con normalidad",
                "Según las mediciones del último minuto, el procesador y la memoria tienen margen disponible.",
                f"CPU promedio {cpu_avg} %, RAM promedio {ram_avg} %.",
                "No se requiere ninguna acción.",
            ),
        )

    return {
        "current": current.to_dict() if current else None,
        "window_seconds": len(window),
        "averages": {
            "cpu_1m": cpu_avg,
            "ram_1m": ram_avg,
            "cpu_long": average(long_window, "cpu_percent"),
            "ram_long": average(long_window, "mem_percent"),
            "long_samples": len(long_window),
        },
        "findings": [f.to_dict() for f in findings],
    }
