-- SafeCity Lubumbashi — données de démonstration (référence).
--
-- Le backend crée automatiquement un compte administrateur et des agents au
-- premier démarrage (backend/database.py). Ce script est fourni pour un
-- amorçage manuel ou une base de démonstration.
-- Remarque : les mots de passe réels sont hachés par l'application ; la valeur
-- ci-dessous est un exemple à remplacer.

INSERT INTO agents (name, phone, status) VALUES
    ('Patrouille Centre-ville',        '+243000000001', 'disponible'),
    ('Patrouille Kenya',               '+243000000002', 'disponible'),
    ('Équipe intervention rapide',     '+243000000003', 'disponible');

INSERT INTO alerts (category, severity, description, lat, lng, status, priority, priority_score, confirmations) VALUES
    ('accident', 'moyen',    'Accident de circulation au carrefour', -11.6620, 27.4820, 'actif',  'moyenne',  0.5, 2),
    ('incendie', 'critique', 'Départ de feu signalé dans un entrepôt', -11.6700, 27.4750, 'actif',  'critique', 0.9, 5),
    ('vol',      'eleve',    'Cambriolage signalé dans le quartier',   -11.6580, 27.4900, 'verifie','haute',    0.7, 3);
