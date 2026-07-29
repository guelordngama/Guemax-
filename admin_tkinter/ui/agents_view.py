"""Vue « Gestion des agents » : statuts en temps réel + points de performance."""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

STATUS_META = {
    "disponible": ("ACTIF", "#22c55e"),
    "en_mission": ("EN MISSION", "#38bdf8"),
    "absent": ("ABSENT", "#f59e0b"),
    "hors_ligne": ("HORS LIGNE", "#94a3b8"),
}
STATUS_ORDER = ["disponible", "en_mission", "absent", "hors_ligne"]
RESULTATS = ["reussie", "partielle", "echouee"]


class AgentsView(ttk.Frame):
    def __init__(self, parent, api, colors, fonts):
        super().__init__(parent, style="TFrame")
        self.api = api
        self.c = colors
        self.f = fonts
        self._build_summary()
        self._build_toolbar()
        self._build_list()

    # -------------------------------------------------------------- summary
    def _build_summary(self):
        c = self.c
        row = tk.Frame(self, bg=c["bg"])
        row.pack(fill="x", pady=(8, 6))
        self.summary_vars = {}
        for status in STATUS_ORDER:
            label, color = STATUS_META[status]
            card = tk.Frame(row, bg=c["panel"])
            card.pack(side="left", expand=True, fill="both", padx=5)
            tk.Frame(card, bg=color, height=3).pack(fill="x")
            var = tk.StringVar(value="0")
            tk.Label(card, textvariable=var, bg=c["panel"], fg=c["text"], font=self.f["kpi"]).pack(anchor="w", padx=14, pady=(8, 0))
            tk.Label(card, text=label, bg=c["panel"], fg=c["muted"], font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=14, pady=(0, 10))
            self.summary_vars[status] = var

    def _build_toolbar(self):
        c = self.c
        bar = tk.Frame(self, bg=c["bg"])
        bar.pack(fill="x", pady=(2, 6))
        tk.Label(bar, text="AGENTS & PERFORMANCE", bg=c["bg"], fg=c["muted"],
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ttk.Button(bar, text="⟳  Rafraîchir", style="Ghost.TButton", command=self.load).pack(side="right")

    # ----------------------------------------------------------------- liste
    def _build_list(self):
        c = self.c
        container = tk.Frame(self, bg=c["bg"])
        container.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(container, bg=c["bg"], highlightthickness=0)
        scroll = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=c["bg"])
        self.inner.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self._win, width=e.width))
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    # --------------------------------------------------------------- données
    def load(self):
        try:
            summary = self.api.agents_summary()
            agents = self.api.list_agents()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erreur", f"Chargement des agents impossible :\n{exc}")
            return
        for status in STATUS_ORDER:
            self.summary_vars[status].set(str(summary.get("byStatus", {}).get(status, 0)))
        self._render_agents(agents)

    def _render_agents(self, agents):
        for child in self.inner.winfo_children():
            child.destroy()
        if not agents:
            tk.Label(self.inner, text="Aucun agent.", bg=self.c["bg"], fg=self.c["muted"]).pack(anchor="w", padx=6, pady=10)
            return
        max_pts = max((a["totalPoints"] for a in agents), default=0) or 1
        for a in sorted(agents, key=lambda x: x["totalPoints"], reverse=True):
            self._agent_card(a, max_pts)

    def _agent_card(self, agent, max_pts):
        c, f = self.c, self.f
        card = tk.Frame(self.inner, bg=c["panel"])
        card.pack(fill="x", padx=4, pady=4)
        label, color = STATUS_META.get(agent["status"], ("—", c["muted"]))

        head = tk.Frame(card, bg=c["panel"])
        head.pack(fill="x", padx=14, pady=(10, 4))
        tk.Label(head, text=agent["name"], bg=c["panel"], fg=c["text"], font=f["h2"]).pack(side="left")
        meta = f"{agent.get('matricule') or ''}  ·  {agent.get('grade') or ''}".strip(" ·")
        tk.Label(head, text=meta, bg=c["panel"], fg=c["muted"], font=f["small"]).pack(side="left", padx=10)
        tk.Label(head, text=label, bg=color, fg="#0b1220", font=("Segoe UI", 8, "bold"),
                 padx=8, pady=1).pack(side="right")

        # Barre de points
        barrow = tk.Frame(card, bg=c["panel"])
        barrow.pack(fill="x", padx=14, pady=(2, 4))
        pb = ttk.Progressbar(barrow, style="Score.Horizontal.TProgressbar",
                             maximum=max_pts, value=agent["totalPoints"], length=100)
        pb.pack(side="left", fill="x", expand=True)
        tk.Label(barrow, text=f"{agent['totalPoints']} pts  ({agent['pointsThisYear']} cette année)",
                 bg=c["panel"], fg=c["accent"], font=f["small"]).pack(side="left", padx=10)

        # Actions
        actions = tk.Frame(card, bg=c["panel"])
        actions.pack(fill="x", padx=14, pady=(2, 10))
        status_cb = ttk.Combobox(actions, width=12, state="readonly", values=STATUS_ORDER)
        status_cb.set(agent["status"])
        status_cb.pack(side="left")
        status_cb.bind("<<ComboboxSelected>>", lambda _e, ag=agent, cb=status_cb: self._change_status(ag, cb.get()))
        ttk.Button(actions, text="+ Points", style="Ghost.TButton",
                   command=lambda ag=agent: self._award(ag)).pack(side="left", padx=6)
        ttk.Button(actions, text="Nouvelle intervention", style="Ghost.TButton",
                   command=lambda ag=agent: self._intervention(ag)).pack(side="left")

    # --------------------------------------------------------------- actions
    def _change_status(self, agent, status):
        try:
            self.api.set_agent_status(agent["id"], status)
            self.load()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erreur", str(exc))

    def _award(self, agent):
        pts = simpledialog.askinteger("Attribuer des points", f"Points à attribuer à {agent['name']} :",
                                      parent=self, minvalue=1, maxvalue=1000)
        if not pts:
            return
        reason = simpledialog.askstring("Motif", "Motif (facultatif) :", parent=self) or ""
        try:
            self.api.award_points(agent["id"], pts, reason)
            self.load()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erreur", str(exc))

    def _intervention(self, agent):
        InterventionDialog(self, self.api, agent, on_done=self.load, colors=self.c, fonts=self.f)


class InterventionDialog(tk.Toplevel):
    """Petite fenêtre pour enregistrer une intervention (avec points auto)."""

    def __init__(self, parent, api, agent, on_done, colors, fonts):
        super().__init__(parent)
        self.api = api
        self.agent = agent
        self.on_done = on_done
        c = colors
        self.title(f"Intervention — {agent['name']}")
        self.configure(bg=c["panel"])
        self.geometry("360x330")
        self.resizable(False, False)

        pad = {"padx": 18, "pady": 4}
        tk.Label(self, text=f"Agent : {agent['name']}", bg=c["panel"], fg=c["text"], font=fonts["h2"]).pack(anchor="w", **pad)

        tk.Label(self, text="Type de mission", bg=c["panel"], fg=c["muted"]).pack(anchor="w", **pad)
        self.type_e = ttk.Entry(self)
        self.type_e.pack(fill="x", **pad)

        tk.Label(self, text="Lieu", bg=c["panel"], fg=c["muted"]).pack(anchor="w", **pad)
        self.lieu_e = ttk.Entry(self)
        self.lieu_e.pack(fill="x", **pad)

        tk.Label(self, text="Durée (minutes)", bg=c["panel"], fg=c["muted"]).pack(anchor="w", **pad)
        self.duree_e = ttk.Entry(self)
        self.duree_e.pack(fill="x", **pad)

        tk.Label(self, text="Résultat", bg=c["panel"], fg=c["muted"]).pack(anchor="w", **pad)
        self.res_cb = ttk.Combobox(self, state="readonly", values=RESULTATS)
        self.res_cb.set("reussie")
        self.res_cb.pack(fill="x", **pad)

        ttk.Button(self, text="Enregistrer", style="Accent.TButton", command=self._save).pack(fill="x", padx=18, pady=12)

    def _save(self):
        payload = {
            "typeMission": self.type_e.get().strip(),
            "lieu": self.lieu_e.get().strip(),
            "resultat": self.res_cb.get(),
        }
        try:
            payload["dureeMinutes"] = int(self.duree_e.get())
        except ValueError:
            payload["dureeMinutes"] = None
        try:
            res = self.api.create_intervention(self.agent["id"], payload)
            messagebox.showinfo("Intervention", f"Enregistrée. Points attribués : {res.get('pointsAwarded', 0)}")
            self.destroy()
            self.on_done()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erreur", str(exc))
