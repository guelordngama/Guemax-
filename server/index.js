/**
 * SafeCity Lubumbashi - Serveur applicatif.
 *
 * Expose une API REST pour les incidents + un canal Socket.io pour la
 * diffusion en temps reel a tous les clients connectes.
 */

import express from 'express';
import { createServer } from 'node:http';
import { Server as SocketServer } from 'socket.io';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { promises as fs } from 'node:fs';
import { randomUUID } from 'node:crypto';

import { IncidentStore } from './store.js';
import {
  LUBUMBASHI_CENTER,
  CATEGORIES,
  SEVERITIES,
  STATUSES,
  CATEGORY_IDS,
  SEVERITY_IDS,
} from './config.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const PUBLIC_DIR = path.join(ROOT, 'public');
const UPLOADS_DIR = path.join(PUBLIC_DIR, 'uploads');
const DATA_FILE = path.join(ROOT, 'data', 'incidents.json');
const PORT = process.env.PORT || 3000;

const app = express();
const httpServer = createServer(app);
const io = new SocketServer(httpServer, { cors: { origin: '*' } });
const store = new IncidentStore(DATA_FILE);

app.use(express.json({ limit: '6mb' })); // marge pour les photos en base64
app.use(express.static(PUBLIC_DIR));

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

function validateIncident(body) {
  const errors = [];
  const { category, severity, description, lat, lng } = body;

  if (!CATEGORY_IDS.has(category)) errors.push('Categorie invalide.');
  if (!SEVERITY_IDS.has(severity)) errors.push('Niveau de gravite invalide.');

  const desc = typeof description === 'string' ? description.trim() : '';
  if (desc.length < 5) errors.push('La description doit contenir au moins 5 caracteres.');
  if (desc.length > 1000) errors.push('La description est trop longue (max 1000 caracteres).');

  const latNum = Number(lat);
  const lngNum = Number(lng);
  if (!Number.isFinite(latNum) || latNum < -90 || latNum > 90) errors.push('Latitude invalide.');
  if (!Number.isFinite(lngNum) || lngNum < -180 || lngNum > 180) errors.push('Longitude invalide.');

  return { errors, value: { category, severity, description: desc, lat: latNum, lng: lngNum } };
}

/**
 * Enregistre une photo transmise en Data URL (base64) dans public/uploads.
 * Retourne le chemin public relatif, ou null si aucune/invalide.
 */
async function savePhoto(dataUrl) {
  if (typeof dataUrl !== 'string') return null;
  const match = dataUrl.match(/^data:image\/(png|jpe?g|webp);base64,([A-Za-z0-9+/=]+)$/);
  if (!match) return null;
  const ext = match[1] === 'jpeg' ? 'jpg' : match[1];
  const buffer = Buffer.from(match[2], 'base64');
  if (buffer.length > 4 * 1024 * 1024) return null; // 4 Mo max
  await fs.mkdir(UPLOADS_DIR, { recursive: true });
  const name = `${Date.now()}-${randomUUID()}.${ext}`;
  await fs.writeFile(path.join(UPLOADS_DIR, name), buffer);
  return `/uploads/${name}`;
}

// ---------------------------------------------------------------------------
// Routes API
// ---------------------------------------------------------------------------

app.get('/api/config', (_req, res) => {
  res.json({ center: LUBUMBASHI_CENTER, categories: CATEGORIES, severities: SEVERITIES });
});

app.get('/api/incidents', (_req, res) => {
  res.json(store.all());
});

app.get('/api/stats', (_req, res) => {
  res.json(store.stats());
});

app.post('/api/incidents', async (req, res) => {
  const { errors, value } = validateIncident(req.body);
  if (errors.length) return res.status(400).json({ errors });

  try {
    const photo = await savePhoto(req.body.photo);
    const incident = await store.create({
      ...value,
      address: typeof req.body.address === 'string' ? req.body.address.slice(0, 200) : null,
      photo,
    });
    io.emit('incident:new', incident); // diffusion temps reel
    res.status(201).json(incident);
  } catch (err) {
    console.error('[api] Creation incident echouee :', err);
    res.status(500).json({ errors: ['Erreur interne du serveur.'] });
  }
});

app.post('/api/incidents/:id/confirm', async (req, res) => {
  const incident = await store.confirm(req.params.id);
  if (!incident) return res.status(404).json({ errors: ['Incident introuvable.'] });
  io.emit('incident:update', incident);
  res.json(incident);
});

app.patch('/api/incidents/:id/status', async (req, res) => {
  const { status } = req.body;
  if (!STATUSES.includes(status)) return res.status(400).json({ errors: ['Statut invalide.'] });
  const incident = await store.updateStatus(req.params.id, status);
  if (!incident) return res.status(404).json({ errors: ['Incident introuvable.'] });
  io.emit('incident:update', incident);
  res.json(incident);
});

// ---------------------------------------------------------------------------
// Temps reel (Socket.io)
// ---------------------------------------------------------------------------

io.on('connection', (socket) => {
  broadcastPresence();
  socket.on('disconnect', () => broadcastPresence());
});

function broadcastPresence() {
  io.emit('presence', { online: io.engine.clientsCount });
}

// ---------------------------------------------------------------------------
// Demarrage
// ---------------------------------------------------------------------------

await store.load();
httpServer.listen(PORT, () => {
  console.log(`\n🚨  SafeCity Lubumbashi`);
  console.log(`    Serveur pret sur http://localhost:${PORT}`);
  console.log(`    ${store.stats().total} incident(s) charge(s).\n`);
});
