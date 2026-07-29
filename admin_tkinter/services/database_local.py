"""Cache local léger (SQLite) des alertes pour consultation hors-ligne.

Permet au poste de la mairie de conserver la dernière liste d'alertes reçue
même en cas de coupure réseau temporaire.
"""

import json
import os
import sqlite3

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache.db")


class LocalCache:
    def __init__(self, path=DEFAULT_PATH):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY, payload TEXT)"
        )
        self.conn.commit()

    def upsert(self, alert):
        self.conn.execute(
            "INSERT OR REPLACE INTO alerts (id, payload) VALUES (?, ?)",
            (alert["id"], json.dumps(alert)),
        )
        self.conn.commit()

    def upsert_many(self, alerts):
        for a in alerts:
            self.conn.execute(
                "INSERT OR REPLACE INTO alerts (id, payload) VALUES (?, ?)",
                (a["id"], json.dumps(a)),
            )
        self.conn.commit()

    def all(self):
        rows = self.conn.execute("SELECT payload FROM alerts").fetchall()
        return [json.loads(r[0]) for r in rows]

    def close(self):
        self.conn.close()
