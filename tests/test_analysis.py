"""Tests de l'analyse des zones à risque (endpoints + fonctions pures)."""

import os
import sys

from conftest import sample_alert

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ai_module"))
import zone_analysis  # noqa: E402

BOUNDS = {"min_lat": -11.78, "max_lat": -11.53, "min_lng": 27.35, "max_lng": 27.62}


# --- Fonctions pures --------------------------------------------------------

def test_hotspots_identifie_la_zone_dense():
    alerts = [
        {"lat": -11.66, "lng": 27.48, "severity": "critique", "category": "agression", "createdAt": "2026-07-29T14:00:00Z"},
        {"lat": -11.66, "lng": 27.48, "severity": "eleve", "category": "vol", "createdAt": "2026-07-29T15:00:00Z"},
        {"lat": -11.55, "lng": 27.60, "severity": "faible", "category": "autre", "createdAt": "2026-07-01T09:00:00Z"},
    ]
    zones = zone_analysis.analyze_hotspots(alerts, BOUNDS)
    assert zones
    assert zones[0]["riskIndex"] == 100.0        # zone la plus dense normalisée à 100
    assert zones[0]["count"] == 2


def test_peak_hours():
    alerts = [{"createdAt": "2026-07-29T14:00:00Z"}, {"createdAt": "2026-07-29T14:30:00Z"},
              {"createdAt": "2026-07-29T09:00:00Z"}]
    res = zone_analysis.peak_hours(alerts)
    assert res["peakHour"] == 14
    assert res["byHour"][14] == 2


def test_heatmap_points():
    pts = zone_analysis.heatmap_points([{"lat": -11.66, "lng": 27.48, "severity": "critique"}])
    assert pts == [[-11.66, 27.48, 1.0]]


# --- Endpoints --------------------------------------------------------------

def test_endpoint_summary(client):
    client.post("/api/alerts", json=sample_alert(lat=-11.66, lng=27.48, severity="critique"))
    client.post("/api/alerts", json=sample_alert(lat=-11.66, lng=27.48, severity="eleve"))
    res = client.get("/api/analysis/summary")
    assert res.status_code == 200
    body = res.get_json()
    assert body["total"] == 2
    assert body["riskiestZone"] is not None


def test_endpoint_hotspots_et_heatmap(client):
    client.post("/api/alerts", json=sample_alert(lat=-11.66, lng=27.48))
    assert client.get("/api/analysis/hotspots").status_code == 200
    heat = client.get("/api/analysis/heatmap").get_json()
    assert len(heat) == 1 and len(heat[0]) == 3
