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
        from models import AgentPoints

        agents = [
            Agent(name="Patrouille Centre-ville", matricule="AG-001", grade="Brigadier",
                  phone="+243000000001", status="disponible"),
            Agent(name="Patrouille Kenya", matricule="AG-002", grade="Agent",
                  phone="+243000000002", status="en_mission"),
            Agent(name="Équipe intervention rapide", matricule="AG-003", grade="Sergent",
                  phone="+243000000003", status="disponible"),
            Agent(name="Patrouille Kampemba", matricule="AG-004", grade="Agent",
                  phone="+243000000004", status="absent"),
            Agent(name="Unité Ruashi", matricule="AG-005", grade="Agent",
                  phone="+243000000005", status="hors_ligne"),
        ]
        db.session.add_all(agents)
        db.session.flush()
        # Quelques points de démonstration (année courante et précédente).
        from datetime import datetime
        year = datetime.utcnow().year
        demo_points = [
            (agents[0], year, 45), (agents[0], year - 1, 30),
            (agents[1], year, 28), (agents[2], year, 62), (agents[2], year - 1, 40),
            (agents[3], year, 12),
        ]
        for agent, yr, pts in demo_points:
            db.session.add(AgentPoints(agent_id=agent.id, year=yr, points=pts,
                                       reason="Performances cumulées"))

    db.session.commit()
