"""Enregistrement centralisé des blueprints de l'API."""

from routes.auth import auth_bp
from routes.alerts import alerts_bp
from routes.users import users_bp


def register_routes(app):
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(alerts_bp, url_prefix="/api/alerts")
    app.register_blueprint(users_bp, url_prefix="/api/users")
