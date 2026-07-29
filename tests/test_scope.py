"""Tests du périmètre géographique Lubumbashi : refus à la soumission + filtre."""

from conftest import sample_alert


def test_alerte_hors_lubumbashi_refusee(client):
    # Kinshasa (~ -4.32, 15.31) : hors de l'emprise de Lubumbashi.
    res = client.post("/api/alerts", json=sample_alert(lat=-4.32, lng=15.31))
    assert res.status_code == 422
    assert res.get_json().get("outOfBounds") is True


def test_alerte_dans_lubumbashi_acceptee(client):
    res = client.post("/api/alerts", json=sample_alert(lat=-11.66, lng=27.48))
    assert res.status_code == 201


def test_scope_lubumbashi_sur_la_liste(client):
    client.post("/api/alerts", json=sample_alert(lat=-11.66, lng=27.48))
    lubumbashi = client.get("/api/alerts?scope=lubumbashi").get_json()
    assert len(lubumbashi) == 1
    assert all(-11.78 <= a["lat"] <= -11.53 for a in lubumbashi)


def test_config_expose_les_bornes(client):
    cfg = client.get("/api/config").get_json()
    assert "bounds" in cfg
    assert cfg["bounds"]["min_lat"] < cfg["bounds"]["max_lat"]
