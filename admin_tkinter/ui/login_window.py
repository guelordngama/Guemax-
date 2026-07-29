"""Fenêtre de connexion de la mairie."""

import tkinter as tk
from tkinter import ttk


class LoginWindow:
    def __init__(self, root, api, on_success):
        self.api = api
        self.on_success = on_success

        self.win = tk.Toplevel(root)
        self.win.title("SafeCity Lubumbashi — Connexion mairie")
        self.win.geometry("380x360")
        self.win.resizable(False, False)
        self.win.configure(bg="#0f172a")
        self.win.protocol("WM_DELETE_WINDOW", root.destroy)

        tk.Label(self.win, text="🚨", font=("Segoe UI Emoji", 42), bg="#0f172a", fg="#e11d48").pack(pady=(28, 4))
        tk.Label(self.win, text="SafeCity Lubumbashi", font=("Segoe UI", 16, "bold"),
                 bg="#0f172a", fg="#e2e8f0").pack()
        tk.Label(self.win, text="Espace mairie — surveillance en temps réel",
                 font=("Segoe UI", 9), bg="#0f172a", fg="#94a3b8").pack(pady=(0, 18))

        form = tk.Frame(self.win, bg="#0f172a")
        form.pack(fill="x", padx=36)

        tk.Label(form, text="Identifiant", bg="#0f172a", fg="#94a3b8", anchor="w").pack(fill="x")
        self.username = ttk.Entry(form)
        self.username.pack(fill="x", pady=(2, 12))
        self.username.insert(0, "admin")

        tk.Label(form, text="Mot de passe", bg="#0f172a", fg="#94a3b8", anchor="w").pack(fill="x")
        self.password = ttk.Entry(form, show="•")
        self.password.pack(fill="x", pady=(2, 8))

        self.error = tk.Label(form, text="", bg="#0f172a", fg="#fca5a5", font=("Segoe UI", 9), wraplength=300)
        self.error.pack(fill="x")

        ttk.Button(form, text="Se connecter", command=self._submit).pack(fill="x", pady=(10, 0))
        self.password.bind("<Return>", lambda _e: self._submit())

    def _submit(self):
        self.error.config(text="")
        ok, result = self.api.login(self.username.get().strip(), self.password.get())
        if ok:
            self.win.destroy()
            self.on_success(result)
        else:
            msg = result if isinstance(result, str) else " ".join(result)
            self.error.config(text=msg)
