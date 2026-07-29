/* Géolocalisation du navigateur (namespace SC). */

window.SC = window.SC || {};

/**
 * Récupère la position GPS de l'utilisateur.
 * @param {(coords:{lat:number,lng:number}) => void} onSuccess
 */
SC.locate = function (onSuccess) {
  if (!navigator.geolocation) {
    SC.toast('Géolocalisation non supportée par ce navigateur.');
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => onSuccess({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
    () => SC.toast("Position indisponible. Vérifiez les autorisations de localisation."),
    { enableHighAccuracy: true, timeout: 8000 }
  );
};
