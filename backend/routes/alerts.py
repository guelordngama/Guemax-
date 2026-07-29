"""Routes des alertes : création citoyenne, consultation, confirmation, statut."""

from flask import Blueprint, current_app, jsonify, request

from database import db
from models import Alert
from socket_events import emit_alert_update, emit_new_alert
from utils.classification_ai import classify_priority
from utils.helpers import STATUSES, save_photo, validate_alert
from utils.security import decode_token


def _current_user_id():
    """Identifiant du citoyen connecté si un jeton valide est fourni, sinon None."""
    header = request.headers.get("Authorization", "")
    token = header[7:] if header.startswith("Bearer ") else None
    payload = decode_token(token) if token else None
    return payload["sub"] if payload else None

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.get("")
def list_alerts():
    """Liste des alertes, du plus récent au plus ancien.

    Filtre facultatif ``?status=`` et ``?category=``.
    """
    query = Alert.query
    status = request.args.get("status")
    category = request.args.get("category")
    if status in STATUSES:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    alerts = query.order_by(Alert.created_at.desc()).all()
    return jsonify([a.to_dict() for a in alerts])


@alerts_bp.post("")
def create_alert():
    """Signalement d'une alerte par un citoyen (anonyme, sans authentification)."""
    data = request.get_json(silent=True) or {}
    errors, clean = validate_alert(data)
    if errors:
        return jsonify({"errors": errors}), 400

    photo = save_photo(
        data.get("photo"),
        current_app.config["UPLOAD_DIR"],
        current_app.config["MAX_PHOTO_BYTES"],
    )
    priority, score = classify_priority(clean["category"], clean["severity"], clean["description"])

    alert = Alert(
        category=clean["category"],
        severity=clean["severity"],
        description=clean["description"],
        lat=clean["lat"],
        lng=clean["lng"],
        address=clean["address"],
        photo=photo,
        priority=priority,
        priority_score=score,
        user_id=_current_user_id(),
    )
    db.session.add(alert)
    db.session.commit()

    emit_new_alert(alert.to_dict())  # diffusion temps réel vers la mairie
    return jsonify(alert.to_dict()), 201


@alerts_bp.get("/<int:alert_id>")
def get_alert(alert_id):
    alert = db.session.get(Alert, alert_id)
    if not alert:
        return jsonify({"errors": ["Alerte introuvable."]}), 404
    return jsonify(alert.to_dict())


@alerts_bp.post("/<int:alert_id>/confirm")
def confirm_alert(alert_id):
    alert = db.session.get(Alert, alert_id)
    if not alert:
        return jsonify({"errors": ["Alerte introuvable."]}), 404
    alert.confirmations += 1
    db.session.commit()
    emit_alert_update(alert.to_dict())
    return jsonify(alert.to_dict())


@alerts_bp.patch("/<int:alert_id>/status")
def update_status(alert_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in STATUSES:
        return jsonify({"errors": ["Statut invalide."]}), 400
    alert = db.session.get(Alert, alert_id)
    if not alert:
        return jsonify({"errors": ["Alerte introuvable."]}), 404
    alert.status = status
    db.session.commit()
    emit_alert_update(alert.to_dict())
    return jsonify(alert.to_dict())


@alerts_bp.get("/stats/summary")
def stats():
    """Statistiques agrégées pour le tableau de bord de la mairie."""
    alerts = Alert.query.all()
    by_status = {"actif": 0, "verifie": 0, "resolu": 0}
    by_category = {}
    by_priority = {"basse": 0, "moyenne": 0, "haute": 0, "critique": 0}
    for a in alerts:
        by_status[a.status] = by_status.get(a.status, 0) + 1
        by_category[a.category] = by_category.get(a.category, 0) + 1
        by_priority[a.priority] = by_priority.get(a.priority, 0) + 1
    return jsonify(
        {
            "total": len(alerts),
            "byStatus": by_status,
            "byCategory": by_category,
            "byPriority": by_priority,
        }
    )
