import {
  CUSTOM_TAGS,
  ZONE_GEOMETRY,
  countActiveFilterRules,
  evaluateAll,
  prepareProjects,
} from './logic.js';
import { FairMapController } from './map.js';
import { TrackerStore } from './store.js';

const BATCH_SIZE = 24;

const UI_TEXT = {
  ar: {
    searchPh: '🔍 بحث: مشروع، مشارك (عربي أو إنجليزي)، S-H5-23، -تجاهل...',
    all: 'الكل',
    prefs: 'تفضيلاتي',
    fav: 'المفضلة',
    todo: 'للزيارة',
    visited: 'زُرت',
    rated: 'مقيّم',
    noted: 'ملاحظات',
    ignored: 'متجاهَل',
    filters: 'فلاتر',
    incMode: '✓ تضمين',
    excMode: '🚫 تجاهل',
    clear: 'مسح',
    showMore: 'عرض المزيد',
    showAll: 'عرض الكل',
    sortBooth: 'الطاولة (A-K)',
    sortMatch: '⚡ التوافق',
    sortNearest: '📍 الأقرب لي',
    sortRating: '⭐ التقييم',
    sortMembers: '👥 الفريق',
    sortCode: 'الكود',
    notePh: '📝 ملاحظة / LinkedIn / تواصل...',
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
    locate: '📍 على الخريطة',
    met: '✓ تواصلت',
    exportJson: '⬇ نسخ احتياطي JSON',
    importMerge: '⬆ استيراد (دمج)',
    importReplace: '⬆ استيراد (استبدال)',
    exportCsv: '📊 تصدير جهات الاتصال CSV',
    resetAll: '🗑️ مسح بياناتي',
    empty: 'لا توجد مشاريع مطابقة',
  },
  en: {
    searchPh: '🔍 Search: project, member (EN/AR), S-H5-23, -exclude...',
    all: 'All',
    prefs: 'My Picks',
    fav: 'Starred',
    todo: 'To Visit',
    visited: 'Visited',
    rated: 'Rated',
    noted: 'Notes',
    ignored: 'Ignored',
    filters: 'Filters',
    incMode: '✓ Include',
    excMode: '🚫 Ignore',
    clear: 'Clear',
    showMore: 'Load more',
    showAll: 'Show all',
    sortBooth: 'Booth (A-K)',
    sortMatch: '⚡ Match',
    sortNearest: '📍 Nearest',
    sortRating: '⭐ Rating',
    sortMembers: '👥 Team',
    sortCode: 'Code',
    notePh: '📝 Note / LinkedIn / Handle...',
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
    locate: '📍 Locate',
    met: '✓ Met',
    exportJson: '⬇ Backup JSON',
    importMerge: '⬆ Import (Merge)',
    importReplace: '⬆ Import (Replace)',
    exportCsv: '📊 Contacts CSV',
    resetAll: '🗑️ Reset Data',
    empty: 'No matching projects',
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
    this.renderedCount = BATCH_SIZE;
    this.openModal = null;
    this.countrySearch = '';
    this.mapCtrl = null;
    this.observer = null;
    this._searchTimer = null;
  }

  async init() {
    const res = await fetch('./data.json');
    const data = await res.json();
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
        this._syncNoteOnly();
      } else if (reason === 'record' && id) {
        this._patchSingleRecord(id);
      } else {
        this.render();
      }
    });
    this.render();
  }

  t(key) {
    const lang = this.store.state.ui.lang === 'en' ? 'en' : 'ar';
    return UI_TEXT[lang][key] || key;
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
      },
    });
  }

  _syncNoteOnly() {
    const { filters, records, prefs } = this.store.state;
    this.evalResult = evaluateAll(this.projects, filters, records, prefs);
    const notedTab = document.querySelector('[data-status="noted"] b');
    if (notedTab) notedTab.textContent = String(this.evalResult.counts.noted);

    const active = document.activeElement;
    if (active?.dataset?.cardNote) {
      const insp = document.querySelector(`[data-insp-note="${active.dataset.cardNote}"]`);
      if (insp && insp !== active) insp.value = active.value;
    } else if (active?.dataset?.inspNote) {
      const cardInp = document.querySelector(`[data-card-note="${active.dataset.inspNote}"]`);
      if (cardInp && cardInp !== active) cardInp.value = active.value;
    }
  }

  /**
   * Ultra-fast O(1) DOM patch when toggling star/visit/rating/tag/ignore on a single card.
   * Avoids rebuilding the entire list DOM on mobile touchscreens.
   */
  _patchSingleRecord(id) {
    const { filters, records, prefs, ui } = this.store.state;
    this.evalResult = evaluateAll(this.projects, filters, records, prefs);
    const { evalById, matched, counts } = this.evalResult;

    this._renderStatusTabs(counts);
    this._renderActiveBar(matched.length);
    this.mapCtrl.sync({ evalById, matched, records, prefs, ui });
    if (this.openModal) this._renderModal();

    const p = this.projectById.get(id);
    if (!p) return;
    const cardEl = document.querySelector(`[data-pid="${id}"]`);
    if (!cardEl) return;

    const ev = evalById.get(id);
    if (!ev?.matches) {
      cardEl.remove();
      return;
    }

    const temp = document.createElement('div');
    temp.innerHTML = this._cardMarkup(p, records[id] || {}, ev);
    const nextCard = temp.firstElementChild;
    if (nextCard) cardEl.replaceWith(nextCard);
  }

  _bindGlobalEvents() {
    const searchEl = document.getElementById('search-input');
    searchEl.value = this.store.state.filters.q || '';
    searchEl.addEventListener('input', (e) => {
      clearTimeout(this._searchTimer);
      const val = e.target.value;
      this._searchTimer = setTimeout(() => {
        this.renderedCount = BATCH_SIZE;
        this.store.updateFilters({ q: val });
      }, 110);
    });

    document.getElementById('search-clear').addEventListener('click', () => {
      searchEl.value = '';
      this.renderedCount = BATCH_SIZE;
      this.store.updateFilters({ q: '' });
    });

    document.getElementById('topbar').addEventListener('click', (e) => {
      const tab = e.target.closest('[data-status]');
      if (tab) {
        this.renderedCount = BATCH_SIZE;
        this.store.updateFilters({ status: tab.dataset.status });
        return;
      }
      const viewBtn = e.target.closest('[data-view]');
      if (viewBtn) {
        this.store.updateUI({ view: viewBtn.dataset.view });
        return;
      }
      const modeBtn = e.target.closest('[data-fmode]');
      if (modeBtn) {
        this.store.updateUI({ filterMode: modeBtn.dataset.fmode });
        return;
      }
      const qCat = e.target.closest('[data-qcat]');
      if (qCat) {
        this.renderedCount = BATCH_SIZE;
        const val = qCat.dataset.qcat;
        if (val === 'adult') {
          const cats = this.store.state.filters.cats;
          const isAdult = cats.inc.length === 2 && cats.inc.includes(3) && cats.inc.includes(4);
          this.store.updateFilters({
            cats: { ...cats, inc: isAdult ? [] : [3, 4], exc: cats.exc.filter((c) => c !== 3 && c !== 4) },
          });
        } else {
          this.store.toggleFacetValue('cats', Number(val));
        }
        return;
      }
      const qZone = e.target.closest('[data-qzone]');
      if (qZone) {
        this.renderedCount = BATCH_SIZE;
        this.store.toggleFacetValue('zones', qZone.dataset.qzone);
        return;
      }
      const topAct = e.target.closest('[data-top-act]');
      if (topAct) {
        const act = topAct.dataset.topAct;
        if (act === 'filters') {
          this.openModal = 'filters';
          this._renderModal();
        } else if (act === 'prefs') {
          this.openModal = 'prefs';
          this._renderModal();
        } else if (act === 'backup') {
          this.openModal = 'backup';
          this._renderModal();
        } else if (act === 'lang') {
          this.store.updateUI({ lang: this.store.state.ui.lang === 'ar' ? 'en' : 'ar' });
        } else if (act === 'theme') {
          this.store.updateUI({ theme: this.store.state.ui.theme === 'dark' ? 'light' : 'dark' });
        }
      }
    });

    document.getElementById('topbar').addEventListener('contextmenu', (e) => {
      const qCat = e.target.closest('[data-qcat]');
      if (qCat && qCat.dataset.qcat !== 'adult') {
        e.preventDefault();
        this.renderedCount = BATCH_SIZE;
        this.store.toggleFacetValue('cats', Number(qCat.dataset.qcat), 'exc');
        return;
      }
      const qZone = e.target.closest('[data-qzone]');
      if (qZone) {
        e.preventDefault();
        this.renderedCount = BATCH_SIZE;
        this.store.toggleFacetValue('zones', qZone.dataset.qzone, 'exc');
      }
    });

    document.getElementById('sort-select').addEventListener('change', (e) => {
      this.renderedCount = BATCH_SIZE;
      this.store.updateFilters({ sortBy: e.target.value });
    });

    document.getElementById('active-bar').addEventListener('click', (e) => {
      const rem = e.target.closest('[data-remove-chip]');
      if (rem) {
        this.renderedCount = BATCH_SIZE;
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
        if (act === 'ignore' && ids.length > 25 && !confirm(`🚫 ${ids.length}?`)) return;
        this.store.bulkAction(ids, act);
        return;
      }
      if (e.target.closest('[data-clear-filters]')) {
        document.getElementById('search-input').value = '';
        this.renderedCount = BATCH_SIZE;
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
            if (window.innerWidth <= 1020) window.scrollTo({ top: 0, behavior: 'smooth' });
            requestAnimationFrame(() => {
              this.mapCtrl._resizeCanvas();
              this.mapCtrl.focusTable(p.table, true);
            });
          }
        } else if (act === 'filter-tag') {
          this.renderedCount = BATCH_SIZE;
          this.store.toggleFacetValue('tags', btn.dataset.tag);
        } else if (act === 'open') {
          this.openModal = { type: 'detail', id };
          this._renderModal();
        } else if (act === 'desc') {
          btn.classList.toggle('expanded');
        }
        return;
      }

      if (e.target.closest('[data-load-more]')) {
        this.renderedCount += BATCH_SIZE;
        this._renderList();
      } else if (e.target.closest('[data-show-all]')) {
        this.renderedCount = this.evalResult?.matched.length || 9999;
        this._renderList();
      }
    });

    listPane.addEventListener('contextmenu', (e) => {
      const tagBtn = e.target.closest('[data-card-act="filter-tag"]');
      if (tagBtn) {
        e.preventDefault();
        this.renderedCount = BATCH_SIZE;
        this.store.toggleFacetValue('tags', tagBtn.dataset.tag, 'exc');
      }
    });

    listPane.addEventListener('input', (e) => {
      if (e.target.dataset.cardNote) {
        this.store.setNote(e.target.dataset.cardNote, e.target.value);
      }
    });

    const overlay = document.getElementById('modal-overlay');
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay || e.target.closest('[data-modal-close]')) {
        this.openModal = null;
        overlay.classList.add('hidden');
        return;
      }
      this._handleModalClick(e);
    });
    overlay.addEventListener('contextmenu', (e) => {
      const fchip = e.target.closest('[data-fchip]');
      if (fchip) {
        e.preventDefault();
        this.renderedCount = BATCH_SIZE;
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
      ['prefs', `⚡ ${this.t('prefs')} <b>${counts.prefs}</b>`],
      ['fav', `★ <b>${counts.fav}</b>`],
      ['todo', `⏳ <b>${counts.todo}</b>`],
      ['visited', `✓ <b>${counts.visited}</b>`],
      ['rated', `⭐ <b>${counts.rated}</b>`],
      ['noted', `📝 <b>${counts.noted}</b>`],
      ['ignored', `🚫 <b>${counts.ignored}</b>`],
    ];
    document.getElementById('status-tabs').innerHTML = statusTabs
      .map(
        ([k, lbl]) =>
          `<button class="stat-tab ${filters.status === k ? 'active' : ''}" data-status="${k}">${lbl}</button>`
      )
      .join('');
  }

  render() {
    const { filters, records, prefs, ui } = this.store.state;
    const lang = ui.lang === 'en' ? 'en' : 'ar';

    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.dataset.theme = ui.theme === 'light' ? 'light' : 'dark';

    this.evalResult = evaluateAll(this.projects, filters, records, prefs);
    const { evalById, matched, counts } = this.evalResult;

    const brandPill = document.querySelector('.brand-pill');
    if (brandPill) brandPill.textContent = `SAIF 26 · ${prefs.myBooth || 'S-H5-23'}`;
    document.getElementById('search-input').placeholder = this.t('searchPh');
    document.getElementById('search-clear').classList.toggle('hidden', !filters.q);

    this._renderStatusTabs(counts);

    const fCount = countActiveFilterRules(filters, prefs);
    document.getElementById('btn-filters').innerHTML = `🎛️ ${this.t('filters')}${
      fCount ? `<span class="count-badge">${fCount}</span>` : ''
    }`;
    document.getElementById('btn-prefs').innerHTML = `⚡ ${this.t('prefs')}`;
    document.getElementById('btn-lang').textContent = lang === 'ar' ? 'EN' : 'ع';
    document.getElementById('btn-theme').textContent = ui.theme === 'light' ? '🌙' : '☀️';

    for (const vb of document.querySelectorAll('[data-view]')) {
      vb.classList.toggle('active', vb.dataset.view === ui.view);
    }

    for (const mb of document.querySelectorAll('[data-fmode]')) {
      mb.classList.toggle('active', mb.dataset.fmode === (ui.filterMode || 'inc'));
    }
    document.querySelector('[data-fmode="inc"]').textContent = this.t('incMode');
    document.querySelector('[data-fmode="exc"]').textContent = this.t('excMode');

    const myZone = (prefs.myBooth || '').split('-')[1]?.[0];
    const catsHtml = [
      `<button class="qpill ${
        filters.cats.inc.length === 2 && filters.cats.inc.includes(3) && filters.cats.inc.includes(4) ? 'inc' : ''
      }" data-qcat="adult">18+</button>`,
      ...[4, 3, 2, 1].map((cid) => {
        const c = this.catMap.get(cid);
        const cls = filters.cats.inc.includes(cid) ? 'inc' : filters.cats.exc.includes(cid) ? 'exc' : '';
        return `<button class="qpill ${cls}" data-qcat="${cid}">${lang === 'ar' ? c.ar : c.en}</button>`;
      }),
    ].join('');

    const zonesHtml = Object.keys(ZONE_GEOMETRY)
      .map((z) => {
        const cls = filters.zones.inc.includes(z) ? 'inc' : filters.zones.exc.includes(z) ? 'exc' : '';
        return `<button class="qpill ${cls}" data-qzone="${z}">${z}${z === myZone ? '📍' : ''}</button>`;
      })
      .join('');

    document.getElementById('quick-pills').innerHTML = `${catsHtml}<span class="divider-v"></span>${zonesHtml}`;

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

    const ws = document.getElementById('workspace');
    ws.className = `workspace mode-${ui.view}`;

    this._renderList();
    if (ui.view !== 'list') {
      requestAnimationFrame(() => this.mapCtrl._resizeCanvas());
    }
    this.mapCtrl.sync({ evalById, matched, records, prefs, ui });
    if (this.openModal) this._renderModal();
  }

  _renderActiveBar(matchedLen) {
    const { filters, ui } = this.store.state;
    const lang = ui.lang === 'en' ? 'en' : 'ar';
    const chips = [];

    const addFacetChips = (key, labelFn) => {
      for (const v of filters[key].inc || []) chips.push([key, 'inc', v, `+ ${labelFn(v)}`]);
      for (const v of filters[key].exc || []) chips.push([key, 'exc', v, `🚫 ${labelFn(v)}`]);
    };

    addFacetChips('cats', (id) => this.catMap.get(id)?.[lang] || id);
    addFacetChips('paths', (id) => {
      const p = this.pathMap.get(id);
      return p ? `${p.icon} ${p[lang]}` : id;
    });
    addFacetChips('zones', (z) => z);
    addFacetChips('rows', (r) => `R${r}`);
    addFacetChips('tags', (id) => {
      const tg = this.tagMap.get(id);
      return tg ? `${tg.icon} ${tg[lang]}` : id;
    });
    addFacetChips('customTags', (id) => {
      const tg = CUSTOM_TAGS.find((t) => t.id === id);
      return tg ? `${tg.icon} ${tg[lang]}` : id;
    });
    addFacetChips('countries', (c) => `${this.meta.countries[c]?.[0] || ''} ${c}`);
    addFacetChips('sizes', (s) => `👥${s}`);

    for (const kw of filters.ignoreKeywords || []) chips.push(['kw', 'exc', kw, `🚫 "${kw}"`]);
    if (filters.intlMode !== 'all') chips.push(['intl', 'inc', filters.intlMode, `🌍 ${filters.intlMode}`]);
    if (filters.langMode !== 'all') chips.push(['lang', 'inc', filters.langMode, `Aa ${filters.langMode}`]);
    if (filters.ratingMode !== 'all') chips.push(['rat', 'inc', filters.ratingMode, `⭐ ${filters.ratingMode}`]);
    if (filters.minMatch > 0) chips.push(['match', 'inc', filters.minMatch, `⚡≥${filters.minMatch}`]);

    const chipsHtml = chips
      .map(
        ([key, mode, val, txt]) =>
          `<button class="active-chip ${mode}" data-remove-chip='${esc(JSON.stringify({ key, mode, val }))}'>${esc(txt)} ✕</button>`
      )
      .join('');

    const clearHtml =
      chips.length || filters.q
        ? `<button class="bulk-btn" data-clear-filters>${this.t('clear')}</button>`
        : '';

    const bulkHtml = `
      <div class="bulk-group">
        <span class="badge-mini">${matchedLen}</span>
        <button class="bulk-btn" data-bulk="fav">★+</button>
        <button class="bulk-btn" data-bulk="visit">✓+</button>
        <button class="bulk-btn" data-bulk="ignore">🚫+</button>
      </div>
    `;

    document.getElementById('active-bar').innerHTML = `${chipsHtml}${clearHtml}${bulkHtml}`;
  }

  _cardMarkup(p, rec, ev) {
    const { prefs, ui, filters } = this.store.state;
    const lang = ui.lang === 'en' ? 'en' : 'ar';
    const myTable = (prefs.myBooth || '').toUpperCase();
    const pathObj = this.pathMap.get(p.path);
    const catObj = this.catMap.get(p.cat);
    const isMe = p.table === myTable;
    const flags = p.allNats.map((n) => this.meta.countries[n]?.[0] || '').join('');

    const stars = [1, 2, 3, 4, 5]
      .map(
        (s) =>
          `<button class="star-btn ${(rec.rat || 0) >= s ? 'on' : ''}" data-card-act="rat" data-id="${p.id}" data-stars="${s}">★</button>`
      )
      .join('');

    const cTags = CUSTOM_TAGS.map(
      (t) =>
        `<button class="tag-pill ${(rec.tags || []).includes(t.id) ? 'on' : ''}" data-card-act="tag" data-id="${p.id}" data-tag="${t.id}">${t.icon}</button>`
    ).join('');

    const autoTags = p.tags
      .slice(0, 4)
      .map((tid) => {
        const tg = this.tagMap.get(tid);
        const activeCls = filters.tags.inc.includes(tid)
          ? 'inc'
          : filters.tags.exc.includes(tid)
          ? 'exc'
          : '';
        return `<button class="auto-tag ${activeCls}" data-card-act="filter-tag" data-tag="${tid}">${tg?.icon || ''} ${tg?.[lang] || tid}</button>`;
      })
      .join('');

    const membersHtml = p.members
      .map((m) => {
        const fl = m.nat ? this.meta.countries[m.nat]?.[0] || '' : '';
        const met = (rec.met || []).includes(m.n);
        const dispName = lang === 'ar' ? m.ar || m.n : m.n;
        const q = encodeURIComponent(`${m.n} ${m.nat || ''}`);
        return `<a class="member-chip ${met ? 'met' : ''}" href="https://www.linkedin.com/search/results/people/?keywords=${q}" target="_blank" rel="noopener" title="${esc(m.n)}">${m.l ? '👑 ' : ''}${esc(dispName)} ${fl}</a>`;
      })
      .join('');

    return `
      <article class="card ${rec.fav ? 'is-fav' : ''} ${rec.vis ? 'is-vis' : ''} ${ev.isIgnored ? 'is-ignored' : ''}" data-pid="${p.id}">
        <div class="card-top">
          <button class="badge-table ${isMe ? 'is-me' : ''}" data-card-act="locate" data-id="${p.id}">${p.table}</button>
          <span class="badge-cat c${p.cat}">${catObj?.[lang] || ''}</span>
          <span class="badge-path">${pathObj?.icon} ${pathObj?.[lang]}</span>
          <span class="badge-mini">${flags} ×${p.members.length}</span>
          <span class="badge-match">⚡${ev.matchScore}</span>
          <div class="card-quick-ops">
            <button class="act-btn fav ${rec.fav ? 'on' : ''}" data-card-act="fav" data-id="${p.id}">${rec.fav ? '★' : '☆'}</button>
            <button class="act-btn vis ${rec.vis ? 'on' : ''}" data-card-act="vis" data-id="${p.id}">✓</button>
            <button class="act-btn ign ${rec.ign ? 'on' : ''}" data-card-act="ign" data-id="${p.id}">🚫</button>
          </div>
        </div>
        <div class="card-title" data-card-act="open" data-id="${p.id}">${esc(p.title)}</div>
        <div class="card-desc" data-card-act="desc">${esc(p.desc)}</div>
        ${autoTags ? `<div class="card-tags-row">${autoTags}</div>` : ''}
        <div class="card-rate-bar">
          <div class="stars-row">${stars}</div>
          ${cTags}
        </div>
        <div class="members-row">${membersHtml}</div>
        <input class="note-inline" type="text" data-card-note="${p.id}" value="${esc(rec.note || '')}" placeholder="${this.t('notePh')}" />
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

    const slice = matched.slice(0, this.renderedCount);
    const cardsHtml = slice
      .map((p) => this._cardMarkup(p, records[p.id] || {}, evalById.get(p.id)))
      .join('');

    const remaining = matched.length - slice.length;
    const footer =
      remaining > 0
        ? `<div id="scroll-sentinel" style="display:flex;gap:8px">
             <button class="load-more-btn" style="flex:1" data-load-more>${this.t('showMore')} (+${Math.min(BATCH_SIZE, remaining)})</button>
             <button class="load-more-btn" data-show-all>${this.t('showAll')} (${matched.length})</button>
           </div>`
        : '';

    pane.innerHTML = cardsHtml + footer;

    if (this.observer) this.observer.disconnect();
    const sentinel = document.getElementById('scroll-sentinel');
    if (sentinel && typeof IntersectionObserver !== 'undefined') {
      this.observer = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting) {
            this.renderedCount += BATCH_SIZE;
            this._renderList();
          }
        },
        { root: pane, rootMargin: '180px' }
      );
      this.observer.observe(sentinel);
    }
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

    if (this.openModal === 'filters') {
      const fMode = ui.filterMode || 'inc';
      const chip = (key, val, label) => {
        const cls = filters[key].inc.includes(val) ? 'inc' : filters[key].exc.includes(val) ? 'exc' : '';
        return `<button class="fchip ${cls}" data-fchip='${esc(JSON.stringify({ key, val }))}'>${label}</button>`;
      };

      const filteredCountries = this.countryCounts.filter(([n]) => {
        if (!this.countrySearch) return true;
        const c = this.meta.countries[n];
        return `${n} ${c?.[1] || ''} ${c?.[2] || ''}`.toLowerCase().includes(this.countrySearch.toLowerCase());
      });

      body.innerHTML = `
        <div class="modal-head">
          <h3>🎛️ ${this.t('filters')}</h3>
          <div class="mode-toggle">
            <button class="${fMode === 'inc' ? 'active' : ''}" data-modal-fmode="inc">${this.t('incMode')}</button>
            <button class="${fMode === 'exc' ? 'active' : ''}" data-modal-fmode="exc">${this.t('excMode')}</button>
          </div>
          <button class="bulk-btn" data-modal-clear-filters>${this.t('clear')}</button>
          <button class="modal-close" data-modal-close>✕</button>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('cats')}</div>
          <div class="chip-grid">${this.meta.cats.map((c) => chip('cats', c.id, c[lang])).join('')}</div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('paths')}</div>
          <div class="chip-grid">${this.meta.paths.map((p) => chip('paths', p.id, `${p.icon} ${p[lang]}`)).join('')}</div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('tags')}</div>
          <div class="chip-grid">${this.meta.tags.map((tg) => chip('tags', tg.id, `${tg.icon} ${tg[lang]}`)).join('')}</div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('customTags')}</div>
          <div class="chip-grid">${CUSTOM_TAGS.map((tg) => chip('customTags', tg.id, `${tg.icon} ${tg[lang]}`)).join('')}</div>
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
          <div class="sec-hdr">${this.t('sizes')} · ${this.t('lang')} · ${this.t('rating')} · ${this.t('minMatch')}</div>
          <div class="chip-grid">
            ${[1, 2, 3, 4, 5, 6].map((s) => chip('sizes', s, `👥${s}`)).join('')}
            <span class="divider-v"></span>
            ${[
              ['all', '🌐 All'],
              ['intl_leader', '🌍 Intl Leader'],
              ['has_intl', '🌐 Any Intl'],
              ['mixed', '🤝 Mixed'],
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
            <span class="divider-v"></span>
            ${[
              ['all', '⭐ All'],
              ['rated', '⭐ >0'],
              ['unrated', '☆ 0'],
              ['3+', '3★+'],
              ['4+', '4★+'],
              ['5', '5★'],
            ]
              .map(([v, l]) => `<button class="fchip ${filters.ratingMode === v ? 'inc' : ''}" data-set-filter='{"ratingMode":"${v}"}'>${l}</button>`)
              .join('')}
            <span class="divider-v"></span>
            ${[0, 30, 50, 70]
              .map((m) => `<button class="fchip ${filters.minMatch === m ? 'inc' : ''}" data-set-filter='{"minMatch":${m}}'>⚡≥${m}</button>`)
              .join('')}
          </div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('countries')} (${this.countryCounts.length})</div>
          <input class="kw-input" id="country-search-input" type="text" value="${esc(this.countrySearch)}" placeholder="🔍 Country..." />
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
          <div class="sec-hdr">${this.t('ignoreKw')}</div>
          <div class="kw-row">
            <input class="kw-input" id="ign-kw-input" type="text" placeholder="${this.t('addKwPh')}" />
            <button class="btn-primary" data-add-ign-kw>${this.t('add')}</button>
          </div>
          <div class="chip-grid">
            ${(filters.ignoreKeywords || [])
              .map((w) => `<button class="fchip exc" data-rem-ign-kw="${esc(w)}">🚫 ${esc(w)} ✕</button>`)
              .join('')}
          </div>
        </div>
      `;
    } else if (this.openModal === 'prefs') {
      const prefBtn = (field, val, label, cls = 'inc') => {
        const active = (prefs[field] || []).includes(val);
        return `<button class="fchip ${active ? cls : ''}" data-pref-toggle='${esc(JSON.stringify({ field, val }))}'>${label}</button>`;
      };

      body.innerHTML = `
        <div class="modal-head">
          <h3>⚡ ${this.t('prefs')}</h3>
          <button class="modal-close" data-modal-close>✕</button>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('myBooth')} · ${this.t('intlBoost')}</div>
          <div class="kw-row">
            <input class="kw-input" id="pref-my-booth" type="text" value="${esc(prefs.myBooth)}" style="max-width:140px;direction:ltr" />
            <input class="kw-input" id="pref-intl-boost" type="number" min="0" max="30" value="${prefs.boostIntl ?? 12}" style="max-width:90px" />
          </div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('prefCats')}</div>
          <div class="chip-grid">${this.meta.cats.map((c) => prefBtn('prefCats', c.id, c[lang])).join('')}</div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('prefPaths')}</div>
          <div class="chip-grid">${this.meta.paths.map((p) => prefBtn('prefPaths', p.id, `${p.icon} ${p[lang]}`)).join('')}</div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('prefTags')}</div>
          <div class="chip-grid">${this.meta.tags.map((t) => prefBtn('prefTags', t.id, `${t.icon} ${t[lang]}`)).join('')}</div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('prefKws')}</div>
          <div class="kw-row">
            <input class="kw-input" id="pref-kw-input" type="text" placeholder="hydrogen, llm, startup..." />
            <button class="btn-primary" data-add-pref-kw>${this.t('add')}</button>
          </div>
          <div class="chip-grid">
            ${(prefs.prefKeywords || [])
              .map((w) => `<button class="fchip inc" data-rem-pref-kw="${esc(w)}">⚡ ${esc(w)} ✕</button>`)
              .join('')}
          </div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('globIgnCats')} / ${this.t('globIgnPaths')} / ${this.t('globIgnTags')}</div>
          <div class="chip-grid">
            ${this.meta.cats.map((c) => prefBtn('ignoreCats', c.id, `🚫 ${c[lang]}`, 'exc')).join('')}
            ${this.meta.paths.map((p) => prefBtn('ignorePaths', p.id, `🚫 ${p.icon} ${p[lang]}`, 'exc')).join('')}
            ${this.meta.tags.map((t) => prefBtn('ignoreTags', t.id, `🚫 ${t.icon} ${t[lang]}`, 'exc')).join('')}
          </div>
        </div>

        <div class="filter-section">
          <div class="sec-hdr">${this.t('globIgnKws')}</div>
          <div class="kw-row">
            <input class="kw-input" id="pref-ign-kw-input" type="text" placeholder="${this.t('addKwPh')}" />
            <button class="btn-danger" data-add-pref-ign-kw>${this.t('add')}</button>
          </div>
          <div class="chip-grid">
            ${(prefs.ignoreKeywords || [])
              .map((w) => `<button class="fchip exc" data-rem-pref-ign-kw="${esc(w)}">🚫 ${esc(w)} ✕</button>`)
              .join('')}
          </div>
        </div>
      `;
    } else if (this.openModal === 'backup') {
      const { counts } = this.evalResult;
      body.innerHTML = `
        <div class="modal-head">
          <h3>💾 localStorage</h3>
          <button class="modal-close" data-modal-close>✕</button>
        </div>
        <div class="chip-grid">
          <span class="badge-mini">★ ${counts.fav}</span>
          <span class="badge-mini">✓ ${counts.visited}</span>
          <span class="badge-mini">⭐ ${counts.rated}</span>
          <span class="badge-mini">📝 ${counts.noted}</span>
          <span class="badge-mini">🚫 ${counts.ignored}</span>
        </div>
        <div class="chip-grid">
          <button class="btn-primary" data-backup-act="export-json">${this.t('exportJson')}</button>
          <button class="btn-primary" data-backup-act="export-csv">${this.t('exportCsv')}</button>
          <label class="fchip" style="cursor:pointer">
            ${this.t('importMerge')}
            <input type="file" accept=".json" id="import-merge-file" style="display:none" />
          </label>
          <label class="fchip" style="cursor:pointer">
            ${this.t('importReplace')}
            <input type="file" accept=".json" id="import-replace-file" style="display:none" />
          </label>
          <button class="btn-danger" data-backup-act="reset">${this.t('resetAll')}</button>
        </div>
      `;
    } else if (this.openModal?.type === 'detail') {
      const p = this.projectById.get(this.openModal.id);
      if (!p) {
        this.openModal = null;
        overlay.classList.add('hidden');
        return;
      }
      const rec = records[p.id] || {};
      const ev = this.evalResult.evalById.get(p.id);
      const pathObj = this.pathMap.get(p.path);
      const catObj = this.catMap.get(p.cat);

      const starRow = [1, 2, 3, 4, 5]
        .map(
          (s) =>
            `<button class="star-btn ${(rec.rat || 0) >= s ? 'on' : ''}" data-detail-act="rat" data-id="${p.id}" data-stars="${s}">★</button>`
        )
        .join('');

      const subBox = (axis, lbl) => {
        const val = rec.sub?.[axis] || 0;
        const stars = [1, 2, 3, 4, 5]
          .map(
            (s) =>
              `<button class="star-btn ${val >= s ? 'on' : ''}" data-detail-act="sub" data-id="${p.id}" data-axis="${axis}" data-stars="${s}">★</button>`
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
              <button class="act-btn vis ${met ? 'on' : ''}" data-detail-act="met" data-id="${p.id}" data-member="${esc(m.n)}">${this.t('met')}</button>
              <span>${m.l ? '👑' : '👤'} <b>${esc(m.ar || m.n)}</b> · <small style="color:var(--muted)">${esc(m.n)}</small> ${fl}</span>
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
          <span class="badge-match">⚡${ev?.matchScore ?? 0}</span>
          <button class="modal-close" data-modal-close>✕</button>
        </div>
        <h3>${esc(p.title)}</h3>
        <div class="chip-grid">
          <span class="badge-path">${pathObj?.icon} ${pathObj?.[lang]}</span>
          ${p.tags
            .map((tid) => {
              const tg = this.tagMap.get(tid);
              return `<span class="auto-tag">${tg?.icon || ''} ${tg?.[lang] || tid}</span>`;
            })
            .join('')}
        </div>
        <div class="detail-desc">${esc(p.desc)}</div>
        <div class="card-rate-bar">
          <button class="act-btn fav ${rec.fav ? 'on' : ''}" data-detail-act="fav" data-id="${p.id}">${rec.fav ? '★' : '☆'}</button>
          <button class="act-btn vis ${rec.vis ? 'on' : ''}" data-detail-act="vis" data-id="${p.id}">✓</button>
          <div class="stars-row">${starRow}</div>
          <button class="act-btn ign ${rec.ign ? 'on' : ''}" data-detail-act="ign" data-id="${p.id}">🚫</button>
          <button class="act-btn" data-detail-act="locate" data-id="${p.id}">${this.t('locate')}</button>
        </div>
        <div class="sub-ratings">
          ${subBox('tech', this.t('subTech'))}
          ${subBox('pitch', this.t('subPitch'))}
          ${subBox('fit', this.t('subFit'))}
        </div>
        <div class="chip-grid">
          ${CUSTOM_TAGS.map(
            (tg) =>
              `<button class="tag-pill ${(rec.tags || []).includes(tg.id) ? 'on' : ''}" data-detail-act="tag" data-id="${p.id}" data-tag="${tg.id}">${tg.icon} ${tg[lang]}</button>`
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
      this.renderedCount = BATCH_SIZE;
      return this.store.resetFilters();
    }

    const fchip = e.target.closest('[data-fchip]');
    if (fchip) {
      this.renderedCount = BATCH_SIZE;
      const { key, val } = JSON.parse(fchip.dataset.fchip);
      return this.store.toggleFacetValue(key, val);
    }

    const setF = e.target.closest('[data-set-filter]');
    if (setF) {
      this.renderedCount = BATCH_SIZE;
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
        this.openModal = null;
        document.getElementById('modal-overlay').classList.add('hidden');
        if (p) {
          if (this.store.state.ui.view === 'list') {
            this.store.updateUI({ view: window.innerWidth <= 900 ? 'map' : 'split' });
          }
          requestAnimationFrame(() => {
            this.mapCtrl._resizeCanvas();
            this.mapCtrl.focusTable(p.table, true);
          });
        }
      }
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
      return this.store.updatePrefs({ myBooth: e.target.value.trim().toUpperCase() || 'S-H5-23' });
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
          this.openModal = null;
          document.getElementById('modal-overlay').classList.add('hidden');
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
