"""Classification de la priorité des alertes.

⚠️  PLACEHOLDER — module d'IA minimal fondé sur des règles.

Le vrai modèle d'apprentissage (SVM entraîné sur ``ai_module/dataset.csv``)
sera intégré dans un second temps via ``ai_module/predict.py``. En attendant,
``classify_priority`` fournit une estimation déterministe combinant la gravité
déclarée, la catégorie et des mots-clés critiques présents dans la description.
L'interface (entrées/sorties) est volontairement identique à celle que le
modèle SVM exposera, afin que le remplacement soit transparent pour le reste
de l'application.
"""

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


def classify_priority(category, severity, description):
    """Retourne ``(label, score)`` où label ∈ {basse, moyenne, haute, critique}.

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
