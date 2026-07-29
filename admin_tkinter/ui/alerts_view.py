"""Vue liste des alertes (tableau + actions de traitement)."""

import tkinter as tk
from tkinter import ttk, messagebox

CATEGORY_LABELS = {
    "vol": "Vol / Cambriolage", "agression": "Agression", "accident": "Accident",
    "incendie": "Incendie", "inondation": "Inondation", "electricite": "Électricité",
    "infrastructure": "Voirie", "autre": "Autre",
}


class AlertsView(ttk.Frame):
    def __init__(self, parent, api):
        super().__init__(parent)
        self.api = api
        self.alerts = {}  # id -> alert

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 6))
        ttk.Button(toolbar, text="✔️ Marquer vérifiée", command=lambda: self._set_status("verifie")).pack(side="left", padx=2)
        ttk.Button(toolbar, text="✅ Marquer résolue", command=lambda: self._set_status("resolu")).pack(side="left", padx=2)
        self.count_label = ttk.Label(toolbar, text="0 alerte(s)")
        self.count_label.pack(side="right")

        columns = ("id", "priority", "category", "severity", "status", "confirmations", "created")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=18)
        headers = {
            "id": "N°", "priority": "Priorité", "category": "Catégorie", "severity": "Gravité",
            "status": "Statut", "confirmations": "Confirm.", "created": "Reçue",
        }
        widths = {"id": 45, "priority": 80, "category": 150, "severity": 80, "status": 80, "confirmations": 70, "created": 150}
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col], anchor="center")
        self.tree.column("category", anchor="w")

        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.tree.tag_configure("critique", background="#7f1d1d", foreground="#fecaca")
        self.tree.tag_configure("haute", background="#7c2d12", foreground="#fdba74")
        self.tree.tag_configure("resolu", foreground="#94a3b8")

    def load(self):
        try:
            self.set_alerts(self.api.list_alerts())
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erreur", f"Impossible de charger les alertes :\n{exc}")

    def set_alerts(self, alerts):
        self.alerts = {a["id"]: a for a in alerts}
        self._render()

    def upsert(self, alert):
        self.alerts[alert["id"]] = alert
        self._render()

    def _render(self):
        self.tree.delete(*self.tree.get_children())
        ordered = sorted(self.alerts.values(), key=lambda a: a["createdAt"], reverse=True)
        for a in ordered:
            tags = []
            if a["status"] == "resolu":
                tags.append("resolu")
            elif a["priority"] in ("critique", "haute"):
                tags.append(a["priority"])
            self.tree.insert("", "end", iid=str(a["id"]), tags=tags, values=(
                a["id"], a["priority"], CATEGORY_LABELS.get(a["category"], a["category"]),
                a["severity"], a["status"], a["confirmations"], a["createdAt"][:16].replace("T", " "),
            ))
        self.count_label.config(text=f"{len(self.alerts)} alerte(s)")

    def _selected_id(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _set_status(self, status):
        alert_id = self._selected_id()
        if not alert_id:
            messagebox.showinfo("Info", "Sélectionnez une alerte dans la liste.")
            return
        try:
            updated = self.api.update_status(alert_id, status)
            if "id" in updated:
                self.upsert(updated)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Erreur", f"Mise à jour impossible :\n{exc}")
