/* Authentification citoyenne : inscription, validation par code, connexion. */

(function () {
  // Déjà connecté ? on va directement au site.
  if (SC.token()) { window.location.href = 'index.html'; return; }

  const $ = (id) => document.getElementById(id);
  const forms = {
    signup: $('signup-form'), login: $('login-form'), verify: $('verify-form'),
    forgot: $('forgot-form'), reset: $('reset-form'),
  };
  const errorBox = $('auth-error');
  const infoBox = $('auth-info');
  const tabs = document.querySelector('.auth-tabs');
  let pendingUsername = null;

  function showError(msg) { errorBox.textContent = msg; errorBox.hidden = false; infoBox.hidden = true; }
  function showInfo(msg) { infoBox.textContent = msg; infoBox.hidden = false; errorBox.hidden = true; }
  function clearMsg() { errorBox.hidden = true; infoBox.hidden = true; }

  function show(mode) {
    clearMsg();
    Object.entries(forms).forEach(([k, f]) => { f.hidden = k !== mode; });
    document.querySelectorAll('.auth-tab').forEach((t) =>
      t.classList.toggle('active', t.dataset.mode === mode));
    // Les onglets ne concernent que inscription/connexion.
    tabs.style.display = (mode === 'signup' || mode === 'login') ? '' : 'none';
  }

  document.querySelectorAll('.auth-tab').forEach((tab) =>
    tab.addEventListener('click', () => show(tab.dataset.mode)));

  function goToVerify(username, devCode) {
    pendingUsername = username;
    show('verify');
    const dev = $('dev-code');
    if (devCode) {
      dev.hidden = false;
      dev.innerHTML = `Mode démo — votre code : <strong>${SC.escapeHtml(devCode)}</strong>`;
    }
  }

  async function postJson(path, body) {
    const res = await fetch(SC.API + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return { res, data: await res.json().catch(() => ({})) };
  }

  // --- Inscription ---------------------------------------------------------
  forms.signup.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMsg();
    const payload = {
      nom: $('s-nom').value.trim(),
      postNom: $('s-postnom').value.trim(),
      prenom: $('s-prenom').value.trim(),
      sexe: $('s-sexe').value,
      username: $('s-username').value.trim(),
      dateNaissance: $('s-dob').value,
      nationalite: $('s-nat').value.trim(),
      ville: $('s-ville').value.trim(),
      commune: $('s-commune').value.trim(),
      quartier: $('s-quartier').value.trim(),
      telephone: $('s-tel').value.trim(),
      email: $('s-email').value.trim(),
      password: $('s-password').value,
    };
    const { res, data } = await postJson('/api/auth/signup', payload);
    if (!res.ok) { showError((data.errors || ['Erreur.']).join(' ')); return; }
    showInfo(data.message || 'Compte créé.');
    goToVerify(data.username, data.devCode);
  });

  // --- Connexion -----------------------------------------------------------
  forms.login.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMsg();
    const username = $('l-username').value.trim();
    const { res, data } = await postJson('/api/auth/login', { username, password: $('l-password').value });
    if (res.status === 403 && data.needsVerification) {
      showInfo('Votre compte doit être validé. Un code vous a été envoyé.');
      await postJson('/api/auth/resend', { username });
      goToVerify(username, null);
      return;
    }
    if (!res.ok) { showError((data.errors || ['Identifiants incorrects.']).join(' ')); return; }
    SC.setSession(data.token, data.user);
    window.location.href = 'index.html';
  });

  // --- Validation ----------------------------------------------------------
  forms.verify.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMsg();
    const { res, data } = await postJson('/api/auth/verify', {
      username: pendingUsername, code: $('v-code').value.trim(),
    });
    if (!res.ok) { showError((data.errors || ['Code incorrect.']).join(' ')); return; }
    SC.setSession(data.token, data.user);
    window.location.href = 'index.html';
  });

  $('v-resend').addEventListener('click', async () => {
    const { data } = await postJson('/api/auth/resend', { username: pendingUsername });
    showInfo('Nouveau code envoyé.');
    if (data.devCode) {
      $('dev-code').hidden = false;
      $('dev-code').innerHTML = `Mode démo — votre code : <strong>${SC.escapeHtml(data.devCode)}</strong>`;
    }
  });

  // --- Mot de passe oublié -------------------------------------------------
  $('l-forgot').addEventListener('click', () => show('forgot'));

  forms.forgot.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMsg();
    const ident = $('fg-ident').value.trim();
    const { data } = await postJson('/api/auth/forgot', { username: ident, email: ident });
    pendingUsername = data.username || ident;
    show('reset');
    showInfo(data.message || 'Si le compte existe, un code a été envoyé.');
    if (data.devCode) {
      $('reset-dev-code').hidden = false;
      $('reset-dev-code').innerHTML = `Mode démo — votre code : <strong>${SC.escapeHtml(data.devCode)}</strong>`;
    }
  });

  forms.reset.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMsg();
    const { res, data } = await postJson('/api/auth/reset', {
      username: pendingUsername, code: $('rs-code').value.trim(), password: $('rs-password').value,
    });
    if (!res.ok) { showError((data.errors || ['Code incorrect.']).join(' ')); return; }
    SC.setSession(data.token, data.user);
    window.location.href = 'index.html';
  });
})();
