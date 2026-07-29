"""Tableau de bord « centre de commandement » de la mairie.

Topbar, indicateurs KPI, onglets (alertes, statistiques), horloge et barre de
statut. Ne traite que les alertes de Lubumbashi et se met à jour en temps réel.
"""

import time
import tkinter as tk
import webbrowser
from tkinter import ttk

from ui.theme import apply_theme
from ui.alerts_view import AlertsView
from ui.stats_view import StatsView
from services.socket_client import SocketClient


class Dashboard:
    def __init__(self, root, api, user):
        self.root = root
        self.api = api
        self.user = user
        self.style, self.c, self.f = apply_theme(root)

        # Emprise géographique (Lubumbashi) pour filtrer le temps réel.
        try:
            self.bounds = self.api.get_config().get("bounds")
        except Exception:
            self.bounds = None

        root.title("SafeCity Lubumbashi — Centre de commandement")
        root.geometry("1180x720")
        root.minsize(1000, 640)
        root.deiconify()
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_topbar()
        self._build_kpis()
        self._build_body()
        self._build_statusbar()

        self._tick_clock()
        self._load_all()
        self._connect_socket()

    # ---------------------------------------------------------------- Topbar
    def _build_topbar(self):
        c, f = self.c, self.f
        bar = tk.Frame(self.root, bg=c["panel"], height=64)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        left = tk.Frame(bar, bg=c["panel"])
        left.pack(side="left", padx=18)
        tk.Label(left, text="🚨", bg=c["panel"], fg=c["primary"], font=("Segoe UI Emoji", 22)).pack(side="left", padx=(0, 10))
        titles = tk.Frame(left, bg=c["panel"])
        titles.pack(side="left")
        tk.Label(titles, text="SafeCity Lubumbashi", bg=c["panel"], fg=c["text"], font=f["title"]).pack(anchor="w")
        tk.Label(titles, text="CENTRE DE COMMANDEMENT · SÉCURITÉ", bg=c["panel"], fg=c["muted"],
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")

        right = tk.Frame(bar, bg=c["panel"])
        right.pack(side="right", padx=18)
        ttk.Button(right, text="🗺  Carte live", style="Ghost.TButton", command=self._open_map).pack(side="right", padx=4)
        ttk.Button(right, text="⟳  Rafraîchir", style="Ghost.TButton", command=self._load_all).pack(side="right", padx=4)

        self.clock_var = tk.StringVar(value="--:--:--")
        tk.Label(right, textvariable=self.clock_var, bg=c["panel"], fg=c["accent"], font=f["mono"]).pack(side="right", padx=14)

        self.presence_var = tk.StringVar(value="0")
        pres = tk.Frame(right, bg=c["panel"])
        pres.pack(side="right", padx=10)
        tk.Label(pres, text="👥", bg=c["panel"], fg=c["muted"]).pack(side="left")
        tk.Label(pres, textvariable=self.presence_var, bg=c["panel"], fg=c["text"], font=f["h2"]).pack(side="left", padx=(4, 0))

        # Indicateur de connexion
        self.conn_dot = tk.Label(right, text="●", bg=c["panel"], fg=c["amber"], font=("Segoe UI", 12))
        self.conn_dot.pack(side="right", padx=(10, 2))
        self.conn_var = tk.StringVar(value="Connexion…")
        tk.Label(right, textvariable=self.conn_var, bg=c["panel"], fg=c["muted"], font=f["small"]).pack(side="right")

    # ------------------------------------------------------------------ KPIs
    def _build_kpis(self):
        c = self.c
        row = tk.Frame(self.root, bg=c["bg"])
        row.pack(fill="x", padx=14, pady=(14, 6))
        self.kpi = {}
        specs = [
            ("total", "TOTAL ALERTES", c["accent"]),
            ("actives", "ACTIVES", c["primary"]),
            ("critiques", "PRIORITÉ CRITIQUE", c["red"]),
            ("resolues", "RÉSOLUES", c["green"]),
            ("agents", "AGENTS", c["blue"]),
        ]
        for key, label, color in specs:
            card = tk.Frame(row, bg=c["panel"], highlightthickness=0)
            card.pack(side="left", expand=True, fill="both", padx=6)
            tk.Frame(card, bg=color, height=3).pack(fill="x")
            inner = tk.Frame(card, bg=c["panel"])
            inner.pack(fill="both", expand=True, padx=16, pady=12)
            var = tk.StringVar(value="0")
            tk.Label(inner, textvariable=var, bg=c["panel"], fg=c["text"], font=self.f["kpi"]).pack(anchor="w")
            tk.Label(inner, text=label, bg=c["panel"], fg=c["muted"], font=("Segoe UI", 8, "bold")).pack(anchor="w")
            self.kpi[key] = var

    # ------------------------------------------------------------------ Body
    def _build_body(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=14, pady=(6, 8))
        self.alerts_view = AlertsView(notebook, self.api, self.c, self.f)
        self.stats_view = StatsView(notebook, self.api, self.c, self.f)
        notebook.add(self.alerts_view, text="  🚨  Alertes  ")
        notebook.add(self.stats_view, text="  📊  Statistiques  ")

    def _build_statusbar(self):
        c, f = self.c, self.f
        bar = tk.Frame(self.root, bg=c["panel"], height=26)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.status_var = tk.StringVar(value="Prêt")
        tk.Label(bar, textvariable=self.status_var, bg=c["panel"], fg=c["muted"], font=f["small"]).pack(side="left", padx=14)
        tk.Label(bar, text="🛰  Zone : LUBUMBASHI uniquement", bg=c["panel"], fg=c["muted"], font=f["small"]).pack(side="left", padx=14)
        tk.Label(bar, text=f"Opérateur : {self.user['username']}", bg=c["panel"], fg=c["muted"], font=f["small"]).pack(side="right", padx=14)

    # -------------------------------------------------------------- Horloge
    def _tick_clock(self):
        self.clock_var.set(time.strftime("%H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    # --------------------------------------------------------------- Données
    def _open_map(self):
        webbrowser.open(f"{self.api.base}/admin/map")

    def _load_all(self):
        self.alerts_view.load()
        self.stats_view.load()
        self._refresh_kpis()
        self.status_var.set(f"Données actualisées à {time.strftime('%H:%M:%S')}")

    def _refresh_kpis(self):
        try:
            stats = self.api.get_stats()
        except Exception:
            return
        self.kpi["total"].set(str(stats.get("total", 0)))
        self.kpi["actives"].set(str(stats.get("byStatus", {}).get("actif", 0)))
        self.kpi["critiques"].set(str(stats.get("byPriority", {}).get("critique", 0)))
        self.kpi["resolues"].set(str(stats.get("byStatus", {}).get("resolu", 0)))
        try:
            self.kpi["agents"].set(str(len(self.api.list_agents())))
        except Exception:
            pass

    # ------------------------------------------------------------- Temps réel
    def _in_scope(self, alert):
        if not self.bounds:
            return True
        b = self.bounds
        return (b["min_lat"] <= alert["lat"] <= b["max_lat"]
                and b["min_lng"] <= alert["lng"] <= b["max_lng"])

    def _connect_socket(self):
        self.socket = SocketClient(
            self.api.base,
            on_new=lambda a: self.root.after(0, self._on_new, a),
            on_update=lambda a: self.root.after(0, self._on_update, a),
            on_presence=lambda p: self.root.after(0, self._on_presence, p),
            on_connect=lambda: self.root.after(0, self._set_conn, True),
            on_disconnect=lambda: self.root.after(0, self._set_conn, False),
        )
        self.socket.connect()

    def _set_conn(self, ok):
        self.conn_dot.config(fg=self.c["green"] if ok else self.c["red"])
        self.conn_var.set("En ligne" if ok else "Hors ligne")

    def _on_new(self, alert):
        if not self._in_scope(alert):
            return  # alerte hors de Lubumbashi : ignorée
        self.alerts_view.upsert(alert)
        self._refresh_kpis()
        self.status_var.set(f"⚠ Nouvelle alerte reçue à {time.strftime('%H:%M:%S')}")

    def _on_update(self, alert):
        if not self._in_scope(alert):
            return
        self.alerts_view.upsert(alert)
        self._refresh_kpis()

    def _on_presence(self, payload):
        self.presence_var.set(str(payload.get("online", 0)))

    def _on_close(self):
        try:
            self.socket.disconnect()
        except Exception:
            pass
        self.root.destroy()
