import { ico } from './icons.js';
import {
  CUSTOM_TAGS,
  HALL_HEIGHT,
  HALL_WIDTH,
  ZONE_GEOMETRY,
  computeWalkingRoute,
  getBoothRect,
  getZoneBox,
  hitTestHall,
  parseTableCode,
} from './logic.js';

const CAT_COLORS = {
  1: '#e11d48',
  2: '#0284c7',
  3: '#6366f1',
  4: '#d97706',
};

const RATING_COLORS = {
  0: '#475569',
  1: '#dc2626',
  2: '#ea580c',
  3: '#ca8a04',
  4: '#65a30d',
  5: '#059669',
};

function matchColor(score) {
  if (score >= 80) return '#10b981';
  if (score >= 60) return '#0891b2';
  if (score >= 40) return '#6366f1';
  if (score >= 20) return '#64748b';
  return '#334155';
}

function escapeHtml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/**
 * Ultra-Light Zero-Lag Map Controller:
 * - Overview ('All'): Direct 1x DPR canvas fitting hall cleanly with native scroll when zoomed.
 * - Zone View ('A'..'K'): Native scrollable LTR grid (`zgrid-inner` max-content) so 01..24 never clips.
 * - Zero emojis anywhere (standardized SVG icons only).
 */
export class FairMapController {
  constructor(container, { meta, projects, onSelectProject, onAction }) {
    this.container = container;
    this.meta = meta;
    this.projects = projects;
    this.onSelectProject = onSelectProject;
    this.onAction = onAction;

    this.pathMap = new Map(meta.paths.map((p) => [p.id, p]));
    this.boothGroups = new Map();
    for (const p of projects) {
      if (!this.boothGroups.has(p.table)) this.boothGroups.set(p.table, []);
      this.boothGroups.get(p.table).push(p);
    }

    this.zoneBoxes = {};
    for (const z of Object.keys(ZONE_GEOMETRY)) {
      this.zoneBoxes[z] = getZoneBox(z);
    }

    this.selectedTable = null;
    this.selectedProjectId = null;
    this.activeZone = null;

    this.stageW = 800;
    this.stageH = 500;
    this.dpr = 1;
    this.canvasZoom = 1;

    this._lastArgs = null;
    this._matchedIds = new Set();
    this._route = [];
    this._routeIndexByTable = new Map();

    this._buildDOM();
    this._bindEvents();
  }

  _buildDOM() {
    this.container.innerHTML = '';

    this.toolbar = document.createElement('div');
    this.toolbar.className = 'map-toolbar';
    this.toolbar.innerHTML = `
      <div class="map-seg">
        <button data-color="status" class="active">${ico('circle')}</button>
        <button data-color="rating">${ico('star')}</button>
        <button data-color="match">${ico('zap')}</button>
        <button data-color="cat">${ico('users')}</button>
        <button data-color="path">${ico('compass')}</button>
      </div>
      <div class="map-toggles">
        <button class="chip-btn" data-toggle="hideFiltered">${ico('eyeOff')}</button>
        <button class="chip-btn" data-toggle="hideIgnored">${ico('ban')}</button>
        <button class="chip-btn" data-toggle="showRoute">${ico('route')}</button>
      </div>
      <div class="map-zoom-btns">
        <button data-zoom="out">${ico('minus')}</button>
        <button data-zoom="in">${ico('plus')}</button>
        <button data-zoom="fit">${ico('maximize')}</button>
        <button data-zoom="me">${ico('pin')}</button>
      </div>
    `;
    this.container.appendChild(this.toolbar);

    this.zoneStrip = document.createElement('div');
    this.zoneStrip.className = 'map-zone-strip';
    const allBtn = document.createElement('button');
    allBtn.className = 'zjump-btn active';
    allBtn.dataset.zjump = 'ALL';
    allBtn.textContent = 'All';
    this.zoneStrip.appendChild(allBtn);

    for (const z of Object.keys(ZONE_GEOMETRY)) {
      const b = document.createElement('button');
      b.className = 'zjump-btn';
      b.dataset.zjump = z;
      b.textContent = z;
      this.zoneStrip.appendChild(b);
    }
    this.container.appendChild(this.zoneStrip);

    this.stage = document.createElement('div');
    this.stage.className = 'map-stage';

    this.canvasScroll = document.createElement('div');
    this.canvasScroll.className = 'canvas-scroll';

    this.canvas = document.createElement('canvas');
    this.canvas.className = 'hall-canvas';
    this.ctx = this.canvas.getContext('2d', { alpha: false });
    this.canvasScroll.appendChild(this.canvas);
    this.stage.appendChild(this.canvasScroll);

    this.zoneGridWrap = document.createElement('div');
    this.zoneGridWrap.className = 'zone-grid-wrap hidden';
    this.stage.appendChild(this.zoneGridWrap);

    this.legend = document.createElement('div');
    this.legend.className = 'map-legend';
    this.stage.appendChild(this.legend);

    this.inspector = document.createElement('div');
    this.inspector.className = 'map-inspector hidden';
    this.stage.appendChild(this.inspector);

    this.container.appendChild(this.stage);

    this.routeStrip = document.createElement('div');
    this.routeStrip.className = 'map-route-strip hidden';
    this.container.appendChild(this.routeStrip);

    if (typeof ResizeObserver !== 'undefined') {
      this._ro = new ResizeObserver(() => this._resizeCanvas());
      this._ro.observe(this.stage);
    }
  }

  _resizeCanvas() {
    if (this.activeZone) return;
    const rect = this.stage.getBoundingClientRect();
    if (!rect.width || !rect.height) return;

    const fitScale = Math.min(rect.width / HALL_WIDTH, rect.height / HALL_HEIGHT) * 0.94;
    const nextW = this.canvasZoom <= 1
      ? Math.round(rect.width)
      : Math.max(Math.round(rect.width), Math.round(HALL_WIDTH * fitScale * this.canvasZoom + 24));
    const nextH = this.canvasZoom <= 1
      ? Math.round(rect.height)
      : Math.max(Math.round(rect.height), Math.round(HALL_HEIGHT * fitScale * this.canvasZoom + 24));

    if (Math.abs(nextW - this.stageW) < 3 && Math.abs(nextH - this.stageH) < 3) return;

    this.stageW = nextW;
    this.stageH = nextH;
    this.dpr = typeof window !== 'undefined' && window.innerWidth <= 900 ? 1 : Math.min(window.devicePixelRatio || 1, 1.5);
    this.canvas.style.width = `${this.stageW}px`;
    this.canvas.style.height = `${this.stageH}px`;
    this.canvas.width = Math.round(this.stageW * this.dpr);
    this.canvas.height = Math.round(this.stageH * this.dpr);
    this._draw();
  }

  _baseFit() {
    const scale = Math.min(this.stageW / HALL_WIDTH, this.stageH / HALL_HEIGHT) * 0.94;
    const ox = (this.stageW - HALL_WIDTH * scale) / 2;
    const oy = (this.stageH - HALL_HEIGHT * scale) / 2;
    return { scale, ox, oy };
  }

  _screenToWorld(clientX, clientY) {
    const rect = this.canvas.getBoundingClientRect();
    const sx = clientX - rect.left;
    const sy = clientY - rect.top;
    const { scale, ox, oy } = this._baseFit();
    return {
      wx: (sx - ox) / (scale || 1),
      wy: (sy - oy) / (scale || 1),
    };
  }

  _bindEvents() {
    this.toolbar.addEventListener('click', (e) => {
      const colorBtn = e.target.closest('[data-color]');
      if (colorBtn) return this.onAction('mapColor', colorBtn.dataset.color);

      const toggleBtn = e.target.closest('[data-toggle]');
      if (toggleBtn) return this.onAction('toggleMapOpt', toggleBtn.dataset.toggle);

      const zBtn = e.target.closest('[data-zoom]');
      if (!zBtn) return;
      const mode = zBtn.dataset.zoom;
      if (mode === 'in') {
        if (this.activeZone) this.resetView();
        this.canvasZoom = Math.min(3.4, +(this.canvasZoom + 0.7).toFixed(1));
        this.stageW = 0;
        this._resizeCanvas();
      } else if (mode === 'out') {
        if (this.activeZone) this.resetView();
        this.canvasZoom = Math.max(1, +(this.canvasZoom - 0.7).toFixed(1));
        this.stageW = 0;
        this._resizeCanvas();
      } else if (mode === 'fit') {
        this.resetView();
      } else if (mode === 'me' && this._lastArgs) {
        if (this._lastArgs.prefs.myBooth) this.focusTable(this._lastArgs.prefs.myBooth, true);
        else this.onAction('openPrefs');
      }
    });

    this.zoneStrip.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-zjump]');
      if (!btn) return;
      const z = btn.dataset.zjump;
      if (z === 'ALL') this.resetView();
      else this.focusZone(z);
    });

    this.canvas.addEventListener('click', (e) => {
      const { wx, wy } = this._screenToWorld(e.clientX, e.clientY);
      const hit = hitTestHall(wx, wy, this.boothGroups);
      if (!hit) {
        this.closeInspector();
        return;
      }
      this.focusZone(hit.zone);
      if (hit.type === 'booth') this.selectTable(hit.table);
    });

    this.zoneGridWrap.addEventListener('click', (e) => {
      const tile = e.target.closest('[data-gtbl]');
      if (tile) {
        this.selectTable(tile.dataset.gtbl);
        return;
      }
      if (e.target.closest('[data-back-all]')) {
        this.resetView();
      }
    });

    this.inspector.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-insp-action]');
      if (!btn) return;
      const act = btn.dataset.inspAction;
      const id = btn.dataset.id;
      if (act === 'close') this.closeInspector();
      else if (act === 'switch') {
        this.selectedProjectId = id;
        this._renderInspector();
      } else if (act === 'open') this.onSelectProject(id);
      else if (act === 'fav') this.onAction('fav', id);
      else if (act === 'vis') this.onAction('vis', id);
      else if (act === 'ign') this.onAction('ign', id);
      else if (act === 'rat') this.onAction('rat', { id, stars: Number(btn.dataset.stars) });
      else if (act === 'tag') this.onAction('tag', { id, tagId: btn.dataset.tag });
    });

    this.inspector.addEventListener('input', (e) => {
      if (e.target.dataset.inspNote) {
        this.onAction('note', { id: e.target.dataset.inspNote, note: e.target.value });
      }
    });

    this.routeStrip.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-route-table]');
      if (btn) this.focusTable(btn.dataset.routeTable, true);
    });
  }

  resetView() {
    this.activeZone = null;
    this.canvasZoom = 1;
    this.stageW = 0;
    this.canvasScroll.classList.remove('hidden');
    this.zoneGridWrap.classList.add('hidden');
    this.legend.classList.remove('hidden');
    this._updateZonePillsActive();
    this._resizeCanvas();
  }

  focusZone(zoneId) {
    if (!ZONE_GEOMETRY[zoneId]) return;
    this.activeZone = zoneId;
    this.canvasScroll.classList.add('hidden');
    this.zoneGridWrap.classList.remove('hidden');
    this.legend.classList.add('hidden');
    this._updateZonePillsActive();
    this._renderZoneGrid();
  }

  focusTable(tableStr, openInspector = true) {
    const parsed = parseTableCode(tableStr);
    if (!parsed) return;
    this.focusZone(parsed.z);
    if (openInspector && this.boothGroups.has(tableStr)) {
      this.selectTable(tableStr);
    }
    const raf = typeof requestAnimationFrame === 'function' ? requestAnimationFrame : (fn) => setTimeout(fn, 0);
    raf(() => {
      const tile = this.zoneGridWrap.querySelector(`[data-gtbl="${tableStr}"]`);
      if (tile?.scrollIntoView) {
        tile.scrollIntoView({ block: 'center', inline: 'center' });
      }
    });
  }

  _updateZonePillsActive() {
    const active = this.activeZone || 'ALL';
    for (const btn of this.zoneStrip.querySelectorAll('[data-zjump]')) {
      btn.classList.toggle('active', btn.dataset.zjump === active);
    }
  }

  selectTable(tableStr) {
    this.selectedTable = tableStr;
    const projs = this.boothGroups.get(tableStr);
    if (projs?.length) this.selectedProjectId = projs[0].id;
    this._renderInspector();
    if (this.activeZone) {
      for (const el of this.zoneGridWrap.querySelectorAll('.ztile.selected')) {
        el.classList.remove('selected');
      }
      const next = this.zoneGridWrap.querySelector(`[data-gtbl="${tableStr}"]`);
      if (next) next.classList.add('selected');
    } else {
      this._draw();
    }
  }

  closeInspector() {
    this.selectedTable = null;
    this.selectedProjectId = null;
    this.inspector.classList.add('hidden');
    if (this.activeZone) {
      for (const el of this.zoneGridWrap.querySelectorAll('.ztile.selected')) {
        el.classList.remove('selected');
      }
    } else {
      this._draw();
    }
  }

  _boothVisual(tableStr) {
    const { evalById, records, prefs, ui } = this._lastArgs;
    const projs = this.boothGroups.get(tableStr);
    const myTable = (prefs.myBooth || '').toUpperCase();
    const isLight = ui.theme === 'light';
    const colorMode = ui.mapColor || 'status';
    const isMe = tableStr === myTable;

    let anyMatches = false;
    let allIgnored = true;
    let anyFav = false;
    let anyVis = false;
    let maxRat = 0;
    let maxScore = 0;
    let primary = projs[0];

    for (const pr of projs) {
      const ev = evalById.get(pr.id);
      const rec = records[pr.id] || {};
      if (this._matchedIds.has(pr.id)) {
        anyMatches = true;
        primary = pr;
      }
      if (!ev?.isIgnored) allIgnored = false;
      if (rec.fav) anyFav = true;
      if (rec.vis) anyVis = true;
      if ((rec.rat || 0) > maxRat) maxRat = rec.rat;
      if ((ev?.matchScore || 0) > maxScore) maxScore = ev.matchScore;
    }

    const hidden =
      (allIgnored && ui.hideIgnoredOnMap && !isMe) ||
      (!anyMatches && !allIgnored && ui.hideFilteredOnMap && !isMe);

    let fill = isLight ? '#94a3b8' : '#475569';
    if (isMe) fill = '#9333ea';
    else if (allIgnored && !anyMatches) fill = isLight ? '#cbd5e1' : '#111827';
    else if (colorMode === 'status') {
      if (anyFav && anyVis) fill = '#0d9488';
      else if (anyFav) fill = '#d97706';
      else if (anyVis) fill = '#059669';
      else if (maxRat > 0) fill = '#7c3aed';
      else if (maxScore >= 50 && anyMatches) fill = '#0284c7';
      else if (anyMatches) fill = isLight ? '#64748b' : '#52637d';
      else fill = isLight ? '#cbd5e1' : '#1f293d';
    } else if (colorMode === 'rating') fill = RATING_COLORS[maxRat] || '#475569';
    else if (colorMode === 'match') fill = matchColor(maxScore);
    else if (colorMode === 'cat') fill = CAT_COLORS[primary.cat] || '#64748b';
    else if (colorMode === 'path') fill = this.pathMap.get(primary.path)?.color || '#64748b';

    return {
      isMe,
      anyMatches,
      allIgnored,
      anyFav,
      anyVis,
      maxRat,
      hidden,
      fill,
      multi: projs.length > 1,
    };
  }

  _tileBadgeHtml(vis, tableStr) {
    const routeNum = this._routeIndexByTable.get(tableStr);
    if (routeNum) return `<i>#${routeNum}</i>`;
    if (vis.isMe) return `<i>ME</i>`;
    if (vis.maxRat) return `<i>${vis.maxRat}${ico('starFill')}</i>`;
    if (vis.anyFav && vis.anyVis) return `<i>${ico('starFill')}${ico('check')}</i>`;
    if (vis.anyFav) return `<i>${ico('starFill')}</i>`;
    if (vis.anyVis) return `<i>${ico('check')}</i>`;
    if (vis.multi) return `<i>x2</i>`;
    return '';
  }

  sync({ evalById, matched, records, prefs, ui }) {
    this._lastArgs = { evalById, matched, records, prefs, ui };
    this._matchedIds = new Set(matched.map((p) => p.id));

    for (const btn of this.toolbar.querySelectorAll('[data-color]')) {
      btn.classList.toggle('active', btn.dataset.color === (ui.mapColor || 'status'));
    }
    this.toolbar.querySelector('[data-toggle="hideFiltered"]').classList.toggle('active', !!ui.hideFilteredOnMap);
    this.toolbar.querySelector('[data-toggle="hideIgnored"]').classList.toggle('active', !!ui.hideIgnoredOnMap);
    this.toolbar.querySelector('[data-toggle="showRoute"]').classList.toggle('active', !!ui.showRoute);
    const meBtn = this.toolbar.querySelector('[data-zoom="me"]');
    if (meBtn) meBtn.classList.toggle('hidden', !prefs.myBooth);

    const zMatch = {};
    const zTotal = {};
    for (const z of Object.keys(ZONE_GEOMETRY)) {
      zMatch[z] = 0;
      zTotal[z] = 0;
    }
    for (const p of this.projects) {
      zTotal[p.z] += 1;
      if (this._matchedIds.has(p.id)) zMatch[p.z] += 1;
    }
    this._zMatch = zMatch;
    this._zTotal = zTotal;

    for (const z of Object.keys(ZONE_GEOMETRY)) {
      const btn = this.zoneStrip.querySelector(`[data-zjump="${z}"]`);
      if (btn) {
        btn.classList.toggle('has-matches', zMatch[z] > 0);
        btn.innerHTML = `${z}<sub>${zMatch[z]}</sub>`;
      }
    }

    this._routeIndexByTable.clear();
    if (ui.showRoute) {
      const todoFavs = matched.filter((p) => records[p.id]?.fav && !records[p.id]?.vis);
      const targets = todoFavs.length ? todoFavs : matched.slice(0, 25);
      this._route = computeWalkingRoute(targets, prefs.myBooth, 25);
      this._route.forEach((p, i) => this._routeIndexByTable.set(p.table, i + 1));
    } else {
      this._route = [];
    }

    this._renderLegend(ui.mapColor || 'status', ui.lang);
    this._renderRouteStrip(prefs);
    if (this.selectedTable) this._renderInspector();

    if (this.activeZone) {
      this._renderZoneGrid();
    } else {
      this._draw();
    }
  }

  refreshBooth(tableStr) {
    if (!this._lastArgs) return;
    if (this.activeZone) {
      const parsed = parseTableCode(tableStr);
      if (parsed?.z === this.activeZone) {
        const tile = this.zoneGridWrap.querySelector(`[data-gtbl="${tableStr}"]`);
        if (tile) {
          const vis = this._boothVisual(tableStr);
          if (vis.hidden) {
            this._renderZoneGrid();
            return;
          }
          tile.style.background = vis.fill;
          tile.classList.toggle('dim', !vis.anyMatches && !vis.allIgnored && !vis.isMe);
          tile.classList.toggle('ign', vis.allIgnored && !vis.anyMatches && !vis.isMe);
          tile.innerHTML = `<b>${parsed.s}</b>${this._tileBadgeHtml(vis, tableStr)}`;
        }
      }
    } else {
      this._draw();
    }
  }

  _draw() {
    if (!this.ctx || !this._lastArgs || this.activeZone) return;
    const ctx = this.ctx;
    const { prefs, ui } = this._lastArgs;
    const isLight = ui.theme === 'light';
    const myTable = (prefs.myBooth || '').toUpperCase();

    ctx.save();
    ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    ctx.fillStyle = isLight ? '#ede9df' : '#111622';
    ctx.fillRect(0, 0, this.stageW, this.stageH);

    const { scale, ox, oy } = this._baseFit();
    ctx.translate(ox, oy);
    ctx.scale(scale, scale);

    ctx.fillStyle = isLight ? 'rgba(2, 132, 199, 0.04)' : 'rgba(96, 165, 250, 0.04)';
    ctx.strokeStyle = isLight ? '#cbd5e1' : '#263248';
    ctx.lineWidth = 1.2;
    ctx.fillRect(8, 8, 842, 678);
    ctx.strokeRect(8, 8, 842, 678);

    ctx.fillStyle = isLight ? 'rgba(124, 58, 237, 0.04)' : 'rgba(167, 139, 250, 0.04)';
    ctx.fillRect(896, 8, 856, 678);
    ctx.strokeRect(896, 8, 856, 678);

    for (const [zId, g] of Object.entries(ZONE_GEOMETRY)) {
      const box = this.zoneBoxes[zId];
      ctx.fillStyle = isLight ? '#faf9f5' : '#182032';
      ctx.fillRect(box.x, box.y, box.w, box.h);
      ctx.strokeStyle = isLight ? '#d6d3c9' : '#2a3750';
      ctx.strokeRect(box.x, box.y, box.w, box.h);

      ctx.fillStyle = isLight ? '#e7e3d8' : '#202b42';
      ctx.fillRect(box.x + 1, box.y + 1, box.w - 2, 23);

      ctx.fillStyle = isLight ? '#0f172a' : '#e6edf3';
      ctx.font = '700 12px sans-serif';
      ctx.textBaseline = 'middle';
      ctx.textAlign = 'left';
      ctx.fillText(zId, box.x + 9, box.y + 13);

      ctx.fillStyle = isLight ? '#475569' : '#9aa8be';
      ctx.font = '600 9.5px sans-serif';
      ctx.fillText(ui.lang === 'ar' ? g.labelAr : g.labelEn, box.x + 24, box.y + 13);

      ctx.fillStyle = isLight ? '#0369a1' : '#7dd3fc';
      ctx.font = '700 10px sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(`${this._zMatch[zId]}/${this._zTotal[zId]}`, box.x + box.w - 9, box.y + 13);
    }

    const batches = new Map();
    const pips = [];

    for (const [tableStr, projs] of this.boothGroups.entries()) {
      const vis = this._boothVisual(tableStr);
      if (vis.hidden) continue;
      const p0 = projs[0];
      const alpha = !vis.anyMatches && !vis.allIgnored && !vis.isMe
        ? (isLight ? 0.22 : 0.16)
        : vis.allIgnored && !vis.anyMatches && !vis.isMe
        ? 0.14
        : 1;
      const key = `${vis.fill}|${alpha}`;
      if (!batches.has(key)) batches.set(key, { fill: vis.fill, alpha, rects: [] });
      batches.get(key).rects.push(p0);
      if (vis.isMe || vis.anyFav || vis.anyVis || vis.multi) {
        pips.push({ p0, vis });
      }
    }

    for (const b of batches.values()) {
      ctx.globalAlpha = b.alpha;
      ctx.fillStyle = b.fill;
      for (const p0 of b.rects) {
        ctx.fillRect(p0.x, p0.y, 14, 22);
      }
    }

    ctx.globalAlpha = 1;
    for (const { p0, vis } of pips) {
      ctx.fillStyle = vis.isMe ? '#ffffff' : vis.anyFav ? '#fef08a' : vis.anyVis ? '#a7f3d0' : '#f472b6';
      ctx.fillRect(p0.x + 9.5, p0.y + 1.5, 3.2, 3.2);
    }

    if (ui.showRoute && this._route.length) {
      const myParsed = parseTableCode(myTable);
      const start = myParsed ? getBoothRect(myParsed.z, myParsed.r, myParsed.s) : this._route[0];
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 2.4;
      ctx.setLineDash([6, 4]);
      ctx.beginPath();
      ctx.moveTo(start.cx, start.cy);
      for (const stop of this._route) ctx.lineTo(stop.cx, stop.cy);
      ctx.stroke();
      ctx.setLineDash([]);

      this._route.forEach((stop, idx) => {
        ctx.fillStyle = '#f59e0b';
        ctx.fillRect(stop.cx - 6, stop.cy - 14, 12, 12);
        ctx.fillStyle = '#0f172a';
        ctx.font = '800 7.5px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(String(idx + 1), stop.cx, stop.cy - 8);
      });
    }

    const myParsed = parseTableCode(myTable);
    if (myParsed) {
      const mr = getBoothRect(myParsed.z, myParsed.r, myParsed.s);
      ctx.strokeStyle = '#d946ef';
      ctx.lineWidth = 2.5;
      ctx.strokeRect(mr.x - 3, mr.y - 3, 20, 28);
    }

    if (this.selectedTable) {
      const sp = parseTableCode(this.selectedTable);
      if (sp) {
        const sr = getBoothRect(sp.z, sp.r, sp.s);
        ctx.strokeStyle = isLight ? '#0f172a' : '#ffffff';
        ctx.lineWidth = 2.5;
        ctx.strokeRect(sr.x - 2.5, sr.y - 2.5, 19, 27);
      }
    }

    ctx.restore();
  }

  _renderZoneGrid() {
    if (!this.activeZone || !this._lastArgs) return;
    const zId = this.activeZone;
    const g = ZONE_GEOMETRY[zId];
    const { ui } = this._lastArgs;
    const lang = ui.lang === 'en' ? 'en' : 'ar';

    let rowsHtml = '';
    for (let r = 1; r <= g.rows; r++) {
      const maxCols = zId === 'E' && r >= 3 ? 18 : zId === 'K' ? [12, 12, 13, 7][r - 1] : g.cols;
      let cellsHtml = '';
      for (let s = 1; s <= maxCols; s++) {
        const tableStr = `S-${zId}${r}-${String(s).padStart(2, '0')}`;
        const projs = this.boothGroups.get(tableStr);
        if (!projs) {
          cellsHtml += `<span class="ztile empty"></span>`;
          continue;
        }
        const vis = this._boothVisual(tableStr);
        if (vis.hidden) {
          cellsHtml += `<span class="ztile hidden-slot">${s}</span>`;
          continue;
        }
        const dimCls = !vis.anyMatches && !vis.allIgnored && !vis.isMe ? 'dim' : vis.allIgnored && !vis.anyMatches && !vis.isMe ? 'ign' : '';
        const selCls = this.selectedTable === tableStr ? 'selected' : '';
        const meCls = vis.isMe ? 'is-me' : '';
        cellsHtml += `<button class="ztile ${dimCls} ${selCls} ${meCls}" data-gtbl="${tableStr}" style="background:${vis.fill}"><b>${s}</b>${this._tileBadgeHtml(vis, tableStr)}</button>`;
      }
      const aisleCls = r % 2 === 0 && r < g.rows ? 'aisle-after' : '';
      rowsHtml += `<div class="zrow ${aisleCls}"><span class="zrow-lbl">R${r}</span><div class="zrow-cells">${cellsHtml}</div></div>`;
    }

    this.zoneGridWrap.innerHTML = `
      <div class="zgrid-head">
        <button class="bulk-btn" data-back-all>${ico('chevLeft')} All</button>
        <b>Zone ${zId}</b>
        <span class="badge-mini">${lang === 'ar' ? g.labelAr : g.labelEn}</span>
        <span class="badge-match">${this._zMatch[zId]}/${this._zTotal[zId]}</span>
      </div>
      <div class="zgrid-rows"><div class="zgrid-inner">${rowsHtml}</div></div>
    `;
  }

  _renderRouteStrip(prefs) {
    this.routeStrip.innerHTML = '';
    if (!this._route.length) {
      this.routeStrip.classList.add('hidden');
      return;
    }
    this.routeStrip.classList.remove('hidden');
    if (prefs.myBooth) {
      const startPill = document.createElement('button');
      startPill.className = 'route-pill start';
      startPill.dataset.routeTable = prefs.myBooth;
      startPill.innerHTML = `${ico('pin')} ${escapeHtml(prefs.myBooth)}`;
      this.routeStrip.appendChild(startPill);
    }

    this._route.forEach((p, idx) => {
      const b = document.createElement('button');
      b.className = 'route-pill';
      b.dataset.routeTable = p.table;
      b.innerHTML = `<span>${idx + 1}.</span> <b>${p.table}</b>`;
      this.routeStrip.appendChild(b);
    });
  }

  _renderLegend(mode, lang) {
    const itemsByMode = {
      status: [
        ['#9333ea', ico('pin')],
        ['#d97706', ico('starFill')],
        ['#059669', ico('check')],
        ['#0d9488', `${ico('starFill')}+${ico('check')}`],
        ['#7c3aed', '1-5'],
        ['#0284c7', `${ico('zap')}50+`],
      ],
      rating: [
        ['#059669', `5${ico('starFill')}`],
        ['#65a30d', `4${ico('starFill')}`],
        ['#ca8a04', `3${ico('starFill')}`],
        ['#ea580c', `2${ico('starFill')}`],
        ['#dc2626', `1${ico('starFill')}`],
      ],
      match: [
        ['#10b981', '80+'],
        ['#0891b2', '60+'],
        ['#6366f1', '40+'],
        ['#64748b', '20+'],
      ],
      cat: [
        ['#d97706', lang === 'ar' ? 'رواد' : '18+Pro'],
        ['#6366f1', lang === 'ar' ? 'جامعي' : '18+Uni'],
        ['#0284c7', '12-17'],
        ['#e11d48', '6-11'],
      ],
      path: this.meta.paths.slice(0, 6).map((p) => [p.color, ico(p.icon)]),
    };
    const items = itemsByMode[mode] || [];
    this.legend.innerHTML = items
      .map(([c, lbl]) => `<span class="leg-i"><i style="background:${c}"></i>${lbl}</span>`)
      .join('');
  }

  _renderInspector() {
    if (!this.selectedTable || !this._lastArgs) return;
    const projs = this.boothGroups.get(this.selectedTable);
    if (!projs?.length) return;
    const { evalById, records, ui } = this._lastArgs;
    const p = projs.find((x) => x.id === this.selectedProjectId) || projs[0];
    const rec = records[p.id] || {};
    const ev = evalById.get(p.id) || {};
    const pathObj = this.pathMap.get(p.path);
    const catObj = this.meta.cats.find((c) => c.id === p.cat);
    const flags = p.allNats.map((n) => this.meta.countries[n]?.[0] || '').join('');

    const switcher =
      projs.length > 1
        ? `<div class="insp-switch">${projs
            .map(
              (sp, i) =>
                `<button class="${sp.id === p.id ? 'active' : ''}" data-insp-action="switch" data-id="${sp.id}">#${i + 1} ${sp.code}</button>`
            )
            .join('')}</div>`
        : '';

    const stars = [1, 2, 3, 4, 5]
      .map(
        (s) =>
          `<button class="star-btn ${(rec.rat || 0) >= s ? 'on' : ''}" data-insp-action="rat" data-id="${p.id}" data-stars="${s}">${ico((rec.rat || 0) >= s ? 'starFill' : 'star')}</button>`
      )
      .join('');

    const tagsHtml = CUSTOM_TAGS.map(
      (t) =>
        `<button class="tag-pill ${(rec.tags || []).includes(t.id) ? 'on' : ''}" data-insp-action="tag" data-id="${p.id}" data-tag="${t.id}">${ico(t.icon)}</button>`
    ).join('');

    this.inspector.innerHTML = `
      ${switcher}
      <div class="insp-head">
        <span class="badge-table">${p.table}</span>
        <span class="badge-cat c${p.cat}">${ui.lang === 'ar' ? catObj?.ar : catObj?.en}</span>
        <span class="badge-path">${ico(pathObj?.icon)} ${ui.lang === 'ar' ? pathObj?.ar : pathObj?.en}</span>
        <span class="badge-mini">${flags} x${p.members.length}</span>
        <span class="badge-match">${ico('zap')} ${ev.matchScore ?? 0}</span>
        <button class="insp-close" data-insp-action="close">${ico('x')}</button>
      </div>
      <div class="insp-title" data-insp-action="open" data-id="${p.id}">${escapeHtml(p.title)}</div>
      <div class="insp-actions">
        <button class="act-btn fav ${rec.fav ? 'on' : ''}" data-insp-action="fav" data-id="${p.id}">${ico(rec.fav ? 'starFill' : 'star')}</button>
        <button class="act-btn vis ${rec.vis ? 'on' : ''}" data-insp-action="vis" data-id="${p.id}">${ico('check')}</button>
        <div class="stars-row">${stars}</div>
        <button class="act-btn ign ${rec.ign ? 'on' : ''}" data-insp-action="ign" data-id="${p.id}">${ico('ban')}</button>
        <button class="act-btn open" data-insp-action="open" data-id="${p.id}">${ico('expand')}</button>
      </div>
      <div class="insp-tags">${tagsHtml}</div>
      <input class="insp-note" type="text" data-insp-note="${p.id}" value="${escapeHtml(rec.note || '')}" placeholder="LinkedIn / @ / ..." />
    `;
    this.inspector.classList.remove('hidden');
  }
}
