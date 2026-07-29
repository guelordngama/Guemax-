# 🚨 SafeCity Lubumbashi

**Application de signalement d'incidents avec géolocalisation en temps réel — une technologie au service de la sécurité de notre communauté. 📍💻**

SafeCity Lubumbashi permet à chaque citoyen de signaler en quelques secondes un
incident de sécurité (vol, agression, accident, incendie, inondation, coupure
d'électricité, problème de voirie…) et de le voir apparaître **instantanément**
sur une carte partagée par toute la communauté.

---

## ✨ Fonctionnalités

- 🗺️ **Carte interactive** centrée sur Lubumbashi (Leaflet + OpenStreetMap, sans clé API).
- 📡 **Géolocalisation en temps réel** : « Ma position » via le GPS du navigateur, ou clic sur la carte.
- ⚡ **Diffusion instantanée** : chaque nouveau signalement apparaît en direct chez tous les utilisateurs connectés (Socket.io).
- 🏷️ **Catégorisation & gravité** : 8 catégories d'incidents, 4 niveaux de gravité.
- 📷 **Photo facultative** jointe au signalement.
- ✔️ **Confirmation communautaire** (« Je confirme ») et suivi du **statut** (actif / vérifié / résolu).
- 🔎 **Filtrage** par catégorie et **fil des incidents récents**.
- 📊 **Tableau de bord** : total, incidents actifs, résolus, présence en ligne.
- 📱 **Responsive** (mobile / tablette / bureau) et **thème clair/sombre** automatique.

---

## 🛠️ Stack technique

| Couche      | Technologie |
|-------------|-------------|
| Backend     | Node.js, Express, Socket.io |
| Persistance | Fichier JSON atomique (aucune dépendance native, démarre partout) |
| Frontend    | HTML/CSS/JavaScript natif, Leaflet |
| Temps réel  | WebSockets via Socket.io |

Aucune base de données externe ni clé d'API n'est requise : l'application
démarre avec un simple `npm install && npm start`.

---

## 🚀 Démarrage rapide

**Prérequis :** Node.js ≥ 18.

```bash
# 1. Installer les dépendances
npm install

# 2. Lancer le serveur
npm start

# 3. Ouvrir l'application
#    http://localhost:3000
```

En développement, `npm run dev` recharge automatiquement le serveur à chaque
modification.

Le port peut être personnalisé : `PORT=8080 npm start`.

---

## 📁 Structure du projet

```
.
├── server/
│   ├── index.js      # Serveur Express + API REST + Socket.io
│   ├── store.js      # Persistance JSON (écriture atomique)
│   └── config.js     # Constantes partagées (catégories, gravités, centre carte)
├── public/
│   ├── index.html    # Interface
│   ├── css/styles.css
│   ├── js/app.js     # Logique cliente (carte, temps réel, formulaire)
│   └── uploads/      # Photos jointes (générées à l'exécution)
├── data/
│   └── incidents.json # Base de données fichier (générée à l'exécution)
└── package.json
```

---

## 🔌 API REST

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET`   | `/api/config` | Centre de la carte, catégories et gravités |
| `GET`   | `/api/incidents` | Liste des incidents (du plus récent au plus ancien) |
| `GET`   | `/api/stats` | Statistiques agrégées |
| `POST`  | `/api/incidents` | Créer un incident |
| `POST`  | `/api/incidents/:id/confirm` | Ajouter une confirmation |
| `PATCH` | `/api/incidents/:id/status` | Changer le statut (`actif`/`verifie`/`resolu`) |

**Exemple — créer un incident :**

```bash
curl -X POST http://localhost:3000/api/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "category": "vol",
    "severity": "eleve",
    "description": "Vol de moto signalé près du marché",
    "lat": -11.6647,
    "lng": 27.4794
  }'
```

### Événements temps réel (Socket.io)

| Événement | Charge utile | Sens |
|-----------|--------------|------|
| `incident:new` | incident | serveur → clients |
| `incident:update` | incident | serveur → clients |
| `presence` | `{ online }` | serveur → clients |

---

## 🔒 Sécurité & validation

- Validation stricte côté serveur (catégorie, gravité, longueur de description, bornes des coordonnées).
- Échappement HTML de tout contenu utilisateur affiché sur la carte et dans le fil.
- Photos limitées à 4 Mo et aux formats image (`png`, `jpg`, `webp`).
- Écriture disque atomique (fichier temporaire + `rename`) pour éviter la corruption des données.

---

## 🗺️ Pistes d'évolution

- Authentification des citoyens et des services d'intervention.
- Notifications push / SMS pour les incidents critiques d'un quartier.
- Zones de chaleur (heatmap) et analyses statistiques par commune.
- Application mobile native et mode hors-ligne.
- Tableau de bord dédié aux autorités locales.

---

## 📜 Licence

MIT — libre d'utilisation au service de la sécurité de la communauté de Lubumbashi.
