"""Tests du filtre géographique « Lubumbashi uniquement » (poste mairie)."""

from conftest import sample_alert


def test_scope_lubumbashi_exclut_les_autres_villes(client):
    # Alerte à Lubumbashi
    client.post("/api/alerts", json=sample_alert(lat=-11.66, lng=27.48))
    # Alerte hors emprise (ex. Kinshasa ~ -4.32, 15.31)
    client.post("/api/alerts", json=sample_alert(lat=-4.32, lng=15.31))

    toutes = client.get("/api/alerts").get_json()
    assert len(toutes) == 2

    lubumbashi = client.get("/api/alerts?scope=lubumbashi").get_json()
    assert len(lubumbashi) == 1
    assert all(-11.78 <= a["lat"] <= -11.53 for a in lubumbashi)


def test_config_expose_les_bornes(client):
    cfg = client.get("/api/config").get_json()
    assert "bounds" in cfg
    assert cfg["bounds"]["min_lat"] < cfg["bounds"]["max_lat"]
