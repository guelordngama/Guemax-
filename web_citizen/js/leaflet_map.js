/* Rendu des alertes sur une carte + fil temps réel (namespace SC). */

window.SC = window.SC || {};

SC.MapView = function (map) {
  this.map = map;
  this.markers = new Map(); // id -> L.marker
};

SC.MapView.prototype.popupHtml = function (a) {
  const cat = SC.categoriesById[a.category] || { label: a.category, icon: '📍' };
  const photo = a.photo ? `<img src="${SC.escapeHtml(a.photo)}" alt="photo" />` : '';
  return `
    <div class="popup">
      <h3>${cat.icon} ${SC.escapeHtml(cat.label)}</h3>
      <p>${SC.escapeHtml(a.description)}</p>
      ${a.address ? `<p>📍 ${SC.escapeHtml(a.address)}</p>` : ''}
      <p><strong>Gravité :</strong> ${SC.escapeHtml(a.severity)} ·
         <strong>Priorité :</strong> ${SC.escapeHtml(a.priority)} ·
         <strong>Statut :</strong> ${SC.escapeHtml(a.status)}</p>
      <p><small>${SC.timeAgo(a.createdAt)} · ✔️ ${a.confirmations} confirmation(s)</small></p>
      ${photo}
      <div class="popup-actions">
        <button onclick="SC.confirmAlert(${a.id})">✔️ Je confirme</button>
      </div>
    </div>`;
};

SC.MapView.prototype.upsert = function (a) {
  const existing = this.markers.get(a.id);
  if (existing) {
    existing.setPopupContent(this.popupHtml(a));
    return;
  }
  const marker = L.marker([a.lat, a.lng], { icon: SC.markerIcon(a.category) })
    .addTo(this.map)
    .bindPopup(this.popupHtml(a));
  this.markers.set(a.id, marker);
};

SC.MapView.prototype.focus = function (a) {
  const marker = this.markers.get(a.id);
  if (marker) {
    this.map.setView([a.lat, a.lng], 16, { animate: true });
    marker.openPopup();
  }
};

/** Confirme une alerte (bouton dans le popup), puis met à jour l'affichage. */
SC.confirmAlert = async function (id) {
  const res = await fetch(SC.API + `/api/alerts/${id}/confirm`, { method: 'POST' });
  if (res.ok) {
    const a = await res.json();
    if (SC.mapView) SC.mapView.upsert(a);
    SC.toast('Merci d\'avoir confirmé cette alerte.');
  }
};
