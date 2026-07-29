"""Gestion des agents : statuts, interventions et points de performance.

Toutes les routes sont réservées à l'administration/supervision.
"""

from datetime import datetime

from flask import Blueprint, jsonify, request

from database import db
from models import Agent, AgentPoints, Intervention
from utils.security import admin_required

agents_bp = Blueprint("agents", __name__)

STATUSES = ("disponible", "en_mission", "absent", "hors_ligne")

# Points attribués automatiquement selon le résultat de l'intervention.
RESULT_POINTS = {"reussie": 10, "partielle": 5, "echouee": 1}


@agents_bp.get("")
@admin_required
def list_agents(current_user_payload=None):
    agents = Agent.query.order_by(Agent.name.asc()).all()
    return jsonify([a.to_dict() for a in agents])


@agents_bp.post("")
@admin_required
def create_agent(current_user_payload=None):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if len(name) < 2:
        return jsonify({"errors": ["Nom de l'agent requis."]}), 400
    agent = Agent(
        name=name,
        matricule=(data.get("matricule") or "").strip() or None,
        grade=(data.get("grade") or "").strip() or None,
        phone=(data.get("phone") or "").strip() or None,
    )
    db.session.add(agent)
    db.session.commit()
    return jsonify(agent.to_dict()), 201


@agents_bp.get("/summary")
@admin_required
def summary(current_user_payload=None):
    agents = Agent.query.all()
    by_status = {s: 0 for s in STATUSES}
    for a in agents:
        by_status[a.status] = by_status.get(a.status, 0) + 1
    leaderboard = sorted(
        ({"id": a.id, "name": a.name, "totalPoints": a.total_points(),
          "pointsThisYear": a.points_this_year(), "status": a.status} for a in agents),
        key=lambda x: x["totalPoints"], reverse=True,
    )[:10]
    return jsonify({"total": len(agents), "byStatus": by_status, "leaderboard": leaderboard})


@agents_bp.patch("/<int:agent_id>/status")
@admin_required
def set_status(agent_id, current_user_payload=None):
    status = (request.get_json(silent=True) or {}).get("status")
    if status not in STATUSES:
        return jsonify({"errors": ["Statut invalide."]}), 400
    agent = db.session.get(Agent, agent_id)
    if not agent:
        return jsonify({"errors": ["Agent introuvable."]}), 404
    agent.status = status
    db.session.commit()
    return jsonify(agent.to_dict())


# --- Points de performance -------------------------------------------------

@agents_bp.get("/<int:agent_id>/points")
@admin_required
def get_points(agent_id, current_user_payload=None):
    agent = db.session.get(Agent, agent_id)
    if not agent:
        return jsonify({"errors": ["Agent introuvable."]}), 404
    history = AgentPoints.query.filter_by(agent_id=agent_id).order_by(
        AgentPoints.created_at.desc()
    ).all()
    by_year = {}
    for p in history:
        by_year[p.year] = by_year.get(p.year, 0) + p.points
    return jsonify({
        "agent": agent.to_dict(),
        "byYear": by_year,
        "history": [p.to_dict() for p in history],
    })


@agents_bp.post("/<int:agent_id>/points")
@admin_required
def award_points(agent_id, current_user_payload=None):
    agent = db.session.get(Agent, agent_id)
    if not agent:
        return jsonify({"errors": ["Agent introuvable."]}), 404
    data = request.get_json(silent=True) or {}
    try:
        points = int(data.get("points"))
    except (TypeError, ValueError):
        return jsonify({"errors": ["Nombre de points invalide."]}), 400

    entry = AgentPoints(
        agent_id=agent_id,
        year=int(data.get("year") or datetime.utcnow().year),
        points=points,
        reason=(data.get("reason") or "").strip() or None,
        lieu=(data.get("lieu") or "").strip() or None,
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({"entry": entry.to_dict(), "agent": agent.to_dict()}), 201


# --- Interventions ---------------------------------------------------------

@agents_bp.get("/<int:agent_id>/interventions")
@admin_required
def list_interventions(agent_id, current_user_payload=None):
    items = Intervention.query.filter_by(agent_id=agent_id).order_by(
        Intervention.created_at.desc()
    ).all()
    return jsonify([i.to_dict() for i in items])


@agents_bp.post("/<int:agent_id>/interventions")
@admin_required
def create_intervention(agent_id, current_user_payload=None):
    agent = db.session.get(Agent, agent_id)
    if not agent:
        return jsonify({"errors": ["Agent introuvable."]}), 404
    data = request.get_json(silent=True) or {}
    resultat = data.get("resultat") if data.get("resultat") in RESULT_POINTS else None

    inter = Intervention(
        agent_id=agent_id,
        alert_id=data.get("alertId"),
        lieu=(data.get("lieu") or "").strip() or None,
        type_mission=(data.get("typeMission") or "").strip() or None,
        duree_minutes=data.get("dureeMinutes"),
        resultat=resultat,
        status="terminee" if resultat else "en_cours",
        notes=(data.get("notes") or "").strip() or None,
    )
    db.session.add(inter)

    # Attribution automatique des points selon l'efficacité (résultat + rapidité).
    awarded = None
    if resultat:
        pts = RESULT_POINTS[resultat]
        try:
            if inter.duree_minutes is not None and int(inter.duree_minutes) <= 30:
                pts += 3  # bonus rapidité
        except (TypeError, ValueError):
            pass
        awarded = AgentPoints(
            agent_id=agent_id, points=pts,
            reason=f"Intervention {resultat}", lieu=inter.lieu,
        )
        db.session.add(awarded)

    db.session.commit()
    return jsonify({
        "intervention": inter.to_dict(),
        "pointsAwarded": awarded.points if awarded else 0,
        "agent": agent.to_dict(),
    }), 201
