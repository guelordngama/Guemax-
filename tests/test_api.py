"""Tests de l'API générale : santé, configuration, authentification."""


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_config_expose_center_et_categories(client):
    res = client.get("/api/config")
    assert res.status_code == 200
    body = res.get_json()
    assert "center" in body and "lat" in body["center"]
    assert len(body["categories"]) >= 1
    assert len(body["severities"]) >= 1


def test_login_admin_reussit(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["token"]
    assert body["user"]["role"] == "admin"


def test_login_mauvais_mot_de_passe(client):
    res = client.post("/api/auth/login", json={"username": "admin", "password": "faux"})
    assert res.status_code == 401


def test_route_admin_exige_un_jeton(client):
    assert client.get("/api/users").status_code == 401


def test_route_admin_accessible_avec_jeton(client, admin_token):
    res = client.get("/api/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert any(u["role"] == "admin" for u in res.get_json())
