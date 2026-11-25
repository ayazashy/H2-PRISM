import {
  CUSTOM_TAGS,
  HALL_HEIGHT,
  HALL_WIDTH,
  ZONE_GEOMETRY,
  computeWalkingRoute,
  getBoothRect,
  getZoneBox,
  parseTableCode,
} from './logic.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

const CAT_COLORS = {
  1: '#fb7185',
  2: '#38bdf8',
  3: '#818cf8',
  4: '#f59e0b',
};

const RATING_COLORS = {
  0: '#334155',
  1: '#ef4444',
  2: '#f97316',
  3: '#eab308',
  4: '#84cc16',
  5: '#10b981',
};

function el(tag, attrs = {}, parent = null) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v !== undefined && v !== null) node.setAttribute(k, String(v));
  }
  if (parent) parent.appendChild(node);
  return node;
}

function matchColor(score) {
  if (score >= 80) return '#10b981';
  if (score >= 60) return '#06b6d4';
  if (score >= 40) return '#6366f1';
  if (score >= 20) return '#64748b';
  return '#334155';
}

export class FairMapController {
  constructor(container, { meta, projects, onSelectProject, onAction }) {
    this.container = container;
    this.meta = meta;
    this.projects = projects;
    this.onSelectProject = onSelectProject;
    this.onAction = onAction;

    this.pathMap = new Map(meta.paths.map((p) => [p.id, p]));
    this.boothGroups = new Map(); // tableStr -> project[]
    for (const p of projects) {
      if (!this.boothGroups.has(p.table)) this.boothGroups.set(p.table, []);
      this.boothGroups.get(p.table).push(p);
    }

    this.boothNodes = new Map(); // tableStr -> { g, rect, pip, label, cross, projects }
    this.zoneHeaders = new Map(); // zoneId -> { statText, favText, box }
    this.selectedTable = null;
    this.selectedProjectId = null;

    // Viewport pan/zoom state (in SVG user units)
    this.zoom = 1;
    this.panX = 0;
    this.panY = 0;
    this.isDragging = false;
    this.dragMoved = false;
    this.pointers = new Map();
    this.pinchStartDist = 0;
    this.pinchStartZoom = 1;

    this._lastArgs = null;
    this._buildDOM();
    this._bindPanZoom();
  }

  _buildDOM() {
    this.container.innerHTML = '';

    // 1. Compact Map Toolbar
    this.toolbar = document.createElement('div');
    this.toolbar.className = 'map-toolbar';
    this.toolbar.innerHTML = `
      <div class="map-seg" data-role="color-modes">
        <button data-color="status" class="active">●</button>
        <button data-color="rating">★</button>
        <button data-color="match">⚡</button>
        <button data-color="cat">👥</button>
        <button data-color="path">🧭</button>
      </div>
      <div class="map-toggles">
        <button class="chip-btn" data-toggle="hideFiltered">👁️‍🗨️</button>
        <button class="chip-btn" data-toggle="hideIgnored">🚫</button>
        <button class="chip-btn" data-toggle="showRoute">〰️</button>
      </div>
      <div class="map-zoom-btns">
        <button data-zoom="in">+</button>
        <button data-zoom="out">−</button>
        <button data-zoom="fit">⊡</button>
        <button data-zoom="me">📍</button>
      </div>
    `;
    this.container.appendChild(this.toolbar);

    // Zone jumper strip
    this.zoneStrip = document.createElement('div');
    this.zoneStrip.className = 'map-zone-strip';
    for (const z of Object.keys(ZONE_GEOMETRY)) {
      const b = document.createElement('button');
      b.className = 'zjump-btn';
      b.dataset.zjump = z;
      b.textContent = z;
      this.zoneStrip.appendChild(b);
    }
    this.container.appendChild(this.zoneStrip);

    // 2. Main Interactive SVG Canvas Wrapper
    this.stage = document.createElement('div');
    this.stage.className = 'map-stage';
    this.svg = el('svg', {
      viewBox: `0 0 ${HALL_WIDTH} ${HALL_HEIGHT}`,
      class: 'hall-svg',
      preserveAspectRatio: 'xMidYMid meet',
    });

    // Defs for glow / pulse
    const defs = el('defs', {}, this.svg);
    const filter = el('filter', { id: 'me-glow', x: '-60%', y: '-60%', width: '220%', height: '220%' }, defs);
    el('feGaussianBlur', { stdDeviation: '3.5', result: 'blur' }, filter);
    const merge = el('feMerge', {}, filter);
    el('feMergeNode', { in: 'blur' }, merge);
    el('feMergeNode', { in: 'SourceGraphic' }, merge);

    this.viewport = el('g', { class: 'map-viewport' }, this.svg);

    // Hall Wings architectural backdrops
    el('rect', { x: 8, y: 8, width: 842, height: 678, rx: 14, class: 'wing-bg wing-youth' }, this.viewport);
    el('rect', { x: 896, y: 8, width: 856, height: 678, rx: 14, class: 'wing-bg wing-pro' }, this.viewport);
    // Central Concourse Spine
    el('line', { x1: 873, y1: 18, x2: 873, y2: 676, class: 'corridor-line' }, this.viewport);

    // Render Zones A..K
    for (const [zId, g] of Object.entries(ZONE_GEOMETRY)) {
      const box = getZoneBox(zId);
      const zGroup = el('g', { class: 'zone-group', 'data-zone': zId }, this.viewport);

      el('rect', {
        x: box.x,
        y: box.y,
        width: box.w,
        height: box.h,
        rx: 9,
        class: 'zone-card',
      }, zGroup);

      // Clickable Zone Header Bar
      const hdr = el('g', { class: 'zone-header', 'data-zone-focus': zId }, zGroup);
      el('rect', {
        x: box.x + 1,
        y: box.y + 1,
        width: box.w - 2,
        height: 23,
        rx: 8,
        class: 'zone-hdr-bg',
      }, hdr);

      const titleTxt = el('text', {
        x: box.x + 10,
        y: box.y + 16,
        class: 'zone-title-txt',
      }, hdr);
      titleTxt.textContent = zId;

      const subTxt = el('text', {
        x: box.x + 26,
        y: box.y + 16,
        class: 'zone-sub-txt',
      }, hdr);
      subTxt.textContent = g.labelEn;

      const statTxt = el('text', {
        x: box.x + box.w - 10,
        y: box.y + 16,
        'text-anchor': 'end',
        class: 'zone-stat-txt',
      }, hdr);

      this.zoneHeaders.set(zId, { titleTxt, subTxt, statTxt, box });

      // Row numbers R1..Rn + missing slot indicators
      for (let r = 1; r <= g.rows; r++) {
        const firstRect = getBoothRect(zId, r, 1);
        const rTxt = el('text', {
          x: box.x + 11,
          y: firstRect.cy + 3.5,
          'text-anchor': 'middle',
          class: 'row-lbl',
        }, zGroup);
        rTxt.textContent = r;

        const maxCols = zId === 'E' && r >= 3 ? 18 : zId === 'K' ? [12, 12, 13, 7][r - 1] : g.cols;
        for (let s = 1; s <= maxCols; s++) {
          const tableStr = `S-${zId}${r}-${String(s).padStart(2, '0')}`;
          const projs = this.boothGroups.get(tableStr);
          const bRect = getBoothRect(zId, r, s);
          if (!projs) {
            // Physical empty gap slot
            el('rect', {
              x: bRect.x,
              y: bRect.y,
              width: bRect.w,
              height: bRect.h,
              rx: 2.5,
              class: 'booth-empty',
            }, zGroup);
            continue;
          }

          const bg = el('g', {
            class: 'booth-node',
            'data-table': tableStr,
          }, zGroup);

          const rect = el('rect', {
            x: bRect.x,
            y: bRect.y,
            width: bRect.w,
            height: bRect.h,
            rx: 2.5,
            class: 'booth-rect',
          }, bg);

          // Tiny corner indicator dot (star / check / multi-team / me)
          const pip = el('circle', {
            cx: bRect.x + bRect.w - 2.6,
            cy: bRect.y + 2.6,
            r: 2,
            class: 'booth-pip',
          }, bg);

          // Semantic zoom seat number
          const label = el('text', {
            x: bRect.cx,
            y: bRect.cy + 2.5,
            'text-anchor': 'middle',
            class: 'booth-num',
          }, bg);
          label.textContent = String(s);

          // Mini rating / status tag when zoomed
          const subLabel = el('text', {
            x: bRect.cx,
            y: bRect.y + bRect.h - 2,
            'text-anchor': 'middle',
            class: 'booth-sub',
          }, bg);

          // Diagonal X for ignored booths
          const cross = el('path', {
            d: `M${bRect.x + 2} ${bRect.y + 2} L${bRect.x + bRect.w - 2} ${bRect.y + bRect.h - 2} M${bRect.x + bRect.w - 2} ${bRect.y + 2} L${bRect.x + 2} ${bRect.y + bRect.h - 2}`,
            class: 'booth-cross',
          }, bg);

          this.boothNodes.set(tableStr, {
            g: bg,
            rect,
            pip,
            label,
            subLabel,
            cross,
            bRect,
            projects: projs,
          });
        }
      }
    }

    // Route overlay layer (above booths)
    this.routeLayer = el('g', { class: 'route-layer' }, this.viewport);
    // Selection & My-Booth rings layer
    this.markerLayer = el('g', { class: 'marker-layer' }, this.viewport);

    this.stage.appendChild(this.svg);

    // Floating Tooltip (desktop hover)
    this.tooltip = document.createElement('div');
    this.tooltip.className = 'map-tooltip hidden';
    this.stage.appendChild(this.tooltip);

    // Floating Legend Strip
    this.legend = document.createElement('div');
    this.legend.className = 'map-legend';
    this.stage.appendChild(this.legend);

    // Floating Booth Inspector Drawer inside map
    this.inspector = document.createElement('div');
    this.inspector.className = 'map-inspector hidden';
    this.stage.appendChild(this.inspector);

    this.container.appendChild(this.stage);

    // 3. Walking Route Strip (shown only when Show Route is ON)
    this.routeStrip = document.createElement('div');
    this.routeStrip.className = 'map-route-strip hidden';
    this.container.appendChild(this.routeStrip);

    this._bindEvents();
  }

  _bindEvents() {
    this.toolbar.addEventListener('click', (e) => {
      const colorBtn = e.target.closest('[data-color]');
      if (colorBtn) {
        this.onAction('mapColor', colorBtn.dataset.color);
        return;
      }
      const toggleBtn = e.target.closest('[data-toggle]');
      if (toggleBtn) {
        this.onAction('toggleMapOpt', toggleBtn.dataset.toggle);
        return;
      }
      const zBtn = e.target.closest('[data-zoom]');
      if (zBtn) {
        const mode = zBtn.dataset.zoom;
        if (mode === 'in') this.zoomBy(1.4);
        else if (mode === 'out') this.zoomBy(1 / 1.4);
        else if (mode === 'fit') this.resetView();
        else if (mode === 'me' && this._lastArgs) {
          this.focusTable(this._lastArgs.prefs.myBooth, true);
        }
      }
    });

    this.zoneStrip.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-zjump]');
      if (!btn) return;
      this.focusZone(btn.dataset.zjump);
    });

    this.svg.addEventListener('click', (e) => {
      if (this.dragMoved) return;
      const zHdr = e.target.closest('[data-zone-focus]');
      if (zHdr) {
        this.focusZone(zHdr.dataset.zoneFocus);
        return;
      }
      const bNode = e.target.closest('[data-table]');
      if (bNode) {
        const table = bNode.dataset.table;
        this.selectTable(table);
      } else {
        this.closeInspector();
      }
    });

    this.svg.addEventListener('pointermove', (e) => {
      if (this.isDragging) return;
      const bNode = e.target.closest('[data-table]');
      if (!bNode) {
        this.tooltip.classList.add('hidden');
        return;
      }
      const table = bNode.dataset.table;
      const node = this.boothNodes.get(table);
      if (!node || !this._lastArgs) return;
      this._showTooltip(e, table, node.projects);
    });

    this.svg.addEventListener('pointerleave', () => {
      this.tooltip.classList.add('hidden');
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
      } else if (act === 'open') {
        this.onSelectProject(id);
      } else if (act === 'fav') this.onAction('fav', id);
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
      if (!btn) return;
      this.focusTable(btn.dataset.routeTable, true);
    });
  }

  _bindPanZoom() {
    const stage = this.stage;

    const getSvgPoint = (clientX, clientY) => {
      const rect = this.svg.getBoundingClientRect();
      // Account for preserveAspectRatio="xMidYMid meet"
      const scale = Math.min(rect.width / HALL_WIDTH, rect.height / HALL_HEIGHT);
      const offsetX = (rect.width - HALL_WIDTH * scale) / 2;
      const offsetY = (rect.height - HALL_HEIGHT * scale) / 2;
      return {
        x: (clientX - rect.left - offsetX) / scale,
        y: (clientY - rect.top - offsetY) / scale,
      };
    };

    stage.addEventListener(
      'wheel',
      (e) => {
        e.preventDefault();
        const factor = e.deltaY < 0 ? 1.18 : 1 / 1.18;
        const pt = getSvgPoint(e.clientX, e.clientY);
        this.zoomAt(factor, pt.x, pt.y);
      },
      { passive: false }
    );

    stage.addEventListener('pointerdown', (e) => {
      if (e.target.closest('.map-inspector') || e.target.closest('.map-legend')) return;
      this.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (this.pointers.size === 1) {
        this.isDragging = true;
        this.dragMoved = false;
        this.dragStart = { x: e.clientX, y: e.clientY, panX: this.panX, panY: this.panY };
      } else if (this.pointers.size === 2) {
        const pts = Array.from(this.pointers.values());
        this.pinchStartDist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
        this.pinchStartZoom = this.zoom;
      }
    });

    window.addEventListener('pointermove', (e) => {
      if (!this.pointers.has(e.pointerId)) return;
      this.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });

      if (this.pointers.size === 2) {
        const pts = Array.from(this.pointers.values());
        const dist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y);
        if (this.pinchStartDist > 0) {
          const midX = (pts[0].x + pts[1].x) / 2;
          const midY = (pts[0].y + pts[1].y) / 2;
          const svgPt = getSvgPoint(midX, midY);
          const targetZoom = Math.max(0.85, Math.min(8, this.pinchStartZoom * (dist / this.pinchStartDist)));
          this.zoomAt(targetZoom / this.zoom, svgPt.x, svgPt.y);
          this.dragMoved = true;
        }
        return;
      }

      if (this.isDragging && this.dragStart) {
        const dx = e.clientX - this.dragStart.x;
        const dy = e.clientY - this.dragStart.y;
        if (Math.hypot(dx, dy) > 4) this.dragMoved = true;
        const rect = this.svg.getBoundingClientRect();
        const scale = Math.min(rect.width / HALL_WIDTH, rect.height / HALL_HEIGHT) || 1;
        this.panX = this.dragStart.panX + dx / scale;
        this.panY = this.dragStart.panY + dy / scale;
        this._applyTransform();
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

  zoomAt(factor, svgX, svgY) {
    const newZoom = Math.max(0.85, Math.min(8, this.zoom * factor));
    const ratio = newZoom / this.zoom;
    this.panX = svgX - (svgX - this.panX) * ratio;
    this.panY = svgY - (svgY - this.panY) * ratio;
    this.zoom = newZoom;
    this._applyTransform();
  }

  zoomBy(factor) {
    this.zoomAt(factor, HALL_WIDTH / 2, HALL_HEIGHT / 2);
  }

  resetView() {
    this.zoom = 1;
    this.panX = 0;
    this.panY = 0;
    this._applyTransform();
  }

  focusZone(zoneId) {
    const box = getZoneBox(zoneId);
    if (!box.w) return;
    const pad = 26;
    const scaleX = HALL_WIDTH / (box.w + pad * 2);
    const scaleY = HALL_HEIGHT / (box.h + pad * 2);
    this.zoom = Math.max(1.2, Math.min(5.5, Math.min(scaleX, scaleY)));
    const cx = box.x + box.w / 2;
    const cy = box.y + box.h / 2;
    this.panX = HALL_WIDTH / 2 - cx * this.zoom;
    this.panY = HALL_HEIGHT / 2 - cy * this.zoom;
    this._applyTransform();
  }

  focusTable(tableStr, openInspector = true) {
    const parsed = parseTableCode(tableStr);
    if (!parsed) return;
    const r = getBoothRect(parsed.z, parsed.r, parsed.s);
    this.zoom = Math.max(this.zoom, 3.6);
    this.panX = HALL_WIDTH / 2 - r.cx * this.zoom;
    this.panY = HALL_HEIGHT / 2 - r.cy * this.zoom;
    this._applyTransform();
    if (openInspector && this.boothNodes.has(tableStr)) {
      this.selectTable(tableStr);
    }
  }

  _applyTransform() {
    this.viewport.setAttribute(
      'transform',
      `translate(${this.panX.toFixed(2)} ${this.panY.toFixed(2)}) scale(${this.zoom.toFixed(3)})`
    );
    this.svg.classList.toggle('map-zoomed', this.zoom >= 1.85);
  }

  selectTable(tableStr) {
    this.selectedTable = tableStr;
    const node = this.boothNodes.get(tableStr);
    if (node) {
      this.selectedProjectId = node.projects[0].id;
    }
    this._renderSelectionRings();
    this._renderInspector();
  }

  closeInspector() {
    this.selectedTable = null;
    this.selectedProjectId = null;
    this.inspector.classList.add('hidden');
    this._renderSelectionRings();
  }

  _showTooltip(e, table, projects) {
    const { evalById, records, ui } = this._lastArgs;
    const p = projects[0];
    const ev = evalById.get(p.id);
    const rec = records[p.id] || {};
    const pathObj = this.pathMap.get(p.path);
    const stageRect = this.stage.getBoundingClientRect();
    const x = Math.min(stageRect.width - 230, Math.max(8, e.clientX - stageRect.left + 12));
    const y = Math.min(stageRect.height - 90, Math.max(8, e.clientY - stageRect.top + 12));

    this.tooltip.style.left = `${x}px`;
    this.tooltip.style.top = `${y}px`;
    this.tooltip.innerHTML = `
      <div class="tt-top">
        <span class="badge-table">${table}</span>
        ${projects.length > 1 ? `<span class="badge-mini">×${projects.length}</span>` : ''}
        <span class="badge-mini">⚡${ev?.matchScore ?? 0}</span>
        ${rec.rat ? `<span class="badge-mini">★${rec.rat}</span>` : ''}
        ${rec.fav ? '<span>⭐</span>' : ''}
        ${rec.vis ? '<span>✅</span>' : ''}
        ${ev?.isIgnored ? '<span>🚫</span>' : ''}
      </div>
      <div class="tt-title">${projects.map((pr) => this._escape(pr.title)).join(' · ')}</div>
      <div class="tt-sub">${pathObj?.icon || ''} ${ui.lang === 'ar' ? pathObj?.ar : pathObj?.en}</div>
    `;
    this.tooltip.classList.remove('hidden');
  }

  _escape(s) {
    return String(s || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /**
   * Synchronize every single booth, zone header, legend, and walking route
   * with the current live evaluation results (100% mirrored with list & filters).
   */
  sync({ evalById, matched, records, prefs, ui }) {
    this._lastArgs = { evalById, matched, records, prefs, ui };
    const matchedIds = new Set(matched.map((p) => p.id));
    const myTable = (prefs.myBooth || '').toUpperCase();
    const colorMode = ui.mapColor || 'status';

    // Update toolbar button states
    for (const btn of this.toolbar.querySelectorAll('[data-color]')) {
      btn.classList.toggle('active', btn.dataset.color === colorMode);
    }
    this.toolbar.querySelector('[data-toggle="hideFiltered"]').classList.toggle('active', !!ui.hideFilteredOnMap);
    this.toolbar.querySelector('[data-toggle="hideIgnored"]').classList.toggle('active', !!ui.hideIgnoredOnMap);
    this.toolbar.querySelector('[data-toggle="showRoute"]').classList.toggle('active', !!ui.showRoute);

    // Zone summaries
    const zoneMatchCounts = {};
    const zoneTotals = {};
    for (const z of Object.keys(ZONE_GEOMETRY)) {
      zoneMatchCounts[z] = 0;
      zoneTotals[z] = 0;
    }

    for (const p of this.projects) {
      zoneTotals[p.z] = (zoneTotals[p.z] || 0) + 1;
      if (matchedIds.has(p.id)) zoneMatchCounts[p.z] = (zoneMatchCounts[p.z] || 0) + 1;
    }

    for (const [zId, hdr] of this.zoneHeaders.entries()) {
      const mCnt = zoneMatchCounts[zId] || 0;
      const tCnt = zoneTotals[zId] || 0;
      hdr.statTxt.textContent = `${mCnt}/${tCnt}`;
      hdr.subTxt.textContent = ui.lang === 'ar' ? ZONE_GEOMETRY[zId].labelAr : ZONE_GEOMETRY[zId].labelEn;
      const zBtn = this.zoneStrip.querySelector(`[data-zjump="${zId}"]`);
      if (zBtn) {
        zBtn.classList.toggle('has-matches', mCnt > 0);
        zBtn.innerHTML = `${zId}<sub>${mCnt}</sub>`;
      }
    }

    // Update every booth tile
    for (const [tableStr, node] of this.boothNodes.entries()) {
      const projs = node.projects;
      const isMe = tableStr === myTable;
      // Aggregate state across projects at this table (normally 1, or 2 at S-E5-09)
      const evals = projs.map((p) => ({ p, ev: evalById.get(p.id), rec: records[p.id] || {} }));
      const anyMatches = evals.some((x) => matchedIds.has(x.p.id));
      const allIgnored = evals.every((x) => x.ev?.isIgnored);
      const anyFav = evals.some((x) => x.rec.fav);
      const anyVis = evals.some((x) => x.rec.vis);
      const maxRat = Math.max(0, ...evals.map((x) => x.rec.rat || 0));
      const maxScore = Math.max(0, ...evals.map((x) => x.ev?.matchScore || 0));
      const primary = evals.find((x) => matchedIds.has(x.p.id)) || evals[0];

      // Visibility rules
      let hidden = false;
      if (allIgnored && ui.hideIgnoredOnMap && !isMe) hidden = true;
      else if (!anyMatches && !allIgnored && ui.hideFilteredOnMap && !isMe) hidden = true;

      node.g.classList.toggle('booth-hidden', hidden);
      node.g.classList.toggle('booth-dimmed', !anyMatches && !allIgnored && !isMe);
      node.g.classList.toggle('booth-ignored', allIgnored && !anyMatches && !isMe);
      node.g.classList.toggle('booth-me', isMe);

      // Determine fill & stroke by Color Mode
      let fill = '#475569';
      let stroke = 'transparent';
      let strokeW = '0.8';

      if (isMe) {
        fill = '#a855f7';
        stroke = '#f5d0fe';
        strokeW = '1.8';
      } else if (allIgnored && !anyMatches) {
        fill = '#0f172a';
      } else if (colorMode === 'status') {
        if (anyFav && anyVis) {
          fill = '#14b8a6';
          stroke = '#fbbf24';
          strokeW = '1.3';
        } else if (anyFav) {
          fill = '#f59e0b';
          stroke = '#fef3c7';
          strokeW = '1.1';
        } else if (anyVis) {
          fill = '#10b981';
        } else if (maxRat > 0) {
          fill = '#8b5cf6';
        } else if (maxScore >= 50 && anyMatches) {
          fill = '#38bdf8';
        } else if (anyMatches) {
          fill = '#64748b';
        } else {
          fill = '#1e293b';
        }
      } else if (colorMode === 'rating') {
        fill = RATING_COLORS[maxRat] || '#334155';
        if (maxRat >= 4) stroke = '#fef08a';
      } else if (colorMode === 'match') {
        fill = matchColor(maxScore);
      } else if (colorMode === 'cat') {
        fill = CAT_COLORS[primary.p.cat] || '#64748b';
      } else if (colorMode === 'path') {
        fill = this.pathMap.get(primary.p.path)?.color || '#64748b';
      }

      node.rect.setAttribute('fill', fill);
      node.rect.setAttribute('stroke', stroke);
      node.rect.setAttribute('stroke-width', strokeW);

      // Corner indicator pip
      let pipFill = 'none';
      if (isMe) pipFill = '#ffffff';
      else if (anyFav) pipFill = '#fef08a';
      else if (anyVis) pipFill = '#a7f3d0';
      else if (projs.length > 1) pipFill = '#f472b6';
      node.pip.setAttribute('fill', pipFill);

      // Semantic subLabel when zoomed
      if (isMe) node.subLabel.textContent = 'ME';
      else if (maxRat > 0) node.subLabel.textContent = `${maxRat}★`;
      else if (anyFav) node.subLabel.textContent = '★';
      else if (anyVis) node.subLabel.textContent = '✓';
      else if (projs.length > 1) node.subLabel.textContent = `×${projs.length}`;
      else node.subLabel.textContent = '';

      node.cross.style.display = allIgnored && !anyMatches ? 'block' : 'none';
    }

    this._renderLegend(colorMode, ui.lang);
    this._renderSelectionRings();
    this._renderRoute(matched, records, prefs, ui);
    if (this.selectedTable) this._renderInspector();
  }

  _renderSelectionRings() {
    this.markerLayer.innerHTML = '';
    const myTable = (this._lastArgs?.prefs?.myBooth || '').toUpperCase();
    const myParsed = parseTableCode(myTable);
    if (myParsed) {
      const r = getBoothRect(myParsed.z, myParsed.r, myParsed.s);
      el('circle', {
        cx: r.cx,
        cy: r.cy,
        r: 13,
        class: 'me-pulse-ring',
        filter: 'url(#me-glow)',
      }, this.markerLayer);
    }

    if (this.selectedTable) {
      const p = parseTableCode(this.selectedTable);
      if (p) {
        const r = getBoothRect(p.z, p.r, p.s);
        el('rect', {
          x: r.x - 3,
          y: r.y - 3,
          width: r.w + 6,
          height: r.h + 6,
          rx: 4,
          class: 'selected-ring',
        }, this.markerLayer);
      }
    }
  }

  _renderRoute(matched, records, prefs, ui) {
    this.routeLayer.innerHTML = '';
    this.routeStrip.innerHTML = '';
    if (!ui.showRoute) {
      this.routeStrip.classList.add('hidden');
      return;
    }

    // Prefer starred unvisited projects within active filter; fallback to top matched
    const todoFavs = matched.filter((p) => records[p.id]?.fav && !records[p.id]?.vis);
    const targets = todoFavs.length > 0 ? todoFavs : matched.slice(0, 25);
    const route = computeWalkingRoute(targets, prefs.myBooth, 25);

    if (!route.length) {
      this.routeStrip.classList.add('hidden');
      return;
    }

    const myParsed = parseTableCode(prefs.myBooth);
    const startPt = myParsed ? getBoothRect(myParsed.z, myParsed.r, myParsed.s) : route[0];
    const pts = [`${startPt.cx},${startPt.cy}`, ...route.map((p) => `${p.cx},${p.cy}`)].join(' ');

    el('polyline', { points: pts, class: 'route-line' }, this.routeLayer);

    route.forEach((p, idx) => {
      const g = el('g', { class: 'route-pin' }, this.routeLayer);
      el('circle', { cx: p.cx, cy: p.cy - 9, r: 6.5, class: 'route-dot' }, g);
      const t = el('text', { x: p.cx, y: p.cy - 6.5, 'text-anchor': 'middle', class: 'route-num' }, g);
      t.textContent = String(idx + 1);
    });

    this.routeStrip.classList.remove('hidden');
    const startPill = document.createElement('button');
    startPill.className = 'route-pill start';
    startPill.dataset.routeTable = prefs.myBooth;
    startPill.textContent = `📍 ${prefs.myBooth}`;
    this.routeStrip.appendChild(startPill);

    route.forEach((p, idx) => {
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
        ['#a855f7', '📍'],
        ['#f59e0b', '★'],
        ['#10b981', '✓'],
        ['#14b8a6', '★+✓'],
        ['#8b5cf6', '⭐1-5'],
        ['#38bdf8', '⚡50+'],
        ['#0f172a', '🚫'],
      ],
      rating: [
        ['#10b981', '5★'],
        ['#84cc16', '4★'],
        ['#eab308', '3★'],
        ['#f97316', '2★'],
        ['#ef4444', '1★'],
        ['#334155', '0★'],
      ],
      match: [
        ['#10b981', '80+'],
        ['#06b6d4', '60+'],
        ['#6366f1', '40+'],
        ['#64748b', '20+'],
      ],
      cat: [
        ['#f59e0b', lang === 'ar' ? 'رواد 18+' : '18+Pro'],
        ['#818cf8', lang === 'ar' ? 'جامعي 18+' : '18+Uni'],
        ['#38bdf8', '12-17'],
        ['#fb7185', '6-11'],
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
    const node = this.boothNodes.get(this.selectedTable);
    if (!node) return;
    const { evalById, records, ui } = this._lastArgs;
    const projs = node.projects;
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
        <span class="badge-path" style="--pc:${pathObj?.color}">${pathObj?.icon} ${ui.lang === 'ar' ? pathObj?.ar : pathObj?.en}</span>
        <span class="badge-mini">${flags} ×${p.members.length}</span>
        <span class="badge-match">⚡${ev.matchScore ?? 0}</span>
        <button class="insp-close" data-insp-action="close">✕</button>
      </div>
      <div class="insp-title" data-insp-action="open" data-id="${p.id}">${this._escape(p.title)}</div>
      <div class="insp-actions">
        <button class="act-btn fav ${rec.fav ? 'on' : ''}" data-insp-action="fav" data-id="${p.id}">${rec.fav ? '★' : '☆'}</button>
        <button class="act-btn vis ${rec.vis ? 'on' : ''}" data-insp-action="vis" data-id="${p.id}">✓</button>
        <div class="stars-row">${stars}</div>
        <button class="act-btn ign ${rec.ign ? 'on' : ''}" data-insp-action="ign" data-id="${p.id}">🚫</button>
        <button class="act-btn open" data-insp-action="open" data-id="${p.id}">⤢</button>
      </div>
      <div class="insp-tags">${tagsHtml}</div>
      <input class="insp-note" type="text" data-insp-note="${p.id}" value="${this._escape(rec.note || '')}" placeholder="📝 LinkedIn / @ / ..." />
    `;
    this.inspector.classList.remove('hidden');
  }
}
