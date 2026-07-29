"""Vue liste des alertes : tableau filtrable + actions de traitement."""

import tkinter as tk
from tkinter import ttk, messagebox

CATEGORY_LABELS = {
    "vol": "Vol / Cambriolage", "agression": "Agression", "accident": "Accident",
    "incendie": "Incendie", "inondation": "Inondation", "electricite": "Électricité",
    "infrastructure": "Voirie", "autre": "Autre",
}
PRIORITY_ORDER = {"critique": 0, "haute": 1, "moyenne": 2, "basse": 3}


class AlertsView(ttk.Frame):
    def __init__(self, parent, api, colors, fonts):
        super().__init__(parent, style="TFrame")
        self.api = api
        self.c = colors
        self.f = fonts
        self.alerts = {}
        self.filter_status = "tous"
        self.filter_category = "toutes"

        self._build_toolbar()
        self._build_table()

    def _build_toolbar(self):
        c = self.c
        bar = tk.Frame(self, bg=c["bg"])
        bar.pack(fill="x", pady=(6, 8))

        tk.Label(bar, text="Statut", bg=c["bg"], fg=c["muted"], font=self.f["small"]).pack(side="left", padx=(2, 4))
        self.status_cb = ttk.Combobox(bar, width=12, state="readonly",
                                      values=["tous", "actif", "verifie", "resolu"])
        self.status_cb.set("tous")
        self.status_cb.pack(side="left", padx=(0, 12))
        self.status_cb.bind("<<ComboboxSelected>>", lambda _e: self._apply_filters())

        tk.Label(bar, text="Catégorie", bg=c["bg"], fg=c["muted"], font=self.f["small"]).pack(side="left", padx=(2, 4))
        self.cat_cb = ttk.Combobox(bar, width=16, state="readonly",
                                   values=["toutes"] + list(CATEGORY_LABELS.keys()))
        self.cat_cb.set("toutes")
        self.cat_cb.pack(side="left", padx=(0, 12))
        self.cat_cb.bind("<<ComboboxSelected>>", lambda _e: self._apply_filters())

        ttk.Button(bar, text="✔  Vérifiée", style="Ghost.TButton",
                   command=lambda: self._set_status("verifie")).pack(side="left", padx=3)
        ttk.Button(bar, text="✅  Résolue", style="Accent.TButton",
                   command=lambda: self._set_status("resolu")).pack(side="left", padx=3)

        self.count_var = tk.StringVar(value="0 alerte(s)")
        tk.Label(bar, textvariable=self.count_var, bg=c["bg"], fg=c["muted"], font=self.f["small"]).pack(side="right", padx=4)

    def _build_table(self):
        c = self.c
        columns = ("id", "priority", "category", "severity", "status", "confirm", "created")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", style="Treeview")
        headers = {
            "id": "N°", "priority": "PRIORITÉ", "category": "CATÉGORIE", "severity": "GRAVITÉ",
            "status": "STATUT", "confirm": "CONFIRM.", "created": "REÇUE",
        }
        widths = {"id": 50, "priority": 90, "category": 170, "severity": 90, "status": 90, "confirm": 80, "created": 150}
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col], anchor="center")
        self.tree.column("category", anchor="w")

        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Couleurs de priorité / statut
        self.tree.tag_configure("critique", foreground="#fca5a5")
        self.tree.tag_configure("haute", foreground="#fdba74")
        self.tree.tag_configure("resolu", foreground=c["muted"])

    # ------------------------------------------------------------- données
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

    def _apply_filters(self):
        self.filter_status = self.status_cb.get()
        self.filter_category = self.cat_cb.get()
        self._render()

    def _visible(self):
        items = list(self.alerts.values())
        if self.filter_status != "tous":
            items = [a for a in items if a["status"] == self.filter_status]
        if self.filter_category != "toutes":
            items = [a for a in items if a["category"] == self.filter_category]
        # Tri : priorité décroissante puis plus récent d'abord.
        items.sort(key=lambda a: (PRIORITY_ORDER.get(a["priority"], 9), ), )
        items.sort(key=lambda a: a["createdAt"], reverse=True)
        items.sort(key=lambda a: PRIORITY_ORDER.get(a["priority"], 9))
        return items

    def _render(self):
        self.tree.delete(*self.tree.get_children())
        for a in self._visible():
            tags = []
            if a["status"] == "resolu":
                tags.append("resolu")
            elif a["priority"] in ("critique", "haute"):
                tags.append(a["priority"])
            self.tree.insert("", "end", iid=str(a["id"]), tags=tags, values=(
                a["id"], a["priority"].upper(), CATEGORY_LABELS.get(a["category"], a["category"]),
                a["severity"], a["status"], a["confirmations"],
                a["createdAt"][:16].replace("T", " "),
            ))
        self.count_var.set(f"{len(self.alerts)} alerte(s) · Lubumbashi")

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
