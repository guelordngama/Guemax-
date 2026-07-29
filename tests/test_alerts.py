"""Tests du cycle de vie des alertes : création, validation, confirmation, statut."""

from conftest import sample_alert


def test_creation_alerte_valide(client):
    res = client.post("/api/alerts", json=sample_alert())
    assert res.status_code == 201
    alert = res.get_json()
    assert alert["category"] == "vol"
    assert alert["status"] == "actif"
    assert alert["confirmations"] == 0
    assert alert["priority"] in ("basse", "moyenne", "haute", "critique")


def test_creation_alerte_invalide(client):
    res = client.post("/api/alerts", json={"category": "xxx", "severity": "eleve", "description": "a", "lat": 999, "lng": 27})
    assert res.status_code == 400
    assert len(res.get_json()["errors"]) >= 1


def test_liste_alertes(client):
    client.post("/api/alerts", json=sample_alert())
    client.post("/api/alerts", json=sample_alert(category="incendie"))
    res = client.get("/api/alerts")
    assert res.status_code == 200
    assert len(res.get_json()) == 2


def test_confirmation_incremente_le_compteur(client):
    created = client.post("/api/alerts", json=sample_alert()).get_json()
    res = client.post(f"/api/alerts/{created['id']}/confirm")
    assert res.status_code == 200
    assert res.get_json()["confirmations"] == 1


def test_changement_de_statut(client):
    created = client.post("/api/alerts", json=sample_alert()).get_json()
    res = client.patch(f"/api/alerts/{created['id']}/status", json={"status": "resolu"})
    assert res.status_code == 200
    assert res.get_json()["status"] == "resolu"


def test_statut_invalide_refuse(client):
    created = client.post("/api/alerts", json=sample_alert()).get_json()
    res = client.patch(f"/api/alerts/{created['id']}/status", json={"status": "n_importe_quoi"})
    assert res.status_code == 400


def test_confirmation_alerte_inexistante(client):
    assert client.post("/api/alerts/99999/confirm").status_code == 404


def test_stats_coherentes(client):
    client.post("/api/alerts", json=sample_alert())
    created = client.post("/api/alerts", json=sample_alert(category="agression", severity="critique")).get_json()
    client.patch(f"/api/alerts/{created['id']}/status", json={"status": "resolu"})

    stats = client.get("/api/alerts/stats/summary").get_json()
    assert stats["total"] == 2
    assert stats["byStatus"]["resolu"] == 1
    assert stats["byStatus"]["actif"] == 1


def test_priorite_critique_pour_agression_grave(client):
    """Le classifieur (placeholder IA) doit hausser la priorité d'une agression critique."""
    alert = client.post(
        "/api/alerts",
        json=sample_alert(category="agression", severity="critique",
                          description="Agression à main armée, personne blessée, urgent"),
    ).get_json()
    assert alert["priority"] in ("haute", "critique")
