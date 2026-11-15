"""Orquestación del análisis estático de un script.

Resultados independientes, como exige el proyecto:
1. Clasificación estadística (regresión logística).
2. Reglas detectadas (catálogo + ATT&CK).
3. Severidad contextual (reglas de contexto: ámbito, destino, ofuscación).
4. Evidencia disponible (líneas concretas).
5. Limitaciones del análisis.

Este módulo NUNCA ejecuta el script: solo manipula texto.
"""

from __future__ import annotations

import json
import re
import time
from functools import lru_cache
from pathlib import Path

import joblib

from .catalog import CATEGORIA_ES, OPERACION, hallazgos
from .deobfuscate import decoded_payloads, normalize_line, obfuscation_signals
from .explain import explain_lines
from .flow import estructuras, flujo_bat
from .model import UMBRAL_SENSIBLE, clasificar_por_reglas, decision_hibrida, top_rasgos
from .reading import LIMITE, decode, tipo_por_nombre

DATA = Path(__file__).parent / "data"


@lru_cache(maxsize=1)
def _model():
    path = DATA / "modelo_scriptlens.joblib"
    if not path.exists():
        return None
    return joblib.load(path)


@lru_cache(maxsize=1)
def _attack() -> dict:
    return json.loads((DATA / "attack_subset.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def model_metrics() -> dict | None:
    p = DATA / "metricas_clasificador.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


_SYSTEM_TARGET = re.compile(r"(?i)c:\\windows|%windir%|%systemroot%|system32|\\program files|hklm\\|hkey_local_machine|HKLM:")
_USER_TARGET = re.compile(r"(?i)%temp%|%userprofile%|\$env:(temp|userprofile)|hkcu|hkey_current_user|\\users\\|\\lab\\|\\parcial\\")


def severidad(findings: list[dict], obf: list[str], flujo: dict, tipo_clase: str) -> dict:
    """Severidad contextual (independiente del modelo): baja, media, alta o crítica."""
    cats = {f["categoria"] for f in findings}
    motivos = []
    score = 0
    if "defensa" in cats:
        score += 4
        motivos.append("Intenta debilitar protecciones del sistema (antivirus, firewall, registros o copias de recuperación).")
    if "persistencia" in cats:
        score += 2
        motivos.append("Se configura para ejecutarse automáticamente en el futuro.")
    if "cuentas" in cats:
        score += 2
        motivos.append("Crea o modifica cuentas o recursos compartidos.")
    if "ejecucion" in cats and "red" in cats:
        score += 3
        motivos.append("Descarga contenido de Internet y ejecuta código construido dinámicamente.")
    elif "red" in cats:
        score += 1
        motivos.append("Se comunica por red.")
    if "borrado" in cats:
        sistema = any(_SYSTEM_TARGET.search(f["codigo"]) for f in findings if f["categoria"] == "borrado")
        score += 3 if sistema else 1
        motivos.append("Borra datos " + ("en carpetas del sistema." if sistema else "(revise qué carpetas)."))
    if "ocultamiento" in cats or obf:
        score += 2
        motivos.append("Oculta su ejecución o su contenido.")
    if flujo.get("posible_ciclo_infinito"):
        score += 1
        motivos.append("Contiene un ciclo sin condición de salida.")
    if any(_SYSTEM_TARGET.search(f["codigo"]) for f in findings if OPERACION[f["categoria"]] != "consulta"):
        score += 1
        motivos.append("Modifica ubicaciones del sistema (requiere privilegios de administrador).")
    nivel = "baja" if score <= 1 else "media" if score <= 3 else "alta" if score <= 6 else "critica"
    if not motivos:
        motivos.append("Solo se detectaron operaciones de consulta o ninguna operación catalogada." if tipo_clase == "consulta" else "Modifica archivos o configuración del usuario.")
    return {"nivel": nivel, "puntos": score, "motivos": motivos}


def analyze(data: bytes, filename: str = "") -> dict:
    t0 = time.perf_counter()
    texto, codificacion = decode(data)
    truncado = len(data) > LIMITE
    tipo = tipo_por_nombre(filename, texto)

    # Análisis sobre el texto original y sobre el texto normalizado (sin ofuscación superficial).
    normalizado = "\n".join(normalize_line(line, tipo) for line in texto.splitlines())
    found = hallazgos(normalizado)
    payloads = decoded_payloads(texto)
    for p in payloads:
        for h in hallazgos(p["texto"]):
            found.append({**h, "linea": p["linea"], "codigo": f"[{p['origen']} decodificado] {h['codigo']}", "decodificado": True})
    for f in found:
        f["operacion"] = OPERACION[f["categoria"]]
        f["categoria_es"] = CATEGORIA_ES[f["categoria"]]

    att = _attack()["tecnicas"]
    tecnicas: dict[str, dict] = {}
    for f in found:
        if f["attack"] != "-":
            t = tecnicas.setdefault(f["attack"], {**att.get(f["attack"], {"id": f["attack"], "nombre": "(sin datos)", "tacticas": [], "url": None}), "lineas": []})
            t["lineas"].append(f["linea"])
    for t in tecnicas.values():
        t["lineas"] = sorted(set(t["lineas"]))

    flujo = flujo_bat(normalizado) if tipo != "powershell" else {"etiquetas": {}, "saltos": [], "ciclos": [], "posible_ciclo_infinito": bool(re.search(r"(?im)^\s*while\s*\(\s*\$true\s*\)", texto)) and not re.search(r"(?i)\bbreak\b|\bexit\b|\breturn\b", texto), "saltos_rotos": []}
    estr = estructuras(texto, tipo)
    obf = obfuscation_signals(texto)

    reglas = clasificar_por_reglas(normalizado + "\n" + "\n".join(p["texto"] for p in payloads))
    model = _model()
    if model is not None:
        proba = {c: round(float(p), 4) for c, p in zip(model.classes_, model.predict_proba([normalizado])[0])}
        ml = max(proba, key=proba.get)
        final = decision_hibrida(reglas, proba)
        rasgos = top_rasgos(model, normalizado)
    else:
        proba, ml, final, rasgos = None, None, reglas, []

    lineas = explain_lines(texto, found, tipo)
    ops = {"consulta": 0, "modificacion": 0, "sensible": 0}
    for f in found:
        ops[f["operacion"]] += 1
    no_cat = sum(1 for line in lineas if line["tipo"] == "no_catalogado")

    limitaciones = [
        "Análisis estático: no se observa lo que el script construye o descarga al ejecutarse.",
        "La probabilidad de la clase «sensible» indica parecido con ejemplos del corpus de entrenamiento; no es la probabilidad de que el script sea malicioso.",
        "El modelo se entrenó con un corpus sintético de 180 scripts; su desempeño en scripts reales debe validarse con más datos etiquetados por dos personas.",
    ]
    if obf:
        limitaciones.append("Se detectó ofuscación: el análisis puede estar incompleto aunque se normalizaron las formas más simples.")
    if no_cat:
        limitaciones.append(f"{no_cat} línea(s) contienen instrucciones que el catálogo no reconoce.")
    if truncado:
        limitaciones.append("El archivo supera 1 MB: solo se analizó el primer megabyte.")
    if model is None:
        limitaciones.append("El modelo estadístico no está disponible; se usa solo la clasificación por reglas.")

    lineas_total = texto.count("\n") + 1 if texto else 0
    return {
        "archivo": filename,
        "tipo": tipo,
        "codificacion": codificacion,
        "bytes": len(data),
        "lineas_total": lineas_total,
        "truncado": truncado,
        "ejecutado": False,
        "clasificacion": {
            "estadistica": {"clase": ml, "probabilidades": proba, "rasgos_relevantes": rasgos},
            "reglas": reglas,
            "hibrida": final,
            "umbral_sensible": UMBRAL_SENSIBLE,
            "nota": "La decisión híbrida marca «sensible» si lo indican las reglas o si el modelo asigna una probabilidad ≥ 0,30 a esa clase.",
        },
        "hallazgos": found,
        "operaciones": ops,
        "tecnicas": sorted(tecnicas.values(), key=lambda t: t["id"]),
        "severidad": severidad(found, obf, flujo, final),
        "flujo": flujo,
        "estructuras": estr,
        "ofuscacion": obf,
        "decodificado": payloads,
        "explicacion_lineas": lineas,
        "limitaciones": limitaciones,
        "attack_version": _attack().get("version_attack"),
        "tiempo_ms": round((time.perf_counter() - t0) * 1000, 1),
    }
