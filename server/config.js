/**
 * config.js - Constantes partagees (categories, severites, statuts).
 * Egalement exposees au frontend via GET /api/config pour eviter la duplication.
 */

// Centre approximatif de Lubumbashi (RDC).
export const LUBUMBASHI_CENTER = { lat: -11.6647, lng: 27.4794 };

export const CATEGORIES = [
  { id: 'vol', label: 'Vol / Cambriolage', icon: '👜', color: '#e11d48' },
  { id: 'agression', label: 'Agression', icon: '🚨', color: '#b91c1c' },
  { id: 'accident', label: 'Accident de circulation', icon: '🚗', color: '#f59e0b' },
  { id: 'incendie', label: 'Incendie', icon: '🔥', color: '#ea580c' },
  { id: 'inondation', label: 'Inondation', icon: '🌊', color: '#0284c7' },
  { id: 'electricite', label: 'Coupure d\'electricite', icon: '⚡', color: '#7c3aed' },
  { id: 'infrastructure', label: 'Voirie / Infrastructure', icon: '🚧', color: '#4b5563' },
  { id: 'autre', label: 'Autre', icon: '📍', color: '#0f766e' },
];

export const SEVERITIES = [
  { id: 'faible', label: 'Faible', weight: 1 },
  { id: 'moyen', label: 'Moyen', weight: 2 },
  { id: 'eleve', label: 'Eleve', weight: 3 },
  { id: 'critique', label: 'Critique', weight: 4 },
];

export const STATUSES = ['actif', 'verifie', 'resolu'];

export const CATEGORY_IDS = new Set(CATEGORIES.map((c) => c.id));
export const SEVERITY_IDS = new Set(SEVERITIES.map((s) => s.id));
