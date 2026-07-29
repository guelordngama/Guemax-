"""Routes de gestion des utilisateurs et des agents (réservées à l'administration)."""

from flask import Blueprint, jsonify, request

from database import db
from models import Agent, User
from utils.security import admin_required

users_bp = Blueprint("users", __name__)


@users_bp.get("")
@admin_required
def list_users(current_user_payload=None):
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users])


@users_bp.get("/agents")
@admin_required
def list_agents(current_user_payload=None):
    agents = Agent.query.order_by(Agent.name.asc()).all()
    return jsonify([a.to_dict() for a in agents])


@users_bp.post("/agents")
@admin_required
def create_agent(current_user_payload=None):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if len(name) < 2:
        return jsonify({"errors": ["Nom de l'agent requis."]}), 400
    agent = Agent(name=name, phone=(data.get("phone") or "").strip() or None)
    db.session.add(agent)
    db.session.commit()
    return jsonify(agent.to_dict()), 201
