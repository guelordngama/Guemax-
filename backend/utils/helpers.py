"""Fonctions utilitaires : constantes partagées, validation, upload de photos."""

import base64
import binascii
import os
import re
import uuid

# --- Référentiels partagés (exposés au frontend via /api/config) -----------

CATEGORIES = [
    {"id": "vol", "label": "Vol / Cambriolage", "icon": "👜", "color": "#e11d48"},
    {"id": "agression", "label": "Agression", "icon": "🚨", "color": "#b91c1c"},
    {"id": "accident", "label": "Accident de circulation", "icon": "🚗", "color": "#f59e0b"},
    {"id": "incendie", "label": "Incendie", "icon": "🔥", "color": "#ea580c"},
    {"id": "inondation", "label": "Inondation", "icon": "🌊", "color": "#0284c7"},
    {"id": "electricite", "label": "Coupure d'électricité", "icon": "⚡", "color": "#7c3aed"},
    {"id": "infrastructure", "label": "Voirie / Infrastructure", "icon": "🚧", "color": "#4b5563"},
    {"id": "autre", "label": "Autre", "icon": "📍", "color": "#0f766e"},
]

SEVERITIES = [
    {"id": "faible", "label": "Faible"},
    {"id": "moyen", "label": "Moyen"},
    {"id": "eleve", "label": "Élevé"},
    {"id": "critique", "label": "Critique"},
]

STATUSES = ("actif", "verifie", "resolu")

CATEGORY_IDS = {c["id"] for c in CATEGORIES}
SEVERITY_IDS = {s["id"] for s in SEVERITIES}


# --- Validation ------------------------------------------------------------

def validate_alert(data):
    """Valide la charge utile d'une alerte. Retourne ``(errors, clean)``."""
    errors = []
    data = data or {}

    category = data.get("category")
    severity = data.get("severity")
    description = (data.get("description") or "").strip()

    if category not in CATEGORY_IDS:
        errors.append("Catégorie invalide.")
    if severity not in SEVERITY_IDS:
        errors.append("Niveau de gravité invalide.")
    if len(description) < 5:
        errors.append("La description doit contenir au moins 5 caractères.")
    if len(description) > 1000:
        errors.append("La description est trop longue (max 1000 caractères).")

    try:
        lat = float(data.get("lat"))
        lng = float(data.get("lng"))
    except (TypeError, ValueError):
        errors.append("Coordonnées manquantes ou invalides.")
        lat = lng = None
    else:
        if not (-90 <= lat <= 90):
            errors.append("Latitude invalide.")
        if not (-180 <= lng <= 180):
            errors.append("Longitude invalide.")

    clean = {
        "category": category,
        "severity": severity,
        "description": description,
        "lat": lat,
        "lng": lng,
        "address": (data.get("address") or None) and str(data.get("address"))[:200],
    }
    return errors, clean


# --- Photos ----------------------------------------------------------------

_DATA_URL_RE = re.compile(r"^data:image/(png|jpe?g|webp);base64,([A-Za-z0-9+/=]+)$")


def save_photo(data_url, upload_dir, max_bytes):
    """Enregistre une image (Data URL base64) et renvoie son chemin public.

    Retourne ``None`` si aucune image valide n'est fournie.
    """
    if not isinstance(data_url, str):
        return None
    match = _DATA_URL_RE.match(data_url)
    if not match:
        return None

    ext = "jpg" if match.group(1) == "jpeg" else match.group(1)
    try:
        raw = base64.b64decode(match.group(2), validate=True)
    except (binascii.Error, ValueError):
        return None
    if len(raw) > max_bytes:
        return None

    os.makedirs(upload_dir, exist_ok=True)
    name = f"{uuid.uuid4().hex}.{ext}"
    with open(os.path.join(upload_dir, name), "wb") as fh:
        fh.write(raw)
    return f"/assets/images/uploads/{name}"
