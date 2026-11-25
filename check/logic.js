/**
 * Pure domain, filtering, ignore, preference scoring, and spatial geometry logic.
 * Shared identically by the checklist view, mirrored map, and automated tests.
 */

export const CUSTOM_TAGS = [
  { id: 'prio', icon: '🔥', en: 'Priority', ar: 'أولوية' },
  { id: 'talked', icon: '🤝', en: 'Networked', ar: 'تواصلت' },
  { id: 'collab', icon: '💡', en: 'Collab', ar: 'تعاون' },
  { id: 'startup', icon: '🚀', en: 'Startup', ar: 'ناشئ' },
  { id: 'demo', icon: '🎤', en: 'Demo', ar: 'عرض' },
  { id: 'revisit', icon: '📌', en: 'Revisit', ar: 'عودة' },
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
    status: 'all', // all | prefs | fav | todo | visited | unvisited | rated | noted | ignored
    cats: { inc: [], exc: [] },
    paths: { inc: [], exc: [] },
    zones: { inc: [], exc: [] },
    rows: { inc: [], exc: [] },
    tags: { inc: [], exc: [] },
    customTags: { inc: [], exc: [] },
    countries: { inc: [], exc: [] },
    sizes: { inc: [], exc: [] },
    intlMode: 'all', // all | intl_leader | has_intl | mixed | saudi_only
    langMode: 'all', // all | en | ar | bi
    ratingMode: 'all', // all | rated | unrated | 3+ | 4+ | 5
    minMatch: 0,
    ignoreKeywords: [],
    sortBy: 'booth', // booth | match | nearest | rating | members | code
  };
}

/**
 * Architectural SVG layout (viewBox 1760 x 694) for Zones A..K.
 * Left wing: Juniors & Youth (A-E), Center bridge: F, Right wing: 18+ Uni & Pro (G-K).
 */
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
  // Paired expo aisles: R1-R2 close, aisle before R3, R3-R4 close, aisle before R5, etc.
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

/**
 * Enrich loaded raw project records once with fast search indexes and spatial coordinates.
 */
export function prepareProjects(rawProjects, meta) {
  const pathMap = new Map(meta.paths.map((p) => [p.id, p]));
  const catMap = new Map(meta.cats.map((c) => [c.id, c]));

  return rawProjects.map((p) => {
    const nats = new Set();
    if (p.nat) nats.add(p.nat);
    for (const m of p.members) {
      if (m.nat) nats.add(m.nat);
    }
    const allNats = Array.from(nats);
    const hasIntl = allNats.some((n) => n !== 'Saudi Arabia');
    const intlLeader = p.nat !== 'Saudi Arabia';
    const mixedNat = allNats.length > 1;
    const leader = p.members.find((m) => m.l === 1) || p.members[0] || { n: '' };

    const pathObj = pathMap.get(p.path);
    const catObj = catMap.get(p.cat);
    const countryTokens = allNats
      .map((n) => {
        const c = meta.countries[n];
        return c ? `${n} ${c[1]} ${c[2]}` : n;
      })
      .join(' ');

    const rect = getBoothRect(p.z, p.r, p.s);

    const searchText = [
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
      p.members.map((m) => m.n).join(' '),
    ]
      .join(' ')
      .toLowerCase();

    return {
      ...p,
      leader: leader.n,
      allNats,
      hasIntl,
      intlLeader,
      mixedNat,
      cx: rect.cx,
      cy: rect.cy,
      searchText,
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
      const k = kw.trim().toLowerCase();
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

export function parseSearchTokens(q) {
  const parts = (q || '')
    .trim()
    .toLowerCase()
    .split(/\s+/)
    .filter(Boolean);
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
  if (!ignoreExc && facet.exc?.includes(value)) return false;
  if (facet.inc?.length && !facet.inc.includes(value)) return false;
  return true;
}

function matchesMultiFacet(values, facet, ignoreExc = false) {
  if (!ignoreExc && facet.exc?.length && values.some((v) => facet.exc.includes(v))) return false;
  if (facet.inc?.length && !values.some((v) => facet.inc.includes(v))) return false;
  return true;
}

/**
 * Single source of truth for evaluating every project against active filters,
 * personal records, ignores, and preferences. Used identically by List and Map.
 */
export function evaluateProject(project, filters, record, prefs, searchTokens, myCoords) {
  const rec = record || {};
  const matchScore = computeMatchScore(project, prefs);
  const dist = myCoords
    ? Math.hypot(project.cx - myCoords.cx, project.cy - myCoords.cy)
    : 0;

  const ignoreReasons = [];
  if (rec.ign) ignoreReasons.push('manual');
  if (prefs.ignoreCats?.includes(project.cat) || filters.cats.exc.includes(project.cat)) {
    ignoreReasons.push('cat');
  }
  if (prefs.ignorePaths?.includes(project.path) || filters.paths.exc.includes(project.path)) {
    ignoreReasons.push('path');
  }
  if (filters.zones.exc.includes(project.z)) ignoreReasons.push('zone');
  if (filters.rows.exc.includes(project.r)) ignoreReasons.push('row');
  if (
    project.tags.some((t) => prefs.ignoreTags?.includes(t) || filters.tags.exc.includes(t))
  ) {
    ignoreReasons.push('tag');
  }
  const userTags = rec.tags || [];
  if (userTags.some((t) => filters.customTags.exc.includes(t))) {
    ignoreReasons.push('customTag');
  }
  if (project.allNats.some((n) => filters.countries.exc.includes(n))) {
    ignoreReasons.push('country');
  }
  if (filters.sizes.exc.includes(project.members.length)) {
    ignoreReasons.push('size');
  }

  const allNegWords = [
    ...(prefs.ignoreKeywords || []),
    ...(filters.ignoreKeywords || []),
    ...searchTokens.neg,
  ];
  for (const kw of allNegWords) {
    const k = (kw || '').trim().toLowerCase();
    if (k && project.searchText.includes(k)) {
      ignoreReasons.push('keyword');
      break;
    }
  }

  const isIgnored = ignoreReasons.length > 0;

  // Status tab logic
  let statusPass = true;
  if (filters.status === 'ignored') {
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

  if (!statusPass) {
    return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  }

  // Positive search tokens
  for (const tok of searchTokens.pos) {
    if (!project.searchText.includes(tok)) {
      return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
    }
  }

  // Inclusion facets (when viewing the 'ignored' tab, ignore .exc rejections so ignored items are inspectable)
  const viewingIgnored = filters.status === 'ignored';
  if (!matchesFacet(project.cat, filters.cats, viewingIgnored)) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  if (!matchesFacet(project.path, filters.paths, viewingIgnored)) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  if (!matchesFacet(project.z, filters.zones, viewingIgnored)) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  if (!matchesFacet(project.r, filters.rows, viewingIgnored)) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  if (!matchesMultiFacet(project.tags, filters.tags, viewingIgnored)) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  if (!matchesMultiFacet(userTags, filters.customTags, viewingIgnored)) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  if (!matchesMultiFacet(project.allNats, filters.countries, viewingIgnored)) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  if (!matchesFacet(project.members.length, filters.sizes, viewingIgnored)) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };

  // International filter
  if (filters.intlMode === 'intl_leader' && !project.intlLeader) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  if (filters.intlMode === 'has_intl' && !project.hasIntl) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  if (filters.intlMode === 'mixed' && !project.mixedNat) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  if (filters.intlMode === 'saudi_only' && project.hasIntl) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };

  // Language filter
  if (filters.langMode !== 'all' && project.lang !== filters.langMode) {
    return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  }

  // Rating filter
  const rat = rec.rat || 0;
  if (filters.ratingMode === 'rated' && rat === 0) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  if (filters.ratingMode === 'unrated' && rat > 0) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  if (filters.ratingMode === '3+' && rat < 3) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  if (filters.ratingMode === '4+' && rat < 4) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  if (filters.ratingMode === '5' && rat < 5) return { matches: false, isIgnored, ignoreReasons, matchScore, dist };

  // Minimum Match Score
  if (filters.minMatch > 0 && matchScore < filters.minMatch) {
    return { matches: false, isIgnored, ignoreReasons, matchScore, dist };
  }

  return { matches: true, isIgnored, ignoreReasons, matchScore, dist };
}

export function evaluateAll(projects, filters, records, prefs) {
  const searchTokens = parseSearchTokens(filters.q);
  const myParsed = parseTableCode(prefs.myBooth);
  const myCoords = myParsed ? getBoothRect(myParsed.z, myParsed.r, myParsed.s) : null;

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
    const ev = evaluateProject(p, filters, rec, prefs, searchTokens, myCoords);
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

  // Sort matched projects
  matched.sort((a, b) => {
    const ea = evalById.get(a.id);
    const eb = evalById.get(b.id);
    const ra = records[a.id]?.rat || 0;
    const rb = records[b.id]?.rat || 0;

    switch (filters.sortBy) {
      case 'match':
        return eb.matchScore - ea.matchScore || a.table.localeCompare(b.table);
      case 'nearest':
        return ea.dist - eb.dist || a.table.localeCompare(b.table);
      case 'rating':
        return rb - ra || eb.matchScore - ea.matchScore || a.table.localeCompare(b.table);
      case 'members':
        return b.members.length - a.members.length || eb.matchScore - ea.matchScore;
      case 'code':
        return a.code.localeCompare(b.code);
      case 'booth':
      default:
        return (
          a.z.localeCompare(b.z) ||
          a.r - b.r ||
          a.s - b.s ||
          a.code.localeCompare(b.code)
        );
    }
  });

  return { evalById, matched, counts, myCoords };
}

/**
 * Nearest-neighbor greedy walking route across selected booths starting from startBooth.
 */
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
      // Slight penalty when switching zones so we finish neighboring aisles first
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
