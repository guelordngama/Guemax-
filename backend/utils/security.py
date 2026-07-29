"""Sécurité : hachage des mots de passe, jetons JWT et décorateurs d'accès."""

from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import current_app, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


def generate_token(user):
    """Crée un JWT signé pour l'utilisateur donné."""
    payload = {
        "sub": user.id,
        "username": user.username,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(hours=current_app.config["JWT_EXPIRES_HOURS"]),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def decode_token(token):
    """Décode un JWT et renvoie sa charge utile, ou ``None`` si invalide."""
    try:
        return jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def _extract_token():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:]
    return None


def token_required(fn):
    """Exige un JWT valide ; injecte ``current_user_payload`` dans kwargs."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        payload = decode_token(token) if token else None
        if not payload:
            return jsonify({"errors": ["Authentification requise."]}), 401
        kwargs["current_user_payload"] = payload
        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    """Exige un JWT valide avec le rôle ``admin``."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_token()
        payload = decode_token(token) if token else None
        if not payload:
            return jsonify({"errors": ["Authentification requise."]}), 401
        if payload.get("role") != "admin":
            return jsonify({"errors": ["Accès réservé à l'administration."]}), 403
        kwargs["current_user_payload"] = payload
        return fn(*args, **kwargs)

    return wrapper
