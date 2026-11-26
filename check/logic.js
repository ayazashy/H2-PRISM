/**
 * Pure domain, bilingual search normalization (AR/EN), filtering, ignore,
 * precomputed scoring, and O(1) spatial geometry logic.
 */

export const CUSTOM_TAGS = [
  { id: 'prio', icon: 'flame', en: 'Priority', ar: 'أولوية' },
  { id: 'talked', icon: 'users', en: 'Networked', ar: 'تواصلت' },
  { id: 'collab', icon: 'lightbulb', en: 'Collab', ar: 'تعاون' },
  { id: 'startup', icon: 'rocket', en: 'Startup', ar: 'ناشئ' },
  { id: 'demo', icon: 'mic', en: 'Demo', ar: 'عرض' },
  { id: 'revisit', icon: 'bookmark', en: 'Revisit', ar: 'عودة' },
];

export const DEFAULT_PREFS = {
  myBooth: 'S-H5-23',
  prefCats: [3, 4],
  prefPaths: [3, 1, 0, 6, 8, 13],
  prefTags: ['ai', 'startup', 'twin', 'cyber'],
  prefKeywords: ['hydrogen', 'physics', 'llm', 'agent', 'quantum', 'radar', 'drone', 'patent'],
  ignoreCats: [],
  ignorePaths: [],
  ignoreTags: [],
  ignoreKeywords: [],
  boostIntl: 12,
};

export function createDefaultFilters() {
  return {
    q: '',
    status: 'all',
    cats: { inc: [], exc: [] },
    paths: { inc: [], exc: [] },
    zones: { inc: [], exc: [] },
    rows: { inc: [], exc: [] },
    tags: { inc: [], exc: [] },
    customTags: { inc: [], exc: [] },
    countries: { inc: [], exc: [] },
    sizes: { inc: [], exc: [] },
    intlMode: 'all',
    langMode: 'all',
    ratingMode: 'all',
    minMatch: 0,
    ignoreKeywords: [],
    sortBy: 'booth',
  };
}

const AR_CHECK_RE = /[\u0600-\u06FF]/;

export function normSearch(str) {
  const s = String(str || '').toLowerCase();
  if (!AR_CHECK_RE.test(s)) {
    return s.replace(/\s+/g, ' ').trim();
  }
  return s
    .replace(/[\u064B-\u065F\u0670\u0640]/g, '')
    .replace(/[أإآٱ]/g, 'ا')
    .replace(/ة/g, 'ه')
    .replace(/ى/g, 'ي')
    .replace(/ؤ/g, 'و')
    .replace(/ئ/g, 'ي')
    .replace(/عبد\s+ال/g, 'عبدال')
    .replace(/\s+/g, ' ')
    .trim();
}

export const HALL_WIDTH = 1760;
export const HALL_HEIGHT = 694;

export const ZONE_GEOMETRY = {
  A: { x: 22, y: 20, cols: 24, rows: 5, wing: 'youth', labelEn: '6-11y', labelAr: '٦-١١' },
  B: { x: 446, y: 20, cols: 24, rows: 5, wing: 'youth', labelEn: '12-17y', labelAr: '١٢-١٧' },
  C: { x: 22, y: 244, cols: 24, rows: 5, wing: 'youth', labelEn: '12-17y', labelAr: '١٢-١٧' },
  D: { x: 446, y: 244, cols: 24, rows: 5, wing: 'youth', labelEn: '12-17y', labelAr: '١٢-١٧' },
  E: { x: 22, y: 468, cols: 24, rows: 5, wing: 'youth', labelEn: '12-17y', labelAr: '١٢-١٧' },
  F: { x: 446, y: 468, cols: 18, rows: 5, wing: 'bridge', labelEn: 'Mixed', labelAr: 'مشترك' },
  G: { x: 910, y: 20, cols: 24, rows: 5, wing: 'pro', labelEn: '18+ Uni', labelAr: 'جامعي' },
  H: { x: 910, y: 244, cols: 24, rows: 5, wing: 'pro', labelEn: '18+ Uni', labelAr: 'جامعي' },
  I: { x: 910, y: 468, cols: 24, rows: 5, wing: 'pro', labelEn: 'Uni/Pro', labelAr: 'جامعي/رواد' },
  J: { x: 1334, y: 20, cols: 24, rows: 7, wing: 'pro', labelEn: '18+ Pro', labelAr: 'رواد/مطورون' },
  K: { x: 1334, y: 318, cols: 13, rows: 4, wing: 'pro', labelEn: '18+ Pro', labelAr: 'رواد/مطورون' },
};

const CELL_W = 14;
const CELL_H = 22;
const GAP_X = 1.8;
const PAD_L = 22;
const PAD_R = 10;
const HEADER_H = 28;
const PAD_B = 10;

function rowOffsetY(row) {
  let y = HEADER_H;
  for (let r = 1; r < row; r++) {
    y += CELL_H + (r % 2 === 0 ? 12 : 4);
  }
  return y;
}

export function getZoneBox(zoneId) {
  const g = ZONE_GEOMETRY[zoneId];
  if (!g) return { x: 0, y: 0, w: 0, h: 0 };
  const w = PAD_L + g.cols * CELL_W + (g.cols - 1) * GAP_X + PAD_R;
  const h = rowOffsetY(g.rows) + CELL_H + PAD_B;
  return { x: g.x, y: g.y, w, h };
}

export function getBoothRect(zoneId, row, seat) {
  const g = ZONE_GEOMETRY[zoneId];
  if (!g) return { x: 0, y: 0, w: CELL_W, h: CELL_H, cx: 0, cy: 0 };
  const x = g.x + PAD_L + (seat - 1) * (CELL_W + GAP_X);
  const y = g.y + rowOffsetY(row);
  return { x, y, w: CELL_W, h: CELL_H, cx: x + CELL_W / 2, cy: y + CELL_H / 2 };
}

export function parseTableCode(tableStr) {
  const m = /^S-([A-Z])(\d+)-(\d+)$/i.exec((tableStr || '').trim());
  if (!m) return null;
  return { z: m[1].toUpperCase(), r: Number(m[2]), s: Number(m[3]) };
}

export function hitTestHall(wx, wy, boothGroups) {
  for (const [zId, g] of Object.entries(ZONE_GEOMETRY)) {
    const box = getZoneBox(zId);
    if (wx < box.x || wx > box.x + box.w || wy < box.y || wy > box.y + box.h) continue;

    if (wy <= box.y + HEADER_H) {
      return { type: 'zone', zone: zId };
    }

    const colStep = CELL_W + GAP_X;
    const seatIdx = Math.floor((wx - (g.x + PAD_L)) / colStep) + 1;
    if (seatIdx >= 1 && seatIdx <= g.cols) {
      for (let r = 1; r <= g.rows; r++) {
        const top = g.y + rowOffsetY(r);
        if (wy >= top - 2 && wy <= top + CELL_H + 2) {
          const tableStr = `S-${zId}${r}-${String(seatIdx).padStart(2, '0')}`;
          if (boothGroups.has(tableStr)) {
            return { type: 'booth', zone: zId, table: tableStr };
          }
        }
      }
    }
    return { type: 'zone', zone: zId };
  }
  return null;
}

export function prepareProjects(rawProjects, meta) {
  const pathMap = new Map(meta.paths.map((p) => [p.id, p]));
  const catMap = new Map(meta.cats.map((c) => [c.id, c]));

  return rawProjects.map((p, idx) => {
    const nats = new Set();
    if (p.nat) nats.add(p.nat);
    for (const m of p.members) {
      if (m.nat) nats.add(m.nat);
    }
    const allNats = Array.from(nats);
    const hasIntl = allNats.some((n) => n !== 'Saudi Arabia');
    const intlLeader = p.nat !== 'Saudi Arabia';
    const mixedNat = allNats.length > 1;
    const leader = p.members.find((m) => m.l === 1) || p.members[0] || { n: '', ar: '' };

    const pathObj = pathMap.get(p.path);
    const catObj = catMap.get(p.cat);
    const countryTokens = allNats
      .map((n) => {
        const c = meta.countries[n];
        return c ? `${n} ${c[1]} ${c[2]}` : n;
      })
      .join(' ');

    const rect = getBoothRect(p.z, p.r, p.s);

    const searchText = normSearch(
      [
        p.code,
        p.table,
        p.z,
        `${p.z}${p.r}`,
        p.title,
        p.desc,
        pathObj ? `${pathObj.en} ${pathObj.ar}` : '',
        catObj ? `${catObj.en} ${catObj.ar}` : '',
        p.tags.join(' '),
        countryTokens,
        p.members.map((m) => `${m.n} ${m.ar || ''}`).join(' '),
      ].join(' ')
    );

    return {
      ...p,
      _idx: idx,
      leader: leader.n,
      leaderAr: leader.ar || leader.n,
      allNats,
      hasIntl,
      intlLeader,
      mixedNat,
      cx: rect.cx,
      cy: rect.cy,
      x: rect.x,
      y: rect.y,
      searchText,
      _score: 0,
      _dist: 0,
    };
  });
}

export function computeMatchScore(project, prefs) {
  let score = 0;
  if (prefs.prefCats?.includes(project.cat)) score += 28;
  if (prefs.prefPaths?.includes(project.path)) score += 26;

  if (prefs.prefTags?.length && project.tags?.length) {
    let tagHits = 0;
    for (const t of project.tags) {
      if (prefs.prefTags.includes(t)) tagHits += 1;
    }
    score += Math.min(24, tagHits * 10);
  }

  if (prefs.prefKeywords?.length) {
    let kwHits = 0;
    for (const kw of prefs.prefKeywords) {
      const k = normSearch(kw);
      if (k && project.searchText.includes(k)) kwHits += 1;
    }
    score += Math.min(30, kwHits * 12);
  }

  if (project.hasIntl) score += Number(prefs.boostIntl ?? 12);
  if (project.members.length >= 2) score += 4;

  const myPos = parseTableCode(prefs.myBooth);
  if (myPos && project.z === myPos.z) {
    score += 5;
    if (project.r === myPos.r) score += 4;
  }

  return Math.max(0, Math.min(100, Math.round(score)));
}

/**
 * Cache match scores & distances onto project objects ONLY when prefs change.
 * Eliminates ~11,000 substring scans per tap/filter interaction.
 */
export function refreshPrefsCache(projects, prefs) {
  const myParsed = parseTableCode(prefs.myBooth);
  const myCoords = myParsed ? getBoothRect(myParsed.z, myParsed.r, myParsed.s) : null;
  const prefCatSet = new Set(prefs.prefCats || []);
  const prefPathSet = new Set(prefs.prefPaths || []);
  const prefTagSet = new Set(prefs.prefTags || []);
  const normKws = (prefs.prefKeywords || []).map(normSearch).filter(Boolean);
  const boostIntl = Number(prefs.boostIntl ?? 12);

  for (const p of projects) {
    let score = 0;
    if (prefCatSet.has(p.cat)) score += 28;
    if (prefPathSet.has(p.path)) score += 26;
    if (prefTagSet.size && p.tags.length) {
      let tagHits = 0;
      for (const t of p.tags) if (prefTagSet.has(t)) tagHits += 1;
      score += Math.min(24, tagHits * 10);
    }
    if (normKws.length) {
      let kwHits = 0;
      for (const k of normKws) if (p.searchText.includes(k)) kwHits += 1;
      score += Math.min(30, kwHits * 12);
    }
    if (p.hasIntl) score += boostIntl;
    if (p.members.length >= 2) score += 4;
    if (myParsed && p.z === myParsed.z) {
      score += 5;
      if (p.r === myParsed.r) score += 4;
    }
    p._score = Math.max(0, Math.min(100, Math.round(score)));
    p._dist = myCoords ? Math.hypot(p.cx - myCoords.cx, p.cy - myCoords.cy) : 0;
  }
  return myCoords;
}

export function parseSearchTokens(q) {
  const normalized = normSearch(q);
  const parts = normalized ? normalized.split(' ').filter(Boolean) : [];
  const pos = [];
  const neg = [];
  for (const tok of parts) {
    if (tok.startsWith('-') && tok.length > 1) {
      neg.push(tok.slice(1));
    } else {
      pos.push(tok);
    }
  }
  return { pos, neg };
}

function matchesFacet(value, facet, ignoreExc = false) {
  if (!ignoreExc && facet.exc.length && facet.exc.includes(value)) return false;
  if (facet.inc.length && !facet.inc.includes(value)) return false;
  return true;
}

function matchesMultiFacet(values, facet, ignoreExc = false) {
  if (!ignoreExc && facet.exc.length && values.some((v) => facet.exc.includes(v))) return false;
  if (facet.inc.length && !values.some((v) => facet.inc.includes(v))) return false;
  return true;
}

/**
 * Compile filter & pref lookup Sets once before looping over projects.
 */
export function buildEvalContext(filters, prefs) {
  const searchTokens = parseSearchTokens(filters.q);
  const allNegWords = [
    ...(prefs.ignoreKeywords || []),
    ...(filters.ignoreKeywords || []),
    ...searchTokens.neg,
  ]
    .map(normSearch)
    .filter(Boolean);

  return {
    filters,
    searchTokens,
    allNegWords,
    globIgnCats: new Set(prefs.ignoreCats || []),
    globIgnPaths: new Set(prefs.ignorePaths || []),
    globIgnTags: new Set(prefs.ignoreTags || []),
    excCats: new Set(filters.cats.exc),
    excPaths: new Set(filters.paths.exc),
    excZones: new Set(filters.zones.exc),
    excRows: new Set(filters.rows.exc),
    excTags: new Set(filters.tags.exc),
    excCustomTags: new Set(filters.customTags.exc),
    excCountries: new Set(filters.countries.exc),
    excSizes: new Set(filters.sizes.exc),
    viewingIgnored: filters.status === 'ignored',
  };
}

export function evaluateProjectFast(p, record, ctx) {
  const rec = record || {};
  const filters = ctx.filters;
  const matchScore = p._score;
  const dist = p._dist;

  let isIgnored =
    !!rec.ign ||
    ctx.globIgnCats.has(p.cat) ||
    ctx.excCats.has(p.cat) ||
    ctx.globIgnPaths.has(p.path) ||
    ctx.excPaths.has(p.path) ||
    ctx.excZones.has(p.z) ||
    ctx.excRows.has(p.r) ||
    ctx.excSizes.has(p.members.length);

  if (!isIgnored && p.tags.length && (ctx.globIgnTags.size || ctx.excTags.size)) {
    for (const t of p.tags) {
      if (ctx.globIgnTags.has(t) || ctx.excTags.has(t)) {
        isIgnored = true;
        break;
      }
    }
  }
  const userTags = rec.tags || [];
  if (!isIgnored && userTags.length && ctx.excCustomTags.size) {
    for (const t of userTags) {
      if (ctx.excCustomTags.has(t)) {
        isIgnored = true;
        break;
      }
    }
  }
  if (!isIgnored && ctx.excCountries.size) {
    for (const n of p.allNats) {
      if (ctx.excCountries.has(n)) {
        isIgnored = true;
        break;
      }
    }
  }
  if (!isIgnored && ctx.allNegWords.length) {
    for (const kw of ctx.allNegWords) {
      if (p.searchText.includes(kw)) {
        isIgnored = true;
        break;
      }
    }
  }

  let statusPass = true;
  if (ctx.viewingIgnored) {
    statusPass = isIgnored;
  } else {
    if (isIgnored) statusPass = false;
    else if (filters.status === 'prefs') statusPass = matchScore >= 40;
    else if (filters.status === 'fav') statusPass = !!rec.fav;
    else if (filters.status === 'todo') statusPass = !!rec.fav && !rec.vis;
    else if (filters.status === 'visited') statusPass = !!rec.vis;
    else if (filters.status === 'unvisited') statusPass = !rec.vis;
    else if (filters.status === 'rated') statusPass = (rec.rat || 0) > 0;
    else if (filters.status === 'noted') statusPass = !!(rec.note && rec.note.trim());
  }

  if (!statusPass) return { matches: false, isIgnored, matchScore, dist };

  for (const tok of ctx.searchTokens.pos) {
    if (!p.searchText.includes(tok)) {
      return { matches: false, isIgnored, matchScore, dist };
    }
  }

  const vi = ctx.viewingIgnored;
  if (!matchesFacet(p.cat, filters.cats, vi)) return { matches: false, isIgnored, matchScore, dist };
  if (!matchesFacet(p.path, filters.paths, vi)) return { matches: false, isIgnored, matchScore, dist };
  if (!matchesFacet(p.z, filters.zones, vi)) return { matches: false, isIgnored, matchScore, dist };
  if (!matchesFacet(p.r, filters.rows, vi)) return { matches: false, isIgnored, matchScore, dist };
  if (!matchesMultiFacet(p.tags, filters.tags, vi)) return { matches: false, isIgnored, matchScore, dist };
  if (!matchesMultiFacet(userTags, filters.customTags, vi)) return { matches: false, isIgnored, matchScore, dist };
  if (!matchesMultiFacet(p.allNats, filters.countries, vi)) return { matches: false, isIgnored, matchScore, dist };
  if (!matchesFacet(p.members.length, filters.sizes, vi)) return { matches: false, isIgnored, matchScore, dist };

  if (filters.intlMode === 'intl_leader' && !p.intlLeader) return { matches: false, isIgnored, matchScore, dist };
  if (filters.intlMode === 'has_intl' && !p.hasIntl) return { matches: false, isIgnored, matchScore, dist };
  if (filters.intlMode === 'mixed' && !p.mixedNat) return { matches: false, isIgnored, matchScore, dist };
  if (filters.intlMode === 'saudi_only' && p.hasIntl) return { matches: false, isIgnored, matchScore, dist };

  if (filters.langMode !== 'all' && p.lang !== filters.langMode) {
    return { matches: false, isIgnored, matchScore, dist };
  }

  const rat = rec.rat || 0;
  if (filters.ratingMode === 'rated' && rat === 0) return { matches: false, isIgnored, matchScore, dist };
  if (filters.ratingMode === 'unrated' && rat > 0) return { matches: false, isIgnored, matchScore, dist };
  if (filters.ratingMode === '3+' && rat < 3) return { matches: false, isIgnored, matchScore, dist };
  if (filters.ratingMode === '4+' && rat < 4) return { matches: false, isIgnored, matchScore, dist };
  if (filters.ratingMode === '5' && rat < 5) return { matches: false, isIgnored, matchScore, dist };

  if (filters.minMatch > 0 && matchScore < filters.minMatch) {
    return { matches: false, isIgnored, matchScore, dist };
  }

  return { matches: true, isIgnored, matchScore, dist };
}

export function evaluateAll(projects, filters, records, prefs) {
  refreshPrefsCache(projects, prefs);
  const ctx = buildEvalContext(filters, prefs);

  const evalById = new Map();
  const matched = [];
  const counts = {
    total: projects.length,
    visible: 0,
    prefs: 0,
    fav: 0,
    todo: 0,
    visited: 0,
    rated: 0,
    noted: 0,
    ignored: 0,
  };

  for (const p of projects) {
    const rec = records[p.id];
    const ev = evaluateProjectFast(p, rec, ctx);
    evalById.set(p.id, ev);

    if (ev.isIgnored) {
      counts.ignored += 1;
    } else {
      counts.visible += 1;
      if (ev.matchScore >= 40) counts.prefs += 1;
      if (rec?.fav) counts.fav += 1;
      if (rec?.fav && !rec?.vis) counts.todo += 1;
      if (rec?.vis) counts.visited += 1;
      if ((rec?.rat || 0) > 0) counts.rated += 1;
      if (rec?.note && rec.note.trim()) counts.noted += 1;
    }

    if (ev.matches) matched.push(p);
  }

  sortMatched(matched, filters.sortBy, records);

  return { evalById, matched, counts };
}

export function sortMatched(matched, sortBy, records) {
  if (sortBy === 'booth') {
    matched.sort((a, b) => a._idx - b._idx);
    return;
  }
  matched.sort((a, b) => {
    switch (sortBy) {
      case 'match':
        return b._score - a._score || a._idx - b._idx;
      case 'nearest':
        return a._dist - b._dist || a._idx - b._idx;
      case 'rating': {
        const ra = records[a.id]?.rat || 0;
        const rb = records[b.id]?.rat || 0;
        return rb - ra || b._score - a._score || a._idx - b._idx;
      }
      case 'members':
        return b.members.length - a.members.length || b._score - a._score || a._idx - b._idx;
      case 'code':
        return a.code < b.code ? -1 : a.code > b.code ? 1 : 0;
      default:
        return a._idx - b._idx;
    }
  });
}

export function computeWalkingRoute(targets, startBooth, maxStops = 30) {
  if (!targets.length) return [];
  const parsed = parseTableCode(startBooth);
  let curr = parsed ? getBoothRect(parsed.z, parsed.r, parsed.s) : { cx: targets[0].cx, cy: targets[0].cy };

  const remaining = targets.slice();
  const route = [];

  while (remaining.length > 0 && route.length < maxStops) {
    let bestIdx = 0;
    let bestD = Infinity;
    for (let i = 0; i < remaining.length; i++) {
      const t = remaining[i];
      const d = Math.hypot(t.cx - curr.cx, t.cy - curr.cy);
      if (d < bestD) {
        bestD = d;
        bestIdx = i;
      }
    }
    const next = remaining.splice(bestIdx, 1)[0];
    route.push(next);
    curr = next;
  }
  return route;
}

export function countActiveFilterRules(filters, prefs) {
  let n = 0;
  const facets = ['cats', 'paths', 'zones', 'rows', 'tags', 'customTags', 'countries', 'sizes'];
  for (const k of facets) {
    n += (filters[k]?.inc?.length || 0) + (filters[k]?.exc?.length || 0);
  }
  if (filters.intlMode !== 'all') n += 1;
  if (filters.langMode !== 'all') n += 1;
  if (filters.ratingMode !== 'all') n += 1;
  if (filters.minMatch > 0) n += 1;
  n += filters.ignoreKeywords?.length || 0;
  n += (prefs.ignoreCats?.length || 0) + (prefs.ignorePaths?.length || 0) + (prefs.ignoreTags?.length || 0) + (prefs.ignoreKeywords?.length || 0);
  return n;
}
