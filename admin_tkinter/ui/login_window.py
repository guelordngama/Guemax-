"""Fenêtre de connexion de la mairie (thème centre de commandement)."""

import tkinter as tk
from tkinter import ttk

from ui.theme import COLORS, fonts


class LoginWindow:
    def __init__(self, root, api, on_success):
        self.api = api
        self.on_success = on_success
        c = COLORS
        f = fonts()

        self.win = tk.Toplevel(root)
        self.win.title("SafeCity Lubumbashi — Connexion mairie")
        self.win.geometry("400x430")
        self.win.resizable(False, False)
        self.win.configure(bg=c["bg"])
        self.win.protocol("WM_DELETE_WINDOW", root.destroy)

        card = tk.Frame(self.win, bg=c["panel"], highlightthickness=0)
        card.pack(fill="both", expand=True, padx=22, pady=22)
        tk.Frame(card, bg=c["primary"], height=4).pack(fill="x")

        inner = tk.Frame(card, bg=c["panel"])
        inner.pack(fill="both", expand=True, padx=28, pady=24)

        tk.Label(inner, text="🚨", bg=c["panel"], fg=c["primary"], font=("Segoe UI Emoji", 40)).pack(pady=(6, 2))
        tk.Label(inner, text="SafeCity Lubumbashi", bg=c["panel"], fg=c["text"], font=f["title"]).pack()
        tk.Label(inner, text="CENTRE DE COMMANDEMENT", bg=c["panel"], fg=c["muted"],
                 font=("Segoe UI", 8, "bold")).pack(pady=(0, 18))

        tk.Label(inner, text="Identifiant", bg=c["panel"], fg=c["muted"], font=f["small"], anchor="w").pack(fill="x")
        self.username = ttk.Entry(inner)
        self.username.pack(fill="x", pady=(3, 12), ipady=3)
        self.username.insert(0, "admin")

        tk.Label(inner, text="Mot de passe", bg=c["panel"], fg=c["muted"], font=f["small"], anchor="w").pack(fill="x")
        self.password = ttk.Entry(inner, show="•")
        self.password.pack(fill="x", pady=(3, 10), ipady=3)

        self.error = tk.Label(inner, text="", bg=c["panel"], fg="#fca5a5", font=f["small"], wraplength=300)
        self.error.pack(fill="x")

        ttk.Button(inner, text="Se connecter", style="Accent.TButton", command=self._submit).pack(fill="x", pady=(12, 0), ipady=3)
        self.password.bind("<Return>", lambda _e: self._submit())
        self.username.focus_set()

    def _submit(self):
        self.error.config(text="")
        ok, result = self.api.login(self.username.get().strip(), self.password.get())
        if ok:
            self.win.destroy()
            self.on_success(result)
        else:
            self.error.config(text=result if isinstance(result, str) else " ".join(result))
