"""Fixtures pytest : application Flask de test + client + jeton admin."""

import os
import sys
import tempfile

# Rendre le paquet backend importable.
BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, BACKEND_DIR)

# Éviter que l'import de app.py (qui instancie une app au niveau module) ne crée
# une base de données dans le dépôt : on redirige vers un fichier temporaire.
os.environ.setdefault(
    "DATABASE_URL", "sqlite:///" + os.path.join(tempfile.gettempdir(), "safecity_import.db")
)

import pytest

from app import create_app
from config import TestConfig
from database import db, seed


@pytest.fixture(scope="session")
def app():
    application = create_app(TestConfig)
    return application


@pytest.fixture()
def client(app):
    # Base propre avant chaque test.
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed(app)
    return app.test_client()


@pytest.fixture()
def admin_token(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    return res.get_json()["token"]


def sample_alert(**overrides):
    payload = {
        "category": "vol",
        "severity": "eleve",
        "description": "Vol signalé près du marché de test",
        "lat": -11.66,
        "lng": 27.48,
    }
    payload.update(overrides)
    return payload
