"""Point d'entrée de l'application de bureau de la mairie (Tkinter).

Usage :  python main.py
Variable d'environnement :  SAFECITY_API (défaut http://localhost:5000)
"""

import os
import sys
import tkinter as tk

# Permet les imports absolus (ui.*, services.*) quel que soit le cwd.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.api_client import ApiClient
from ui.dashboard import Dashboard
from ui.login_window import LoginWindow
from ui.theme import apply_theme

API_BASE = os.environ.get("SAFECITY_API", "http://localhost:5000")


def main():
    api = ApiClient(API_BASE)
    root = tk.Tk()
    apply_theme(root)  # thème appliqué dès le départ (login + dashboard)
    root.withdraw()  # masqué jusqu'à la connexion

    def on_success(user):
        Dashboard(root, api, user)

    LoginWindow(root, api, on_success)
    root.mainloop()


if __name__ == "__main__":
    main()
