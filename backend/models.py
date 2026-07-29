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
    created_at = db.Column(db.DateTime, default=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
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
    phone = db.Column(db.String(30))
    status = db.Column(db.String(20), default="disponible")  # disponible | en_intervention
    created_at = db.Column(db.DateTime, default=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "status": self.status,
        }


class Intervention(db.Model):
    __tablename__ = "interventions"

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey("alerts.id"), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey("agents.id"))
    status = db.Column(db.String(20), default="en_cours")  # en_cours | terminee | annulee
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "alertId": self.alert_id,
            "agentId": self.agent_id,
            "status": self.status,
            "notes": self.notes,
            "createdAt": self.created_at.isoformat() + "Z",
            "updatedAt": self.updated_at.isoformat() + "Z",
        }
