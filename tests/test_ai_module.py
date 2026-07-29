"""Tests du module d'IA (classifieur SVM de priorité).

Ignorés automatiquement si scikit-learn / le modèle entraîné ne sont pas
disponibles (par ex. en CI) — le backend retombe alors sur les règles.
"""

import os

import pytest

pytest.importorskip("sklearn")
pytest.importorskip("joblib")

AI_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ai_module")
MODEL = os.path.join(AI_DIR, "model_svm.joblib")

pytestmark = pytest.mark.skipif(not os.path.exists(MODEL), reason="modèle SVM non entraîné")


@pytest.fixture(scope="module")
def predictor():
    import sys
    sys.path.insert(0, AI_DIR)
    import predict
    predict.load_model()
    return predict


def test_predict_retourne_un_label_valide(predictor):
    label, score = predictor.predict_priority("vol", "moyen", "Vol de téléphone au marché")
    assert label in ("basse", "moyenne", "haute", "critique")
    assert 0.0 <= score <= 1.0


def test_agression_armee_est_prioritaire(predictor):
    label, _ = predictor.predict_priority(
        "agression", "critique", "Agression à main armée, personne blessée, urgent"
    )
    assert label in ("haute", "critique")


def test_incident_mineur_est_basse_priorite(predictor):
    label, _ = predictor.predict_priority(
        "infrastructure", "faible", "Petit nid-de-poule sur la route"
    )
    assert label in ("basse", "moyenne")
