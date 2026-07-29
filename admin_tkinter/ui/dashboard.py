"""Tableau de bord de la mairie : alertes, statistiques, carte live, temps réel."""

import tkinter as tk
import webbrowser
from tkinter import ttk

from ui.alerts_view import AlertsView
from ui.stats_view import StatsView
from services.socket_client import SocketClient


class Dashboard:
    def __init__(self, root, api, user):
        self.root = root
        self.api = api
        self.user = user

        root.title("SafeCity Lubumbashi — Tableau de bord mairie")
        root.geometry("980x620")
        root.deiconify()
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_topbar()

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.alerts_view = AlertsView(notebook, api)
        self.stats_view = StatsView(notebook, api)
        notebook.add(self.alerts_view, text="  🚨 Alertes  ")
        notebook.add(self.stats_view, text="  📊 Statistiques  ")

        self._load_all()
        self._connect_socket()

    # --- Interface ---------------------------------------------------------
    def _build_topbar(self):
        bar = ttk.Frame(self.root, padding=(12, 10))
        bar.pack(fill="x")

        ttk.Label(bar, text="🚨 SafeCity Lubumbashi", font=("Segoe UI", 14, "bold")).pack(side="left")
        ttk.Label(bar, text=f"  ·  Connecté : {self.user['username']}").pack(side="left")

        self.presence_var = tk.StringVar(value="● 0 citoyen(s) en ligne")
        ttk.Label(bar, textvariable=self.presence_var, foreground="#16a34a").pack(side="right", padx=(8, 0))
        ttk.Button(bar, text="🔄 Rafraîchir", command=self._load_all).pack(side="right", padx=4)
        ttk.Button(bar, text="🗺️ Ouvrir la carte live", command=self._open_map).pack(side="right", padx=4)

    def _open_map(self):
        webbrowser.open(f"{self.api.base}/admin/map")

    # --- Données -----------------------------------------------------------
    def _load_all(self):
        self.alerts_view.load()
        self.stats_view.load()

    def _refresh_stats(self):
        self.stats_view.load()

    # --- Temps réel --------------------------------------------------------
    def _connect_socket(self):
        # Les callbacks arrivent depuis un thread d'arrière-plan : on repasse
        # sur le thread principal Tkinter via root.after.
        self.socket = SocketClient(
            self.api.base,
            on_new=lambda a: self.root.after(0, self._on_new, a),
            on_update=lambda a: self.root.after(0, self._on_update, a),
            on_presence=lambda p: self.root.after(0, self._on_presence, p),
        )
        self.socket.connect()

    def _on_new(self, alert):
        self.alerts_view.upsert(alert)
        self._refresh_stats()

    def _on_update(self, alert):
        self.alerts_view.upsert(alert)
        self._refresh_stats()

    def _on_presence(self, payload):
        self.presence_var.set(f"● {payload.get('online', 0)} citoyen(s) en ligne")

    def _on_close(self):
        try:
            self.socket.disconnect()
        except Exception:  # noqa: BLE001
            pass
        self.root.destroy()
