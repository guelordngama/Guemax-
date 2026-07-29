"""Tests du flux de comptes citoyens : inscription → validation → connexion."""


def _signup(client, **over):
    payload = {
        "nom": "Kabila", "postNom": "Mwamba", "username": "citoyen1",
        "password": "motdepasse", "email": "citoyen1@gmail.com",
        "ville": "Lubumbashi", "nationalite": "Congolaise",
        "dateNaissance": "1998-05-12",
    }
    payload.update(over)
    return client.post("/api/auth/signup", json=payload)


def test_signup_cree_un_compte_non_valide(client):
    res = _signup(client)
    assert res.status_code == 201
    body = res.get_json()
    assert body["username"] == "citoyen1"
    assert "devCode" in body  # mode démo


def test_signup_champs_manquants(client):
    res = client.post("/api/auth/signup", json={"username": "x"})
    assert res.status_code == 400
    assert len(res.get_json()["errors"]) >= 1


def test_login_bloque_avant_validation(client):
    _signup(client)
    res = client.post("/api/auth/login", json={"username": "citoyen1", "password": "motdepasse"})
    assert res.status_code == 403
    assert res.get_json().get("needsVerification") is True


def test_validation_puis_connexion(client):
    code = _signup(client).get_json()["devCode"]
    res = client.post("/api/auth/verify", json={"username": "citoyen1", "code": code})
    assert res.status_code == 200
    assert res.get_json()["token"]

    login = client.post("/api/auth/login", json={"username": "citoyen1", "password": "motdepasse"})
    assert login.status_code == 200
    assert login.get_json()["user"]["isVerified"] is True


def test_code_incorrect_refuse(client):
    _signup(client)
    res = client.post("/api/auth/verify", json={"username": "citoyen1", "code": "000000"})
    assert res.status_code == 400


def test_renvoi_de_code(client):
    _signup(client)
    res = client.post("/api/auth/resend", json={"username": "citoyen1"})
    assert res.status_code == 200
    assert "devCode" in res.get_json()


def test_admin_login_sans_validation(client):
    # Le compte admin (interne) ne nécessite pas de validation par code.
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
