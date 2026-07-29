"""Vue « Analyse IA » : zones à risque, heures de pointe, carte de chaleur."""

import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox

RISK_COLORS = {"critique": "#ef4444", "eleve": "#fb923c", "moyen": "#f59e0b", "faible": "#22c55e"}
CATEGORY_LABELS = {
    "vol": "Vol", "agression": "Agression", "accident": "Accident", "incendie": "Incendie",
    "inondation": "Inondation", "electricite": "Électricité", "infrastructure": "Voirie", "autre": "Autre",
}


class AnalysisView(ttk.Frame):
    def __init__(self, parent, api, colors, fonts):
        super().__init__(parent, style="TFrame")
        self.api = api
        self.c = colors
        self.f = fonts

        bar = tk.Frame(self, bg=colors["bg"])
        bar.pack(fill="x", pady=(8, 6))
        tk.Label(bar, text="🧠  ANALYSE PRÉDICTIVE DES ZONES À RISQUE", bg=colors["bg"],
                 fg=colors["muted"], font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        ttk.Button(bar, text="🗺  Heatmap", style="Ghost.TButton", command=self._open_heatmap).pack(side="right", padx=3)
        ttk.Button(bar, text="⟳  Rafraîchir", style="Ghost.TButton", command=self.load).pack(side="right", padx=3)

        self.banner = tk.Frame(self, bg=colors["panel"])
        self.banner.pack(fill="x", padx=4, pady=(0, 8))
        self.banner_var = tk.StringVar(value="Analyse en attente de données…")
        tk.Label(self.banner, textvariable=self.banner_var, bg=colors["panel"], fg=colors["text"],
                 font=fonts["h2"], anchor="w", justify="left").pack(fill="x", padx=16, pady=12)

        body = tk.Frame(self, bg=colors["bg"])
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=colors["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        tk.Label(left, text="ZONES À RISQUE", bg=colors["bg"], fg=colors["muted"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=4, pady=(0, 4))
        self.zones_frame = tk.Frame(left, bg=colors["bg"])
        self.zones_frame.pack(fill="both", expand=True)

        right = tk.Frame(body, bg=colors["bg"], width=420)
        right.pack(side="right", fill="both")
        tk.Label(right, text="HEURES À RISQUE (24 H)", bg=colors["bg"], fg=colors["muted"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=4, pady=(0, 4))
        self.hours_canvas = tk.Canvas(right, bg=colors["panel"], height=180, highlightthickness=0)
        self.hours_canvas.pack(fill="x", padx=4)

    def _open_heatmap(self):
        webbrowser.open(f"{self.api.base}/admin/map?heat=1")

    def load(self):
        try:
            summary = self.api.analysis_summary()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erreur", f"Analyse indisponible :\n{exc}")
            return
        self._render_banner(summary)
        self._render_zones(summary.get("topZones", []))
        self._render_hours(summary.get("byHour", []), summary.get("peakHour"))

    def _render_banner(self, summary):
        rz = summary.get("riskiestZone")
        if not rz:
            self.banner_var.set("Aucune donnée d'incident à analyser pour le moment.")
            return
        ph = summary.get("peakHour")
        heure = f"{ph:02d}h" if ph is not None else "—"
        self.banner_var.set(
            f"⚠ Zone la plus à risque : {rz['zone']}  ·  indice {rz['riskIndex']}/100 "
            f"({rz['riskLevel']})\nHeure de pointe des incidents : {heure}  ·  "
            f"{summary.get('total', 0)} incident(s) analysé(s)"
        )

    def _render_zones(self, zones):
        for child in self.zones_frame.winfo_children():
            child.destroy()
        if not zones:
            tk.Label(self.zones_frame, text="Aucune zone active.", bg=self.c["bg"], fg=self.c["muted"]).pack(anchor="w", padx=6, pady=8)
            return
        for z in zones:
            color = RISK_COLORS.get(z["riskLevel"], self.c["accent"])
            card = tk.Frame(self.zones_frame, bg=self.c["panel"])
            card.pack(fill="x", padx=2, pady=3)
            head = tk.Frame(card, bg=self.c["panel"])
            head.pack(fill="x", padx=12, pady=(8, 2))
            tk.Label(head, text=z["zone"], bg=self.c["panel"], fg=self.c["text"], font=self.f["body"]).pack(side="left")
            tk.Label(head, text=f"{z['riskIndex']:.0f}/100", bg=self.c["panel"], fg=color,
                     font=("Segoe UI", 10, "bold")).pack(side="right")
            track = tk.Frame(card, bg=self.c["panel2"], height=10)
            track.pack(fill="x", padx=12, pady=(0, 4))
            track.pack_propagate(False)
            tk.Frame(track, bg=color, height=10).place(x=0, y=0, relwidth=max(z["riskIndex"] / 100, 0.02), relheight=1)
            info = f"{z['count']} incident(s) · {CATEGORY_LABELS.get(z['dominantCategory'], z['dominantCategory'])} · {z['riskLevel']}"
            tk.Label(card, text=info, bg=self.c["panel"], fg=self.c["muted"], font=self.f["small"]).pack(anchor="w", padx=12, pady=(0, 8))

    def _render_hours(self, by_hour, peak):
        cv = self.hours_canvas
        cv.delete("all")
        by_hour = by_hour or [0] * 24
        cv.update_idletasks()
        w = cv.winfo_width() or 400
        h = 180
        pad = 24
        bar_w = (w - 2 * pad) / 24
        mx = max(by_hour) or 1
        for i, v in enumerate(by_hour):
            x0 = pad + i * bar_w
            bar_h = (v / mx) * (h - 40)
            color = "#e11d48" if i == peak else "#3b82f6"
            cv.create_rectangle(x0 + 1, h - 20 - bar_h, x0 + bar_w - 1, h - 20, fill=color, outline="")
            if i % 3 == 0:
                cv.create_text(x0 + bar_w / 2, h - 8, text=str(i), fill="#8aa0b6", font=("Segoe UI", 7))
