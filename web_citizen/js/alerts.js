/* Logique applicative du site citoyen (namespace SC).
   Deux pages : accueil (carte temps réel) et formulaire de signalement. */

window.SC = window.SC || {};

// --- Page ACCUEIL : carte temps réel + fil + statistiques ------------------

async function initHomePage() {
  const map = SC.createMap('map');
  const view = new SC.MapView(map);
  SC.mapView = view;

  const alerts = await fetch(SC.API + '/api/alerts').then((r) => r.json());
  const store = new Map();
  alerts.forEach((a) => { store.set(a.id, a); view.upsert(a); });

  renderFeed(store, view);
  await refreshStats();

  const socket = io();
  socket.on('alert:new', (a) => {
    if (store.has(a.id)) return;
    store.set(a.id, a);
    view.upsert(a);
    renderFeed(store, view);
    refreshStats();
    const cat = SC.categoriesById[a.category];
    SC.toast(`🚨 Nouvelle alerte : ${cat ? cat.label : a.category}`);
  });
  socket.on('alert:update', (a) => {
    store.set(a.id, a);
    view.upsert(a);
    renderFeed(store, view);
    refreshStats();
  });
  socket.on('presence', ({ online }) => {
    const el = document.getElementById('presence-count');
    if (el) el.textContent = online;
  });
}

function renderFeed(store, view) {
  const feed = document.getElementById('feed');
  if (!feed) return;
  const list = [...store.values()].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  if (!list.length) {
    feed.innerHTML = '<li class="feed-empty">Aucune alerte signalée pour le moment.</li>';
    return;
  }
  feed.innerHTML = list.map((a) => {
    const cat = SC.categoriesById[a.category] || { label: a.category, icon: '📍', color: '#666' };
    return `
      <li class="feed-item" style="border-left-color:${cat.color}" data-id="${a.id}">
        <div class="fi-top">
          <span class="fi-cat">${cat.icon} ${SC.escapeHtml(cat.label)}</span>
          <span class="fi-time">${SC.timeAgo(a.createdAt)}</span>
        </div>
        <p class="fi-desc">${SC.escapeHtml(a.description)}</p>
        <div class="fi-meta">
          <span class="badge badge-sev-${a.severity}">${SC.escapeHtml(a.severity)}</span>
          <span class="badge badge-status-${a.status}">${SC.escapeHtml(a.status)}</span>
          <span class="badge badge-prio-${a.priority}">priorité ${SC.escapeHtml(a.priority)}</span>
        </div>
      </li>`;
  }).join('');
  feed.querySelectorAll('.feed-item').forEach((li) => {
    li.addEventListener('click', () => view.focus(store.get(Number(li.dataset.id))));
  });
}

async function refreshStats() {
  const el = document.getElementById('stats');
  if (!el) return;
  const s = await fetch(SC.API + '/api/alerts/stats/summary').then((r) => r.json());
  el.innerHTML = `
    <div class="stat-card"><div class="stat-value">${s.total}</div><div class="stat-label">Total</div></div>
    <div class="stat-card"><div class="stat-value" style="color:var(--primary)">${s.byStatus.actif}</div><div class="stat-label">Actives</div></div>
    <div class="stat-card"><div class="stat-value" style="color:var(--green)">${s.byStatus.resolu}</div><div class="stat-label">Résolues</div></div>`;
}

// --- Page FORMULAIRE : signalement d'une alerte ----------------------------

function initReportPage() {
  const draft = { lat: null, lng: null, severity: 'moyen', photo: null };
  const map = SC.createMap('map');
  let draftMarker = null;

  const setLocation = (lat, lng) => {
    draft.lat = lat; draft.lng = lng;
    const disp = document.getElementById('coords-display');
    disp.textContent = `📍 ${lat.toFixed(5)}, ${lng.toFixed(5)}`;
    disp.classList.add('set');
    if (draftMarker) draftMarker.setLatLng([lat, lng]);
    else draftMarker = L.marker([lat, lng]).addTo(map);
    map.setView([lat, lng], 15);
  };

  map.on('click', (e) => setLocation(e.latlng.lat, e.latlng.lng));

  // Catégories
  const catSelect = document.getElementById('f-category');
  SC.config.categories.forEach((c) => {
    catSelect.insertAdjacentHTML('beforeend', `<option value="${c.id}">${c.icon} ${c.label}</option>`);
  });

  // Gravité
  const sevGroup = document.getElementById('severity-group');
  SC.config.severities.forEach((s) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'sev-btn' + (s.id === draft.severity ? ' active' : '');
    btn.textContent = s.label;
    btn.addEventListener('click', () => {
      draft.severity = s.id;
      sevGroup.querySelectorAll('.sev-btn').forEach((b) => b.classList.toggle('active', b === btn));
    });
    sevGroup.appendChild(btn);
  });

  document.getElementById('f-use-location').addEventListener('click', () =>
    SC.locate((c) => setLocation(c.lat, c.lng)));

  document.getElementById('f-photo').addEventListener('change', (e) => {
    const file = e.target.files[0];
    const preview = document.getElementById('photo-preview');
    if (!file) { draft.photo = null; preview.hidden = true; return; }
    if (file.size > 4 * 1024 * 1024) { SC.toast('Photo trop lourde (max 4 Mo).'); return; }
    const reader = new FileReader();
    reader.onload = () => { draft.photo = reader.result; preview.src = reader.result; preview.hidden = false; };
    reader.readAsDataURL(file);
  });

  document.getElementById('report-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorBox = document.getElementById('form-error');
    errorBox.hidden = true;
    if (draft.lat == null) {
      errorBox.textContent = 'Veuillez indiquer la localisation (GPS ou clic sur la carte).';
      errorBox.hidden = false;
      return;
    }
    const payload = {
      category: document.getElementById('f-category').value,
      severity: draft.severity,
      description: document.getElementById('f-description').value.trim(),
      lat: draft.lat, lng: draft.lng, photo: draft.photo,
    };
    const btn = document.getElementById('submit-report');
    btn.disabled = true; btn.textContent = 'Envoi...';
    try {
      const res = await fetch(SC.API + '/api/alerts', {
        method: 'POST',
        headers: SC.authHeaders(),
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        errorBox.textContent = (data.errors || ['Erreur inconnue.']).join(' ');
        errorBox.hidden = false;
        return;
      }
      SC.toast('✅ Alerte transmise. Merci pour votre vigilance !');
      setTimeout(() => { window.location.href = 'index.html'; }, 1200);
    } catch (err) {
      errorBox.textContent = 'Connexion au serveur impossible.';
      errorBox.hidden = false;
    } finally {
      btn.disabled = false; btn.textContent = "Envoyer l'alerte";
    }
  });
}

// --- Amorçage --------------------------------------------------------------

(async function bootstrap() {
  if (!SC.requireAuth()) return; // redirige vers auth.html si non connecté
  await SC.loadConfig();
  SC.renderAccount();
  if (document.getElementById('report-form')) initReportPage();
  else if (document.getElementById('map')) initHomePage();
})().catch((err) => {
  console.error(err);
  SC.toast('Erreur de chargement de l\'application.');
});
