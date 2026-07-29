# 🚨 SafeCity Lubumbashi

**Système d'alerte et de signalement d'incidents avec géolocalisation en temps réel — la technologie au service de la sécurité de notre communauté. 📍💻**

SafeCity Lubumbashi met en relation les **citoyens** et les **services de la mairie** :
un citoyen signale une alerte depuis un site web (avec sa position GPS), et cette
alerte apparaît **instantanément** sur le tableau de bord de la mairie (application
de bureau) ainsi que sur une carte partagée.

```
CITOYEN (site web) → GPS + formulaire → API Flask → Base de données
                                             ↓
                                        Socket.IO (temps réel)
                                             ↓
                              MAIRIE (app Tkinter) → carte Leaflet → intervention
```

---

## 🧩 Architecture

| Composant | Rôle | Technologie |
|-----------|------|-------------|
| **backend/** | API REST + temps réel + base de données + IA | Python, Flask, Flask-SocketIO, SQLAlchemy |
| **web_citizen/** | Site citoyen : signalement + carte publique | HTML/CSS/JS, Leaflet |
| **admin_tkinter/** | Poste de la mairie : surveillance temps réel | Python, Tkinter |
| **database/** | Schéma et données de référence | SQL (SQLite par défaut) |
| **tests/** | Tests automatisés | pytest |

> Le module d'IA (`backend/utils/classification_ai.py`) fournit actuellement une
> **classification de priorité par règles** (placeholder). Le vrai modèle **SVM**
> entraîné (`ai_module/`), la documentation (`docs/`) et le déploiement
> (`deployment/`) sont prévus dans les étapes suivantes ; l'interface du
> classifieur est déjà stable pour un remplacement transparent.

---

## 🚀 Démarrage rapide

**Prérequis :** Python ≥ 3.10.

```bash
# 1. Environnement virtuel + dépendances
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt

# 2. Lancer le backend (API + temps réel + site citoyen)
cd backend
python app.py
#   → Site citoyen : http://localhost:5000/
#   → Carte mairie : http://localhost:5000/admin/map
#   → API          : http://localhost:5000/api/

# 3. Lancer l'application de bureau de la mairie (dans un autre terminal)
cd admin_tkinter
python main.py
#   Connexion par défaut :  admin  /  admin123
```

> ⚠️ Le compte administrateur par défaut (`admin` / `admin123`) est destiné au
> développement. Définissez `ADMIN_USERNAME` / `ADMIN_PASSWORD` (et `JWT_SECRET`,
> `SECRET_KEY`) via des variables d'environnement en production.

---

## ✨ Fonctionnalités (cœur fonctionnel)

**Site citoyen**
- 🗺️ Carte des alertes centrée sur Lubumbashi (Leaflet + OpenStreetMap, sans clé API)
- 📡 Signalement par **position GPS** ou clic sur la carte
- 🏷️ 8 catégories d'incidents, 4 niveaux de gravité, photo facultative
- ⚡ Mise à jour **temps réel** de la carte et du fil des alertes
- ✔️ Confirmation communautaire d'une alerte

**Poste mairie (Tkinter)**
- 🔐 Connexion sécurisée (JWT)
- 📋 Tableau des alertes trié par priorité, réception **temps réel**
- 🔄 Traitement : marquer une alerte *vérifiée* / *résolue*
- 📊 Statistiques (par statut, catégorie, priorité)
- 🗺️ Carte live ouverte dans le navigateur

**Backend**
- 🧠 Classification automatique de la **priorité** des alertes (placeholder IA)
- 🔒 Validation stricte, hachage des mots de passe, authentification JWT

---

## 📁 Arborescence

```
security-alert-system/
├── backend/
│   ├── app.py              # Application Flask (API + Socket.IO + fichiers statiques)
│   ├── config.py           # Configuration (env, base, secrets)
│   ├── models.py           # Modèles : User, Alert, Agent, Intervention
│   ├── database.py         # Init SQLAlchemy + données de départ
│   ├── socket_events.py    # Événements temps réel
│   ├── routes/             # auth.py · alerts.py · users.py
│   ├── utils/              # security.py · classification_ai.py · helpers.py
│   └── requirements.txt
├── web_citizen/
│   ├── index.html          # Carte publique temps réel
│   ├── alert.html          # Formulaire de signalement
│   ├── js/                 # gps.js · alerts.js · leaflet_map.js
│   ├── leaflet/map_config.js
│   └── assets/css/style.css
├── admin_tkinter/
│   ├── main.py             # Point d'entrée du poste mairie
│   ├── ui/                 # login_window · dashboard · alerts_view · stats_view
│   ├── services/           # api_client · socket_client · database_local
│   └── map/leaflet_view.html
├── database/               # schema.sql · seed_data.sql
├── tests/                  # test_api.py · test_alerts.py · test_socket.py
├── requirements.txt
└── README.md
```

---

## 🔌 API REST

| Méthode | Route | Accès | Description |
|---------|-------|-------|-------------|
| `GET`   | `/api/config` | public | Centre carte, catégories, gravités |
| `GET`   | `/api/health` | public | Sonde de disponibilité |
| `POST`  | `/api/auth/login` | public | Connexion (renvoie un JWT) |
| `POST`  | `/api/auth/register` | admin | Créer un compte agent/admin |
| `GET`   | `/api/alerts` | public | Liste des alertes (filtres `status`, `category`) |
| `POST`  | `/api/alerts` | public | Créer une alerte (citoyen) |
| `POST`  | `/api/alerts/<id>/confirm` | public | Confirmer une alerte |
| `PATCH` | `/api/alerts/<id>/status` | public* | Changer le statut |
| `GET`   | `/api/alerts/stats/summary` | public | Statistiques agrégées |
| `GET`   | `/api/users` | admin | Liste des utilisateurs |
| `GET`/`POST` | `/api/users/agents` | admin | Gestion des agents |

**Événements Socket.IO :** `alert:new`, `alert:update`, `presence`.

---

## 🧪 Tests

```bash
pytest -q
```

Les tests couvrent l'API (santé, config, authentification), le cycle de vie des
alertes (création, validation, confirmation, statut, statistiques, priorité) et
le canal temps réel Socket.IO. La CI (GitHub Actions) les exécute sur Python
3.10, 3.11 et 3.12.

---

## 🗺️ Étapes suivantes (déjà prévues dans la structure)

- 🧠 **ai_module/** : entraînement du modèle **SVM** et intégration réelle.
- 📄 **docs/** : mémoire, présentation mairie, diagrammes UML et d'architecture.
- ☁️ **deployment/** : Nginx, Gunicorn, HTTPS/SSL, script d'installation serveur.
- 👮 Gestion des **interventions** et affectation des **agents** aux alertes.

---

## 📜 Licence

MIT — au service de la sécurité de la communauté de Lubumbashi.
