"""Routes d'authentification : connexion et enregistrement de comptes."""

from flask import Blueprint, jsonify, request

from database import db
from models import User
from utils.security import (
    admin_required,
    generate_token,
    hash_password,
    verify_password,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(user.password_hash, password):
        return jsonify({"errors": ["Identifiants incorrects."]}), 401

    return jsonify({"token": generate_token(user), "user": user.to_dict()})


@auth_bp.post("/register")
@admin_required
def register(current_user_payload=None):
    """Création d'un compte (agent ou admin). Réservé à l'administration."""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    role = data.get("role") if data.get("role") in ("agent", "admin") else "agent"

    errors = []
    if len(username) < 3:
        errors.append("Nom d'utilisateur trop court (min 3 caractères).")
    if "@" not in email:
        errors.append("Adresse e-mail invalide.")
    if len(password) < 6:
        errors.append("Mot de passe trop court (min 6 caractères).")
    if User.query.filter((User.username == username) | (User.email == email)).first():
        errors.append("Nom d'utilisateur ou e-mail déjà utilisé.")
    if errors:
        return jsonify({"errors": errors}), 400

    user = User(username=username, email=email, password_hash=hash_password(password), role=role)
    db.session.add(user)
    db.session.commit()
    return jsonify({"user": user.to_dict()}), 201


@auth_bp.get("/me")
def me():
    from utils.security import decode_token

    header = request.headers.get("Authorization", "")
    token = header[7:] if header.startswith("Bearer ") else None
    payload = decode_token(token) if token else None
    if not payload:
        return jsonify({"errors": ["Authentification requise."]}), 401
    user = db.session.get(User, payload["sub"])
    if not user:
        return jsonify({"errors": ["Utilisateur introuvable."]}), 404
    return jsonify({"user": user.to_dict()})
