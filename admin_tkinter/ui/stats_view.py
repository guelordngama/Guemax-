"""Vue statistiques (tableau de bord synthétique)."""

import tkinter as tk
from tkinter import ttk

CATEGORY_LABELS = {
    "vol": "Vol / Cambriolage", "agression": "Agression", "accident": "Accident",
    "incendie": "Incendie", "inondation": "Inondation", "electricite": "Électricité",
    "infrastructure": "Voirie", "autre": "Autre",
}


class StatsView(ttk.Frame):
    def __init__(self, parent, api):
        super().__init__(parent)
        self.api = api

        self.cards = ttk.Frame(self)
        self.cards.pack(fill="x", pady=(4, 16))

        self.card_vars = {}
        for key, label in [("total", "Total"), ("actif", "Actives"),
                           ("verifie", "Vérifiées"), ("resolu", "Résolues")]:
            frame = ttk.Frame(self.cards, relief="ridge", borderwidth=1, padding=12)
            frame.pack(side="left", expand=True, fill="both", padx=4)
            var = tk.StringVar(value="0")
            tk.Label(frame, textvariable=var, font=("Segoe UI", 22, "bold")).pack()
            ttk.Label(frame, text=label).pack()
            self.card_vars[key] = var

        ttk.Label(self, text="Répartition par catégorie", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.cat_frame = ttk.Frame(self)
        self.cat_frame.pack(fill="x", pady=(6, 16))

        ttk.Label(self, text="Répartition par priorité", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.prio_frame = ttk.Frame(self)
        self.prio_frame.pack(fill="x", pady=6)

    def load(self):
        try:
            self.render(self.api.get_stats())
        except Exception as exc:  # noqa: BLE001
            print(f"[stats] {exc}")

    def render(self, stats):
        self.card_vars["total"].set(str(stats.get("total", 0)))
        by_status = stats.get("byStatus", {})
        for key in ("actif", "verifie", "resolu"):
            self.card_vars[key].set(str(by_status.get(key, 0)))

        self._render_bars(self.cat_frame, stats.get("byCategory", {}), CATEGORY_LABELS)
        self._render_bars(self.prio_frame, stats.get("byPriority", {}), None)

    @staticmethod
    def _render_bars(container, data, labels):
        for child in container.winfo_children():
            child.destroy()
        if not data:
            ttk.Label(container, text="Aucune donnée.").pack(anchor="w")
            return
        total = max(sum(data.values()), 1)
        for key, value in sorted(data.items(), key=lambda kv: kv[1], reverse=True):
            row = ttk.Frame(container)
            row.pack(fill="x", pady=2)
            name = labels.get(key, key) if labels else key
            ttk.Label(row, text=name, width=20, anchor="w").pack(side="left")
            bar = "█" * int(round((value / total) * 28))
            ttk.Label(row, text=f"{bar}  {value}", foreground="#e11d48").pack(side="left")
