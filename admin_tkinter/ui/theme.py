"""Thème « centre de commandement » (sombre) pour l'application de la mairie.

Configure un style ttk cohérent (couleurs, polices, Treeview, Notebook,
boutons) appliqué à toute l'application pour un rendu professionnel.
"""

import tkinter.font as tkfont
from tkinter import ttk

COLORS = {
    "bg": "#0b1220",       # fond principal (bleu nuit profond)
    "panel": "#111d31",    # panneaux / cartes
    "panel2": "#18273f",   # survol / entrées
    "border": "#26374f",
    "text": "#e6edf6",
    "muted": "#8aa0b6",
    "primary": "#e11d48",  # rouge alerte
    "primary_dk": "#9f1239",
    "accent": "#38bdf8",   # cyan
    "green": "#22c55e",
    "amber": "#f59e0b",
    "red": "#ef4444",
    "blue": "#3b82f6",
}


def fonts():
    return {
        "title": ("Segoe UI Semibold", 15),
        "h2": ("Segoe UI Semibold", 12),
        "body": ("Segoe UI", 10),
        "small": ("Segoe UI", 9),
        "kpi": ("Segoe UI", 26, "bold"),
        "mono": ("Consolas", 11),
    }


def apply_theme(root):
    """Applique le thème sombre à la racine et retourne (style, COLORS, fonts)."""
    c = COLORS
    f = fonts()
    root.configure(bg=c["bg"])
    try:
        root.option_add("*Font", f["body"])
    except Exception:
        pass

    style = ttk.Style(root)
    style.theme_use("clam")

    # Conteneurs
    style.configure("TFrame", background=c["bg"])
    style.configure("Card.TFrame", background=c["panel"], relief="flat")
    style.configure("Topbar.TFrame", background=c["panel"])
    style.configure("Status.TFrame", background=c["panel"])

    # Labels
    style.configure("TLabel", background=c["bg"], foreground=c["text"], font=f["body"])
    style.configure("Card.TLabel", background=c["panel"], foreground=c["text"])
    style.configure("Muted.TLabel", background=c["bg"], foreground=c["muted"], font=f["small"])
    style.configure("CardMuted.TLabel", background=c["panel"], foreground=c["muted"], font=f["small"])
    style.configure("Title.TLabel", background=c["panel"], foreground=c["text"], font=f["title"])
    style.configure("H2.TLabel", background=c["bg"], foreground=c["text"], font=f["h2"])
    style.configure("KPI.TLabel", background=c["panel"], foreground=c["text"], font=f["kpi"])
    style.configure("Clock.TLabel", background=c["panel"], foreground=c["accent"], font=f["mono"])

    # Boutons
    style.configure(
        "TButton", background=c["panel2"], foreground=c["text"], font=f["body"],
        borderwidth=0, focuscolor=c["panel"], padding=(12, 7),
    )
    style.map("TButton", background=[("active", c["border"])])
    style.configure("Accent.TButton", background=c["primary"], foreground="#ffffff", padding=(14, 7))
    style.map("Accent.TButton", background=[("active", c["primary_dk"])])
    style.configure("Ghost.TButton", background=c["panel2"], foreground=c["text"])
    style.map("Ghost.TButton", background=[("active", c["border"])])

    # Entrées
    style.configure(
        "TEntry", fieldbackground=c["panel2"], foreground=c["text"],
        insertcolor=c["text"], bordercolor=c["border"], borderwidth=1, padding=6,
    )
    style.configure(
        "TCombobox", fieldbackground=c["panel2"], background=c["panel2"],
        foreground=c["text"], arrowcolor=c["text"], bordercolor=c["border"],
    )

    # Notebook
    style.configure("TNotebook", background=c["bg"], borderwidth=0)
    style.configure(
        "TNotebook.Tab", background=c["panel"], foreground=c["muted"],
        padding=(18, 9), font=f["h2"], borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", c["bg"])],
        foreground=[("selected", c["text"])],
    )

    # Treeview
    style.configure(
        "Treeview", background=c["panel"], fieldbackground=c["panel"],
        foreground=c["text"], rowheight=28, borderwidth=0, font=f["body"],
    )
    style.map("Treeview", background=[("selected", c["blue"])], foreground=[("selected", "#ffffff")])
    style.configure(
        "Treeview.Heading", background=c["panel2"], foreground=c["muted"],
        font=f["small"], relief="flat", padding=6,
    )
    style.map("Treeview.Heading", background=[("active", c["border"])])

    # Barre de progression (pour les points d'agents plus tard)
    style.configure(
        "Score.Horizontal.TProgressbar", troughcolor=c["panel2"],
        background=c["accent"], borderwidth=0,
    )

    return style, c, f
