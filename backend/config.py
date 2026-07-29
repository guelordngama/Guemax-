"""Configuration de l'application Flask.

Les valeurs sensibles (clés secrètes, URI de base de données) peuvent être
surchargées par des variables d'environnement afin de ne rien coder en dur en
production.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

# Centre approximatif de Lubumbashi (RDC).
LUBUMBASHI_CENTER = {"lat": -11.6647, "lng": 27.4794}

# Emprise géographique de Lubumbashi. Le poste de la mairie ne traite que les
# alertes situées dans ces limites (les autres villes sont ignorées).
LUBUMBASHI_BOUNDS = {
    "min_lat": -11.78, "max_lat": -11.53,
    "min_lng": 27.35, "max_lng": 27.62,
}


def in_lubumbashi(lat, lng):
    """Vrai si les coordonnées sont dans l'emprise de Lubumbashi."""
    b = LUBUMBASHI_BOUNDS
    return (
        lat is not None and lng is not None
        and b["min_lat"] <= lat <= b["max_lat"]
        and b["min_lng"] <= lng <= b["max_lng"]
    )


class Config:
    """Configuration de base commune à tous les environnements."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "safecity-lubumbashi-secret-dev")
    JWT_SECRET = os.environ.get("JWT_SECRET", "safecity-lubumbashi-jwt-dev")
    JWT_EXPIRES_HOURS = int(os.environ.get("JWT_EXPIRES_HOURS", "12"))

    # Validation des comptes citoyens par code.
    # En mode démo (défaut), le code est journalisé et renvoyé par l'API pour
    # permettre la validation sans service d'envoi ; passer AUTH_DEV_MODE=0 pour
    # le désactiver une fois un vrai envoi SMTP/SMS branché.
    AUTH_DEV_MODE = os.environ.get("AUTH_DEV_MODE", "1") == "1"
    VERIFICATION_TTL_MINUTES = int(os.environ.get("VERIFICATION_TTL_MINUTES", "15"))

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(PROJECT_DIR, "database", "security_alert.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Dossier où sont enregistrées les photos jointes aux alertes.
    UPLOAD_DIR = os.path.join(PROJECT_DIR, "web_citizen", "assets", "images", "uploads")
    MAX_PHOTO_BYTES = 4 * 1024 * 1024  # 4 Mo

    # Compte administrateur créé au premier démarrage (mairie).
    DEFAULT_ADMIN = {
        "username": os.environ.get("ADMIN_USERNAME", "admin"),
        "email": os.environ.get("ADMIN_EMAIL", "admin@safecity.cd"),
        "password": os.environ.get("ADMIN_PASSWORD", "admin123"),
    }


class TestConfig(Config):
    """Configuration dédiée aux tests : base SQLite en mémoire."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET = "test-secret"
