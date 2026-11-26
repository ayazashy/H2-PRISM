import { ico, initIconSprite } from './icons.js';
import {
  CUSTOM_TAGS,
  ZONE_GEOMETRY,
  buildEvalContext,
  countActiveFilterRules,
  evaluateAll,
  evaluateProjectFast,
  prepareProjects,
  sortMatched,
} from './logic.js';
import { FairMapController } from './map.js';
import { TrackerStore } from './store.js';

const PAGE_SIZE = 15;

const UI_TEXT = {
  ar: {
    searchPh: 'بحث: مشروع، مشارك (عربي أو إنجليزي)، S-B1-05، -استبعاد...',
    all: 'الكل',
    prefs: 'تفضيلاتي',
    fav: 'المفضلة',
    todo: 'للزيارة',
    visited: 'زُرت',
    rated: 'مقيّم',
    noted: 'ملاحظات',
    ignored: 'متجاهَل',
    filters: 'فلاتر',
    incMode: 'تضمين',
    excMode: 'تجاهل',
    clear: 'مسح',
    sortBooth: 'الطاولة (A-K)',
    sortMatch: 'التوافق',
    sortNearest: 'الأقرب لي',
    sortRating: 'التقييم',
    sortMembers: 'الفريق',
    sortCode: 'الكود',
    notePh: 'ملاحظة / LinkedIn / تواصل...',
    cats: 'الفئات العمرية',
    paths: 'المجالات',
    zones: 'المناطق',
    rows: 'الصفوف',
    tags: 'وسوم تقنية',
    customTags: 'وسومي',
    countries: 'الجنسيات',
    sizes: 'حجم الفريق',
    lang: 'اللغة',
    rating: 'التقييم',
    minMatch: 'أقل توافق',
    ignoreKw: 'كلمات متجاهلة (تختفي من القائمة والخريطة)',
    addKwPh: 'اكتب كلمة لتجاهل مشاريعها...',
    add: '+',
    myBooth: 'طاولتي',
    prefCats: 'فئات مفضلة',
    prefPaths: 'مجالات مفضلة',
    prefTags: 'وسوم مفضلة',
    prefKws: 'كلمات مفتاحية مفضلة (تزيد التوافق)',
    globIgnCats: 'تجاهل دائم للفئات',
    globIgnPaths: 'تجاهل دائم للمجالات',
    globIgnTags: 'تجاهل دائم للوسوم',
    globIgnKws: 'تجاهل دائم لكلمات',
    intlBoost: 'نقاط إضافية للفرق الدولية',
    subTech: 'تقنية',
    subPitch: 'عرض',
    subFit: 'تعاون',
    locate: 'على الخريطة',
    met: 'تواصلت',
    exportJson: 'نسخ احتياطي JSON',
    importMerge: 'استيراد (دمج)',
    importReplace: 'استيراد (استبدال)',
    exportCsv: 'تصدير جهات الاتصال CSV',
    resetAll: 'مسح بياناتي',
    empty: 'لا توجد مشاريع مطابقة',
    helpTitle: 'دليل الاستخدام ومعاني الرموز',
    helpSub: 'دليل تفاعلي سريع لمشاريع معرض SAIF 2026 — تحفظ جميع تقييماتك وملاحظاتك محليا على جهازك.',
    helpQuick: 'طريقة الاستخدام',
    helpSymbols: 'معاني الأزرار والرموز',
    helpTags: 'وسوم البطاقات السريعة',
    helpMapColors: 'ألوان الخريطة والمسار',
    helpStart: 'ابدأ التصفح',
    helpSetBooth: 'تحديد طاولتي (اختياري)',
  },
  en: {
    searchPh: 'Search: project, member (EN/AR), S-B1-05, -exclude...',
    all: 'All',
    prefs: 'My Picks',
    fav: 'Starred',
    todo: 'To Visit',
    visited: 'Visited',
    rated: 'Rated',
    noted: 'Notes',
    ignored: 'Ignored',
    filters: 'Filters',
    incMode: 'Include',
    excMode: 'Ignore',
    clear: 'Clear',
    sortBooth: 'Booth (A-K)',
    sortMatch: 'Match',
    sortNearest: 'Nearest',
    sortRating: 'Rating',
    sortMembers: 'Team',
    sortCode: 'Code',
    notePh: 'Note / LinkedIn / Handle...',
    cats: 'Age Categories',
    paths: 'Event Paths',
    zones: 'Zones',
    rows: 'Rows',
    tags: 'Tech Tags',
    customTags: 'My Tags',
    countries: 'Nationalities',
    sizes: 'Team Size',
    lang: 'Script',
    rating: 'Rating',
    minMatch: 'Min Match',
    ignoreKw: 'Ignored Keywords (List & Map)',
    addKwPh: 'Keyword to ignore...',
    add: '+',
    myBooth: 'My Booth',
    prefCats: 'Preferred Categories',
    prefPaths: 'Preferred Paths',
    prefTags: 'Preferred Tags',
    prefKws: 'Boost Keywords',
    globIgnCats: 'Always Ignore Categories',
    globIgnPaths: 'Always Ignore Paths',
    globIgnTags: 'Always Ignore Tags',
    globIgnKws: 'Always Ignore Keywords',
    intlBoost: 'International Team Boost',
    subTech: 'Tech',
    subPitch: 'Pitch',
    subFit: 'Collab',
    locate: 'Locate',
    met: 'Met',
    exportJson: 'Backup JSON',
    importMerge: 'Import (Merge)',
    importReplace: 'Import (Replace)',
    exportCsv: 'Contacts CSV',
    resetAll: 'Reset Data',
    empty: 'No matching projects',
    helpTitle: 'Instructions & Symbol Guide',
    helpSub: 'Fast checklist and floorplan explorer for SAIF 2026. All bookmarks, ratings, and notes stay locally on your device.',
    helpQuick: 'How to Use',
    helpSymbols: 'Buttons & Status Symbols',
    helpTags: 'Quick Card Tags',
    helpMapColors: 'Map Colors & Route',
    helpStart: 'Start Exploring',
    helpSetBooth: 'Set My Booth (Optional)',
  },
};

function esc(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function downloadFile(filename, content, mime = 'application/json') {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

class FairApp {
  constructor() {
    this.store = new TrackerStore();
    this.meta = null;
    this.projects = [];
    this.projectById = new Map();
    this.pathMap = new Map();
    this.catMap = new Map();
    this.tagMap = new Map();
    this.countryCounts = [];
    this.evalResult = null;
    this._evalCtx = null;
    this.page = 0;
    this.openModal = null;
    this.countrySearch = '';
    this.mapCtrl = null;
    this._searchTimer = null;
    this.drawerOpen = false;
  }

  async init() {
    initIconSprite();
    const res = await fetch('./data.json');
    const data = await res.json();
    if (typeof window !== 'undefined') window.__SAIF_RAW_DATA__ = data;
    this.meta = data.meta;
    this.projects = prepareProjects(data.projects, data.meta);
    for (const p of this.projects) this.projectById.set(p.id, p);
    this.pathMap = new Map(this.meta.paths.map((p) => [p.id, p]));
    this.catMap = new Map(this.meta.cats.map((c) => [c.id, c]));
    this.tagMap = new Map(this.meta.tags.map((t) => [t.id, t]));

    const cFreq = new Map();
    for (const p of this.projects) {
      for (const n of p.allNats) cFreq.set(n, (cFreq.get(n) || 0) + 1);
    }
    this.countryCounts = Array.from(cFreq.entries()).sort((a, b) => b[1] - a[1]);

    this._initMap();
    this._bindGlobalEvents();
    this.store.subscribe((_state, reason, id) => {
      if (reason === 'note') {
        this._syncNoteOnly(id);
      } else if (reason === 'record' && id) {
        this._patchSingleRecord(id);
      } else {
        this.render();
      }
    });
    this.render();
    if (!this.store.state.ui.seenGuide) {
      this.openModal = 'help';
      this._renderModal();
    }
  }

  t(key) {
    const lang = this.store.state.ui.lang === 'en' ? 'en' : 'ar';
    return UI_TEXT[lang][key] || key;
  }

  _closeModal() {
    const closingHelp = this.openModal === 'help' && !this.store.state.ui.seenGuide;
    this.openModal = null;
    document.getElementById('modal-overlay').classList.add('hidden');
    document.getElementById('modal-body').innerHTML = '';
    if (closingHelp) this.store.updateUI({ seenGuide: true });
  }

  _initMap() {
    const mapPane = document.getElementById('map-pane');
    this.mapCtrl = new FairMapController(mapPane, {
      meta: this.meta,
      projects: this.projects,
      onSelectProject: (id) => {
        this.openModal = { type: 'detail', id };
        this._renderModal();
      },
      onAction: (action, payload) => {
        if (action === 'mapColor') this.store.updateUI({ mapColor: payload });
        else if (action === 'toggleMapOpt') {
          this.store.updateUI({ [payload]: !this.store.state.ui[payload] });
        } else if (action === 'fav') this.store.toggleFav(payload);
        else if (action === 'vis') this.store.toggleVisited(payload);
        else if (action === 'ign') this.store.toggleIgnore(payload);
        else if (action === 'rat') this.store.setRating(payload.id, payload.stars);
        else if (action === 'tag') this.store.toggleCustomTag(payload.id, payload.tagId);
        else if (action === 'note') this.store.setNote(payload.id, payload.note);
        else if (action === 'openPrefs') {
          this.openModal = 'prefs';
          this._renderModal();
        }
      },
    });
  }

  _syncNoteOnly(id) {
    const rec = this.store.state.records[id] || {};
    const notedTab = document.querySelector('[data-status="noted"] b');
    if (notedTab) {
      let nCnt = 0;
      for (const r of Object.values(this.store.state.records)) {
        if (!r.ign && r.note && r.note.trim()) nCnt += 1;
      }
      this.evalResult.counts.noted = nCnt;
      notedTab.textContent = String(nCnt);
    }

    const active = document.activeElement;
    if (active?.dataset?.inspNote) {
      const cardEl = document.querySelector(`[data-pid="${id}"]`);
      if (cardEl && this.evalResult) {
        const temp = document.createElement('div');
        temp.innerHTML = this._cardMarkup(this.projectById.get(id), rec, this.evalResult.evalById.get(id));
        if (temp.firstElementChild) cardEl.replaceWith(temp.firstElementChild);
      }
    }
  }

  _patchSingleRecord(id) {
    const p = this.projectById.get(id);
    if (!p || !this.evalResult || !this._evalCtx) return;

    const { filters, records, prefs } = this.store.state;
    const { evalById, matched, counts } = this.evalResult;
    const oldEv = evalById.get(id);
    const newRec = records[id] || {};
    const newEv = evaluateProjectFast(p, newRec, this._evalCtx);

    if (oldEv.isIgnored !== newEv.isIgnored) {
      counts.ignored += newEv.isIgnored ? 1 : -1;
      counts.visible += newEv.isIgnored ? -1 : 1;
      if (newEv.matchScore >= 40) counts.prefs += newEv.isIgnored ? -1 : 1;
    }

    let fav = 0, todo = 0, visited = 0, rated = 0, noted = 0;
    for (const [rid, r] of Object.entries(records)) {
      const ev = rid === id ? newEv : evalById.get(rid);
      if (ev?.isIgnored) continue;
      if (r.fav) {
        fav += 1;
        if (!r.vis) todo += 1;
      }
      if (r.vis) visited += 1;
      if ((r.rat || 0) > 0) rated += 1;
      if (r.note && r.note.trim()) noted += 1;
    }
    counts.fav = fav;
    counts.todo = todo;
    counts.visited = visited;
    counts.rated = rated;
    counts.noted = noted;

    evalById.set(id, newEv);

    if (oldEv.matches !== newEv.matches || this.store.state.ui.showRoute) {
      if (oldEv.matches !== newEv.matches) {
        if (newEv.matches) {
          matched.push(p);
          sortMatched(matched, filters.sortBy, records);
        } else {
          const idx = matched.indexOf(p);
          if (idx !== -1) matched.splice(idx, 1);
        }
      }
      this.mapCtrl.sync({ evalById, matched, records, prefs, ui: this.store.state.ui });
    } else {
      this.mapCtrl.refreshBooth(p.table);
      if (this.mapCtrl.selectedTable === p.table) this.mapCtrl._renderInspector();
    }

    this._renderStatusTabs(counts);
    const bulkCount = document.querySelector('#active-bar .bulk-group .badge-mini');
    if (bulkCount) bulkCount.textContent = String(matched.length);

    if (this.openModal) this._renderModal();

    const cardEl = document.querySelector(`[data-pid="${id}"]`);
    if (cardEl) {
      if (!newEv.matches) {
        cardEl.remove();
      } else {
        const temp = document.createElement('div');
        temp.innerHTML = this._cardMarkup(p, newRec, newEv);
        if (temp.firstElementChild) cardEl.replaceWith(temp.firstElementChild);
      }
    }
  }

  _bindGlobalEvents() {
    const searchEl = document.getElementById('search-input');
    searchEl.value = this.store.state.filters.q || '';
    searchEl.addEventListener('input', (e) => {
      clearTimeout(this._searchTimer);
      const val = e.target.value;
      this._searchTimer = setTimeout(() => {
        this.page = 0;
        this.store.updateFilters({ q: val });
      }, 140);
    });

    document.getElementById('search-clear').addEventListener('click', () => {
      searchEl.value = '';
      this.page = 0;
      this.store.updateFilters({ q: '' });
    });

    document.getElementById('topbar').addEventListener('click', (e) => {
      const viewBtn = e.target.closest('[data-view]');
      if (viewBtn) return this.store.updateUI({ view: viewBtn.dataset.view });

      const topAct = e.target.closest('[data-top-act]');
      if (!topAct) return;
      const act = topAct.dataset.topAct;
      if (act === 'prefs' || act === 'filters') {
        this.openModal = 'prefs';
        this._renderModal();
      } else if (act === 'help') {
        this.openModal = 'help';
        this._renderModal();
      } else if (act === 'backup') {
        this.openModal = 'backup';
        this._renderModal();
      } else if (act === 'lang') {
        this.store.updateUI({ lang: this.store.state.ui.lang === 'ar' ? 'en' : 'ar' });
      } else if (act === 'theme') {
        this.store.updateUI({ theme: this.store.state.ui.theme === 'dark' ? 'light' : 'dark' });
      }
    });

    document.getElementById('drawer-toggle').addEventListener('click', () => {
      this.drawerOpen = !this.drawerOpen;
      this._syncDrawer();
    });

    document.getElementById('bottom-drawer').addEventListener('click', (e) => {
      const tab = e.target.closest('[data-status]');
      if (tab) {
        this.page = 0;
        return this.store.updateFilters({ status: tab.dataset.status });
      }
    });

    document.getElementById('sort-select').addEventListener('change', (e) => {
      this.page = 0;
      this.store.updateFilters({ sortBy: e.target.value });
    });

    document.getElementById('active-bar').addEventListener('click', (e) => {
      const rem = e.target.closest('[data-remove-chip]');
      if (rem) {
        this.page = 0;
        const { key, mode, val } = JSON.parse(rem.dataset.removeChip);
        if (key === 'kw') this.store.removeIgnoreKeyword(val);
        else if (key === 'intl') this.store.updateFilters({ intlMode: 'all' });
        else if (key === 'lang') this.store.updateFilters({ langMode: 'all' });
        else if (key === 'rat') this.store.updateFilters({ ratingMode: 'all' });
        else if (key === 'match') this.store.updateFilters({ minMatch: 0 });
        else this.store.clearFacetValue(key, mode, val);
        return;
      }
      const bulk = e.target.closest('[data-bulk]');
      if (bulk && this.evalResult) {
        const ids = this.evalResult.matched.map((p) => p.id);
        if (!ids.length) return;
        const act = bulk.dataset.bulk;
        if (act === 'ignore' && ids.length > 25 && !confirm(`Ignore ${ids.length}?`)) return;
        return this.store.bulkAction(ids, act);
      }
      if (e.target.closest('[data-clear-filters]')) {
        document.getElementById('search-input').value = '';
        this.page = 0;
        this.store.resetFilters();
      }
    });

    const listPane = document.getElementById('list-pane');
    listPane.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-card-act]');
      if (btn) {
        const act = btn.dataset.cardAct;
        const id = btn.dataset.id;
        if (act === 'fav') this.store.toggleFav(id);
        else if (act === 'vis') this.store.toggleVisited(id);
        else if (act === 'ign') this.store.toggleIgnore(id);
        else if (act === 'rat') this.store.setRating(id, Number(btn.dataset.stars));
        else if (act === 'tag') this.store.toggleCustomTag(id, btn.dataset.tag);
        else if (act === 'locate') {
          const p = this.projectById.get(id);
          if (p) {
            if (this.store.state.ui.view === 'list') {
              this.store.updateUI({ view: window.innerWidth <= 900 ? 'map' : 'split' });
            }
            requestAnimationFrame(() => this.mapCtrl.focusTable(p.table, true));
          }
        } else if (act === 'open') {
          this.openModal = { type: 'detail', id };
          this._renderModal();
        } else if (act === 'desc') {
          btn.classList.toggle('expanded');
        }
        return;
      }

      const pgBtn = e.target.closest('[data-page-to]');
      if (pgBtn && this.evalResult) {
        const totalPages = Math.max(1, Math.ceil(this.evalResult.matched.length / PAGE_SIZE));
        this.page = Math.max(0, Math.min(totalPages - 1, Number(pgBtn.dataset.pageTo)));
        this._renderList();
        listPane.scrollTop = 0;
      }
    });

    const overlay = document.getElementById('modal-overlay');
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay || e.target.closest('[data-modal-close]')) {
        return this._closeModal();
      }
      this._handleModalClick(e);
    });
    overlay.addEventListener('contextmenu', (e) => {
      const fchip = e.target.closest('[data-fchip]');
      if (fchip) {
        e.preventDefault();
        this.page = 0;
        const { key, val } = JSON.parse(fchip.dataset.fchip);
        this.store.toggleFacetValue(key, val, 'exc');
      }
    });
    overlay.addEventListener('input', (e) => this._handleModalInput(e));
    overlay.addEventListener('change', (e) => this._handleModalChange(e));
    overlay.addEventListener('keydown', (e) => {
      if (e.key !== 'Enter') return;
      if (e.target.id === 'ign-kw-input') {
        e.preventDefault();
        this.store.addIgnoreKeyword(e.target.value);
      } else if (e.target.id === 'pref-kw-input') {
        e.preventDefault();
        const w = e.target.value.trim().toLowerCase();
        if (w) {
          const set = new Set(this.store.state.prefs.prefKeywords || []);
          set.add(w);
          this.store.updatePrefs({ prefKeywords: Array.from(set) });
        }
      } else if (e.target.id === 'pref-ign-kw-input') {
        e.preventDefault();
        const w = e.target.value.trim().toLowerCase();
        if (w) {
          const set = new Set(this.store.state.prefs.ignoreKeywords || []);
          set.add(w);
          this.store.updatePrefs({ ignoreKeywords: Array.from(set) });
        }
      }
    });
  }

  _renderStatusTabs(counts) {
    const { filters } = this.store.state;
    const statusTabs = [
      ['all', `${this.t('all')} <b>${counts.visible}</b>`],
      ['fav', `${ico('starFill')} <b>${counts.fav}</b>`],
      ['todo', `${ico('clock')} <b>${counts.todo}</b>`],
      ['visited', `${ico('check')} <b>${counts.visited}</b>`],
      ['rated', `${ico('star')} <b>${counts.rated}</b>`],
      ['noted', `${ico('note')} <b>${counts.noted}</b>`],
      ['ignored', `${ico('ban')} <b>${counts.ignored}</b>`],
    ];
    document.getElementById('status-tabs').innerHTML = statusTabs
      .map(
        ([k, lbl]) =>
          `<button class="stat-tab ${filters.status === k ? 'active' : ''}" data-status="${k}">${lbl}</button>`
      )
      .join('');
  }

  _syncDrawer(matchedLen = this.evalResult?.matched?.length ?? 0) {
    const { filters, prefs } = this.store.state;
    const fCount = countActiveFilterRules(filters, prefs);
    const panel = document.getElementById('drawer-panel');
    const toggle = document.getElementById('drawer-toggle');
    if (panel) panel.classList.toggle('hidden', !this.drawerOpen);
    if (toggle) {
      const sortLbl = this.t({
        booth: 'sortBooth',
        match: 'sortMatch',
        nearest: 'sortNearest',
        rating: 'sortRating',
        members: 'sortMembers',
        code: 'sortCode',
      }[filters.sortBy] || 'sortBooth');
      toggle.setAttribute('aria-expanded', String(this.drawerOpen));
      toggle.innerHTML = `${ico(this.drawerOpen ? 'chevDown' : 'chevUp')} <span class="badge-mini">${matchedLen}</span> <span>${sortLbl}</span>${
        fCount ? `<span class="count-badge">${fCount}</span>` : ''
      }`;
    }
  }

  render() {
    const { filters, records, prefs, ui } = this.store.state;
    const lang = ui.lang === 'en' ? 'en' : 'ar';

    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.dataset.theme = ui.theme === 'light' ? 'light' : 'dark';

    this._evalCtx = buildEvalContext(filters, prefs);
    this.evalResult = evaluateAll(this.projects, filters, records, prefs);
    const { evalById, matched, counts } = this.evalResult;

    const brandPill = document.querySelector('.brand-pill');
    if (brandPill) brandPill.textContent = 'SAIF 2026';
    document.getElementById('search-input').placeholder = this.t('searchPh');
    document.getElementById('search-clear').classList.toggle('hidden', !filters.q);

    this._renderStatusTabs(counts);

    const fCount = countActiveFilterRules(filters, prefs);
    document.getElementById('btn-prefs').innerHTML = `${ico('zap')} ${this.t('prefs')}${
      fCount ? `<span class="count-badge">${fCount}</span>` : ''
    }`;
    document.getElementById('btn-lang').textContent = lang === 'ar' ? 'EN' : 'ع';
    document.getElementById('btn-theme').innerHTML = ico(ui.theme === 'light' ? 'moon' : 'sun');

    for (const vb of document.querySelectorAll('[data-view]')) {
      vb.classList.toggle('active', vb.dataset.view === ui.view);
    }

    const sortSel = document.getElementById('sort-select');
    sortSel.innerHTML = [
      ['booth', this.t('sortBooth')],
      ['match', this.t('sortMatch')],
      ['nearest', this.t('sortNearest')],
      ['rating', this.t('sortRating')],
      ['members', this.t('sortMembers')],
      ['code', this.t('sortCode')],
    ]
      .map(([v, l]) => `<option value="${v}" ${filters.sortBy === v ? 'selected' : ''}>${l}</option>`)
      .join('');

    this._renderActiveBar(matched.length);
    this._syncDrawer(matched.length);

    const ws = document.getElementById('workspace');
    ws.className = `workspace mode-${ui.view}`;
    document.body.className = `view-${ui.view}`;

    if (ui.view !== 'map') {
      this._renderList();
    }
    this.mapCtrl.sync({ evalById, matched, records, prefs, ui });
    if (ui.view !== 'list') {
      requestAnimationFrame(() => this.mapCtrl._resizeCanvas());
    }
    if (this.openModal) this._renderModal();
  }

  _renderActiveBar(matchedLen) {
    const { filters, ui } = this.store.state;
    const lang = ui.lang === 'en' ? 'en' : 'ar';
    const chips = [];

    const addFacetChips = (key, labelFn) => {
      for (const v of filters[key].inc || []) chips.push([key, 'inc', v, `+ ${labelFn(v)}`]);
      for (const v of filters[key].exc || []) chips.push([key, 'exc', v, `${ico('ban')} ${labelFn(v)}`]);
    };

    addFacetChips('cats', (id) => esc(this.catMap.get(id)?.[lang] || id));
    addFacetChips('paths', (id) => {
      const p = this.pathMap.get(id);
      return p ? `${ico(p.icon)} ${esc(p[lang])}` : esc(id);
    });
    addFacetChips('zones', (z) => esc(z));
    addFacetChips('rows', (r) => `R${r}`);
    addFacetChips('tags', (id) => {
      const tg = this.tagMap.get(id);
      return tg ? `${ico(tg.icon)} ${esc(tg[lang])}` : esc(id);
    });
    addFacetChips('customTags', (id) => {
      const tg = CUSTOM_TAGS.find((t) => t.id === id);
      return tg ? `${ico(tg.icon)} ${esc(tg[lang])}` : esc(id);
    });
    addFacetChips('countries', (c) => `${this.meta.countries[c]?.[0] || ''} ${esc(c)}`);
    addFacetChips('sizes', (s) => `${ico('users')} ${s}`);

    for (const kw of filters.ignoreKeywords || []) chips.push(['kw', 'exc', kw, `${ico('ban')} "${esc(kw)}"`]);
    if (filters.intlMode !== 'all') chips.push(['intl', 'inc', filters.intlMode, `${ico('globe')} ${esc(filters.intlMode)}`]);
    if (filters.langMode !== 'all') chips.push(['lang', 'inc', filters.langMode, `Aa ${esc(filters.langMode)}`]);
    if (filters.ratingMode !== 'all') chips.push(['rat', 'inc', filters.ratingMode, `${ico('starFill')} ${esc(filters.ratingMode)}`]);
    if (filters.minMatch > 0) chips.push(['match', 'inc', filters.minMatch, `${ico('zap')} >=${filters.minMatch}`]);

    const chipsHtml = chips
      .map(
        ([key, mode, val, html]) =>
          `<button class="active-chip ${mode}" data-remove-chip='${esc(JSON.stringify({ key, mode, val }))}'>${html} ${ico('x')}</button>`
      )
      .join('');

    const clearHtml =
      chips.length || filters.q
        ? `<button class="bulk-btn" data-clear-filters>${this.t('clear')}</button>`
        : '';

    const bulkHtml = `
      <span class="badge-mini">${matchedLen}</span>
      <button class="bulk-btn" data-bulk="fav">${ico('starFill')}+</button>
      <button class="bulk-btn" data-bulk="visit">${ico('check')}+</button>
      <button class="bulk-btn" data-bulk="ignore">${ico('ban')}+</button>
    `;

    document.getElementById('active-chips').innerHTML = `${chipsHtml}${clearHtml}`;
    document.getElementById('bulk-group').innerHTML = bulkHtml;
  }

  _cardMarkup(p, rec, ev) {
    const { prefs, ui } = this.store.state;
    const lang = ui.lang === 'en' ? 'en' : 'ar';
    const myTable = (prefs.myBooth || '').toUpperCase();
    const pathObj = this.pathMap.get(p.path);
    const catObj = this.catMap.get(p.cat);
    const isMe = p.table === myTable;
    const flags = p.allNats.map((n) => this.meta.countries[n]?.[0] || '').join('');

    const stars = [1, 2, 3, 4, 5]
      .map(
        (s) =>
          `<button class="star-btn ${(rec.rat || 0) >= s ? 'on' : ''}" data-card-act="rat" data-id="${p.id}" data-stars="${s}">${ico((rec.rat || 0) >= s ? 'starFill' : 'star')}</button>`
      )
      .join('');

    const activeTagsHtml = (rec.tags || [])
      .map((tid) => {
        const t = CUSTOM_TAGS.find((x) => x.id === tid);
        return t ? `<button class="tag-pill on" data-card-act="tag" data-id="${p.id}" data-tag="${t.id}">${ico(t.icon)}</button>` : '';
      })
      .join('');

    const membersHtml = p.members
      .map((m) => {
        const fl = m.nat ? this.meta.countries[m.nat]?.[0] || '' : '';
        const met = (rec.met || []).includes(m.n);
        const dispName = lang === 'ar' ? m.ar || m.n : m.n;
        const q = encodeURIComponent(`${m.n} ${m.nat || ''}`);
        return `<a class="member-chip ${met ? 'met' : ''}" href="https://www.linkedin.com/search/results/people/?keywords=${q}" target="_blank" rel="noopener" title="${esc(m.n)}">${m.l ? ico('crown') : ''}${esc(dispName)} ${fl}</a>`;
      })
      .join('');

    const noteHtml = rec.note
      ? `<div class="note-preview" data-card-act="open" data-id="${p.id}">${ico('note')} ${esc(rec.note)}</div>`
      : '';

    return `
      <article class="card ${rec.fav ? 'is-fav' : ''} ${rec.vis ? 'is-vis' : ''} ${ev.isIgnored ? 'is-ignored' : ''}" data-pid="${p.id}">
        <div class="card-top">
          <button class="badge-table ${isMe ? 'is-me' : ''}" data-card-act="locate" data-id="${p.id}">${p.table}</button>
          <span class="badge-cat c${p.cat}">${catObj?.[lang] || ''}</span>
          <span class="badge-path">${ico(pathObj?.icon)} ${pathObj?.[lang]}</span>
          <span class="badge-mini">${flags} x${p.members.length}</span>
          <span class="badge-match">${ico('zap')} ${ev.matchScore}</span>
          <div class="card-quick-ops">
            <button class="act-btn fav ${rec.fav ? 'on' : ''}" data-card-act="fav" data-id="${p.id}">${ico(rec.fav ? 'starFill' : 'star')}</button>
            <button class="act-btn vis ${rec.vis ? 'on' : ''}" data-card-act="vis" data-id="${p.id}">${ico('check')}</button>
            <button class="act-btn ign ${rec.ign ? 'on' : ''}" data-card-act="ign" data-id="${p.id}">${ico('ban')}</button>
          </div>
        </div>
        <div class="card-title" data-card-act="open" data-id="${p.id}">${esc(p.title)}</div>
        <div class="card-desc" data-card-act="desc">${esc(p.desc)}</div>
        <div class="card-rate-bar">
          <div class="stars-row">${stars}</div>
          ${activeTagsHtml}
          <button class="tag-pill" data-card-act="open" data-id="${p.id}">${ico('tag')}+</button>
        </div>
        <div class="members-row">${membersHtml}</div>
        ${noteHtml}
      </article>
    `;
  }

  _renderList() {
    const pane = document.getElementById('list-pane');
    const { matched, evalById } = this.evalResult;
    const { records } = this.store.state;

    if (!matched.length) {
      pane.innerHTML = `<div class="card" style="text-align:center;padding:30px;color:var(--muted)">${this.t('empty')}</div>`;
      return;
    }

    const totalPages = Math.max(1, Math.ceil(matched.length / PAGE_SIZE));
    if (this.page >= totalPages) this.page = totalPages - 1;
    const start = this.page * PAGE_SIZE;
    const slice = matched.slice(start, start + PAGE_SIZE);
    const cardsHtml = slice
      .map((p) => this._cardMarkup(p, records[p.id] || {}, evalById.get(p.id)))
      .join('');

    const pager =
      totalPages > 1
        ? `<div class="pager-bar">
             <button class="load-more-btn" data-page-to="0" ${this.page === 0 ? 'disabled' : ''}>«</button>
             <button class="load-more-btn" data-page-to="${this.page - 1}" ${this.page === 0 ? 'disabled' : ''}>${ico('chevLeft')}</button>
             <span class="pager-info">${this.page + 1} / ${totalPages} (${matched.length})</span>
             <button class="load-more-btn" data-page-to="${this.page + 1}" ${this.page >= totalPages - 1 ? 'disabled' : ''}>${ico('chevRight')}</button>
             <button class="load-more-btn" data-page-to="${totalPages - 1}" ${this.page >= totalPages - 1 ? 'disabled' : ''}>»</button>
           </div>`
        : '';

    pane.innerHTML = cardsHtml + pager;
  }

  _renderModal() {
    const overlay = document.getElementById('modal-overlay');
    const body = document.getElementById('modal-body');
    if (!this.openModal) {
      overlay.classList.add('hidden');
      return;
    }

    const { filters, prefs, records, ui } = this.store.state;
    const lang = ui.lang === 'en' ? 'en' : 'ar';

    if (this.openModal === 'prefs' || this.openModal === 'filters') {
      const fMode = ui.filterMode || 'inc';
      const chip = (key, val, label) => {
        const cls = filters[key].inc.includes(val) ? 'inc' : filters[key].exc.includes(val) ? 'exc' : '';
        return `<button class="fchip ${cls}" data-fchip='${esc(JSON.stringify({ key, val }))}'>${label}</button>`;
      };
      const isAdult = filters.cats.inc.length === 2 && filters.cats.inc.includes(3) && filters.cats.inc.includes(4);

      const filteredCountries = this.countryCounts.filter(([n]) => {
        if (!this.countrySearch) return true;
        const c = this.meta.countries[n];
        return `${n} ${c?.[1] || ''} ${c?.[2] || ''}`.toLowerCase().includes(this.countrySearch.toLowerCase());
      });

      body.innerHTML = `
        <div class="modal-head">
          <h3>${ico('zap')} ${this.t('prefs')}</h3>
          <div class="mode-toggle">
            <button class="${fMode === 'inc' ? 'active' : ''}" data-modal-fmode="inc">${ico('check')} ${this.t('incMode')}</button>
            <button class="${fMode === 'exc' ? 'active' : ''}" data-modal-fmode="exc">${ico('ban')} ${this.t('excMode')}</button>
          </div>
          <button class="bulk-btn" data-modal-clear-filters>${this.t('clear')}</button>
          <button class="modal-close" data-modal-close>${ico('x')}</button>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('cats')}</div>
          <div class="chip-grid">
            <button class="fchip ${isAdult ? 'inc' : ''}" data-adult-toggle>18+</button>
            ${this.meta.cats.map((c) => chip('cats', c.id, c[lang])).join('')}
          </div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('paths')}</div>
          <div class="chip-grid">${this.meta.paths.map((p) => chip('paths', p.id, `${ico(p.icon)} ${p[lang]}`)).join('')}</div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('zones')} / ${this.t('rows')}</div>
          <div class="chip-grid">
            ${Object.keys(ZONE_GEOMETRY).map((z) => chip('zones', z, z)).join('')}
            <span class="divider-v"></span>
            ${[1, 2, 3, 4, 5, 6, 7].map((r) => chip('rows', r, `R${r}`)).join('')}
          </div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('rating')} · ${this.t('minMatch')} · ${this.t('sizes')} · ${this.t('lang')}</div>
          <div class="chip-grid">
            ${[
              ['all', `${ico('star')} All`],
              ['rated', `${ico('starFill')} >0`],
              ['unrated', `${ico('star')} 0`],
              ['3+', `3${ico('starFill')}+`],
              ['4+', `4${ico('starFill')}+`],
              ['5', `5${ico('starFill')}`],
            ]
              .map(([v, l]) => `<button class="fchip ${filters.ratingMode === v ? 'inc' : ''}" data-set-filter='{"ratingMode":"${v}"}'>${l}</button>`)
              .join('')}
            <span class="divider-v"></span>
            ${[0, 30, 50, 70]
              .map((m) => `<button class="fchip ${filters.minMatch === m ? 'inc' : ''}" data-set-filter='{"minMatch":${m}}'>${ico('zap')} >=${m}</button>`)
              .join('')}
            <span class="divider-v"></span>
            ${[1, 2, 3, 4, 5, 6].map((s) => chip('sizes', s, `${ico('users')} ${s}`)).join('')}
            <span class="divider-v"></span>
            ${[
              ['all', `${ico('globe')} All`],
              ['intl_leader', `${ico('globe')} Intl Leader`],
              ['has_intl', `${ico('globe')} Any Intl`],
              ['mixed', `${ico('users')} Mixed`],
              ['saudi_only', '🇸🇦 Only'],
            ]
              .map(([v, l]) => `<button class="fchip ${filters.intlMode === v ? 'inc' : ''}" data-set-filter='{"intlMode":"${v}"}'>${l}</button>`)
              .join('')}
            <span class="divider-v"></span>
            ${[
              ['all', 'Aa All'],
              ['en', 'EN'],
              ['ar', 'AR'],
              ['bi', 'EN+AR'],
            ]
              .map(([v, l]) => `<button class="fchip ${filters.langMode === v ? 'inc' : ''}" data-set-filter='{"langMode":"${v}"}'>${l}</button>`)
              .join('')}
          </div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('tags')} · ${this.t('customTags')}</div>
          <div class="chip-grid">
            ${this.meta.tags.map((tg) => chip('tags', tg.id, `${ico(tg.icon)} ${tg[lang]}`)).join('')}
            <span class="divider-v"></span>
            ${CUSTOM_TAGS.map((tg) => chip('customTags', tg.id, `${ico(tg.icon)} ${tg[lang]}`)).join('')}
          </div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('countries')} (${this.countryCounts.length})</div>
          <input class="kw-input" id="country-search-input" type="text" value="${esc(this.countrySearch)}" placeholder="Country..." />
          <div class="chip-grid" style="max-height:130px;overflow-y:auto">
            ${filteredCountries
              .map(([name, cnt]) => {
                const c = this.meta.countries[name];
                return chip('countries', name, `${c?.[0] || ''} ${lang === 'ar' ? c?.[2] || name : name} (${cnt})`);
              })
              .join('')}
          </div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('ignoreKw')} · ${this.t('prefKws')}</div>
          <div class="kw-row">
            <input class="kw-input" id="ign-kw-input" type="text" placeholder="${this.t('addKwPh')}" />
            <button class="btn-danger" data-add-ign-kw>${ico('ban')} ${this.t('add')}</button>
          </div>
          <div class="chip-grid">
            ${(filters.ignoreKeywords || [])
              .map((w) => `<button class="fchip exc" data-rem-ign-kw="${esc(w)}">${ico('ban')} ${esc(w)} ${ico('x')}</button>`)
              .join('')}
          </div>
          <div class="kw-row" style="margin-top:4px">
            <input class="kw-input" id="pref-kw-input" type="text" placeholder="hydrogen, llm, startup..." />
            <button class="btn-primary" data-add-pref-kw>${ico('zap')} ${this.t('add')}</button>
          </div>
          <div class="chip-grid">
            ${(prefs.prefKeywords || [])
              .map((w) => `<button class="fchip inc" data-rem-pref-kw="${esc(w)}">${ico('zap')} ${esc(w)} ${ico('x')}</button>`)
              .join('')}
          </div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('myBooth')} · ${this.t('intlBoost')}</div>
          <div class="kw-row">
            <input class="kw-input" id="pref-my-booth" type="text" value="${esc(prefs.myBooth)}" placeholder="S-B1-05" style="max-width:140px;direction:ltr" />
            <input class="kw-input" id="pref-intl-boost" type="number" min="0" max="30" value="${prefs.boostIntl ?? 12}" style="max-width:90px" />
          </div>
        </div>
      `;
    } else if (this.openModal === 'backup') {
      const { counts } = this.evalResult;
      body.innerHTML = `
        <div class="modal-head">
          <h3>${ico('save')} localStorage</h3>
          <button class="modal-close" data-modal-close>${ico('x')}</button>
        </div>
        <div class="chip-grid">
          <span class="badge-mini">${ico('starFill')} ${counts.fav}</span>
          <span class="badge-mini">${ico('check')} ${counts.visited}</span>
          <span class="badge-mini">${ico('star')} ${counts.rated}</span>
          <span class="badge-mini">${ico('note')} ${counts.noted}</span>
          <span class="badge-mini">${ico('ban')} ${counts.ignored}</span>
        </div>
        <div class="chip-grid">
          <button class="btn-primary" data-backup-act="export-json">${ico('download')} ${this.t('exportJson')}</button>
          <button class="btn-primary" data-backup-act="export-csv">${ico('table')} ${this.t('exportCsv')}</button>
          <label class="fchip" style="cursor:pointer">
            ${ico('upload')} ${this.t('importMerge')}
            <input type="file" accept=".json" id="import-merge-file" style="display:none" />
          </label>
          <label class="fchip" style="cursor:pointer">
            ${ico('upload')} ${this.t('importReplace')}
            <input type="file" accept=".json" id="import-replace-file" style="display:none" />
          </label>
          <button class="btn-danger" data-backup-act="reset">${ico('trash')} ${this.t('resetAll')}</button>
        </div>
      `;
    } else if (this.openModal === 'help') {
      const steps =
        lang === 'ar'
          ? [
              ['search', '<b>البحث الذكي:</b> ابحث باسم المشروع، اسم المشارك بالعربي أو الإنجليزي، رقم الطاولة (<code>S-B1-05</code>)، أو اكتب <code>-كلمة</code> لاستبعاد نتائجها.'],
              ['zap', '<b>تفضيلاتي:</b> اضبط مجالاتك المفضلة أو المستبعدة (تضمين / تجاهل)، المناطق، الجنسيات، التقييم أو التوافق من زر <b>تفضيلاتي</b>، ومن السهم السفلي بدّل الفرز والتصنيف.'],
              ['map', '<b>الخريطة والمسار:</b> الخريطة الرسمية تملأ الشاشة وتُبرز مشاريعك المفضلة والمُتحقق منها والمقيّمة مع إمكانية التعديل المباشر عند الضغط على أي بوث.'],
              ['pin', '<b>تخصيص طاولتك (اختياري):</b> إذا كانت لديك طاولة، أضف رقمها من <b>تفضيلاتي</b> لترتيب المشاريع حسب الأقرب وتمييزها على الخريطة.'],
              ['save', '<b>حفظ محلي ونسخ احتياطي:</b> جميع اختياراتك وملاحظاتك تبقى على جهازك، ويمكنك تصديرها JSON أو CSV في أي وقت.'],
            ]
          : [
              ['search', '<b>Smart Search:</b> Search projects, member names (EN or AR), booth codes (<code>S-B1-05</code>), or prefix <code>-word</code> to exclude terms.'],
              ['zap', '<b>My Picks:</b> Configure whitelists, ignores, zones, countries, ratings, and min match in one place via <b>My Picks</b>, and use the bottom edge arrow drawer for sorting & status tabs.'],
              ['map', '<b>Full-Screen Official Map:</b> Highlighted Favourite, Checked, and Starred booths float directly on the Hall 4 map with live inline checklist buttons on click.'],
              ['pin', '<b>Optional Booth Setup:</b> If exhibiting, enter your own booth in <b>My Picks</b> to enable Nearest sorting and map highlight.'],
              ['save', '<b>Local Storage & Export:</b> Everything saves automatically on your device; export/import JSON or CSV anytime.'],
            ];

      const symLegend = [
        ['starFill', lang === 'ar' ? 'مفضلة / للزيارة' : 'Starred / To Visit'],
        ['check', lang === 'ar' ? 'تمت الزيارة' : 'Visited'],
        ['star', lang === 'ar' ? 'تقييم 1-5 + تقنية/عرض/تعاون' : '1-5 Stars & Sub-ratings'],
        ['ban', lang === 'ar' ? 'تجاهل وإخفاء من القائمة والخريطة' : 'Ignore & hide from List/Map'],
        ['pin', lang === 'ar' ? 'تحديد الموقع على الخريطة / طاولتك' : 'Locate on Map / Your Booth'],
        ['note', lang === 'ar' ? 'ملاحظات سريعة أو رابط تواصل' : 'Quick Note / Contact Link'],
        ['zap', lang === 'ar' ? 'نسبة التوافق مع تفضيلاتك' : 'Match Score from My Picks'],
        ['sliders', lang === 'ar' ? 'فلاتر متقدمة (منطقة، مجال، جنسية)' : 'Advanced Filters'],
        ['eyeOff', lang === 'ar' ? 'إخفاء غير المطابق من الخريطة' : 'Hide Unmatched on Map'],
        ['route', lang === 'ar' ? 'مسار جولة لأقرب الطاولات' : 'Nearest Walking Route'],
        ['expand', lang === 'ar' ? 'فتح بطاقة التفاصيل الكاملة' : 'Open Full Project Details'],
        ['save', lang === 'ar' ? 'تصدير / استيراد النسخة الاحتياطية' : 'Backup Export / Import'],
      ];

      const mapColors = [
        ['#d97706', lang === 'ar' ? 'مفضلة' : 'Starred'],
        ['#059669', lang === 'ar' ? 'تمت الزيارة' : 'Visited'],
        ['#0d9488', lang === 'ar' ? 'مفضلة + تمت الزيارة' : 'Starred + Visited'],
        ['#7c3aed', lang === 'ar' ? 'مقيّم (1-5)' : 'Rated (1-5)'],
        ['#0284c7', lang === 'ar' ? 'توافق 50+' : 'Match 50+'],
        ['#9333ea', lang === 'ar' ? 'طاولتك (عند تحديدها)' : 'Your Booth (if set)'],
      ];

      body.innerHTML = `
        <div class="modal-head">
          <h3>${ico('help')} ${this.t('helpTitle')}</h3>
          <div style="display:flex;gap:6px;align-items:center">
            <button class="fchip" data-help-lang type="button">${lang === 'ar' ? 'EN' : 'ع'}</button>
            <button class="modal-close" data-modal-close type="button">${ico('x')}</button>
          </div>
        </div>
        <p class="guide-sub">${this.t('helpSub')}</p>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('helpQuick')}</div>
          <div class="guide-list">
            ${steps.map(([ic, txt]) => `<div class="guide-step">${ico(ic)} <span>${txt}</span></div>`).join('')}
          </div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('helpSymbols')}</div>
          <div class="guide-grid">
            ${symLegend.map(([ic, lbl]) => `<div class="guide-item"><span class="guide-ico">${ico(ic)}</span><span>${lbl}</span></div>`).join('')}
          </div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('helpTags')}</div>
          <div class="guide-grid">
            ${CUSTOM_TAGS.map((tg) => `<div class="guide-item"><span class="guide-ico">${ico(tg.icon)}</span><span>${tg[lang]}</span></div>`).join('')}
          </div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('helpMapColors')}</div>
          <div class="guide-grid">
            ${mapColors.map(([col, lbl]) => `<div class="guide-item"><span class="guide-swatch" style="background:${col}"></span><span>${lbl}</span></div>`).join('')}
          </div>
        </div>

        <div class="guide-foot">
          <button class="fchip" data-help-prefs type="button">${ico('pin')} ${this.t('helpSetBooth')}</button>
          <button class="btn-primary" data-modal-close type="button">${this.t('helpStart')}</button>
        </div>
      `;
    } else if (this.openModal?.type === 'detail') {
      const p = this.projectById.get(this.openModal.id);
      if (!p) {
        this._closeModal();
        return;
      }
      const rec = records[p.id] || {};
      const ev = this.evalResult.evalById.get(p.id);
      const pathObj = this.pathMap.get(p.path);
      const catObj = this.catMap.get(p.cat);

      const starRow = [1, 2, 3, 4, 5]
        .map(
          (s) =>
            `<button class="star-btn ${(rec.rat || 0) >= s ? 'on' : ''}" data-detail-act="rat" data-id="${p.id}" data-stars="${s}">${ico((rec.rat || 0) >= s ? 'starFill' : 'star')}</button>`
        )
        .join('');

      const subBox = (axis, lbl) => {
        const val = rec.sub?.[axis] || 0;
        const stars = [1, 2, 3, 4, 5]
          .map(
            (s) =>
              `<button class="star-btn ${val >= s ? 'on' : ''}" data-detail-act="sub" data-id="${p.id}" data-axis="${axis}" data-stars="${s}">${ico(val >= s ? 'starFill' : 'star')}</button>`
          )
          .join('');
        return `<div class="sub-rate-box"><span>${lbl}</span><div class="stars-row">${stars}</div></div>`;
      };

      const membersHtml = p.members
        .map((m) => {
          const fl = m.nat ? this.meta.countries[m.nat]?.[0] || '' : '';
          const met = (rec.met || []).includes(m.n);
          const q = encodeURIComponent(`${m.n} ${m.nat || ''}`);
          return `
            <div class="detail-member-row">
              <button class="act-btn vis ${met ? 'on' : ''}" data-detail-act="met" data-id="${p.id}" data-member="${esc(m.n)}">${ico('check')} ${this.t('met')}</button>
              <span>${ico(m.l ? 'crown' : 'user')} <b>${esc(m.ar || m.n)}</b> · <small style="color:var(--muted)">${esc(m.n)}</small> ${fl}</span>
              <a href="https://www.linkedin.com/search/results/people/?keywords=${q}" target="_blank" rel="noopener">LinkedIn ↗</a>
            </div>
          `;
        })
        .join('');

      body.innerHTML = `
        <div class="modal-head">
          <span class="badge-table">${p.table}</span>
          <span class="badge-mini">${p.code}</span>
          <span class="badge-cat c${p.cat}">${catObj?.[lang] || ''}</span>
          <span class="badge-match">${ico('zap')} ${ev?.matchScore ?? 0}</span>
          <button class="modal-close" data-modal-close>${ico('x')}</button>
        </div>
        <h3>${esc(p.title)}</h3>
        <div class="chip-grid">
          <span class="badge-path">${ico(pathObj?.icon)} ${pathObj?.[lang]}</span>
          ${p.tags
            .map((tid) => {
              const tg = this.tagMap.get(tid);
              return `<span class="badge-mini">${ico(tg?.icon)} ${tg?.[lang] || tid}</span>`;
            })
            .join('')}
        </div>
        <div class="detail-desc">${esc(p.desc)}</div>
        <div class="card-rate-bar">
          <button class="act-btn fav ${rec.fav ? 'on' : ''}" data-detail-act="fav" data-id="${p.id}">${ico(rec.fav ? 'starFill' : 'star')}</button>
          <button class="act-btn vis ${rec.vis ? 'on' : ''}" data-detail-act="vis" data-id="${p.id}">${ico('check')}</button>
          <div class="stars-row">${starRow}</div>
          <button class="act-btn ign ${rec.ign ? 'on' : ''}" data-detail-act="ign" data-id="${p.id}">${ico('ban')}</button>
          <button class="act-btn" data-detail-act="locate" data-id="${p.id}">${ico('pin')} ${this.t('locate')}</button>
        </div>
        <div class="sub-ratings">
          ${subBox('tech', this.t('subTech'))}
          ${subBox('pitch', this.t('subPitch'))}
          ${subBox('fit', this.t('subFit'))}
        </div>
        <div class="chip-grid">
          ${CUSTOM_TAGS.map(
            (tg) =>
              `<button class="tag-pill ${(rec.tags || []).includes(tg.id) ? 'on' : ''}" data-detail-act="tag" data-id="${p.id}" data-tag="${tg.id}">${ico(tg.icon)} ${tg[lang]}</button>`
          ).join('')}
        </div>
        <textarea class="kw-input" rows="2" data-detail-note="${p.id}" placeholder="${this.t('notePh')}">${esc(rec.note || '')}</textarea>
        <div class="detail-members">${membersHtml}</div>
      `;
    }

    overlay.classList.remove('hidden');
  }

  _handleModalClick(e) {
    const fmode = e.target.closest('[data-modal-fmode]');
    if (fmode) return this.store.updateUI({ filterMode: fmode.dataset.modalFmode });

    if (e.target.closest('[data-modal-clear-filters]')) {
      document.getElementById('search-input').value = '';
      this.page = 0;
      return this.store.resetFilters();
    }

    if (e.target.closest('[data-adult-toggle]')) {
      this.page = 0;
      const cats = this.store.state.filters.cats;
      const isAdult = cats.inc.length === 2 && cats.inc.includes(3) && cats.inc.includes(4);
      return this.store.updateFilters({
        cats: { ...cats, inc: isAdult ? [] : [3, 4], exc: cats.exc.filter((c) => c !== 3 && c !== 4) },
      });
    }

    const fchip = e.target.closest('[data-fchip]');
    if (fchip) {
      this.page = 0;
      const { key, val } = JSON.parse(fchip.dataset.fchip);
      return this.store.toggleFacetValue(key, val);
    }

    const setF = e.target.closest('[data-set-filter]');
    if (setF) {
      this.page = 0;
      return this.store.updateFilters(JSON.parse(setF.dataset.setFilter));
    }

    if (e.target.closest('[data-add-ign-kw]')) {
      const inp = document.getElementById('ign-kw-input');
      if (inp?.value) {
        this.store.addIgnoreKeyword(inp.value);
        inp.value = '';
      }
      return;
    }

    const remKw = e.target.closest('[data-rem-ign-kw]');
    if (remKw) return this.store.removeIgnoreKeyword(remKw.dataset.remIgnKw);

    const pTog = e.target.closest('[data-pref-toggle]');
    if (pTog) {
      const { field, val } = JSON.parse(pTog.dataset.prefToggle);
      const curr = new Set(this.store.state.prefs[field] || []);
      if (curr.has(val)) curr.delete(val);
      else curr.add(val);
      return this.store.updatePrefs({ [field]: Array.from(curr) });
    }

    if (e.target.closest('[data-add-pref-kw]')) {
      const inp = document.getElementById('pref-kw-input');
      const w = inp?.value?.trim().toLowerCase();
      if (w) {
        const set = new Set(this.store.state.prefs.prefKeywords || []);
        set.add(w);
        this.store.updatePrefs({ prefKeywords: Array.from(set) });
      }
      return;
    }

    const remPrefKw = e.target.closest('[data-rem-pref-kw]');
    if (remPrefKw) {
      const w = remPrefKw.dataset.remPrefKw;
      return this.store.updatePrefs({
        prefKeywords: (this.store.state.prefs.prefKeywords || []).filter((x) => x !== w),
      });
    }

    if (e.target.closest('[data-add-pref-ign-kw]')) {
      const inp = document.getElementById('pref-ign-kw-input');
      const w = inp?.value?.trim().toLowerCase();
      if (w) {
        const set = new Set(this.store.state.prefs.ignoreKeywords || []);
        set.add(w);
        this.store.updatePrefs({ ignoreKeywords: Array.from(set) });
      }
      return;
    }

    const remPrefIgn = e.target.closest('[data-rem-pref-ign-kw]');
    if (remPrefIgn) {
      const w = remPrefIgn.dataset.remPrefIgnKw;
      return this.store.updatePrefs({
        ignoreKeywords: (this.store.state.prefs.ignoreKeywords || []).filter((x) => x !== w),
      });
    }

    const bAct = e.target.closest('[data-backup-act]');
    if (bAct) {
      const act = bAct.dataset.backupAct;
      if (act === 'export-json') {
        downloadFile(`saif-checklist-backup-${new Date().toISOString().slice(0, 10)}.json`, this.store.exportJSON());
      } else if (act === 'export-csv') {
        downloadFile(
          `saif-contacts-${new Date().toISOString().slice(0, 10)}.csv`,
          this.store.exportContactsCSV(this.projects, this.meta),
          'text/csv;charset=utf-8'
        );
      } else if (act === 'reset') {
        if (confirm('Reset all favorites, ratings, notes, and ignores?')) {
          localStorage.removeItem('saif_fair_tracker_v1');
          location.reload();
        }
      }
      return;
    }

    const dAct = e.target.closest('[data-detail-act]');
    if (dAct) {
      const act = dAct.dataset.detailAct;
      const id = dAct.dataset.id;
      if (act === 'fav') this.store.toggleFav(id);
      else if (act === 'vis') this.store.toggleVisited(id);
      else if (act === 'ign') this.store.toggleIgnore(id);
      else if (act === 'rat') this.store.setRating(id, Number(dAct.dataset.stars));
      else if (act === 'sub') this.store.setSubRating(id, dAct.dataset.axis, Number(dAct.dataset.stars));
      else if (act === 'tag') this.store.toggleCustomTag(id, dAct.dataset.tag);
      else if (act === 'met') this.store.toggleMet(id, dAct.dataset.member);
      else if (act === 'locate') {
        const p = this.projectById.get(id);
        this._closeModal();
        if (p) {
          if (this.store.state.ui.view === 'list') {
            this.store.updateUI({ view: window.innerWidth <= 900 ? 'map' : 'split' });
          }
          requestAnimationFrame(() => this.mapCtrl.focusTable(p.table, true));
        }
      }
      return;
    }

    if (e.target.closest('[data-help-lang]')) {
      return this.store.updateUI({ lang: this.store.state.ui.lang === 'ar' ? 'en' : 'ar' });
    }
    if (e.target.closest('[data-help-prefs]')) {
      this.openModal = 'prefs';
      if (!this.store.state.ui.seenGuide) {
        return this.store.updateUI({ seenGuide: true });
      }
      return this._renderModal();
    }
  }

  _handleModalInput(e) {
    if (e.target.id === 'country-search-input') {
      this.countrySearch = e.target.value;
      const pos = e.target.selectionStart;
      this._renderModal();
      const el = document.getElementById('country-search-input');
      if (el) {
        el.focus();
        el.setSelectionRange(pos, pos);
      }
      return;
    }
    if (e.target.dataset.detailNote) {
      this.store.setNote(e.target.dataset.detailNote, e.target.value);
    }
  }

  _handleModalChange(e) {
    if (e.target.id === 'pref-my-booth') {
      return this.store.updatePrefs({ myBooth: e.target.value.trim().toUpperCase() });
    }
    if (e.target.id === 'pref-intl-boost') {
      return this.store.updatePrefs({ boostIntl: Math.max(0, Math.min(30, Number(e.target.value) || 0)) });
    }
    if (e.target.id === 'import-merge-file' || e.target.id === 'import-replace-file') {
      const file = e.target.files?.[0];
      if (!file) return;
      const merge = e.target.id === 'import-merge-file';
      file.text().then((txt) => {
        try {
          this.store.importJSON(txt, merge);
          this._closeModal();
        } catch (err) {
          alert(err.message);
        }
      });
    }
  }
}

window.addEventListener('DOMContentLoaded', () => {
  const app = new FairApp();
  app.init();
});
