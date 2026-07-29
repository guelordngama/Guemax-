"""Modèles de données SQLAlchemy : utilisateurs, alertes, agents, interventions."""

from datetime import datetime

from database import db


def _now():
    return datetime.utcnow()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="citizen")  # citizen | admin | agent

    # Profil citoyen
    nom = db.Column(db.String(80))
    post_nom = db.Column(db.String(80))
    prenom = db.Column(db.String(80))
    sexe = db.Column(db.String(10))          # M | F | Autre
    date_naissance = db.Column(db.String(20))
    ville = db.Column(db.String(80))
    commune = db.Column(db.String(80))
    quartier = db.Column(db.String(80))
    nationalite = db.Column(db.String(80))
    telephone = db.Column(db.String(30))

    # Validation du compte par code
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(10))
    verification_expires = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "nom": self.nom,
            "postNom": self.post_nom,
            "prenom": self.prenom,
            "sexe": self.sexe,
            "ville": self.ville,
            "commune": self.commune,
            "quartier": self.quartier,
            "nationalite": self.nationalite,
            "telephone": self.telephone,
            "isVerified": self.is_verified,
            "createdAt": self.created_at.isoformat() + "Z",
        }


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(40), nullable=False)
    severity = db.Column(db.String(20), nullable=False)   # faible | moyen | eleve | critique
    description = db.Column(db.Text, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(200))
    photo = db.Column(db.String(300))
    status = db.Column(db.String(20), default="actif")    # actif | verifie | resolu
    priority = db.Column(db.String(20), default="moyenne")  # attribuée par l'IA/le classifieur
    priority_score = db.Column(db.Float, default=0.0)
    confirmations = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))  # citoyen signalant (facultatif)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    interventions = db.relationship("Intervention", backref="alert", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "lat": self.lat,
            "lng": self.lng,
            "address": self.address,
            "photo": self.photo,
            "status": self.status,
            "priority": self.priority,
            "priorityScore": self.priority_score,
            "confirmations": self.confirmations,
            "createdAt": self.created_at.isoformat() + "Z",
            "updatedAt": self.updated_at.isoformat() + "Z",
        }


class Agent(db.Model):
    __tablename__ = "agents"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    matricule = db.Column(db.String(30))
    grade = db.Column(db.String(60))
    phone = db.Column(db.String(30))
    # disponible (actif) | en_mission | absent | hors_ligne
    status = db.Column(db.String(20), default="disponible")
    created_at = db.Column(db.DateTime, default=_now)

    points = db.relationship("AgentPoints", backref="agent", lazy=True)

    def total_points(self):
        return sum(p.points for p in self.points)

    def points_this_year(self):
        year = _now().year
        return sum(p.points for p in self.points if p.year == year)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "matricule": self.matricule,
            "grade": self.grade,
            "phone": self.phone,
            "status": self.status,
            "totalPoints": self.total_points(),
            "pointsThisYear": self.points_this_year(),
        }


class AgentPoints(db.Model):
    """Points de performance attribués à un agent, conservés par année."""

    __tablename__ = "agent_points"

    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey("agents.id"), nullable=False)
    year = db.Column(db.Integer, nullable=False, default=lambda: _now().year)
    points = db.Column(db.Integer, default=0)
    reason = db.Column(db.String(200))
    lieu = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "agentId": self.agent_id,
            "year": self.year,
            "points": self.points,
            "reason": self.reason,
            "lieu": self.lieu,
            "date": self.created_at.strftime("%Y-%m-%d"),
            "heure": self.created_at.strftime("%H:%M"),
        }


class Intervention(db.Model):
    __tablename__ = "interventions"

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey("alerts.id"))
    agent_id = db.Column(db.Integer, db.ForeignKey("agents.id"))
    status = db.Column(db.String(20), default="en_cours")  # en_cours | terminee | annulee
    lieu = db.Column(db.String(120))
    type_mission = db.Column(db.String(60))
    duree_minutes = db.Column(db.Integer)
    resultat = db.Column(db.String(20))  # reussie | partielle | echouee
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "alertId": self.alert_id,
            "agentId": self.agent_id,
            "status": self.status,
            "lieu": self.lieu,
            "typeMission": self.type_mission,
            "dureeMinutes": self.duree_minutes,
            "resultat": self.resultat,
            "notes": self.notes,
            "date": self.created_at.strftime("%Y-%m-%d"),
            "heure": self.created_at.strftime("%H:%M"),
            "createdAt": self.created_at.isoformat() + "Z",
            "updatedAt": self.updated_at.isoformat() + "Z",
        }
