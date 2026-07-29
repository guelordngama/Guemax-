"""Vue statistiques : répartition par catégorie et par priorité."""

import tkinter as tk
from tkinter import ttk

CATEGORY_LABELS = {
    "vol": "Vol / Cambriolage", "agression": "Agression", "accident": "Accident",
    "incendie": "Incendie", "inondation": "Inondation", "electricite": "Électricité",
    "infrastructure": "Voirie", "autre": "Autre",
}
PRIORITY_COLORS = {"basse": "#22c55e", "moyenne": "#f59e0b", "haute": "#fb923c", "critique": "#ef4444"}


class StatsView(ttk.Frame):
    def __init__(self, parent, api, colors, fonts):
        super().__init__(parent, style="TFrame")
        self.api = api
        self.c = colors
        self.f = fonts

        wrap = tk.Frame(self, bg=colors["bg"])
        wrap.pack(fill="both", expand=True, pady=8)

        self._section(wrap, "RÉPARTITION PAR CATÉGORIE")
        self.cat_frame = tk.Frame(wrap, bg=colors["bg"])
        self.cat_frame.pack(fill="x", padx=6, pady=(4, 18))

        self._section(wrap, "RÉPARTITION PAR PRIORITÉ")
        self.prio_frame = tk.Frame(wrap, bg=colors["bg"])
        self.prio_frame.pack(fill="x", padx=6, pady=4)

    def _section(self, parent, title):
        tk.Label(parent, text=title, bg=self.c["bg"], fg=self.c["muted"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=6, pady=(6, 0))

    def load(self):
        try:
            self.render(self.api.get_stats())
        except Exception as exc:  # noqa: BLE001
            print(f"[stats] {exc}")

    def render(self, stats):
        self._bars(self.cat_frame, stats.get("byCategory", {}), CATEGORY_LABELS, None)
        self._bars(self.prio_frame, stats.get("byPriority", {}), None, PRIORITY_COLORS)

    def _bars(self, container, data, labels, colors):
        for child in container.winfo_children():
            child.destroy()
        if not data or sum(data.values()) == 0:
            tk.Label(container, text="Aucune donnée.", bg=self.c["bg"], fg=self.c["muted"]).pack(anchor="w")
            return
        total = max(sum(data.values()), 1)
        for key, value in sorted(data.items(), key=lambda kv: kv[1], reverse=True):
            row = tk.Frame(container, bg=self.c["bg"])
            row.pack(fill="x", pady=3)
            name = labels.get(key, key) if labels else key.capitalize()
            tk.Label(row, text=name, width=20, anchor="w", bg=self.c["bg"], fg=self.c["text"],
                     font=self.f["body"]).pack(side="left")
            track = tk.Frame(row, bg=self.c["panel2"], height=16, width=460)
            track.pack(side="left", fill="x", expand=True, padx=8)
            track.pack_propagate(False)
            color = colors.get(key, self.c["accent"]) if colors else self.c["accent"]
            fill = tk.Frame(track, bg=color, height=16)
            fill.place(x=0, y=0, relwidth=max(value / total, 0.02), relheight=1)
            tk.Label(row, text=str(value), width=4, anchor="e", bg=self.c["bg"], fg=self.c["text"],
                     font=self.f["body"]).pack(side="left")
