import { DEFAULT_PREFS, createDefaultFilters } from './logic.js';

export const STORAGE_KEY = 'saif_fair_tracker_v1';

const memoryFallback = new Map();

function readRawStorage() {
  try {
    if (typeof localStorage !== 'undefined') {
      return localStorage.getItem(STORAGE_KEY);
    }
  } catch (_) {}
  return memoryFallback.get(STORAGE_KEY) || null;
}

function writeRawStorage(value) {
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, value);
      return;
    }
  } catch (_) {}
  memoryFallback.set(STORAGE_KEY, value);
}

export function createDefaultState() {
  return {
    v: 1,
    records: {}, // { [projectId]: { fav?, vis?, visAt?, rat?, sub?, ign?, tags?, note?, met? } }
    prefs: structuredClone(DEFAULT_PREFS),
    filters: createDefaultFilters(),
    ui: {
      lang: 'ar',
      theme: 'dark',
      view: 'split', // split | list | map
      mapColor: 'status', // status | rating | match | cat | path
      hideFilteredOnMap: false,
      hideIgnoredOnMap: false,
      showRoute: false,
      filterMode: 'inc', // inc | exc (1-tap switch between Include and Ignore)
    },
  };
}

function mergeDeepState(parsed) {
  const base = createDefaultState();
  if (!parsed || typeof parsed !== 'object') return base;
  return {
    v: 1,
    records: parsed.records && typeof parsed.records === 'object' ? parsed.records : {},
    prefs: { ...base.prefs, ...(parsed.prefs || {}) },
    filters: { ...base.filters, ...(parsed.filters || {}) },
    ui: { ...base.ui, ...(parsed.ui || {}) },
  };
}

export class TrackerStore {
  constructor() {
    this.state = this.load();
    this.listeners = new Set();
  }

  load() {
    const raw = readRawStorage();
    if (!raw) return createDefaultState();
    try {
      return mergeDeepState(JSON.parse(raw));
    } catch (_) {
      return createDefaultState();
    }
  }

  save(reason = 'all') {
    writeRawStorage(JSON.stringify(this.state));
    for (const cb of this.listeners) cb(this.state, reason);
  }

  subscribe(cb) {
    this.listeners.add(cb);
    return () => this.listeners.delete(cb);
  }

  getRecord(id) {
    return this.state.records[id] || {};
  }

  _mutateRecord(id, mutator, reason = 'all') {
    const curr = { ...(this.state.records[id] || {}) };
    mutator(curr);
    // Prune empty keys & delete record if completely empty to keep localStorage crisp
    if (!curr.fav) delete curr.fav;
    if (!curr.vis) {
      delete curr.vis;
      delete curr.visAt;
    }
    if (!curr.rat) delete curr.rat;
    if (!curr.ign) delete curr.ign;
    if (!curr.tags?.length) delete curr.tags;
    if (!curr.met?.length) delete curr.met;
    if (!curr.note || !curr.note.trim()) delete curr.note;
    if (curr.sub && !Object.values(curr.sub).some(Boolean)) delete curr.sub;

    if (Object.keys(curr).length === 0) {
      delete this.state.records[id];
    } else {
      this.state.records[id] = curr;
    }
    this.save(reason);
  }

  toggleFav(id) {
    this._mutateRecord(id, (r) => {
      r.fav = r.fav ? 0 : 1;
      if (r.fav && r.ign) r.ign = 0;
    });
  }

  toggleVisited(id) {
    this._mutateRecord(id, (r) => {
      if (r.vis) {
        r.vis = 0;
        delete r.visAt;
      } else {
        r.vis = 1;
        r.visAt = Date.now();
        if (r.ign) r.ign = 0;
      }
    });
  }

  setRating(id, stars) {
    this._mutateRecord(id, (r) => {
      r.rat = r.rat === stars ? 0 : stars;
      if (r.rat > 0 && r.ign) r.ign = 0;
    });
  }

  setSubRating(id, axis, stars) {
    this._mutateRecord(id, (r) => {
      const sub = { ...(r.sub || {}) };
      sub[axis] = sub[axis] === stars ? 0 : stars;
      r.sub = sub;
    });
  }

  toggleIgnore(id) {
    this._mutateRecord(id, (r) => {
      r.ign = r.ign ? 0 : 1;
    });
  }

  toggleCustomTag(id, tagId) {
    this._mutateRecord(id, (r) => {
      const set = new Set(r.tags || []);
      if (set.has(tagId)) set.delete(tagId);
      else set.add(tagId);
      r.tags = Array.from(set);
    });
  }

  toggleMet(id, memberName) {
    this._mutateRecord(id, (r) => {
      const set = new Set(r.met || []);
      if (set.has(memberName)) set.delete(memberName);
      else set.add(memberName);
      r.met = Array.from(set);
    });
  }

  setNote(id, note) {
    this._mutateRecord(
      id,
      (r) => {
        r.note = note;
      },
      'note'
    );
  }

  bulkAction(ids, action) {
    for (const id of ids) {
      const curr = { ...(this.state.records[id] || {}) };
      if (action === 'fav') {
        curr.fav = 1;
        delete curr.ign;
      } else if (action === 'unfav') {
        delete curr.fav;
      } else if (action === 'visit') {
        curr.vis = 1;
        curr.visAt = curr.visAt || Date.now();
        delete curr.ign;
      } else if (action === 'ignore') {
        curr.ign = 1;
      } else if (action === 'unignore') {
        delete curr.ign;
      }
      if (Object.keys(curr).length === 0) delete this.state.records[id];
      else this.state.records[id] = curr;
    }
    this.save();
  }

  toggleFacetValue(facetKey, value, forceMode = null) {
    const mode = forceMode || this.state.ui.filterMode || 'inc';
    const facet = this.state.filters[facetKey];
    if (!facet) return;
    const inc = new Set(facet.inc || []);
    const exc = new Set(facet.exc || []);

    if (mode === 'inc') {
      if (inc.has(value)) inc.delete(value);
      else {
        inc.add(value);
        exc.delete(value);
      }
    } else {
      if (exc.has(value)) exc.delete(value);
      else {
        exc.add(value);
        inc.delete(value);
      }
    }

    this.state.filters[facetKey] = {
      inc: Array.from(inc),
      exc: Array.from(exc),
    };
    this.save();
  }

  clearFacetValue(facetKey, mode, value) {
    const facet = this.state.filters[facetKey];
    if (!facet) return;
    facet[mode] = (facet[mode] || []).filter((v) => v !== value);
    this.save();
  }

  addIgnoreKeyword(word) {
    const w = word.trim().toLowerCase();
    if (!w) return;
    const set = new Set(this.state.filters.ignoreKeywords || []);
    set.add(w);
    this.state.filters.ignoreKeywords = Array.from(set);
    this.save();
  }

  removeIgnoreKeyword(word) {
    this.state.filters.ignoreKeywords = (this.state.filters.ignoreKeywords || []).filter((w) => w !== word);
    this.save();
  }

  resetFilters() {
    this.state.filters = createDefaultFilters();
    this.save();
  }

  updateFilters(patch) {
    this.state.filters = { ...this.state.filters, ...patch };
    this.save();
  }

  updatePrefs(patch) {
    this.state.prefs = { ...this.state.prefs, ...patch };
    this.save();
  }

  updateUI(patch) {
    this.state.ui = { ...this.state.ui, ...patch };
    this.save();
  }

  exportJSON() {
    return JSON.stringify(
      {
        exportedAt: new Date().toISOString(),
        ...this.state,
      },
      null,
      2
    );
  }

  importJSON(jsonStr, merge = true) {
    const parsed = JSON.parse(jsonStr);
    if (!parsed || typeof parsed !== 'object') throw new Error('Invalid JSON');
    if (!merge) {
      this.state = mergeDeepState(parsed);
      this.save();
      return;
    }
    const mergedRecords = { ...this.state.records };
    for (const [id, rec] of Object.entries(parsed.records || {})) {
      const prev = mergedRecords[id] || {};
      mergedRecords[id] = {
        ...prev,
        ...rec,
        tags: Array.from(new Set([...(prev.tags || []), ...(rec.tags || [])])),
        met: Array.from(new Set([...(prev.met || []), ...(rec.met || [])])),
        note: [prev.note, rec.note].filter(Boolean).join(' | ') || undefined,
      };
    }
    this.state = {
      ...this.state,
      records: mergedRecords,
      prefs: parsed.prefs ? { ...this.state.prefs, ...parsed.prefs } : this.state.prefs,
    };
    this.save();
  }

  exportContactsCSV(projects, meta) {
    const pathMap = new Map(meta.paths.map((p) => [p.id, p.en]));
    const header = [
      'Table',
      'Code',
      'Title',
      'Category',
      'Path',
      'Country',
      'Fav',
      'Visited',
      'Rating',
      'Tags',
      'MetWith',
      'Members',
      'Note',
    ];
    const rows = [header];
    for (const p of projects) {
      const r = this.state.records[p.id];
      if (!r || (!r.fav && !r.vis && !r.rat && !r.note && !(r.tags && r.tags.length))) continue;
      rows.push([
        p.table,
        p.code,
        p.title,
        `Cat ${p.cat}`,
        pathMap.get(p.path) || '',
        p.nat,
        r.fav ? '1' : '0',
        r.vis ? '1' : '0',
        r.rat ? String(r.rat) : '',
        (r.tags || []).join(';'),
        (r.met || []).join(';'),
        p.members.map((m) => `${m.n}${m.nat ? ' (' + m.nat + ')' : ''}`).join('; '),
        r.note || '',
      ]);
    }
    const esc = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
    return '\uFEFF' + rows.map((row) => row.map(esc).join(',')).join('\r\n');
  }
}
