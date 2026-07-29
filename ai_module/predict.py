"""Prédiction de la priorité d'une alerte à l'aide du modèle SVM entraîné.

Expose ``predict_priority(category, severity, description) -> (label, score)``,
interface identique à celle du classifieur de secours du backend
(``backend/utils/classification_ai.py``) pour un remplacement transparent.

Usage CLI :
    python predict.py "Agression à main armée, personne blessée" --category agression --severity critique
"""

import argparse
import os

import joblib

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_svm.joblib")

_model = None


def build_features(category, severity, description):
    """Construit le texte d'entrée du modèle : description enrichie du contexte.

    La catégorie et la gravité sont ajoutées sous forme de jetons dédiés pour
    que le TF-IDF les prenne en compte au même titre que les mots du texte.
    Cette fonction DOIT être identique entre l'entraînement et la prédiction.
    """
    description = (description or "").strip()
    return f"{description} __cat_{category}__ __sev_{severity}__"


def load_model(path=MODEL_PATH):
    """Charge (et met en cache) le modèle entraîné."""
    global _model
    if _model is None:
        _model = joblib.load(path)
    return _model


def predict_priority(category, severity, description):
    """Retourne ``(label, score)`` où label ∈ {basse, moyenne, haute, critique}
    et score est la probabilité de la classe prédite (0–1).
    """
    model = load_model()
    text = build_features(category, severity, description)
    proba = model.predict_proba([text])[0]
    idx = int(proba.argmax())
    return str(model.classes_[idx]), round(float(proba[idx]), 3)


def _cli():
    parser = argparse.ArgumentParser(description="Prédire la priorité d'une alerte (SVM).")
    parser.add_argument("description", help="Texte de l'alerte")
    parser.add_argument("--category", default="autre")
    parser.add_argument("--severity", default="moyen")
    args = parser.parse_args()
    label, score = predict_priority(args.category, args.severity, args.description)
    print(f"Priorité prédite : {label}  (confiance {score:.0%})")


if __name__ == "__main__":
    _cli()
