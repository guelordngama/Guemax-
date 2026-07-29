"""Client Socket.IO temps réel (côté mairie).

Le client tourne dans un thread d'arrière-plan. Comme Tkinter n'est pas
thread-safe, les callbacks fournis doivent reprogrammer les mises à jour d'UI
sur le thread principal (typiquement via ``root.after``).
"""

import socketio


class SocketClient:
    def __init__(self, base_url, on_new=None, on_update=None, on_presence=None,
                 on_connect=None, on_disconnect=None):
        self.base = base_url.rstrip("/")
        self.sio = socketio.Client(reconnection=True)

        @self.sio.event
        def connect():
            if on_connect:
                on_connect()

        @self.sio.event
        def disconnect():
            if on_disconnect:
                on_disconnect()

        @self.sio.on("alert:new")
        def _new(data):
            if on_new:
                on_new(data)

        @self.sio.on("alert:update")
        def _update(data):
            if on_update:
                on_update(data)

        @self.sio.on("presence")
        def _presence(data):
            if on_presence:
                on_presence(data)

    def connect(self):
        try:
            self.sio.connect(self.base)
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"[socket] Connexion impossible : {exc}")
            return False

    def disconnect(self):
        try:
            self.sio.disconnect()
        except Exception:  # noqa: BLE001
            pass
