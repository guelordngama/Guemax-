"""Canal temps réel (Socket.IO).

On expose une unique instance ``socketio`` initialisée dans ``app.py`` et
importée par les routes pour diffuser les événements aux clients connectés
(site citoyen + tableau de bord mairie).
"""

from flask_socketio import SocketIO

# ``threading`` évite toute dépendance native (eventlet/gevent) : démarre partout.
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")

# Nombre de clients actuellement connectés (présence).
_connected = 0


@socketio.on("connect")
def _on_connect():
    global _connected
    _connected += 1
    socketio.emit("presence", {"online": _connected})


@socketio.on("disconnect")
def _on_disconnect():
    global _connected
    _connected = max(0, _connected - 1)
    socketio.emit("presence", {"online": _connected})


def emit_new_alert(alert_dict):
    socketio.emit("alert:new", alert_dict)


def emit_alert_update(alert_dict):
    socketio.emit("alert:update", alert_dict)
