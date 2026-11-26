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

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  if (typeof ctx.roundRect === 'function') {
    ctx.roundRect(x, y, w, h, r);
  } else {
    ctx.rect(x, y, w, h);
  }
}

/**
 * High-performance 60fps HTML5 Canvas Floorplan Controller.
 * Zero per-booth SVG DOM nodes; renders all 1,241 physical booths + routes in ~1.5ms.
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
    this.activeZone = null; // null = All hall overview

    // World-to-canvas transform: screenX = offsetX + worldX * scale
    this.zoom = 1;
    this.panX = 0;
    this.panY = 0;
    this.stageW = 800;
    this.stageH = 500;
    this.dpr = 1;

    this.pointers = new Map();
    this.isDragging = false;
    this.dragMoved = false;
    this.dragStart = null;
    this.pinchDist = 0;
    this.pinchZoom = 1;
    this._rafPending = false;
    this._lastArgs = null;
    this._route = [];

    this._buildDOM();
    this._bindEvents();
    this._bindPanZoom();
  }

  _buildDOM() {
    this.container.innerHTML = '';

    this.toolbar = document.createElement('div');
    this.toolbar.className = 'map-toolbar';
    this.toolbar.innerHTML = `
      <div class="map-seg">
        <button data-color="status" class="active">●</button>
        <button data-color="rating">★</button>
        <button data-color="match">⚡</button>
        <button data-color="cat">👥</button>
        <button data-color="path">🧭</button>
      </div>
      <div class="map-toggles">
        <button class="chip-btn" data-toggle="hideFiltered">👁️</button>
        <button class="chip-btn" data-toggle="hideIgnored">🚫</button>
        <button class="chip-btn" data-toggle="showRoute">〰️</button>
      </div>
      <div class="map-zoom-btns">
        <button data-zoom="out">−</button>
        <button data-zoom="in">+</button>
        <button data-zoom="fit">⊡</button>
        <button data-zoom="me">📍</button>
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

    this.canvas = document.createElement('canvas');
    this.canvas.className = 'hall-canvas';
    this.ctx = this.canvas.getContext('2d', { alpha: false });
    this.stage.appendChild(this.canvas);

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
    const rect = this.stage.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    this.stageW = rect.width;
    this.stageH = rect.height;
    this.dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.canvas.width = Math.round(rect.width * this.dpr);
    this.canvas.height = Math.round(rect.height * this.dpr);
    this._scheduleDraw();
  }

  _baseFit() {
    const scale = Math.min(this.stageW / HALL_WIDTH, this.stageH / HALL_HEIGHT) * 0.96;
    const ox = (this.stageW - HALL_WIDTH * scale) / 2;
    const oy = (this.stageH - HALL_HEIGHT * scale) / 2;
    return { scale, ox, oy };
  }

  _screenToWorld(clientX, clientY) {
    const rect = this.canvas.getBoundingClientRect();
    const sx = clientX - rect.left;
    const sy = clientY - rect.top;
    const { scale, ox, oy } = this._baseFit();
    const wx = ((sx - ox) / scale - this.panX) / this.zoom;
    const wy = ((sy - oy) / scale - this.panY) / this.zoom;
    return { wx, wy };
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
      if (mode === 'in') this.zoomBy(1.45);
      else if (mode === 'out') this.zoomBy(1 / 1.45);
      else if (mode === 'fit') this.resetView();
      else if (mode === 'me' && this._lastArgs) {
        this.focusTable(this._lastArgs.prefs.myBooth, true);
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
      if (this.dragMoved) return;
      const { wx, wy } = this._screenToWorld(e.clientX, e.clientY);
      const hit = hitTestHall(wx, wy, this.boothGroups);
      if (!hit) {
        this.closeInspector();
        return;
      }
      if (hit.type === 'zone') {
        this.focusZone(hit.zone);
        return;
      }
      // On very zoomed-out hall overview on mobile, first tap zooms comfortably to zone + selects booth!
      if (this.zoom < 1.35) {
        this.focusTable(hit.table, true);
      } else {
        this.selectTable(hit.table);
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

  _bindPanZoom() {
    const el = this.canvas;

    el.addEventListener(
      'wheel',
      (e) => {
        e.preventDefault();
        const factor = e.deltaY < 0 ? 1.2 : 1 / 1.2;
        const { wx, wy } = this._screenToWorld(e.clientX, e.clientY);
        this._zoomAtWorld(factor, wx, wy);
      },
      { passive: false }
    );

    el.addEventListener('pointerdown', (e) => {
      this.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (this.pointers.size === 1) {
        this.isDragging = true;
        this.dragMoved = false;
        this.dragStart = { x: e.clientX, y: e.clientY, panX: this.panX, panY: this.panY };
      } else if (this.pointers.size === 2) {
        const pts = Array.from(this.pointers.values());
        this.pinchDist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
        this.pinchZoom = this.zoom;
      }
    });

    window.addEventListener('pointermove', (e) => {
      if (!this.pointers.has(e.pointerId)) return;
      this.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });

      if (this.pointers.size === 2) {
        const pts = Array.from(this.pointers.values());
        const dist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
        if (this.pinchDist > 0) {
          const midX = (pts[0].x + pts[1].x) / 2;
          const midY = (pts[0].y + pts[1].y) / 2;
          const { wx, wy } = this._screenToWorld(midX, midY);
          const nextZoom = Math.max(0.85, Math.min(8, this.pinchZoom * (dist / this.pinchDist)));
          this._zoomAtWorld(nextZoom / this.zoom, wx, wy);
          this.dragMoved = true;
        }
        return;
      }

      if (this.isDragging && this.dragStart) {
        const dx = e.clientX - this.dragStart.x;
        const dy = e.clientY - this.dragStart.y;
        if (Math.hypot(dx, dy) > 4) this.dragMoved = true;
        const { scale } = this._baseFit();
        this.panX = this.dragStart.panX + dx / (scale || 1);
        this.panY = this.dragStart.panY + dy / (scale || 1);
        this._scheduleDraw();
      }
    });

    const endPtr = (e) => {
      this.pointers.delete(e.pointerId);
      if (this.pointers.size === 0) {
        this.isDragging = false;
        setTimeout(() => {
          this.dragMoved = false;
        }, 0);
      }
    };
    window.addEventListener('pointerup', endPtr);
    window.addEventListener('pointercancel', endPtr);
  }

  _zoomAtWorld(factor, wx, wy) {
    const newZoom = Math.max(0.85, Math.min(8, this.zoom * factor));
    // Keep world point (wx, wy) under same screen point
    const screenRelX = this.panX + wx * this.zoom;
    const screenRelY = this.panY + wy * this.zoom;
    this.zoom = newZoom;
    this.panX = screenRelX - wx * this.zoom;
    this.panY = screenRelY - wy * this.zoom;
    this._scheduleDraw();
  }

  zoomBy(factor) {
    const { wx, wy } = this._screenToWorld(
      this.canvas.getBoundingClientRect().left + this.stageW / 2,
      this.canvas.getBoundingClientRect().top + this.stageH / 2
    );
    this._zoomAtWorld(factor, wx, wy);
  }

  resetView() {
    this.activeZone = null;
    this.zoom = 1;
    this.panX = 0;
    this.panY = 0;
    this._updateZonePillsActive();
    this._scheduleDraw();
  }

  focusZone(zoneId) {
    const box = this.zoneBoxes[zoneId];
    if (!box) return;
    this.activeZone = zoneId;
    this._updateZonePillsActive();

    const { scale, oy } = this._baseFit();
    const fitW = this.stageW / ((box.w + 26) * scale);
    const fitH = this.stageH / ((box.h + 26) * scale);
    this.zoom = Math.max(1.2, Math.min(6.5, Math.min(fitW, fitH)));
    const cx = box.x + box.w / 2;
    const cy = box.y + box.h / 2;
    this.panX = HALL_WIDTH / 2 - cx * this.zoom;
    this.panY = (this.stageH * 0.52 - oy) / scale - cy * this.zoom;
    this._scheduleDraw();
  }

  focusTable(tableStr, openInspector = true) {
    const parsed = parseTableCode(tableStr);
    if (!parsed) return;
    this.activeZone = parsed.z;
    this._updateZonePillsActive();

    const { scale, oy } = this._baseFit();
    const r = getBoothRect(parsed.z, parsed.r, parsed.s);
    this.zoom = Math.max(this.zoom, 3.8);
    this.panX = HALL_WIDTH / 2 - r.cx * this.zoom;
    // Place booth in lower half when inspector card is open at top
    const targetYFrac = openInspector ? 0.68 : 0.5;
    this.panY = (this.stageH * targetYFrac - oy) / scale - r.cy * this.zoom;
    if (openInspector && this.boothGroups.has(tableStr)) {
      this.selectTable(tableStr);
    } else {
      this._scheduleDraw();
    }
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
    this._scheduleDraw();
  }

  closeInspector() {
    this.selectedTable = null;
    this.selectedProjectId = null;
    this.inspector.classList.add('hidden');
    this._scheduleDraw();
  }

  sync({ evalById, matched, records, prefs, ui }) {
    this._lastArgs = { evalById, matched, records, prefs, ui };
    const matchedIds = new Set(matched.map((p) => p.id));
    this._matchedIds = matchedIds;

    for (const btn of this.toolbar.querySelectorAll('[data-color]')) {
      btn.classList.toggle('active', btn.dataset.color === (ui.mapColor || 'status'));
    }
    this.toolbar.querySelector('[data-toggle="hideFiltered"]').classList.toggle('active', !!ui.hideFilteredOnMap);
    this.toolbar.querySelector('[data-toggle="hideIgnored"]').classList.toggle('active', !!ui.hideIgnoredOnMap);
    this.toolbar.querySelector('[data-toggle="showRoute"]').classList.toggle('active', !!ui.showRoute);

    // Update zone match counts
    const zMatch = {};
    const zTotal = {};
    for (const z of Object.keys(ZONE_GEOMETRY)) {
      zMatch[z] = 0;
      zTotal[z] = 0;
    }
    for (const p of this.projects) {
      zTotal[p.z] += 1;
      if (matchedIds.has(p.id)) zMatch[p.z] += 1;
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

    // Compute route
    if (ui.showRoute) {
      const todoFavs = matched.filter((p) => records[p.id]?.fav && !records[p.id]?.vis);
      const targets = todoFavs.length ? todoFavs : matched.slice(0, 25);
      this._route = computeWalkingRoute(targets, prefs.myBooth, 25);
    } else {
      this._route = [];
    }

    this._renderLegend(ui.mapColor || 'status', ui.lang);
    this._renderRouteStrip(prefs);
    if (this.selectedTable) this._renderInspector();

    if (!this.stageW || !this.stageH) this._resizeCanvas();
    this._scheduleDraw();
  }

  _scheduleDraw() {
    if (this._rafPending) return;
    this._rafPending = true;
    const raf = typeof requestAnimationFrame === 'function' ? requestAnimationFrame : (fn) => setTimeout(fn, 0);
    raf(() => {
      this._rafPending = false;
      this._draw();
    });
  }

  _draw() {
    if (!this.ctx || !this._lastArgs) return;
    const ctx = this.ctx;
    const { evalById, records, prefs, ui } = this._lastArgs;
    const isLight = ui.theme === 'light';
    const matchedIds = this._matchedIds;
    const myTable = (prefs.myBooth || '').toUpperCase();
    const colorMode = ui.mapColor || 'status';

    ctx.save();
    ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);

    // Clear background
    ctx.fillStyle = isLight ? '#ede9df' : '#111622';
    ctx.fillRect(0, 0, this.stageW, this.stageH);

    // Apply hall fit + pan + zoom
    const { scale, ox, oy } = this._baseFit();
    const totalScale = scale * this.zoom;
    ctx.translate(ox + this.panX * scale, oy + this.panY * scale);
    ctx.scale(totalScale, totalScale);

    // Wing backdrops
    ctx.fillStyle = isLight ? 'rgba(2, 132, 199, 0.04)' : 'rgba(96, 165, 250, 0.035)';
    ctx.strokeStyle = isLight ? '#cbd5e1' : '#263248';
    ctx.lineWidth = 1.2;
    roundRect(ctx, 8, 8, 842, 678, 12);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = isLight ? 'rgba(124, 58, 237, 0.04)' : 'rgba(167, 139, 250, 0.04)';
    roundRect(ctx, 896, 8, 856, 678, 12);
    ctx.fill();
    ctx.stroke();

    // Central spine line
    ctx.save();
    ctx.setLineDash([7, 6]);
    ctx.beginPath();
    ctx.moveTo(873, 18);
    ctx.lineTo(873, 676);
    ctx.stroke();
    ctx.restore();

    // Zone containers & headers
    for (const [zId, g] of Object.entries(ZONE_GEOMETRY)) {
      const box = this.zoneBoxes[zId];
      ctx.fillStyle = isLight ? '#faf9f5' : '#182032';
      ctx.strokeStyle = this.activeZone === zId ? '#38bdf8' : isLight ? '#d6d3c9' : '#2a3750';
      ctx.lineWidth = this.activeZone === zId ? 2 : 1;
      roundRect(ctx, box.x, box.y, box.w, box.h, 8);
      ctx.fill();
      ctx.stroke();

      // Zone header bar
      ctx.fillStyle = isLight ? '#e7e3d8' : '#202b42';
      roundRect(ctx, box.x + 1, box.y + 1, box.w - 2, 23, 7);
      ctx.fill();

      ctx.fillStyle = isLight ? '#0f172a' : '#e6edf3';
      ctx.font = '700 12px "IBM Plex Sans Arabic", sans-serif';
      ctx.textBaseline = 'middle';
      ctx.textAlign = 'left';
      ctx.fillText(zId, box.x + 9, box.y + 13);

      ctx.fillStyle = isLight ? '#475569' : '#9aa8be';
      ctx.font = '600 9.5px "IBM Plex Sans Arabic", sans-serif';
      ctx.fillText(ui.lang === 'ar' ? g.labelAr : g.labelEn, box.x + 24, box.y + 13);

      ctx.fillStyle = isLight ? '#0369a1' : '#7dd3fc';
      ctx.font = '700 10px "IBM Plex Sans Arabic", sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(`${this._zMatch[zId]}/${this._zTotal[zId]}`, box.x + box.w - 9, box.y + 13);

      // Row numbers
      ctx.fillStyle = isLight ? '#64748b' : '#7e8da6';
      ctx.font = '700 8px sans-serif';
      ctx.textAlign = 'center';
      for (let r = 1; r <= g.rows; r++) {
        const fr = getBoothRect(zId, r, 1);
        ctx.fillText(String(r), box.x + 11, fr.cy);
      }
    }

    const showLabels = this.zoom >= 1.75;

    // Draw all 1,241 physical booths
    for (const [tableStr, projs] of this.boothGroups.entries()) {
      const p0 = projs[0];
      const isMe = tableStr === myTable;
      let anyMatches = false;
      let allIgnored = true;
      let anyFav = false;
      let anyVis = false;
      let maxRat = 0;
      let maxScore = 0;
      let primary = p0;

      for (const pr of projs) {
        const ev = evalById.get(pr.id);
        const rec = records[pr.id] || {};
        if (matchedIds.has(pr.id)) {
          anyMatches = true;
          primary = pr;
        }
        if (!ev?.isIgnored) allIgnored = false;
        if (rec.fav) anyFav = true;
        if (rec.vis) anyVis = true;
        if ((rec.rat || 0) > maxRat) maxRat = rec.rat;
        if ((ev?.matchScore || 0) > maxScore) maxScore = ev.matchScore;
      }

      if (allIgnored && ui.hideIgnoredOnMap && !isMe) continue;
      if (!anyMatches && !allIgnored && ui.hideFilteredOnMap && !isMe) continue;

      let alpha = 1;
      if (!anyMatches && !allIgnored && !isMe) alpha = isLight ? 0.22 : 0.16;
      else if (allIgnored && !anyMatches && !isMe) alpha = 0.12;

      let fill = isLight ? '#94a3b8' : '#475569';
      let stroke = null;

      if (isMe) {
        fill = '#9333ea';
        stroke = '#f5d0fe';
      } else if (allIgnored && !anyMatches) {
        fill = isLight ? '#cbd5e1' : '#0f172a';
      } else if (colorMode === 'status') {
        if (anyFav && anyVis) {
          fill = '#0d9488';
          stroke = '#fbbf24';
        } else if (anyFav) {
          fill = '#d97706';
          stroke = '#fde68a';
        } else if (anyVis) {
          fill = '#059669';
        } else if (maxRat > 0) {
          fill = '#7c3aed';
        } else if (maxScore >= 50 && anyMatches) {
          fill = '#0284c7';
        } else if (anyMatches) {
          fill = isLight ? '#64748b' : '#52637d';
        } else {
          fill = isLight ? '#cbd5e1' : '#1f293d';
        }
      } else if (colorMode === 'rating') {
        fill = RATING_COLORS[maxRat] || '#475569';
        if (maxRat >= 4) stroke = '#fef08a';
      } else if (colorMode === 'match') {
        fill = matchColor(maxScore);
      } else if (colorMode === 'cat') {
        fill = CAT_COLORS[primary.cat] || '#64748b';
      } else if (colorMode === 'path') {
        fill = this.pathMap.get(primary.path)?.color || '#64748b';
      }

      ctx.globalAlpha = alpha;
      ctx.fillStyle = fill;
      roundRect(ctx, p0.x, p0.y, 14, 22, 2.5);
      ctx.fill();

      if (stroke) {
        ctx.strokeStyle = stroke;
        ctx.lineWidth = isMe ? 1.8 : 1.1;
        ctx.stroke();
      }

      // Corner pip
      if (isMe || anyFav || anyVis || projs.length > 1) {
        ctx.fillStyle = isMe ? '#ffffff' : anyFav ? '#fef08a' : anyVis ? '#a7f3d0' : '#f472b6';
        ctx.beginPath();
        ctx.arc(p0.x + 11.4, p0.y + 2.8, 1.9, 0, Math.PI * 2);
        ctx.fill();
      }

      // Seat number & badge when zoomed in
      if (showLabels && alpha > 0.15) {
        ctx.fillStyle = '#ffffff';
        ctx.font = '700 6.2px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(String(p0.s), p0.cx, p0.cy - (maxRat || anyFav || anyVis || isMe ? 2 : 0));

        const sub = isMe ? 'ME' : maxRat ? `${maxRat}★` : anyFav ? '★' : anyVis ? '✓' : projs.length > 1 ? `×${projs.length}` : '';
        if (sub) {
          ctx.fillStyle = '#fef08a';
          ctx.font = '700 4.8px sans-serif';
          ctx.fillText(sub, p0.cx, p0.y + 18.2);
        }
      }

      // Cross on ignored booths
      if (allIgnored && !anyMatches && !isMe) {
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 1.1;
        ctx.beginPath();
        ctx.moveTo(p0.x + 2.5, p0.y + 3);
        ctx.lineTo(p0.x + 11.5, p0.y + 19);
        ctx.moveTo(p0.x + 11.5, p0.y + 3);
        ctx.lineTo(p0.x + 2.5, p0.y + 19);
        ctx.stroke();
      }
    }

    ctx.globalAlpha = 1;

    // Walking route overlay
    if (ui.showRoute && this._route.length) {
      const myParsed = parseTableCode(myTable);
      const start = myParsed ? getBoothRect(myParsed.z, myParsed.r, myParsed.s) : this._route[0];

      ctx.save();
      ctx.strokeStyle = '#f59e0b';
      ctx.lineWidth = 2.4;
      ctx.setLineDash([6, 4]);
      ctx.beginPath();
      ctx.moveTo(start.cx, start.cy);
      for (const stop of this._route) ctx.lineTo(stop.cx, stop.cy);
      ctx.stroke();
      ctx.restore();

      this._route.forEach((stop, idx) => {
        ctx.fillStyle = '#f59e0b';
        ctx.strokeStyle = '#0f172a';
        ctx.lineWidth = 1.1;
        ctx.beginPath();
        ctx.arc(stop.cx, stop.cy - 8, 6.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = '#0f172a';
        ctx.font = '800 7px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(String(idx + 1), stop.cx, stop.cy - 8);
      });
    }

    // My Booth halo & Selected Booth ring
    const myParsed = parseTableCode(myTable);
    if (myParsed) {
      const mr = getBoothRect(myParsed.z, myParsed.r, myParsed.s);
      ctx.strokeStyle = '#d946ef';
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.arc(mr.cx, mr.cy, 13, 0, Math.PI * 2);
      ctx.stroke();
    }

    if (this.selectedTable) {
      const sp = parseTableCode(this.selectedTable);
      if (sp) {
        const sr = getBoothRect(sp.z, sp.r, sp.s);
        ctx.strokeStyle = isLight ? '#0f172a' : '#ffffff';
        ctx.lineWidth = 2.4;
        roundRect(ctx, sr.x - 2.5, sr.y - 2.5, 19, 27, 4);
        ctx.stroke();
      }
    }

    ctx.restore();
  }

  _renderRouteStrip(prefs) {
    this.routeStrip.innerHTML = '';
    if (!this._route.length) {
      this.routeStrip.classList.add('hidden');
      return;
    }
    this.routeStrip.classList.remove('hidden');
    const startPill = document.createElement('button');
    startPill.className = 'route-pill start';
    startPill.dataset.routeTable = prefs.myBooth;
    startPill.textContent = `📍 ${prefs.myBooth}`;
    this.routeStrip.appendChild(startPill);

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
        ['#9333ea', '📍'],
        ['#d97706', '★'],
        ['#059669', '✓'],
        ['#0d9488', '★+✓'],
        ['#7c3aed', '⭐'],
        ['#0284c7', '⚡50+'],
      ],
      rating: [
        ['#059669', '5★'],
        ['#65a30d', '4★'],
        ['#ca8a04', '3★'],
        ['#ea580c', '2★'],
        ['#dc2626', '1★'],
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
      path: this.meta.paths.slice(0, 6).map((p) => [p.color, p.icon]),
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
          `<button class="star-btn ${(rec.rat || 0) >= s ? 'on' : ''}" data-insp-action="rat" data-id="${p.id}" data-stars="${s}">★</button>`
      )
      .join('');

    const tagsHtml = CUSTOM_TAGS.map(
      (t) =>
        `<button class="tag-pill ${(rec.tags || []).includes(t.id) ? 'on' : ''}" data-insp-action="tag" data-id="${p.id}" data-tag="${t.id}">${t.icon}</button>`
    ).join('');

    this.inspector.innerHTML = `
      ${switcher}
      <div class="insp-head">
        <span class="badge-table">${p.table}</span>
        <span class="badge-cat c${p.cat}">${ui.lang === 'ar' ? catObj?.ar : catObj?.en}</span>
        <span class="badge-path p${p.path}">${pathObj?.icon} ${ui.lang === 'ar' ? pathObj?.ar : pathObj?.en}</span>
        <span class="badge-mini">${flags} ×${p.members.length}</span>
        <span class="badge-match">⚡${ev.matchScore ?? 0}</span>
        <button class="insp-close" data-insp-action="close">✕</button>
      </div>
      <div class="insp-title" data-insp-action="open" data-id="${p.id}">${escapeHtml(p.title)}</div>
      <div class="insp-actions">
        <button class="act-btn fav ${rec.fav ? 'on' : ''}" data-insp-action="fav" data-id="${p.id}">${rec.fav ? '★' : '☆'}</button>
        <button class="act-btn vis ${rec.vis ? 'on' : ''}" data-insp-action="vis" data-id="${p.id}">✓</button>
        <div class="stars-row">${stars}</div>
        <button class="act-btn ign ${rec.ign ? 'on' : ''}" data-insp-action="ign" data-id="${p.id}">🚫</button>
        <button class="act-btn open" data-insp-action="open" data-id="${p.id}">⤢</button>
      </div>
      <div class="insp-tags">${tagsHtml}</div>
      <input class="insp-note" type="text" data-insp-note="${p.id}" value="${escapeHtml(rec.note || '')}" placeholder="📝 LinkedIn / @ / ..." />
    `;
    this.inspector.classList.remove('hidden');
  }
}
