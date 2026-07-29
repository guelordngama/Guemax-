/**
 * Tests de fumee - verifient que le serveur demarre et que l'API repond
 * correctement (cas valides, validation, confirmation, statut, stats).
 *
 * Le serveur est lance dans un processus enfant sur un port dedie, avec un
 * fichier de donnees temporaire isole (DATA_FILE) nettoye a la fin.
 */

import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { promises as fs } from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const PORT = process.env.TEST_PORT || 3311;
const BASE = `http://localhost:${PORT}`;
const DATA_FILE = path.join(os.tmpdir(), `safecity-test-${Date.now()}.json`);

let server;

const validIncident = {
  category: 'vol',
  severity: 'eleve',
  description: 'Incident de test de fumee',
  lat: -11.66,
  lng: 27.48,
};

function post(body) {
  return fetch(`${BASE}/api/incidents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

before(async () => {
  server = spawn(process.execPath, ['server/index.js'], {
    cwd: ROOT,
    env: { ...process.env, PORT: String(PORT), DATA_FILE },
    stdio: 'ignore',
  });

  const deadline = Date.now() + 15000;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`${BASE}/api/config`);
      if (res.ok) return;
    } catch {
      /* le serveur n'est pas encore pret */
    }
    await new Promise((r) => setTimeout(r, 300));
  }
  throw new Error("Le serveur n'a pas demarre dans le delai imparti.");
});

after(async () => {
  if (server) server.kill();
  await fs.rm(DATA_FILE, { force: true });
});

test('GET /api/config renvoie le centre et les categories', async () => {
  const res = await fetch(`${BASE}/api/config`);
  assert.equal(res.status, 200);
  const body = await res.json();
  assert.equal(typeof body.center.lat, 'number');
  assert.equal(typeof body.center.lng, 'number');
  assert.ok(Array.isArray(body.categories) && body.categories.length > 0);
  assert.ok(Array.isArray(body.severities) && body.severities.length > 0);
});

test('POST /api/incidents (valide) cree un incident actif', async () => {
  const res = await post(validIncident);
  assert.equal(res.status, 201);
  const inc = await res.json();
  assert.equal(inc.category, 'vol');
  assert.equal(inc.status, 'actif');
  assert.equal(inc.confirmations, 0);
  assert.ok(inc.id);
});

test('POST /api/incidents (invalide) renvoie 400 avec des erreurs', async () => {
  const res = await post({ category: 'inconnu', severity: 'eleve', description: 'x', lat: 999, lng: 27.48 });
  assert.equal(res.status, 400);
  const body = await res.json();
  assert.ok(Array.isArray(body.errors));
  assert.ok(body.errors.length >= 1);
});

test('confirmation puis passage au statut resolu', async () => {
  const created = await post(validIncident).then((r) => r.json());

  const confirmed = await fetch(`${BASE}/api/incidents/${created.id}/confirm`, { method: 'POST' })
    .then((r) => r.json());
  assert.equal(confirmed.confirmations, 1);

  const resolved = await fetch(`${BASE}/api/incidents/${created.id}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'resolu' }),
  }).then((r) => r.json());
  assert.equal(resolved.status, 'resolu');
});

test('confirmation sur un id inexistant renvoie 404', async () => {
  const res = await fetch(`${BASE}/api/incidents/inexistant/confirm`, { method: 'POST' });
  assert.equal(res.status, 404);
});

test('GET /api/stats renvoie des compteurs coherents', async () => {
  const res = await fetch(`${BASE}/api/stats`);
  assert.equal(res.status, 200);
  const stats = await res.json();
  assert.equal(typeof stats.total, 'number');
  assert.ok(stats.total >= 1);
  assert.ok(stats.byStatus && typeof stats.byStatus.actif === 'number');
});

test('le client Socket.io est servi', async () => {
  const res = await fetch(`${BASE}/socket.io/socket.io.js`);
  assert.equal(res.status, 200);
});
