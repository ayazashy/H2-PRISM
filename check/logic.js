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
  myBooth: '',
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

export const HALL_WIDTH = 2120;
export const HALL_HEIGHT = 900;

const M_PX = 10;
const HALL_OX = 60;
const HALL_OY = 110;
const mx = (m) => Math.round((HALL_OX + m * M_PX) * 10) / 10;
const my = (m) => Math.round((HALL_OY + m * M_PX) * 10) / 10;

// Official SAIF Hall 4 geometry from map.saifair.sa (sef-plan.js)
const OFF_STRIPS = [68, 72.5, 77, 81.5, 86, 90.5, 95, 99.5, 104, 108.5, 113, 118.07, 122.6,
  131.6, 136.1, 141.1, 145.6, 150.1, 154.6, 159.1, 163.6, 168, 172.6, 177, 181.6, 186];
const OFF_BANDS = [5.2, 20.2, 35.2, 50.2];
const OFF_MEDIA_GAP = { x0: 115, x1: 141.1 };
const OFF_EAST_BOOTHS = { x0: 191.5, x1: 193.5, per: 6, blocks: [[-0.9, 8.7], [14.2, 23.4], [29.2, 38.7], [44.5, 53.5], [59.2, 67.6]] };
const OFF_WALL_BOOTHS = [{ x0: 108.25, x1: 118.05, per: 7 }, { x0: 144.25, x1: 154.05, per: 7 }];
const OFF_ZONES_META = [
  { letter: 'A', cols: 5, rows: 5, slots: 24, wing: 'youth', labelEn: '6-11y', labelAr: '٦-١١' },
  { letter: 'B', cols: 5, rows: 5, slots: 24, wing: 'youth', labelEn: '12-17y', labelAr: '١٢-١٧' },
  { letter: 'C', cols: 5, rows: 5, slots: 24, wing: 'youth', labelEn: '12-17y', labelAr: '١٢-١٧' },
  { letter: 'D', cols: 5, rows: 5, slots: 24, wing: 'youth', labelEn: '12-17y', labelAr: '١٢-١٧' },
  { letter: 'E', cols: 5, rows: 5, slots: 24, wing: 'youth', labelEn: '12-17y', labelAr: '١٢-١٧' },
  { letter: 'F', cols: 5, rows: 5, slots: 18, wing: 'bridge', labelEn: 'Mixed', labelAr: 'مشترك' },
  { letter: 'G', cols: 5, rows: 5, slots: 24, wing: 'pro', labelEn: '18+ Uni', labelAr: 'جامعي' },
  { letter: 'H', cols: 5, rows: 5, slots: 24, wing: 'pro', labelEn: '18+ Uni', labelAr: 'جامعي' },
  { letter: 'I', cols: 5, rows: 5, slots: 24, wing: 'pro', labelEn: 'Uni/Pro', labelAr: 'جامعي/رواد' },
  { letter: 'J', cols: 7, rows: 7, slots: 24, wing: 'pro', labelEn: '18+ Pro', labelAr: 'رواد/مطورون' },
  { letter: 'K', cols: 4, rows: 4, slots: 13, wing: 'pro', labelEn: '18+ Wall', labelAr: 'جدار/رواد' },
];

const OFFICIAL_BOOTH_RECTS = new Map();
const OFFICIAL_ZONE_BOXES = {};

(function buildOfficialRects() {
  const skip = (band, x) => band === 0 && x > OFF_MEDIA_GAP.x0 && x < OFF_MEDIA_GAP.x1;
  const desc = OFF_STRIPS.slice().reverse();
  const colIndex = (sx, col) => desc.indexOf(sx) * 2 + (col === 'east' ? 0 : 1);
  const zoneOfCol = (c) => {
    let acc = 0;
    for (let i = 0; i < 10; i++) {
      acc += OFF_ZONES_META[i].cols;
      if (c < acc) return i;
    }
    return 9;
  };
  const zoneStart = (zi) => OFF_ZONES_META.slice(0, zi).reduce((a, z) => a + z.cols, 0);

  const boundsByZ = {};
  const recordRect = (zLetter, code, xM, zM, wM = 1, dM = 2) => {
    const x = mx(xM - wM / 2);
    const y = my(zM - dM / 2);
    const w = wM * M_PX;
    const h = dM * M_PX;
    const rect = { x, y, w, h, cx: x + w / 2, cy: y + h / 2 };
    OFFICIAL_BOOTH_RECTS.set(code, rect);
    const b = (boundsByZ[zLetter] ||= { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity });
    if (x < b.minX) b.minX = x;
    if (y < b.minY) b.minY = y;
    if (x + w > b.maxX) b.maxX = x + w;
    if (y + h > b.maxY) b.maxY = y + h;
  };

  OFF_BANDS.forEach((z0, band) => {
    const strips = OFF_STRIPS.filter((x) => !skip(band, x)).slice().reverse();
    strips.forEach((sx) => {
      ['east', 'west'].forEach((col) => {
        const zi = zoneOfCol(colIndex(sx, col));
        const zLetter = OFF_ZONES_META[zi].letter;
        const zc = colIndex(sx, col) - zoneStart(zi) + 1;
        for (let r = 0; r < 6; r++) {
          const num = (OFF_BANDS.length - 1 - band) * 6 + (6 - r);
          const code = `S-${zLetter}${zc}-${String(num).padStart(2, '0')}`;
          const xM = sx + (col === 'east' ? 1.5 : 0.5);
          const zM = z0 + r * 2 + 1;
          recordRect(zLetter, code, xM, zM, 1, 2);
        }
      });
    });
  });

  const wallRowSlots = (a0, a1, per) => {
    const mid = per - 2, i0 = a0 + 0.65, i1 = a1 - 0.65, step = (i1 - i0) / mid;
    return [
      { a: a0 + 0.3, d: 1.3, side: true },
      ...Array.from({ length: mid }, (_, i) => ({ a: i0 + (i + 0.5) * step, d: 1.25, side: false })),
      { a: a1 - 0.3, d: 1.3, side: true },
    ];
  };
  let kCol = 1, kNum = 0;
  const nextK = () => {
    if (kNum === 12) { kCol++; kNum = 0; }
    return `S-K${kCol}-${String(++kNum).padStart(2, '0')}`;
  };
  OFF_EAST_BOOTHS.blocks.slice().sort((a, b) => b[0] - a[0]).forEach(([z0, z1]) => {
    wallRowSlots(z0, z1, OFF_EAST_BOOTHS.per).reverse().forEach((slot) => {
      recordRect('K', nextK(), OFF_EAST_BOOTHS.x1 - slot.d, slot.a, slot.side ? 1.6 : 1, slot.side ? 1 : 1.6);
    });
  });
  OFF_WALL_BOOTHS.slice().sort((a, b) => b.x0 - a.x0).forEach((row, i) => {
    if (i === 1) { kCol++; kNum = 0; }
    wallRowSlots(row.x0, row.x1, row.per).reverse().forEach((slot) => {
      recordRect('K', `S-K${kCol}-${String(++kNum).padStart(2, '0')}`, slot.a, -6.9 + slot.d, slot.side ? 1 : 1.6, slot.side ? 1.6 : 1);
    });
  });

  for (const z of OFF_ZONES_META) {
    const b = boundsByZ[z.letter];
    OFFICIAL_ZONE_BOXES[z.letter] = b
      ? { x: b.minX - 6, y: b.minY - 26, w: b.maxX - b.minX + 12, h: b.maxY - b.minY + 32 }
      : { x: 0, y: 0, w: 0, h: 0 };
  }
})();

export const ZONE_GEOMETRY = Object.fromEntries(
  OFF_ZONES_META.map((z) => [
    z.letter,
    {
      x: OFFICIAL_ZONE_BOXES[z.letter].x,
      y: OFFICIAL_ZONE_BOXES[z.letter].y,
      cols: z.slots,
      rows: z.rows,
      wing: z.wing,
      labelEn: z.labelEn,
      labelAr: z.labelAr,
    },
  ])
);

export function getZoneBox(zoneId) {
  return OFFICIAL_ZONE_BOXES[zoneId] || { x: 0, y: 0, w: 0, h: 0 };
}

export function getBoothRect(zoneId, row, seat) {
  const code = `S-${zoneId}${row}-${String(seat).padStart(2, '0')}`;
  return OFFICIAL_BOOTH_RECTS.get(code) || { x: 0, y: 0, w: 10, h: 20, cx: 5, cy: 10 };
}

export function parseTableCode(tableStr) {
  const m = /^S-([A-Z])(\d+)-(\d+)$/i.exec((tableStr || '').trim());
  if (!m) return null;
  return { z: m[1].toUpperCase(), r: Number(m[2]), s: Number(m[3]) };
}

export function hitTestHall(wx, wy, boothGroups) {
  for (const [tableStr, rect] of OFFICIAL_BOOTH_RECTS.entries()) {
    if (wx >= rect.x - 1 && wx <= rect.x + rect.w + 1 && wy >= rect.y - 1 && wy <= rect.y + rect.h + 1) {
      if (!boothGroups || boothGroups.has(tableStr)) {
        return { type: 'booth', zone: tableStr[2], table: tableStr };
      }
    }
  }
  for (const [zId, box] of Object.entries(OFFICIAL_ZONE_BOXES)) {
    if (wx >= box.x && wx <= box.x + box.w && wy >= box.y && wy <= box.y + box.h) {
      return { type: 'zone', zone: zId };
    }
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
      w: rect.w,
      h: rect.h,
      searchText,
      _score: 0,
      _dist: 0,
    };
  });
}

export function computeMatchScore(project, prefs, filters = null) {
  let score = 0;
  const cats = filters?.cats?.inc?.length ? [...new Set([...(prefs.prefCats || []), ...filters.cats.inc])] : prefs.prefCats;
  const paths = filters?.paths?.inc?.length ? [...new Set([...(prefs.prefPaths || []), ...filters.paths.inc])] : prefs.prefPaths;
  const tags = filters?.tags?.inc?.length ? [...new Set([...(prefs.prefTags || []), ...filters.tags.inc])] : prefs.prefTags;
  if (cats?.includes(project.cat)) score += 28;
  if (paths?.includes(project.path)) score += 26;

  if (tags?.length && project.tags?.length) {
    let tagHits = 0;
    for (const t of project.tags) {
      if (tags.includes(t)) tagHits += 1;
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
 * Cache match scores & distances onto project objects ONLY when prefs or whitelists change.
 * Eliminates ~11,000 substring scans per tap/filter interaction.
 */
export function refreshPrefsCache(projects, prefs, filters = null) {
  const myParsed = parseTableCode(prefs.myBooth);
  const myCoords = myParsed ? getBoothRect(myParsed.z, myParsed.r, myParsed.s) : null;
  const prefCatSet = new Set([...(prefs.prefCats || []), ...(filters?.cats?.inc || [])]);
  const prefPathSet = new Set([...(prefs.prefPaths || []), ...(filters?.paths?.inc || [])]);
  const prefTagSet = new Set([...(prefs.prefTags || []), ...(filters?.tags?.inc || [])]);
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
  refreshPrefsCache(projects, prefs, filters);
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
