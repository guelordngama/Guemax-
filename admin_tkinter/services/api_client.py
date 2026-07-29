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

    # --- Configuration -----------------------------------------------------
    def get_config(self):
        return requests.get(f"{self.base}/api/config", timeout=10).json()

    # --- Alertes -----------------------------------------------------------
    def list_alerts(self, scope="lubumbashi"):
        # Par défaut, le poste mairie ne récupère que les alertes de Lubumbashi.
        params = {"scope": scope} if scope else {}
        return requests.get(f"{self.base}/api/alerts", params=params, timeout=10).json()

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
        res = requests.get(f"{self.base}/api/agents", headers=self._headers(), timeout=10)
        return res.json() if res.status_code == 200 else []

    def agents_summary(self):
        res = requests.get(f"{self.base}/api/agents/summary", headers=self._headers(), timeout=10)
        return res.json() if res.status_code == 200 else {"byStatus": {}, "total": 0, "leaderboard": []}

    def set_agent_status(self, agent_id, status):
        res = requests.patch(f"{self.base}/api/agents/{agent_id}/status",
                             json={"status": status}, headers=self._headers(), timeout=10)
        return res.json()

    def award_points(self, agent_id, points, reason="", lieu=""):
        res = requests.post(f"{self.base}/api/agents/{agent_id}/points",
                            json={"points": points, "reason": reason, "lieu": lieu},
                            headers=self._headers(), timeout=10)
        return res.json()

    def create_intervention(self, agent_id, payload):
        res = requests.post(f"{self.base}/api/agents/{agent_id}/interventions",
                            json=payload, headers=self._headers(), timeout=10)
        return res.json()
