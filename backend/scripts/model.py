"""Clasificador de riesgo: consulta / modifica / sensible.

Reproduce el pipeline del proyecto original (guía 03B, §10.4 y §10.5):
- Rasgos: TF-IDF de n-gramas de caracteres (3 a 5, «char_wb», min_df=2,
  máx. 20 000) unido al logaritmo de los conteos de hallazgos por categoría.
- Modelo: regresión logística multiclase con ``class_weight="balanced"``.
- Baseline sin IA: reglas fijas sobre las categorías detectadas.
- Política híbrida: «sensible» si lo indican las reglas O el modelo con p ≥ 0,30.

Importante: la probabilidad de la clase «sensible» indica cuánto se parece el
texto a los ejemplos sensibles del corpus; NO es la probabilidad de que el
script sea malware.
"""

from __future__ import annotations

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from .catalog import CATEGORIAS, hallazgos

CLASES = ["consulta", "modifica", "sensible"]
UMBRAL_SENSIBLE = 0.30
SENSIBLES = {"persistencia", "borrado", "ocultamiento", "red", "cuentas", "procesos", "ejecucion", "defensa"}
MODIFICA = {"escritura", "registro"}


class ConteoCategorias(BaseEstimator, TransformerMixin):
    """Convierte cada script en el número de hallazgos por categoría (escala log1p)."""

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        filas = []
        for texto in X:
            h = hallazgos(texto)
            filas.append([sum(1 for f in h if f["categoria"] == c) for c in CATEGORIAS])
        return np.log1p(np.array(filas, dtype=float))


def crear_modelo() -> Pipeline:
    rasgos = FeatureUnion(
        [
            ("ngramas", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=True, min_df=2, max_features=20000)),
            ("categorias", ConteoCategorias()),
        ]
    )
    return Pipeline([("rasgos", rasgos), ("clf", LogisticRegression(max_iter=3000, class_weight="balanced"))])


def clasificar_por_reglas(texto: str) -> str:
    """Baseline sin IA (idéntico al original, con las 2 categorías de la ampliación)."""
    cats = {h["categoria"] for h in hallazgos(texto)}
    if cats & SENSIBLES:
        return "sensible"
    if cats & MODIFICA:
        return "modifica"
    return "consulta"


def decision_hibrida(reglas: str, proba: dict[str, float]) -> str:
    if reglas == "sensible" or proba.get("sensible", 0.0) >= UMBRAL_SENSIBLE:
        return "sensible"
    return max(proba, key=proba.get)


def top_rasgos(modelo: Pipeline, texto: str, clase: str = "sensible", k: int = 8) -> list[dict]:
    """Rasgos que más empujan hacia una clase en este script (interpretabilidad)."""
    rasgos: FeatureUnion = modelo.named_steps["rasgos"]
    clf: LogisticRegression = modelo.named_steps["clf"]
    x = rasgos.transform([texto])
    x = x.toarray()[0] if hasattr(x, "toarray") else np.asarray(x)[0]
    idx = list(clf.classes_).index(clase)
    contrib = x * clf.coef_[idx]
    names = list(rasgos.transformer_list[0][1].get_feature_names_out()) + [f"[categoría] {c}" for c in CATEGORIAS]
    order = np.argsort(contrib)[::-1][:k]
    return [{"rasgo": names[i], "aporte": round(float(contrib[i]), 4)} for i in order if contrib[i] > 0]
