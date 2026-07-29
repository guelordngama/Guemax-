-- SafeCity Lubumbashi — schéma de la base de données (référence).
--
-- Les tables sont créées automatiquement par SQLAlchemy au démarrage du
-- backend (voir backend/database.py). Ce fichier documente la structure et
-- permet une création manuelle sous SQLite/PostgreSQL si nécessaire.

CREATE TABLE IF NOT EXISTS users (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    username             VARCHAR(80)  NOT NULL UNIQUE,
    email                VARCHAR(120) NOT NULL UNIQUE,
    password_hash        VARCHAR(256) NOT NULL,
    role                 VARCHAR(20)  DEFAULT 'citizen',   -- citizen | admin | agent
    nom                  VARCHAR(80),
    post_nom             VARCHAR(80),
    date_naissance       VARCHAR(20),
    ville                VARCHAR(80),
    nationalite          VARCHAR(80),
    is_verified          BOOLEAN      DEFAULT 0,
    verification_code    VARCHAR(10),
    verification_expires TIMESTAMP,
    created_at           TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    category       VARCHAR(40)  NOT NULL,
    severity       VARCHAR(20)  NOT NULL,           -- faible | moyen | eleve | critique
    description    TEXT         NOT NULL,
    lat            REAL         NOT NULL,
    lng            REAL         NOT NULL,
    address        VARCHAR(200),
    photo          VARCHAR(300),
    status         VARCHAR(20)  DEFAULT 'actif',    -- actif | verifie | resolu
    priority       VARCHAR(20)  DEFAULT 'moyenne',  -- basse | moyenne | haute | critique
    priority_score REAL         DEFAULT 0.0,
    confirmations  INTEGER      DEFAULT 0,
    user_id        INTEGER      REFERENCES users(id),   -- citoyen signalant (facultatif)
    created_at     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agents (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       VARCHAR(120) NOT NULL,
    phone      VARCHAR(30),
    status     VARCHAR(20)  DEFAULT 'disponible',   -- disponible | en_intervention
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS interventions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id   INTEGER NOT NULL REFERENCES alerts(id),
    agent_id   INTEGER REFERENCES agents(id),
    status     VARCHAR(20) DEFAULT 'en_cours',      -- en_cours | terminee | annulee
    notes      TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alerts_status   ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_created  ON alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_category ON alerts(category);
