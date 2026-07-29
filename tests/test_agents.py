"""Tests de la gestion des agents : statuts, points, interventions."""


def _auth(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


def test_liste_agents_requiert_admin(client):
    assert client.get("/api/agents").status_code == 401


def test_liste_agents(client, admin_token):
    res = client.get("/api/agents", headers=_auth(admin_token))
    assert res.status_code == 200
    agents = res.get_json()
    assert len(agents) >= 3
    assert "totalPoints" in agents[0] and "status" in agents[0]


def test_summary_par_statut(client, admin_token):
    res = client.get("/api/agents/summary", headers=_auth(admin_token))
    assert res.status_code == 200
    body = res.get_json()
    assert set(body["byStatus"]) == {"disponible", "en_mission", "absent", "hors_ligne"}
    assert body["total"] >= 3
    assert isinstance(body["leaderboard"], list)


def test_changer_statut(client, admin_token):
    agent_id = client.get("/api/agents", headers=_auth(admin_token)).get_json()[0]["id"]
    res = client.patch(f"/api/agents/{agent_id}/status", json={"status": "en_mission"},
                       headers=_auth(admin_token))
    assert res.status_code == 200
    assert res.get_json()["status"] == "en_mission"


def test_statut_invalide(client, admin_token):
    agent_id = client.get("/api/agents", headers=_auth(admin_token)).get_json()[0]["id"]
    res = client.patch(f"/api/agents/{agent_id}/status", json={"status": "n_importe"},
                       headers=_auth(admin_token))
    assert res.status_code == 400


def test_attribution_de_points(client, admin_token):
    agent = client.get("/api/agents", headers=_auth(admin_token)).get_json()[0]
    before = agent["totalPoints"]
    res = client.post(f"/api/agents/{agent['id']}/points",
                      json={"points": 15, "reason": "Excellente intervention", "lieu": "Kenya"},
                      headers=_auth(admin_token))
    assert res.status_code == 201
    assert res.get_json()["agent"]["totalPoints"] == before + 15


def test_intervention_attribue_points_automatiquement(client, admin_token):
    agent = client.get("/api/agents", headers=_auth(admin_token)).get_json()[0]
    before = agent["totalPoints"]
    res = client.post(f"/api/agents/{agent['id']}/interventions",
                      json={"lieu": "Centre-ville", "typeMission": "patrouille",
                            "dureeMinutes": 20, "resultat": "reussie"},
                      headers=_auth(admin_token))
    assert res.status_code == 201
    body = res.get_json()
    assert body["pointsAwarded"] >= 10          # base réussie
    assert body["pointsAwarded"] >= 13          # + bonus rapidité (<=30 min)
    assert body["agent"]["totalPoints"] == before + body["pointsAwarded"]
    assert body["intervention"]["resultat"] == "reussie"


def test_historique_points_par_annee(client, admin_token):
    agent_id = client.get("/api/agents", headers=_auth(admin_token)).get_json()[0]["id"]
    res = client.get(f"/api/agents/{agent_id}/points", headers=_auth(admin_token))
    assert res.status_code == 200
    assert "byYear" in res.get_json()
