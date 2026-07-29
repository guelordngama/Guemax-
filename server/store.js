/**
 * store.js - Persistance legere basee sur un fichier JSON.
 *
 * On evite volontairement toute dependance native (sqlite, etc.) afin que
 * l'application demarre partout sans etape de compilation. Les incidents sont
 * conserves en memoire et ecrits sur disque de maniere atomique (fichier
 * temporaire + rename) apres chaque modification.
 */

import { promises as fs } from 'node:fs';
import path from 'node:path';
import { randomUUID } from 'node:crypto';

export class IncidentStore {
  constructor(filePath) {
    this.filePath = filePath;
    /** @type {Map<string, object>} */
    this.incidents = new Map();
    this._writeChain = Promise.resolve();
  }

  /** Charge les incidents existants depuis le disque (si le fichier existe). */
  async load() {
    await fs.mkdir(path.dirname(this.filePath), { recursive: true });
    try {
      const raw = await fs.readFile(this.filePath, 'utf8');
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        for (const inc of parsed) this.incidents.set(inc.id, inc);
      }
    } catch (err) {
      if (err.code !== 'ENOENT') {
        console.error('[store] Lecture impossible, demarrage a vide :', err.message);
      }
    }
    return this;
  }

  /** Ecriture atomique serialisee pour eviter les corruptions concurrentes. */
  _persist() {
    const snapshot = JSON.stringify([...this.incidents.values()], null, 2);
    this._writeChain = this._writeChain.then(async () => {
      const tmp = `${this.filePath}.${randomUUID()}.tmp`;
      await fs.writeFile(tmp, snapshot, 'utf8');
      await fs.rename(tmp, this.filePath);
    }).catch((err) => console.error('[store] Ecriture echouee :', err.message));
    return this._writeChain;
  }

  /** Retourne les incidents tries du plus recent au plus ancien. */
  all() {
    return [...this.incidents.values()].sort(
      (a, b) => new Date(b.createdAt) - new Date(a.createdAt)
    );
  }

  get(id) {
    return this.incidents.get(id) || null;
  }

  /** Cree un nouvel incident valide et le persiste. */
  async create(data) {
    const now = new Date().toISOString();
    const incident = {
      id: randomUUID(),
      category: data.category,
      severity: data.severity,
      description: data.description,
      lat: data.lat,
      lng: data.lng,
      address: data.address || null,
      photo: data.photo || null,
      status: 'actif', // actif | verifie | resolu
      confirmations: 0,
      createdAt: now,
      updatedAt: now,
    };
    this.incidents.set(incident.id, incident);
    await this._persist();
    return incident;
  }

  /** Incremente le compteur de confirmations ("Je confirme"). */
  async confirm(id) {
    const inc = this.incidents.get(id);
    if (!inc) return null;
    inc.confirmations += 1;
    inc.updatedAt = new Date().toISOString();
    await this._persist();
    return inc;
  }

  /** Change le statut d'un incident (verifie / resolu). */
  async updateStatus(id, status) {
    const inc = this.incidents.get(id);
    if (!inc) return null;
    inc.status = status;
    inc.updatedAt = new Date().toISOString();
    await this._persist();
    return inc;
  }

  /** Statistiques agregees pour le tableau de bord. */
  stats() {
    const byCategory = {};
    const byStatus = { actif: 0, verifie: 0, resolu: 0 };
    for (const inc of this.incidents.values()) {
      byCategory[inc.category] = (byCategory[inc.category] || 0) + 1;
      if (byStatus[inc.status] !== undefined) byStatus[inc.status] += 1;
    }
    return { total: this.incidents.size, byCategory, byStatus };
  }
}
