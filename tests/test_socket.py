"""Tests du canal temps réel (Socket.IO)."""

from socket_events import socketio


def test_client_socketio_se_connecte(app):
    client = socketio.test_client(app)
    assert client.is_connected()
    client.disconnect()


def test_evenement_presence_a_la_connexion(app):
    client = socketio.test_client(app)
    received = client.get_received()
    events = [msg["name"] for msg in received]
    assert "presence" in events
    client.disconnect()
