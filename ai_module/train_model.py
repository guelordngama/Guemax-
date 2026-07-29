"""Entraîne le classifieur SVM de priorité des alertes.

Lit ``dataset.csv``, entraîne un pipeline TF-IDF + SVM linéaire, évalue sur un
jeu de test et sauvegarde le modèle dans ``model_svm.joblib``.

Usage :  python train_model.py
"""

import os

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC

from predict import build_features, MODEL_PATH

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(HERE, "dataset.csv")


def load_dataset(path=DATASET_PATH):
    df = pd.read_csv(path)
    df = df.dropna(subset=["description", "category", "severity", "priority"])
    X = [build_features(r.category, r.severity, r.description) for r in df.itertuples()]
    y = df["priority"].tolist()
    return X, y


def build_pipeline():
    # SVM linéaire calibré (Platt/sigmoïde) pour obtenir des probabilités
    # fiables via predict_proba, sans le paramètre `probability` déprécié.
    svm = CalibratedClassifierCV(
        SVC(kernel="linear", class_weight="balanced", random_state=42),
        method="sigmoid",
        ensemble=False,
    )
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, lowercase=True)),
        ("svm", svm),
    ])


def main():
    X, y = load_dataset()
    print(f"Jeu de données : {len(X)} exemples, {len(set(y))} classes de priorité.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nExactitude (test) : {acc:.1%}\n")
    print(classification_report(y_test, y_pred, zero_division=0))

    joblib.dump(pipeline, MODEL_PATH)
    print(f"Modèle sauvegardé : {MODEL_PATH}")


if __name__ == "__main__":
    main()
