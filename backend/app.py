"""SafeCity Lubumbashi — application Flask.

Assemble l'API REST, le canal temps réel (Socket.IO), la base de données et
sert le site citoyen (``web_citizen``) ainsi que la carte du tableau de bord
de la mairie.

Lancement :  python app.py   (depuis le dossier backend/)
"""

import os
import sys

# Permet les imports absolus (models, database, routes...) quel que soit le cwd.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import Config, LUBUMBASHI_CENTER
from database import init_db
from routes import register_routes
from socket_events import socketio
from utils.helpers import CATEGORIES, SEVERITIES

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_CITIZEN_DIR = os.path.join(PROJECT_DIR, "web_citizen")
ADMIN_MAP_DIR = os.path.join(PROJECT_DIR, "admin_tkinter", "map")


def create_app(config_object=Config):
    app = Flask(__name__, static_folder=WEB_CITIZEN_DIR, static_url_path="")
    app.config.from_object(config_object)

    CORS(app)
    init_db(app)
    register_routes(app)
    socketio.init_app(app)

    # --- Configuration partagée avec le frontend ---------------------------
    @app.get("/api/config")
    def api_config():
        return jsonify(
            {"center": LUBUMBASHI_CENTER, "categories": CATEGORIES, "severities": SEVERITIES}
        )

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    # --- Site citoyen ------------------------------------------------------
    @app.get("/")
    def citizen_home():
        return send_from_directory(WEB_CITIZEN_DIR, "index.html")

    # --- Carte du tableau de bord (ouverte par l'app Tkinter de la mairie) --
    @app.get("/admin/map")
    def admin_map():
        return send_from_directory(ADMIN_MAP_DIR, "leaflet_view.html")

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    print("\n🚨  SafeCity Lubumbashi — serveur Flask")
    print(f"    Site citoyen  : http://localhost:{port}/")
    print(f"    Carte mairie  : http://localhost:{port}/admin/map")
    print(f"    API           : http://localhost:{port}/api/\n")
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
