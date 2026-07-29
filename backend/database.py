"""Initialisation de la base de données (SQLAlchemy) et données de départ.

On expose une unique instance ``db`` importée par les modèles et les routes.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Attache SQLAlchemy à l'application et crée les tables si besoin."""
    db.init_app(app)
    with app.app_context():
        # Import tardif pour éviter les imports circulaires.
        from models import User, Alert, Agent, Intervention  # noqa: F401

        db.create_all()
        seed(app)


def seed(app):
    """Crée le compte administrateur par défaut et quelques agents de démo."""
    from models import User, Agent
    from utils.security import hash_password

    admin_cfg = app.config["DEFAULT_ADMIN"]
    if not User.query.filter_by(username=admin_cfg["username"]).first():
        db.session.add(
            User(
                username=admin_cfg["username"],
                email=admin_cfg["email"],
                password_hash=hash_password(admin_cfg["password"]),
                role="admin",
                is_verified=True,
            )
        )

    if Agent.query.count() == 0:
        db.session.add_all(
            [
                Agent(name="Patrouille Centre-ville", phone="+243000000001"),
                Agent(name="Patrouille Kenya", phone="+243000000002"),
                Agent(name="Équipe intervention rapide", phone="+243000000003"),
            ]
        )

    db.session.commit()
