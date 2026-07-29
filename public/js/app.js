/* ---------------------------------------------------------------------------
   SafeCity Lubumbashi - Application cliente
   Carte Leaflet + temps reel Socket.io + signalement d'incidents.
   --------------------------------------------------------------------------- */

const state = {
  config: null,
  incidents: new Map(),   // id -> incident
  markers: new Map(),     // id -> L.marker
  categories: new Map(),  // id -> {label, icon, color}
  filter: '',
  draft: { lat: null, lng: null, severity: 'moyen', photo: null },
};

let map;
let draftMarker = null;

// --- Utilitaires ------------------------------------------------------------

const $ = (sel) => document.querySelector(sel);

function timeAgo(iso) {
  const diff = Math.floor((Date.now() - new Date(iso)) / 1000);
  if (diff < 60) return 'a l\'instant';
  if (diff < 3600) return `il y a ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `il y a ${Math.floor(diff / 3600)} h`;
  return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

function toast(message) {
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = message;
  $('#toasts').appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity .3s'; }, 4200);
  setTimeout(() => el.remove(), 4600);
}

// --- Initialisation ---------------------------------------------------------

async function init() {
  state.config = await fetch('/api/config').then((r) => r.json());
  state.config.categories.forEach((c) => state.categories.set(c.id, c));

  initMap();
  buildCategoryOptions();
  buildSeverityButtons();

  const incidents = await fetch('/api/incidents').then((r) => r.json());
  incidents.forEach((inc) => addIncident(inc, false));
  renderFeed();
  await refreshStats();

  initSocket();
  bindUI();
}

function initMap() {
  const { lat, lng } = state.config.center;
  map = L.map('map', { zoomControl: true }).setView([lat, lng], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap',
  }).addTo(map);

  // Cliquer sur la carte definit la position du brouillon (quand la modale est ouverte).
  map.on('click', (e) => {
    if ($('#modal').hidden) return;
    setDraftLocation(e.latlng.lat, e.latlng.lng);
  });
}

// --- Marqueurs & incidents --------------------------------------------------

function makeIcon(category) {
  const cat = state.categories.get(category) || { icon: '📍', color: '#0f766e' };
  return L.divIcon({
    className: '',
    html: `<div class="incident-marker" style="background:${cat.color}"><span>${cat.icon}</span></div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 34],
    popupAnchor: [0, -34],
  });
}

function popupHtml(inc) {
  const cat = state.categories.get(inc.category) || { label: inc.category, icon: '📍' };
  const photo = inc.photo ? `<img src="${escapeHtml(inc.photo)}" alt="photo de l'incident" />` : '';
  return `
    <div class="popup">
      <h3>${cat.icon} ${escapeHtml(cat.label)}</h3>
      <p>${escapeHtml(inc.description)}</p>
      ${inc.address ? `<p>📍 ${escapeHtml(inc.address)}</p>` : ''}
      <p><strong>Gravite :</strong> ${escapeHtml(inc.severity)} · <strong>Statut :</strong> ${escapeHtml(inc.status)}</p>
      <p><small>${timeAgo(inc.createdAt)} · ✔️ ${inc.confirmations} confirmation(s)</small></p>
      ${photo}
      <div class="popup-actions">
        <button onclick="window.SafeCity.confirm('${inc.id}')">✔️ Je confirme</button>
        <button class="secondary" onclick="window.SafeCity.resolve('${inc.id}')">✅ Résolu</button>
      </div>
    </div>`;
}

function addIncident(inc, isNew) {
  state.incidents.set(inc.id, inc);
  const marker = L.marker([inc.lat, inc.lng], { icon: makeIcon(inc.category) })
    .addTo(map)
    .bindPopup(popupHtml(inc));
  state.markers.set(inc.id, marker);
  applyFilterToMarker(inc.id);
  if (isNew) {
    marker.setZIndexOffset(1000);
  }
}

function updateIncident(inc) {
  state.incidents.set(inc.id, inc);
  const marker = state.markers.get(inc.id);
  if (marker) marker.setPopupContent(popupHtml(inc));
  renderFeed();
}

function applyFilterToMarker(id) {
  const inc = state.incidents.get(id);
  const marker = state.markers.get(id);
  if (!inc || !marker) return;
  const visible = !state.filter || inc.category === state.filter;
  if (visible && !map.hasLayer(marker)) marker.addTo(map);
  if (!visible && map.hasLayer(marker)) map.removeLayer(marker);
}

// --- Rendu du panneau -------------------------------------------------------

function renderFeed() {
  const feed = $('#feed');
  const list = [...state.incidents.values()]
    .filter((inc) => !state.filter || inc.category === state.filter)
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

  if (!list.length) {
    feed.innerHTML = '<li class="feed-empty">Aucun incident pour ce filtre.</li>';
    return;
  }

  feed.innerHTML = list.map((inc) => {
    const cat = state.categories.get(inc.category) || { label: inc.category, icon: '📍', color: '#666' };
    return `
      <li class="feed-item" style="border-left-color:${cat.color}" data-id="${inc.id}">
        <div class="fi-top">
          <span class="fi-cat">${cat.icon} ${escapeHtml(cat.label)}</span>
          <span class="fi-time">${timeAgo(inc.createdAt)}</span>
        </div>
        <p class="fi-desc">${escapeHtml(inc.description)}</p>
        <div class="fi-meta">
          <span class="badge badge-sev-${inc.severity}">${escapeHtml(inc.severity)}</span>
          <span class="badge badge-status-${inc.status}">${escapeHtml(inc.status)}</span>
          <span class="badge" style="background:transparent;color:var(--text-muted)">✔️ ${inc.confirmations}</span>
        </div>
      </li>`;
  }).join('');

  feed.querySelectorAll('.feed-item').forEach((li) => {
    li.addEventListener('click', () => {
      const inc = state.incidents.get(li.dataset.id);
      const marker = state.markers.get(li.dataset.id);
      if (inc && marker) {
        map.setView([inc.lat, inc.lng], 16, { animate: true });
        marker.openPopup();
      }
    });
  });
}

async function refreshStats() {
  const stats = await fetch('/api/stats').then((r) => r.json());
  $('#stats').innerHTML = `
    <div class="stat-card"><div class="stat-value">${stats.total}</div><div class="stat-label">Total</div></div>
    <div class="stat-card"><div class="stat-value" style="color:var(--primary)">${stats.byStatus.actif}</div><div class="stat-label">Actifs</div></div>
    <div class="stat-card"><div class="stat-value" style="color:var(--green)">${stats.byStatus.resolu}</div><div class="stat-label">Résolus</div></div>`;
}

// --- Temps reel -------------------------------------------------------------

function initSocket() {
  const socket = io();
  socket.on('incident:new', (inc) => {
    if (state.incidents.has(inc.id)) return;
    addIncident(inc, true);
    renderFeed();
    refreshStats();
    const cat = state.categories.get(inc.category);
    toast(`🚨 Nouvel incident : ${cat ? cat.label : inc.category}`);
  });
  socket.on('incident:update', (inc) => { updateIncident(inc); refreshStats(); });
  socket.on('presence', ({ online }) => { $('#presence-count').textContent = online; });
}

// --- Formulaire de signalement ---------------------------------------------

function buildCategoryOptions() {
  const filter = $('#filter-category');
  const formSelect = $('#f-category');
  state.config.categories.forEach((c) => {
    filter.insertAdjacentHTML('beforeend', `<option value="${c.id}">${c.icon} ${c.label}</option>`);
    formSelect.insertAdjacentHTML('beforeend', `<option value="${c.id}">${c.icon} ${c.label}</option>`);
  });
}

function buildSeverityButtons() {
  const group = $('#severity-group');
  state.config.severities.forEach((s) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'sev-btn' + (s.id === state.draft.severity ? ' active' : '');
    btn.textContent = s.label;
    btn.dataset.sev = s.id;
    btn.addEventListener('click', () => {
      state.draft.severity = s.id;
      group.querySelectorAll('.sev-btn').forEach((b) => b.classList.toggle('active', b === btn));
    });
    group.appendChild(btn);
  });
}

function setDraftLocation(lat, lng) {
  state.draft.lat = lat;
  state.draft.lng = lng;
  const display = $('#coords-display');
  display.textContent = `📍 ${lat.toFixed(5)}, ${lng.toFixed(5)}`;
  display.classList.add('set');

  if (draftMarker) draftMarker.setLatLng([lat, lng]);
  else draftMarker = L.marker([lat, lng], { opacity: 0.7 }).addTo(map);
}

function clearDraftMarker() {
  if (draftMarker) { map.removeLayer(draftMarker); draftMarker = null; }
}

function openModal() {
  $('#modal').hidden = false;
  toast('Cliquez sur la carte ou utilisez « Ma position » pour localiser l\'incident.');
}

function closeModal() {
  $('#modal').hidden = true;
  $('#report-form').reset();
  $('#form-error').hidden = true;
  $('#photo-preview').hidden = true;
  $('#coords-display').textContent = 'Aucune position sélectionnée';
  $('#coords-display').classList.remove('set');
  state.draft = { lat: null, lng: null, severity: 'moyen', photo: null };
  $('#severity-group').querySelectorAll('.sev-btn').forEach((b) =>
    b.classList.toggle('active', b.dataset.sev === 'moyen'));
  clearDraftMarker();
}

function locateUser(centerMap) {
  if (!navigator.geolocation) return toast('Géolocalisation non supportée par ce navigateur.');
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const { latitude, longitude } = pos.coords;
      if (centerMap) map.setView([latitude, longitude], 15);
      if (!$('#modal').hidden) setDraftLocation(latitude, longitude);
    },
    () => toast('Impossible d\'obtenir votre position. Vérifiez les autorisations.'),
    { enableHighAccuracy: true, timeout: 8000 }
  );
}

function readPhoto(file) {
  return new Promise((resolve) => {
    if (!file) return resolve(null);
    if (file.size > 4 * 1024 * 1024) { toast('Photo trop lourde (max 4 Mo).'); return resolve(null); }
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => resolve(null);
    reader.readAsDataURL(file);
  });
}

async function submitReport(e) {
  e.preventDefault();
  const errorBox = $('#form-error');
  errorBox.hidden = true;

  if (state.draft.lat == null) {
    errorBox.textContent = 'Veuillez sélectionner une position sur la carte.';
    errorBox.hidden = false;
    return;
  }

  const payload = {
    category: $('#f-category').value,
    severity: state.draft.severity,
    description: $('#f-description').value.trim(),
    lat: state.draft.lat,
    lng: state.draft.lng,
    photo: state.draft.photo,
  };

  const submitBtn = $('#submit-report');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Envoi...';

  try {
    const res = await fetch('/api/incidents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      errorBox.textContent = (data.errors || ['Erreur inconnue.']).join(' ');
      errorBox.hidden = false;
      return;
    }
    // L'incident nous reviendra aussi via Socket.io ; on l'ajoute localement au cas ou.
    if (!state.incidents.has(data.id)) { addIncident(data, false); renderFeed(); refreshStats(); }
    toast('✅ Merci ! Votre signalement a été transmis.');
    closeModal();
    map.setView([data.lat, data.lng], 16);
  } catch (err) {
    errorBox.textContent = 'Connexion au serveur impossible.';
    errorBox.hidden = false;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Envoyer le signalement';
  }
}

// --- Liaison de l'interface -------------------------------------------------

function bindUI() {
  $('#btn-report').addEventListener('click', openModal);
  $('#modal-close').addEventListener('click', closeModal);
  $('#cancel-report').addEventListener('click', closeModal);
  $('#report-form').addEventListener('submit', submitReport);
  $('#f-use-location').addEventListener('click', () => locateUser(false));
  $('#btn-locate').addEventListener('click', () => locateUser(true));

  $('#f-photo').addEventListener('change', async (e) => {
    const dataUrl = await readPhoto(e.target.files[0]);
    state.draft.photo = dataUrl;
    const preview = $('#photo-preview');
    if (dataUrl) { preview.src = dataUrl; preview.hidden = false; }
    else preview.hidden = true;
  });

  $('#filter-category').addEventListener('change', (e) => {
    state.filter = e.target.value;
    state.markers.forEach((_, id) => applyFilterToMarker(id));
    renderFeed();
  });

  $('#modal').addEventListener('click', (e) => { if (e.target === $('#modal')) closeModal(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !$('#modal').hidden) closeModal(); });
}

// --- API exposee aux popups -------------------------------------------------

window.SafeCity = {
  async confirm(id) {
    const inc = await fetch(`/api/incidents/${id}/confirm`, { method: 'POST' }).then((r) => r.json());
    if (inc && inc.id) { updateIncident(inc); toast('Merci d\'avoir confirmé cet incident.'); }
  },
  async resolve(id) {
    const inc = await fetch(`/api/incidents/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'resolu' }),
    }).then((r) => r.json());
    if (inc && inc.id) { updateIncident(inc); refreshStats(); toast('Incident marqué comme résolu.'); }
  },
};

init().catch((err) => {
  console.error(err);
  document.body.insertAdjacentHTML('afterbegin',
    '<p style="padding:20px;color:#fca5a5">Erreur de chargement de l\'application.</p>');
});
