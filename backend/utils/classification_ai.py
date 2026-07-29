"""Classification de la priorité des alertes.

Utilise le modèle d'apprentissage **SVM** (``ai_module/model_svm.joblib``)
lorsqu'il est disponible, et retombe automatiquement sur un classifieur par
règles si scikit-learn ou le modèle ne sont pas présents (par ex. en CI). Les
deux voies exposent la même interface :

    classify_priority(category, severity, description) -> (label, score)

où ``label`` ∈ {basse, moyenne, haute, critique} et ``score`` ∈ [0, 1].
"""

import os
import sys

# --- Chargement paresseux du modèle SVM (facultatif) -----------------------

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_AI_DIR = os.path.join(_PROJECT_DIR, "ai_module")
_svm = None            # module ai_module.predict une fois chargé
_svm_ready = None      # None = pas encore tenté ; True/False ensuite


def _try_load_svm():
    """Tente de charger le modèle SVM une seule fois. Retourne True si prêt."""
    global _svm, _svm_ready
    if _svm_ready is not None:
        return _svm_ready
    try:
        if _AI_DIR not in sys.path:
            sys.path.insert(0, _AI_DIR)
        import predict as svm_predict  # depuis ai_module/

        svm_predict.load_model()  # échoue si le fichier .joblib est absent
        _svm = svm_predict
        _svm_ready = True
    except Exception:  # scikit-learn absent, modèle non entraîné, etc.
        _svm_ready = False
    return _svm_ready


# --- Classifieur de secours par règles -------------------------------------

SEVERITY_WEIGHT = {"faible": 1, "moyen": 2, "eleve": 3, "critique": 4}

# Catégories intrinsèquement plus urgentes.
CATEGORY_WEIGHT = {
    "agression": 3,
    "incendie": 3,
    "accident": 2,
    "vol": 2,
    "inondation": 2,
    "electricite": 1,
    "infrastructure": 1,
    "autre": 1,
}

CRITICAL_KEYWORDS = (
    "arme", "couteau", "sang", "blesse", "blessé", "mort", "urgent",
    "enfant", "feu", "explosion", "noyade", "secours", "danger",
)


def _classify_by_rules(category, severity, description):
    """Estimation déterministe par règles (repli si le SVM est indisponible).

    Le score est normalisé entre 0 et 1 pour rester comparable à une sortie de
    modèle probabiliste.
    """
    score = SEVERITY_WEIGHT.get(severity, 1) + CATEGORY_WEIGHT.get(category, 1)

    text = (description or "").lower()
    keyword_hits = sum(1 for kw in CRITICAL_KEYWORDS if kw in text)
    score += min(keyword_hits, 3)

    # Score max théorique = 4 (gravité) + 3 (catégorie) + 3 (mots-clés) = 10.
    normalized = round(min(score, 10) / 10, 3)

    if normalized >= 0.8:
        label = "critique"
    elif normalized >= 0.6:
        label = "haute"
    elif normalized >= 0.35:
        label = "moyenne"
    else:
        label = "basse"

    return label, normalized


# --- Interface publique -----------------------------------------------------

def classify_priority(category, severity, description):
    """Classe la priorité d'une alerte : SVM si disponible, sinon règles.

    Retourne ``(label, score)`` avec label ∈ {basse, moyenne, haute, critique}.
    """
    if _try_load_svm():
        try:
            return _svm.predict_priority(category, severity, description)
        except Exception:
            pass  # en cas de souci d'inférence, on retombe sur les règles
    return _classify_by_rules(category, severity, description)
