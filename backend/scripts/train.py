"""Entrenamiento y evaluación reproducibles del clasificador de scripts.

Uso (PowerShell, raíz del repositorio):
    .\\.venv\\Scripts\\python -m backend.scripts.train

1. Genera el corpus sintético (180 scripts, 60 por clase).
2. Validación cruzada estratificada de 5 pliegues (como el original) para el
   baseline de reglas, el modelo de regresión logística y la política híbrida.
3. Reentrena con todo el corpus y guarda el modelo.
4. Evalúa sobre el conjunto realista independiente (18 scripts escritos a mano,
   no usados en el entrenamiento).
5. Escribe métricas en JSON y un informe en docs/pruebas/evaluacion_clasificador.md.
"""

from __future__ import annotations

import csv
import json
import platform
import time
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.metrics import classification_report, confusion_matrix, f1_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from .corpus import generar
from .model import CLASES, UMBRAL_SENSIBLE, clasificar_por_reglas, crear_modelo, decision_hibrida
from .reading import decode

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = Path(__file__).parent / "data" / "modelo_scriptlens.joblib"
METRICS_PATH = Path(__file__).parent / "data" / "metricas_clasificador.json"
REPORT_PATH = ROOT / "docs" / "pruebas" / "evaluacion_clasificador.md"
REAL_DIR = ROOT / "tests" / "fixtures" / "scripts_reales"


def _metrics(y, pred) -> dict:
    rep = classification_report(y, pred, labels=CLASES, digits=3, zero_division=0, output_dict=True)
    consulta_idx = [i for i, t in enumerate(y) if t == "consulta"]
    fp_consulta = sum(1 for i in consulta_idx if pred[i] == "sensible") / max(1, len(consulta_idx))
    return {
        "por_clase": {c: {k: round(rep[c][k], 3) for k in ("precision", "recall", "f1-score", "support")} for c in CLASES},
        "f1_macro": round(f1_score(y, pred, average="macro", labels=CLASES, zero_division=0), 3),
        "recall_sensible": round(recall_score(y, pred, labels=["sensible"], average="macro", zero_division=0), 3),
        "falsos_positivos_consulta": round(fp_consulta, 3),
        "matriz_confusion": confusion_matrix(y, pred, labels=CLASES).tolist(),
    }


def _hybrid(model_or_probas, X, reglas):
    out = []
    for i, _ in enumerate(X):
        proba = model_or_probas[i]
        out.append(decision_hibrida(reglas[i], proba))
    return out


def main() -> dict:
    t0 = time.time()
    filas = generar()
    X = [f["texto"] for f in filas]
    y = [f["etiqueta"] for f in filas]
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    pred_base = [clasificar_por_reglas(t) for t in X]
    probas_cv = cross_val_predict(crear_modelo(), X, y, cv=cv, method="predict_proba")
    clases_modelo = sorted(set(y))  # orden de LogisticRegression.classes_
    proba_dicts = [dict(zip(clases_modelo, p)) for p in probas_cv]
    pred_ml = [max(p, key=p.get) for p in proba_dicts]
    pred_hib = _hybrid(proba_dicts, X, pred_base)

    resultados = {
        "corpus": {"total": len(X), "por_clase": {c: y.count(c) for c in CLASES}, "origen": {o: sum(1 for f in filas if f["origen"] == o) for o in {f["origen"] for f in filas}}},
        "validacion_cruzada": {"baseline": _metrics(y, pred_base), "modelo": _metrics(y, pred_ml), "hibrida": _metrics(y, pred_hib)},
    }

    modelo = crear_modelo().fit(X, y)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, MODEL_PATH)

    # Conjunto realista independiente
    real = list(csv.DictReader(open(REAL_DIR / "etiquetas.csv", encoding="utf-8")))
    Xr = [decode((REAL_DIR / r["archivo"]).read_bytes())[0] for r in real]
    yr = [r["etiqueta"] for r in real]
    t_start = time.perf_counter()
    pr = [dict(zip(modelo.classes_, p)) for p in modelo.predict_proba(Xr)]
    elapsed = (time.perf_counter() - t_start) / max(1, len(Xr))
    br = [clasificar_por_reglas(t) for t in Xr]
    mr = [max(p, key=p.get) for p in pr]
    hr = [decision_hibrida(b, p) for b, p in zip(br, pr)]
    resultados["realista"] = {
        "total": len(Xr),
        "baseline": _metrics(yr, br),
        "modelo": _metrics(yr, mr),
        "hibrida": _metrics(yr, hr),
        "detalle": [
            {"archivo": r["archivo"], "real": yr[i], "reglas": br[i], "modelo": mr[i], "p_sensible": round(float(pr[i].get("sensible", 0)), 3), "hibrida": hr[i]}
            for i, r in enumerate(real)
        ],
    }
    resultados["entorno"] = {
        "fecha": time.strftime("%Y-%m-%d %H:%M"),
        "python": platform.python_version(),
        "scikit_learn": sklearn.__version__,
        "numpy": np.__version__,
        "umbral_sensible": UMBRAL_SENSIBLE,
        "segundos_por_script_modelo": round(elapsed, 4),
        "duracion_total_s": round(time.time() - t0, 2),
    }
    METRICS_PATH.write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding="utf-8")
    _report(resultados)
    print(json.dumps({k: {m: v["f1_macro"] for m, v in resultados[k].items() if isinstance(v, dict) and "f1_macro" in v} for k in ("validacion_cruzada", "realista")}, indent=1))
    return resultados


def _table(m: dict) -> str:
    rows = ["| Clase | Precisión | Recall | F1 | Soporte |", "|---|---|---|---|---|"]
    for c in CLASES:
        p = m["por_clase"][c]
        rows.append(f"| {c} | {p['precision']} | {p['recall']} | {p['f1-score']} | {int(p['support'])} |")
    rows.append(f"\nF1 macro: **{m['f1_macro']}** · Recall «sensible»: **{m['recall_sensible']}** · Falsos positivos en «consulta»: **{m['falsos_positivos_consulta'] * 100:.1f} %**\n")
    mc = m["matriz_confusion"]
    rows.append("Matriz de confusión (filas = real, columnas = predicho: consulta, modifica, sensible):\n")
    rows.append("```\n" + "\n".join(f"{CLASES[i]:<9} {row}" for i, row in enumerate(mc)) + "\n```")
    return "\n".join(rows)


def _report(r: dict) -> None:
    e = r["entorno"]
    lines = [
        "# Evaluación del clasificador de scripts",
        "",
        f"Generado automáticamente por `python -m backend.scripts.train` el {e['fecha']} (Python {e['python']}, scikit-learn {e['scikit_learn']}).",
        "",
        "## Advertencias de interpretación",
        "",
        "- El corpus de entrenamiento es **sintético** y lo generan las mismas reglas que se evalúan; sus cifras **no** deben presentarse como desempeño en el mundo real (advertencia ya presente en la guía original 03B, §11.3).",
        "- El conjunto «realista» tiene solo 18 scripts escritos y etiquetados por **una** persona; el acuerdo entre dos etiquetadores (kappa de Cohen ≥ 0,7) sigue **pendiente**.",
        "- La probabilidad de la clase «sensible» mide el parecido con los ejemplos sensibles del corpus; **no es la probabilidad de que un script sea malware**.",
        "",
        f"## Corpus sintético ({r['corpus']['total']} scripts) — validación cruzada estratificada de 5 pliegues",
        "",
    ]
    for name, key in (("Baseline sin IA (reglas)", "baseline"), ("Modelo (regresión logística balanceada)", "modelo"), (f"Política híbrida (reglas o p(sensible) ≥ {e['umbral_sensible']})", "hibrida")):
        lines += [f"### {name}", "", _table(r["validacion_cruzada"][key]), ""]
    lines += [f"## Conjunto realista independiente ({r['realista']['total']} scripts no vistos en el entrenamiento)", ""]
    for name, key in (("Baseline sin IA (reglas)", "baseline"), ("Modelo", "modelo"), ("Política híbrida", "hibrida")):
        lines += [f"### {name}", "", _table(r["realista"][key]), ""]
    lines += ["### Detalle por script", "", "| Archivo | Real | Reglas | Modelo | p(sensible) | Híbrida |", "|---|---|---|---|---|---|"]
    for d in r["realista"]["detalle"]:
        lines.append(f"| {d['archivo']} | {d['real']} | {d['reglas']} | {d['modelo']} | {d['p_sensible']} | {d['hibrida']} |")
    lines += ["", f"Tiempo medio de clasificación por script: {e['segundos_por_script_modelo']} s (meta original: < 2 s).", ""]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
