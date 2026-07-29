/* Configuration Leaflet partagée + utilitaires communs (namespace global SC). */

window.SC = window.SC || {};

// Même origine que le backend Flask (le site est servi par Flask).
SC.API = '';

SC.config = null;
SC.categoriesById = {};

// --- Session / authentification citoyenne ---------------------------------

SC.token = () => localStorage.getItem('safecity_token');

SC.user = () => {
  try { return JSON.parse(localStorage.getItem('safecity_user') || 'null'); }
  catch (_e) { return null; }
};

SC.setSession = (token, user) => {
  localStorage.setItem('safecity_token', token);
  localStorage.setItem('safecity_user', JSON.stringify(user));
};

SC.logout = () => {
  localStorage.removeItem('safecity_token');
  localStorage.removeItem('safecity_user');
  window.location.href = 'auth.html';
};

/** En-têtes HTTP incluant le jeton si présent. */
SC.authHeaders = (base) => {
  const h = Object.assign({ 'Content-Type': 'application/json' }, base || {});
  const t = SC.token();
  if (t) h['Authorization'] = 'Bearer ' + t;
  return h;
};

/** Redirige vers la page d'authentification si aucun jeton n'est présent. */
SC.requireAuth = () => {
  if (!SC.token()) { window.location.href = 'auth.html'; return false; }
  return true;
};

/** Injecte le nom d'utilisateur + un bouton de déconnexion dans l'en-tête. */
SC.renderAccount = () => {
  const el = document.getElementById('account');
  const u = SC.user();
  if (!el || !u) return;
  el.innerHTML = `<span class="account-name">👤 ${SC.escapeHtml(u.username)}</span>
    <button class="btn btn-ghost btn-sm" id="btn-logout">Déconnexion</button>`;
  document.getElementById('btn-logout').addEventListener('click', SC.logout);
};

/** Charge la configuration (centre, catégories, gravités) depuis l'API. */
SC.loadConfig = async function () {
  SC.config = await fetch(SC.API + '/api/config').then((r) => r.json());
  SC.config.categories.forEach((c) => { SC.categoriesById[c.id] = c; });
  return SC.config;
};

/** Crée une carte Leaflet centrée sur Lubumbashi. */
SC.createMap = function (elementId, zoom) {
  const { lat, lng } = SC.config.center;
  const map = L.map(elementId, { zoomControl: true }).setView([lat, lng], zoom || 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap',
  }).addTo(map);
  return map;
};

/** Icône colorée en forme de goutte selon la catégorie de l'alerte. */
SC.markerIcon = function (category) {
  const cat = SC.categoriesById[category] || { icon: '📍', color: '#0f766e' };
  return L.divIcon({
    className: '',
    html: `<div class="incident-marker" style="background:${cat.color}"><span>${cat.icon}</span></div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 34],
    popupAnchor: [0, -34],
  });
};

SC.escapeHtml = function (str) {
  return String(str).replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
};

SC.timeAgo = function (iso) {
  const diff = Math.floor((Date.now() - new Date(iso)) / 1000);
  if (diff < 60) return "à l'instant";
  if (diff < 3600) return `il y a ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `il y a ${Math.floor(diff / 3600)} h`;
  return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
};

SC.toast = function (message) {
  let box = document.getElementById('toasts');
  if (!box) {
    box = document.createElement('div');
    box.id = 'toasts';
    box.className = 'toast-container';
    document.body.appendChild(box);
  }
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = message;
  box.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity .3s'; }, 4200);
  setTimeout(() => el.remove(), 4600);
};
