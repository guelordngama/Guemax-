"""Analyse prédictive des zones à risque (IA géospatiale).

Fonctions pures opérant sur une liste d'alertes (dictionnaires) :
- découpage de la ville en grille,
- indice de risque par zone (densité pondérée par gravité et récence),
- heures de pointe des incidents,
- points pour carte de chaleur (heatmap).

Aucune dépendance externe : utilisable côté backend comme en autonome.
"""

from datetime import datetime, timezone

SEVERITY_WEIGHT = {"faible": 1, "moyen": 2, "eleve": 3, "critique": 4}
GRID_N = 6  # nombre de divisions par axe (grille GRID_N x GRID_N)


def _parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _recency_factor(created_at, now=None):
    """Pondère les incidents récents plus fortement."""
    now = now or datetime.now(timezone.utc)
    dt = _parse_dt(created_at)
    if not dt:
        return 1.0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    days = max((now - dt).total_seconds() / 86400, 0)
    if days <= 7:
        return 1.6
    if days <= 30:
        return 1.0
    if days <= 90:
        return 0.6
    return 0.3


def _cardinal(row, col, n):
    """Nom lisible d'une zone selon sa position (Nord/Sud, Ouest/Est)."""
    ns = "Nord" if row < n / 3 else ("Sud" if row >= 2 * n / 3 else "Centre")
    we = "Ouest" if col < n / 3 else ("Est" if col >= 2 * n / 3 else "")
    name = f"{ns}-{we}" if we and ns != "Centre" else (we or ns)
    return f"Secteur {name} ({chr(65 + row)}{col + 1})"


def _risk_level(score):
    if score >= 75:
        return "critique"
    if score >= 50:
        return "eleve"
    if score >= 25:
        return "moyen"
    return "faible"


def analyze_hotspots(alerts, bounds, grid_n=GRID_N, now=None):
    """Découpe la ville en grille et calcule un indice de risque par zone.

    Retourne la liste des zones actives triées par indice décroissant.
    """
    if not bounds:
        return []
    lat_min, lat_max = bounds["min_lat"], bounds["max_lat"]
    lng_min, lng_max = bounds["min_lng"], bounds["max_lng"]
    lat_span = (lat_max - lat_min) or 1e-9
    lng_span = (lng_max - lng_min) or 1e-9

    cells = {}
    for a in alerts:
        lat, lng = a.get("lat"), a.get("lng")
        if lat is None or lng is None:
            continue
        row = min(int((lat - lat_min) / lat_span * grid_n), grid_n - 1)
        col = min(int((lng - lng_min) / lng_span * grid_n), grid_n - 1)
        if not (0 <= row < grid_n and 0 <= col < grid_n):
            continue
        cell = cells.setdefault((row, col), {"count": 0, "score": 0.0, "cats": {}})
        weight = SEVERITY_WEIGHT.get(a.get("severity"), 1) * _recency_factor(a.get("createdAt"), now)
        cell["count"] += 1
        cell["score"] += weight
        cat = a.get("category", "autre")
        cell["cats"][cat] = cell["cats"].get(cat, 0) + 1

    if not cells:
        return []

    max_score = max(c["score"] for c in cells.values()) or 1.0
    zones = []
    for (row, col), c in cells.items():
        center_lat = lat_min + (row + 0.5) / grid_n * lat_span
        center_lng = lng_min + (col + 0.5) / grid_n * lng_span
        risk = round(c["score"] / max_score * 100, 1)
        dominant = max(c["cats"].items(), key=lambda kv: kv[1])[0]
        zones.append({
            "zone": _cardinal(row, col, grid_n),
            "lat": round(center_lat, 5),
            "lng": round(center_lng, 5),
            "count": c["count"],
            "riskIndex": risk,
            "riskLevel": _risk_level(risk),
            "dominantCategory": dominant,
        })
    zones.sort(key=lambda z: z["riskIndex"], reverse=True)
    return zones


def peak_hours(alerts):
    """Répartition des incidents par heure de la journée (0–23)."""
    hours = [0] * 24
    for a in alerts:
        dt = _parse_dt(a.get("createdAt"))
        if dt:
            hours[dt.hour] += 1
    peak = max(range(24), key=lambda h: hours[h]) if any(hours) else None
    return {"byHour": hours, "peakHour": peak}


def heatmap_points(alerts):
    """Points [lat, lng, poids] pour une couche de chaleur Leaflet."""
    pts = []
    for a in alerts:
        if a.get("lat") is None or a.get("lng") is None:
            continue
        weight = SEVERITY_WEIGHT.get(a.get("severity"), 1) / 4.0
        pts.append([a["lat"], a["lng"], round(weight, 3)])
    return pts


def summarize(alerts, bounds, now=None):
    """Synthèse pour le tableau de bord IA."""
    zones = analyze_hotspots(alerts, bounds, now=now)
    ph = peak_hours(alerts)
    by_category = {}
    for a in alerts:
        by_category[a.get("category", "autre")] = by_category.get(a.get("category", "autre"), 0) + 1
    return {
        "total": len(alerts),
        "topZones": zones[:5],
        "byCategory": by_category,
        "peakHour": ph["peakHour"],
        "byHour": ph["byHour"],
        "riskiestZone": zones[0] if zones else None,
    }
