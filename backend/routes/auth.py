"""Routes d'authentification : inscription citoyenne, validation par code,
connexion et création de comptes internes (agent/admin)."""

import secrets
from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request

from database import db
from models import User
from utils.security import (
    admin_required,
    decode_token,
    generate_token,
    hash_password,
    verify_password,
)

auth_bp = Blueprint("auth", __name__)


def _generate_code():
    """Code de validation à 6 chiffres."""
    return f"{secrets.randbelow(1_000_000):06d}"


def _issue_code(user):
    """Génère, stocke et « envoie » un code de validation.

    En mode démo, le code est journalisé et renvoyé par l'API. Pour un envoi
    réel, brancher ici un service SMTP/SMS et désactiver AUTH_DEV_MODE.
    """
    code = _generate_code()
    user.verification_code = code
    user.verification_expires = datetime.utcnow() + timedelta(
        minutes=current_app.config["VERIFICATION_TTL_MINUTES"]
    )
    db.session.commit()
    print(f"[AUTH] Code de validation pour {user.username} : {code}")
    return code


def _dev_code_payload(code):
    """Inclut le code dans la réponse uniquement en mode démo."""
    return {"devCode": code} if current_app.config.get("AUTH_DEV_MODE") else {}


# --- Inscription citoyenne (1re visite) ------------------------------------

@auth_bp.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    nom = (data.get("nom") or "").strip()
    post_nom = (data.get("postNom") or data.get("post_nom") or "").strip()
    prenom = (data.get("prenom") or "").strip()
    sexe = (data.get("sexe") or "").strip()
    ville = (data.get("ville") or "").strip()
    commune = (data.get("commune") or "").strip()
    quartier = (data.get("quartier") or "").strip()
    nationalite = (data.get("nationalite") or "").strip()
    telephone = (data.get("telephone") or "").strip()
    date_naissance = (data.get("dateNaissance") or data.get("date_naissance") or "").strip()

    errors = []
    if len(nom) < 2:
        errors.append("Le nom est requis.")
    if len(username) < 3:
        errors.append("Le nom d'utilisateur doit contenir au moins 3 caractères.")
    if "@" not in email or "." not in email:
        errors.append("Adresse e-mail invalide.")
    if len(password) < 6:
        errors.append("Le mot de passe doit contenir au moins 6 caractères.")
    if not ville:
        errors.append("La ville est requise.")
    if User.query.filter((User.username == username) | (User.email == email)).first():
        errors.append("Nom d'utilisateur ou e-mail déjà utilisé.")
    if errors:
        return jsonify({"errors": errors}), 400

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role="citizen",
        nom=nom,
        post_nom=post_nom or None,
        prenom=prenom or None,
        sexe=sexe or None,
        ville=ville,
        commune=commune or None,
        quartier=quartier or None,
        nationalite=nationalite or None,
        telephone=telephone or None,
        date_naissance=date_naissance or None,
        is_verified=False,
    )
    db.session.add(user)
    db.session.commit()

    code = _issue_code(user)
    return jsonify({
        "message": "Compte créé. Un code de validation vous a été envoyé.",
        "username": user.username,
        **_dev_code_payload(code),
    }), 201


# --- Validation du compte par code -----------------------------------------

@auth_bp.post("/verify")
def verify():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    code = (data.get("code") or "").strip()

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"errors": ["Compte introuvable."]}), 404
    if user.is_verified:
        return jsonify({"token": generate_token(user), "user": user.to_dict()})
    if not user.verification_code or user.verification_code != code:
        return jsonify({"errors": ["Code de validation incorrect."]}), 400
    if user.verification_expires and datetime.utcnow() > user.verification_expires:
        return jsonify({"errors": ["Code expiré. Veuillez en demander un nouveau."]}), 400

    user.is_verified = True
    user.verification_code = None
    user.verification_expires = None
    db.session.commit()
    return jsonify({"token": generate_token(user), "user": user.to_dict()})


@auth_bp.post("/resend")
def resend():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"errors": ["Compte introuvable."]}), 404
    if user.is_verified:
        return jsonify({"message": "Compte déjà validé."})
    code = _issue_code(user)
    return jsonify({"message": "Nouveau code envoyé.", **_dev_code_payload(code)})


# --- Mot de passe oublié ----------------------------------------------------

@auth_bp.post("/forgot")
def forgot():
    """Demande de réinitialisation : envoie un code par e-mail (mode démo)."""
    data = request.get_json(silent=True) or {}
    ident = (data.get("username") or data.get("email") or "").strip()
    user = User.query.filter(
        (User.username == ident) | (User.email == ident)
    ).first()
    # Réponse volontairement neutre pour ne pas divulguer l'existence du compte.
    if not user:
        return jsonify({"message": "Si le compte existe, un code a été envoyé."})
    code = _issue_code(user)
    return jsonify({"message": "Si le compte existe, un code a été envoyé.",
                    "username": user.username, **_dev_code_payload(code)})


@auth_bp.post("/reset")
def reset():
    """Réinitialise le mot de passe à l'aide du code reçu."""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    code = (data.get("code") or "").strip()
    new_password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not user.verification_code or user.verification_code != code:
        return jsonify({"errors": ["Code de réinitialisation incorrect."]}), 400
    if user.verification_expires and datetime.utcnow() > user.verification_expires:
        return jsonify({"errors": ["Code expiré. Veuillez recommencer."]}), 400
    if len(new_password) < 6:
        return jsonify({"errors": ["Le mot de passe doit contenir au moins 6 caractères."]}), 400

    user.password_hash = hash_password(new_password)
    user.verification_code = None
    user.verification_expires = None
    user.is_verified = True  # la maîtrise de l'e-mail est prouvée
    db.session.commit()
    return jsonify({"token": generate_token(user), "user": user.to_dict()})


# --- Connexion --------------------------------------------------------------

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(user.password_hash, password):
        return jsonify({"errors": ["Identifiants incorrects."]}), 401

    if user.role == "citizen" and not user.is_verified:
        return jsonify({
            "errors": ["Compte non validé. Veuillez saisir le code de validation."],
            "needsVerification": True,
            "username": user.username,
        }), 403

    return jsonify({"token": generate_token(user), "user": user.to_dict()})


# --- Comptes internes (agent/admin), réservé à l'administration -------------

@auth_bp.post("/register")
@admin_required
def register(current_user_payload=None):
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

    user = User(
        username=username, email=email, password_hash=hash_password(password),
        role=role, is_verified=True,
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"user": user.to_dict()}), 201


@auth_bp.get("/me")
def me():
    header = request.headers.get("Authorization", "")
    token = header[7:] if header.startswith("Bearer ") else None
    payload = decode_token(token) if token else None
    if not payload:
        return jsonify({"errors": ["Authentification requise."]}), 401
    user = db.session.get(User, payload["sub"])
    if not user:
        return jsonify({"errors": ["Utilisateur introuvable."]}), 404
    return jsonify({"user": user.to_dict()})
