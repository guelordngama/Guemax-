"""Analyse IA des zones à risque (hotspots, heures de pointe, heatmap).

S'appuie sur ``ai_module/zone_analysis.py`` (fonctions pures) appliqué aux
alertes de Lubumbashi enregistrées en base.
"""

import os
import sys

from flask import Blueprint, jsonify

from config import LUBUMBASHI_BOUNDS
from models import Alert

# Rendre ai_module importable.
_AI_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ai_module")
if _AI_DIR not in sys.path:
    sys.path.insert(0, _AI_DIR)
import zone_analysis  # noqa: E402

analysis_bp = Blueprint("analysis", __name__)


def _lubumbashi_alerts():
    b = LUBUMBASHI_BOUNDS
    alerts = Alert.query.filter(
        Alert.lat.between(b["min_lat"], b["max_lat"]),
        Alert.lng.between(b["min_lng"], b["max_lng"]),
    ).all()
    return [a.to_dict() for a in alerts]


@analysis_bp.get("/hotspots")
def hotspots():
    return jsonify(zone_analysis.analyze_hotspots(_lubumbashi_alerts(), LUBUMBASHI_BOUNDS))


@analysis_bp.get("/peak-hours")
def peak():
    return jsonify(zone_analysis.peak_hours(_lubumbashi_alerts()))


@analysis_bp.get("/heatmap")
def heatmap():
    return jsonify(zone_analysis.heatmap_points(_lubumbashi_alerts()))


@analysis_bp.get("/summary")
def summary():
    return jsonify(zone_analysis.summarize(_lubumbashi_alerts(), LUBUMBASHI_BOUNDS))
