"""Client HTTP vers l'API Flask (côté mairie)."""

import requests


class ApiClient:
    def __init__(self, base_url):
        self.base = base_url.rstrip("/")
        self.token = None
        self.user = None

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    # --- Authentification --------------------------------------------------
    def login(self, username, password):
        res = requests.post(
            f"{self.base}/api/auth/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if res.status_code == 200:
            data = res.json()
            self.token = data["token"]
            self.user = data["user"]
            return True, data["user"]
        return False, (res.json().get("errors", ["Échec de connexion."]))

    # --- Alertes -----------------------------------------------------------
    def list_alerts(self):
        return requests.get(f"{self.base}/api/alerts", timeout=10).json()

    def get_stats(self):
        return requests.get(f"{self.base}/api/alerts/stats/summary", timeout=10).json()

    def update_status(self, alert_id, status):
        res = requests.patch(
            f"{self.base}/api/alerts/{alert_id}/status",
            json={"status": status},
            headers=self._headers(),
            timeout=10,
        )
        return res.json()

    # --- Agents ------------------------------------------------------------
    def list_agents(self):
        res = requests.get(f"{self.base}/api/users/agents", headers=self._headers(), timeout=10)
        return res.json() if res.status_code == 200 else []
