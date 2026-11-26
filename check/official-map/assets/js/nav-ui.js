/* =========================================================
   واجهة التنقّل فوق الخريطة — نسخة الويب من «المرشد بالتجربة الكاملة» في تحكيم.
     · «من / إلى» ثابتة في الزاوية — الخريطة للإرشاد وحده: بحث يتسامح مع الهمزات والتاء المربوطة
       والأرقام الهندية والتشكيل، ويرتّب ما يبدأ بما كتبته أولًا.
     · الحقل المفتوح يقبل أيضًا الضغط على طاولة في الخريطة نفسها.
     · اكتمال الحقلين ⇠ الطريق يُرسم، وأسفل الشاشة مدّته وطوله و«ابدأ».
     · «ابدأ» ⇠ رحلة بمراحل: تعليمة كل منعطف في الأعلى، ورجوع/تالي في الأسفل،
       وفي آخرها «وصلت» — ووجهتك تصبح نقطة انطلاقك القادمة.
   ========================================================= */
import { button, iconButton, pressable, field, icon, esc } from '../primitives/ui.js';
import { tr, EN } from './i18n.js';

const I = {
  close: icon('<path d="M18 6L6 18M6 6l12 12"/>', 16),
  swap: icon('<path d="M7 4v16M7 4L3 8M7 4l4 4M17 20V4M17 20l-4-4M17 20l4-4"/>', 18),
  clear: icon('<circle cx="12" cy="12" r="9"/><path d="M15 9l-6 6M9 9l6 6"/>', 16),
  walk: icon('<circle cx="13" cy="4" r="2"/><path d="M10 21l2-6 3 3v3M8 12l2-4 4 1 2 4 3 1"/>', 18),
  back: icon('<path d="M9 6l6 6-6 6"/>', 18, 2.4),
  from: '<i class="nav-field__from" aria-hidden="true"></i>',
  to: icon('<path d="M12 21s-7-6.2-7-11.5a7 7 0 0114 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>', 18)
};
// أيقونة كبيرة لنوع المكان في النتائج — كإطارات نتائج التطبيق
const KIND = {
  team: ['<circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2.5"/><path d="M3 20v-1a6 6 0 0112 0v1M15 20v-1a4 4 0 017 0v1"/>', 'brand', tr('فريق', 'Team')],
  table: ['<rect x="3" y="8" width="18" height="4" rx="1"/><path d="M6 12v8M18 12v8"/>', 'brand', tr('طاولة', 'Table')],
  zone: ['<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>', 'ok', tr('منطقة', 'Zone')],
  entrance: ['<path d="M3 21h18M6 21V4a1 1 0 011-1h10a1 1 0 011 1v17"/><path d="M14 12h.01"/>', 'warn', tr('مدخل', 'Entrance')],
  registration: ['<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2"/><path d="M6 16a3 3 0 016 0M14 10h4M14 14h3"/>', 'warn', tr('تسجيل', 'Registration')],
  photo: ['<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>', 'warn', tr('تصوير', 'Photo spot')],
  stage: ['<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0014 0M12 18v3"/>', 'brand', tr('المسرح', 'Stage')],
  vip: ['<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>', 'warn', tr('كبار الشخصيات', 'VIP')],
  pillar: ['<path d="M4 21h16M5 4h14M7 4v17M17 4v17M12 4v17"/>', 'idle', tr('عمود', 'Pillar')],
  booth: ['<path d="M4 20V9l8-5 8 5v11"/><path d="M4 13h16M9 20v-4h6v4"/>', 'brand', tr('بوث', 'Booth')],
  room: ['<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M4 12h6M14 4v6"/>', 'idle', tr('قاعة', 'Room')],
  door: ['<path d="M3 21h18M6 21V4a1 1 0 011-1h10a1 1 0 011 1v17"/><path d="M14 12h.01"/>', 'warn', tr('مدخل', 'Entrance')],
  exit: ['<path d="M15 4h4v16h-4M10 8l-4 4 4 4M6 12h10"/>', 'ok', tr('مخرج طوارئ', 'Emergency exit')],
  service: ['<circle cx="12" cy="12" r="9"/><path d="M12 8v.01M11 12h1v5h1"/>', 'idle', tr('خدمة', 'Service')],
  seats: ['<path d="M5 11V6a2 2 0 012-2h10a2 2 0 012 2v5M3 11h18v4H3zM5 15v5M19 15v5"/>', 'brand', tr('جلوس', 'Seating')],
  food: ['<path d="M7 3v8a2 2 0 002 2v8M11 3v8M17 3c-2 0-3 2-3 5s1 4 3 4v9"/>', 'warn', tr('طعام', 'Food')],
  here: ['<circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2"/>', 'brand', tr('موقعك', 'Your location')],
  kiosk: ['<rect x="7" y="3" width="10" height="13" rx="1.5"/><path d="M12 16v5M8 21h8"/>', 'idle', tr('شاشة إرشاد', 'Info kiosk')],
  office: ['<rect x="4" y="7" width="16" height="13" rx="2"/><path d="M9 7V5a1 1 0 011-1h4a1 1 0 011 1v2M4 13h16"/>', 'idle', tr('مكتب', 'Office')],
  firstaid: ['<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M12 8v8M8 12h8"/>', 'warn', tr('إسعاف', 'First aid')],
  info: ['<circle cx="12" cy="12" r="9"/><path d="M12 8v.01M11 12h1v5h1"/>', 'brand', tr('استعلامات', 'Information')],
  shop: ['<path d="M5 8h14l-1 12H6zM9 8V6a3 3 0 016 0v2"/>', 'idle', tr('متجر', 'Shop')],
  elevator: ['<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M9 9l3-3 3 3M9 15l3 3 3-3"/>', 'idle', tr('مصعد', 'Elevator')],
  prayer: ['<path d="M7 20v-7a5 5 0 0110 0v7M12 6V3M4 20V9l1-2 1 2v11M18 20V9l1-2 1 2v11M3 20h18M11 20v-3a1 1 0 012 0v3"/>', 'brand', tr('مصلى', 'Prayer room')],
  stairs: ['<path d="M4 20h4v-4h4v-4h4V8h4"/>', 'idle', tr('درج', 'Stairs')],
  toilet: ['<circle cx="8" cy="5" r="2"/><circle cx="16" cy="5" r="2"/><path d="M6 21v-7H5l1-5h4l1 5h-1v7M16 9v12M14 9h4v6h-4z"/>', 'idle', tr('دورات مياه', 'Restrooms')]
};
const MANEUVER = {
  right: '<path d="M6 20v-7a4 4 0 014-4h9M15 5l4 4-4 4"/>',
  left: '<path d="M18 20v-7a4 4 0 00-4-4H5M9 5L5 9l4 4"/>',
  'slight-right': '<path d="M7 20V12l9-8M10 4h6v6"/>',
  'slight-left': '<path d="M17 20V12L8 4M14 4H8v6"/>',
  arrive: '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0114 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
  straight: '<path d="M12 20V4M6 10l6-6 6 6"/>'
};
const ORDER = ['here', 'team', 'entrance', 'door', 'stage', 'zone', 'booth', 'registration', 'vip', 'room', 'service', 'toilet', 'food', 'seats', 'exit', 'photo', 'table', 'pillar'];
const n = v => Number(v).toLocaleString('en-US');
// العدد مع المعدود: خطوة · خطوتان · 3 خطوات · 11 خطوة
const stepsWord = c => EN ? n(c) + (c === 1 ? ' step' : ' steps')
  : c === 1 ? 'خطوة واحدة' : c === 2 ? 'خطوتان' : c <= 10 ? n(c) + ' خطوات' : n(c) + ' خطوة';

/* ---------- البحث: نفس تطبيع VenueSearch في التطبيق ---------- */
const FOLD = { 'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا', 'ة': 'ه', 'ى': 'ي', 'ؤ': 'و', 'ئ': 'ي', 'ـ': '', '-': '', '·': ' ', '،': ' ' };
export function normalize(text) {
  let s = String(text || '').normalize('NFKD').replace(/[̀-ًͯ-ٰٟ]/g, '').toLowerCase();
  s = [...s].map(c => {
    if (FOLD[c] !== undefined) return FOLD[c];
    const k = c.charCodeAt(0);
    if (k >= 0x660 && k <= 0x669) return String(k - 0x660);
    if (k >= 0x6F0 && k <= 0x6F9) return String(k - 0x6F0);
    return c;
  }).join('');
  return s.split(/\s+/).filter(Boolean).join(' ');
}
function makeIndex(places) {
  const entries = places.map(place => {
    const name = normalize(place.name), aliases = (place.aliases || []).map(normalize);
    return { place, name, words: name.split(' '), aliases, hay: [name, normalize(place.sub), ...aliases].join(' ') };
  });
  return q => {
    q = normalize(q);
    if (!q) return [];
    const tokens = q.split(' ');
    return entries.filter(e => tokens.every(t => e.hay.includes(t))).map(e => {
      const score = e.aliases.includes(q) || e.name === q ? 0 : e.name.startsWith(q) ? 1
        : e.words.some(w => w.startsWith(tokens[0])) ? 2 : e.name.includes(q) ? 3 : 4;
      return [e.place, score * 10 + (ORDER.indexOf(e.place.kind) + 1 || 9)];
    // تعادل بين جناحين: بترتيب الكود (C4-20 ثم C4-21)، لا بطول اسم الفريق
    }).sort((a, b) => a[1] - b[1] || (a[0].code && b[0].code ? a[0].code.localeCompare(b[0].code, 'en', { numeric: true })
      : a[0].name.length - b[0].name.length)).slice(0, 40).map(x => x[0]);
  };
}

/* =========================================================
   التركيب
   ========================================================= */
// map: طبقة الإرشاد (wayfinding.js) — حالة الحدث للأسماء والطاولات
export function mountNavUI(venue, map, mountNav, site) {
  // المشرف: الاتجاهات ليست أساس عمله — البطاقة مطويّة في زرّ بزاوية الخريطة حتى يطلبها (admin-ui.js)
  const ADMIN = document.body.classList.contains('is-admin');
  const ui = { open: !ADMIN, editing: null, from: null, to: null, text: { from: '', to: '' },
    route: null, failed: false, journey: null, places: [], heading: 0 };
  let find = () => [];

  const nav = mountNav(venue, site, map.state, msg => {
    if (msg.type === 'places') { ui.places = msg.items; find = makeIndex(msg.items); }
    else if (msg.type === 'route') {
      ui.route = msg.ok ? msg : null; ui.failed = !msg.ok; ui.journey = null;
      render();
      // جاء من رمز الشاشة بمسار: التوجيه يبدأ وحده — «التالي» حتى الوصول
      if (ui.route && ui.autostart) { ui.autostart = false; setTimeout(() => nav.startJourney(), 700); }
    } else if (msg.type === 'journey') { ui.journey = { step: msg.step, count: msg.count }; render(); }
    else if (msg.type === 'camera') { ui.heading = msg.heading; renderCompass(); }
  });
  // وصلت الفرق من الباك اند: يُعاد بناء الفهرس فيُبحث بأسمائها وأكوادها
  document.addEventListener('map:data', () => nav.reindex());

  /* ---------- الأسطح ---------- */
  const card = document.createElement('section');
  card.className = 'nav-card';
  card.setAttribute('aria-label', tr('الاتجاهات داخل القاعة', 'Directions inside the hall'));
  card.hidden = true;
  document.body.appendChild(card);

  const bottom = document.createElement('div');
  bottom.className = 'nav-bottom';
  bottom.setAttribute('role', 'region');
  bottom.setAttribute('aria-label', tr('الطريق', 'Route'));
  bottom.setAttribute('aria-live', 'polite');
  bottom.hidden = true;
  document.body.appendChild(bottom);

  const banner = document.createElement('div');
  banner.className = 'nav-banner';
  banner.setAttribute('aria-live', 'polite');
  banner.hidden = true;
  document.body.appendChild(banner);

  // البوصلة تظهر حين يدور المشهد عن اتجاهه الأصلي، وتعيده بضغطة — كخرائط Apple
  const compass = document.createElement('div');
  compass.className = 'nav-compass';
  const bar = document.querySelector('.map-bar');
  (bar || document.body).appendChild(compass);

  /* ---------- الحالة ---------- */
  const setPlace = (field, place) => {
    ui[field] = place;
    ui.text[field] = place ? place.name : '';
  };
  function routeIfReady() {
    if (ui.from && ui.to && ui.from.id !== ui.to.id) { nav.route(ui.from.id, ui.to.id); return; }
    ui.route = null; ui.failed = false;
    nav.clearRoute();
    // مكان واحد فقط: دبّوس عليه والكاميرا تذهب إليه
    const one = ui.to || ui.from;
    if (one) nav.focus(one.id);
  }
  function open(toId) {
    if (ui.journey) return;              // أثناء الرحلة الوجهة ثابتة حتى تنهيها
    ui.open = true;
    nav.reindex();
    // حقل مفتوح ⇠ المكان يملؤه هو، لا «إلى» دائمًا
    if (toId && ui.editing && nav.place(toId)) { pick(ui.editing, nav.place(toId)); return; }
    if (toId) {
      const place = nav.place(toId);
      if (place) setPlace('to', place);
      // من لم يحدّد مكانه يبدأ من المدخل الأقرب لما يعرفه الزوار، ويغيّره من «من»
      if (!ui.from) setPlace('from', nav.place(home()));
      ui.editing = null;
      routeIfReady();
    } else ui.editing = ui.to ? 'from' : 'to';
    render(true);
  }
  // نقطة الانطلاق الافتراضية: موقع شاشة الإرشاد إن كانت الصفحة تعمل عليها، وإلا مدخل الموقع
  const home = () => site.here ? 'here' : site.start || 'entrance:0';
  // البطاقة لا تُغلق: المسح يعيدها كما بدأت — «من» موقعك الحالي على الشاشة، وفارغة في غيرها
  // refocus=false: مسح بلا إعادة فتح القائمة (زرّ X وقائمة النتائج مفتوحة)
  function close(refocus = true) {
    nav.clearRoute();
    Object.assign(ui, { editing: null, route: null, failed: false, journey: null });
    setPlace('from', site.here ? nav.place('here') : null); setPlace('to', null);
    // المشرف: المسح يطوي البطاقة في زرّها
    if (ADMIN && refocus) { ui.open = false; render(); return; }
    render();
    const input = card.querySelector('[data-input="to"]');
    if (input && refocus) input.focus({ preventScroll: true });
  }
  // في البطاقة ما يُمسح: وجهة، أو نص مكتوب، أو بداية غير الافتراضية
  const filled = () => !!(ui.to || ui.text.to || ui.text.from !== (site.here ? tr('موقعك الحالي', 'Your location') : ''));

  /* ---------- الرسم ---------- */
  function fieldRow(f) {
    const on = ui.editing === f;
    return '<div class="nav-field' + (on ? ' is-on' : '') + '" data-field="' + f + '">' +
      '<span class="nav-field__icon nav-field__icon--' + f + '">' + I[f] + '</span>' +
      '<span class="nav-field__label">' + (f === 'from' ? tr('من', 'From') : tr('إلى', 'To')) + '</span>' +
      field(f === 'from' ? tr('من أين تنطلق؟', 'Where are you starting?') : tr('إلى أين؟', 'Where to?'), { 'data-input': f, value: ui.text[f], autocomplete: 'off', enterkeyhint: 'search' }) +
      (on && ui.text[f] ? iconButton(I.clear, tr('مسح', 'Clear'), { 'data-n': 'clear', 'data-f': f }, 'nav-field__clear') : '') +
    '</div>';
  }
  function matches(f) {
    const text = ui.text[f];
    if (text && !(ui[f] && ui[f].name === text)) return find(text);
    // بلا كتابة: ما يحتاجه الزائر عادة — المداخل والمسرح والتسجيل
    const other = ui[f === 'from' ? 'to' : 'from'];
    const list = site.suggest
      ? site.suggest.map(id => ui.places.find(p => p.id === id)).filter(Boolean)
      : ui.places.filter(p => ['entrance', 'stage', 'registration'].includes(p.kind));
    // في «من» على شاشة الإرشاد: موقعك الحالي أولًا
    const here = f === 'from' && site.here ? [nav.place('here')].filter(Boolean) : [];
    return here.concat(list).filter(p => !other || p.id !== other.id);
  }
  const frame = p => {
    const k = KIND[p.kind] || KIND.pillar;
    return pressable(
      '<span class="nav-place__icon nav-place__icon--' + k[1] + '">' + icon(k[0], 22, 1.9) + '</span>' +
      '<span class="nav-place__main"><b>' + esc(p.name) + '</b><span>' + esc(p.sub || k[2]) + '</span></span>',
      'nav-place', { 'data-n': 'pick', 'data-id': p.id });
  };
  function results() {
    const f = ui.editing;
    if (!f) return '';
    const list = matches(f), typed = ui.text[f] && !(ui[f] && ui[f].name === ui.text[f]);
    return '<div class="nav-results" role="listbox" aria-label="' + tr('نتائج البحث', 'Search results') + '">' +
      (!typed ? '<p class="nav-results__hint">' + esc(site.hint || tr('اكتب اسم فريق أو طاولة أو منطقة أو مدخل أو عمود — أو اضغط طاولة على الخريطة', 'Type a team, table, zone, entrance or pillar — or tap a table on the map')) + '</p>' : '') +
      (list.length ? list.map(frame).join('') : typed ? '<p class="nav-results__empty">' + tr('لا شيء بهذا الاسم في القاعة', 'Nothing in the hall matches that') + '</p>' : '') +
    '</div>';
  }

  function renderCard(entering) {
    const keep = document.activeElement && card.contains(document.activeElement) ? document.activeElement.dataset.input : null;
    card.hidden = !ui.open || !!ui.journey;
    if (card.hidden) return;
    card.innerHTML =
      '<div class="nav-card__box">' +
        '<div class="nav-card__head"><h2>' + tr('الاتجاهات', 'Directions') + '</h2>' +
          // X ظاهر متى كانت البطاقة مفعّلة — فيها ما يُمسح، أو حقل مفتوح بقائمة النتائج (ليُعرف كيف يُخرج منها)
          (filled() || ui.editing || ADMIN ? iconButton(I.close, tr('مسح الاتجاهات', 'Clear directions'), { 'data-n': 'close' }) : '') + '</div>' +
        '<div class="nav-card__fields"><div class="nav-card__rows">' + fieldRow('from') + fieldRow('to') + '</div>' +
          (ui.from || ui.to ? iconButton(I.swap, tr('تبديل البداية والوجهة', 'Swap start and destination'), { 'data-n': 'swap' }, 'nav-card__swap') : '') +
        '</div>' +
      '</div>' + results();
    const target = keep || (entering && ui.editing);
    if (target) {
      const input = card.querySelector('[data-input="' + target + '"]');
      input.focus({ preventScroll: true });
      input.setSelectionRange(input.value.length, input.value.length);
    }
  }

  function renderBottom() {
    let html = '';
    const r = ui.route, j = ui.journey;
    if (j && r) {
      const last = j.step >= j.count - 1, legs = Math.max(1, j.count - 1);
      html = '<div class="nav-pill nav-journey">' +
        '<p class="nav-pill__text"><b>' + (last ? tr('عند الوجهة', 'At your destination') : tr('الخطوة ', 'Step ') + n(j.step + 1) + tr(' من ', ' of ') + n(legs)) + '</b>' +
          (ui.to ? '<span>' + esc(ui.to.name) + '</span>' : '') + '</p>' +
        iconButton(I.back, tr('الخطوة السابقة', 'Previous step'), { 'data-n': 'prev', disabled: j.step === 0 }, 'nav-journey__prev') +
        button(last ? tr('وصلت', 'Arrived') : tr('التالي', 'Next'), { variant: 'primary', size: 'lg', attrs: { 'data-n': 'next' }, cls: last ? 'nav-arrived' : '' }) +
      '</div>';
    } else if (r && !ui.editing) {
      html = '<div class="nav-pill nav-route">' +
        '<p class="nav-pill__text"><b>' + n(r.minutes) + tr(' د', ' min') + '</b><span>' + n(r.meters) + tr(' م مشيًا', ' m walk') + (site.here ? tr(' إلى ', ' to ') + esc(ui.to ? ui.to.name : '') : ' · ' + stepsWord(r.steps.length)) + '</span></p>' +
        // على شاشة الإرشاد: المسار نظرة عامة فقط — لا خطوات ولا «ابدأ»؛ التوجيه خطوة بخطوة في الجوال (رمز QR)
        (site.here ? '' :
          '<ol class="nav-route__steps">' + r.steps.map(s => '<li><span>' + icon(MANEUVER[s.icon] || MANEUVER.straight, 16) + '</span>' + esc(s.text) + '</li>').join('') + '</ol>' +
          button(tr('ابدأ', 'Start'), { variant: 'primary', size: 'lg', icon: I.walk, attrs: { 'data-n': 'start' } })) +
        iconButton(I.close, tr('إلغاء الطريق', 'Cancel route'), { 'data-n': 'unroute' }, 'nav-pill__close') +
      '</div>';
    } else if (ui.failed && !ui.editing && ui.from && ui.to) {
      html = '<p class="nav-pill nav-failed">' + tr('لم نجد طريقًا بين هذين المكانين', 'No route found between these two places') + '</p>';
    }
    bottom.hidden = !html;
    bottom.innerHTML = html;
  }

  function renderBanner() {
    const r = ui.route, j = ui.journey;
    banner.hidden = !(r && j);
    if (banner.hidden) return;
    const step = r.steps[Math.min(j.step, r.steps.length - 1)], last = j.step >= j.count - 1, legs = Math.max(1, j.count - 1);
    // التعليمة نفسها هي العنوان؛ والطول من المخطط تقريبي — لا عدّاد يدّعي معرفة مكانك
    banner.innerHTML =
      '<span class="nav-banner__icon' + (last ? ' is-arrived' : '') + '">' + icon(MANEUVER[step.icon] || MANEUVER.straight, 34, 2.4) + '</span>' +
      '<p class="nav-banner__text"><b>' + esc(step.text) + '</b><span>' +
        (last ? tr('أنت عند وجهتك', 'You have arrived') : tr(j.step === legs - 1 ? 'على بُعد نحو ' : 'بعد نحو ', 'In about ') + n(step.meters) + tr(' م', ' m')) + '</span></p>' +
      iconButton(I.close, tr('إنهاء التوجيه', 'End guidance'), { 'data-n': 'end' }, 'nav-banner__end');
  }

  function renderCompass() {
    const off = Math.abs(ui.heading) > 1.5;
    compass.hidden = !off;
    compass.innerHTML = off ? iconButton('<i class="nav-needle" style="transform:rotate(' + ui.heading + 'deg)"></i>', tr('إعادة الاتجاه', 'Reset heading'), { 'data-n': 'north' }, 'nav-compass__btn') : '';
  }

  // الطريق يتمركز في الجزء الظاهر من الخريطة: بطاقة الاتجاهات تغطي الطرف الأيمن
  function applyInsets() {
    // بلا طريق لا نزيح المشهد: فتح البطاقة وحده لا يحرّك القاعة
    const r = card.hidden || !ui.route ? null : card.getBoundingClientRect();
    // على الشاشة الضيقة البطاقة بعرضها كله فوق المشهد: لا جانب نزيح عنه.
    // بالعربية البطاقة في اليمين، وبالإنجليزية في اليسار
    const side = r && r.width && r.width < innerWidth / 2;
    const onRight = side && r.left > innerWidth / 2;
    // وما يغطي الخريطة دون أن يزيحها — يبقى المسار وطرفاه خارجه:
    // البطاقة بعرض الشاشة فوق، وشريط الطريق تحت، وأزرار الخريطة على جانبها
    const cover = { top: 0, bottom: 0, left: 0, right: 0 };
    if (ui.route) {
      if (r && r.height && !side) cover.top = Math.max(0, r.bottom);
      const b = bottom.hidden ? null : bottom.getBoundingClientRect();
      if (b && b.height) cover.bottom = Math.max(0, innerHeight - b.top);
      const dock = document.querySelector('.map-dock'), d = dock && dock.getBoundingClientRect();
      if (d && d.width && getComputedStyle(dock).visibility !== 'hidden') {
        if (d.left > innerWidth / 2) cover.right = innerWidth - d.left; else cover.left = d.right;
      }
    }
    nav.setInsets(side && !onRight ? Math.max(0, r.right) : 0, onRight ? Math.max(0, innerWidth - r.left) : 0, cover);
  }

  function render(entering) {
    document.body.classList.toggle('is-routing', ui.open);
    document.body.classList.toggle('is-journey', !!ui.journey);
    document.body.classList.toggle('is-picking', !!ui.editing);   // قائمة النتائج مفتوحة
    document.body.classList.toggle('has-route', !!ui.route);
    renderCard(entering);
    renderBottom();
    renderBanner();
    applyInsets();
    // المسار الحالي لمن يحتاجه (رمز QR على شاشة الإرشاد)
    document.dispatchEvent(new CustomEvent('map:route', { detail: ui.route && ui.from && ui.to
      ? { from: ui.from.id, to: ui.to.id, fromName: ui.from.name, toName: ui.to.name } : null }));
    syncUrl();
  }
  // نقطة البداية والوجهة في الرابط نفسه (?from=…&to=…): يُنسخ ويُشارك ويُعاد تحميله على المسار نفسه.
  // لا على شاشات الإرشاد — رابطها ثابت بموقعها (?kiosk=…)
  function syncUrl() {
    if (site.here) return;
    const q = new URLSearchParams(location.search);
    // دائمًا «من» ثم «إلى»
    q.delete('from'); q.delete('to');
    ['from', 'to'].forEach(f => { if (ui[f]) q.set(f, ui[f].id); });
    q.delete('go');
    const next = location.pathname + (q.toString() ? '?' + q.toString().replace(/%3A/g, ':') : '') + location.hash;
    if (next !== location.pathname + location.search + location.hash) history.replaceState(history.state, '', next);
  }

  /* ---------- الأحداث ---------- */
  function pick(f, place) {
    setPlace(f, place);
    // الحقل التالي الفارغ يُفتح مباشرة؛ وإن اكتمل الاثنان نرسم الطريق
    ui.editing = f === 'from' && !ui.to ? 'to' : f === 'to' && !ui.from ? 'from' : null;
    // الحقل يفقد التركيز قبل الرسم، وإلا أعاده الرسم وفتح البحث من جديد
    if (!ui.editing && document.activeElement && card.contains(document.activeElement)) document.activeElement.blur();
    routeIfReady();
    render(true);
  }
  function finish() {
    // عند الوجهة: ينتهي التوجيه، ووجهتك تصبح نقطة انطلاقك القادمة
    const here = ui.to;
    nav.stopJourney(); nav.clearRoute();
    ui.journey = null; ui.route = null;
    setPlace('from', here); setPlace('to', null);
    ui.editing = 'to';
    if (here) nav.focus(here.id);
    render(true);
  }

  function onClick(e) {
    const el = e.target.closest('[data-n]');
    if (el) {
      const a = el.dataset.n;
      // والقائمة مفتوحة: X يمسح ما كُتب (إن وُجد) ويغلقها؛ وإلا فهو المسح المعتاد
      if (a === 'close') { if (ui.editing && !ADMIN) { if (filled()) close(false); closeResults(); } else close(); }
      else if (a === 'swap') {
        [ui.from, ui.to] = [ui.to, ui.from];
        [ui.text.from, ui.text.to] = [ui.text.to, ui.text.from];
        routeIfReady(); render();
      } else if (a === 'clear') {
        setPlace(el.dataset.f, null); nav.clearRoute(); ui.route = null; ui.failed = false; render(true);
      } else if (a === 'pick') { const p = nav.place(el.dataset.id); if (p) pick(ui.editing || 'to', p); }
      else if (a === 'start') nav.startJourney();
      else if (a === 'unroute') { nav.clearRoute(); ui.route = null; setPlace('to', null); ui.editing = 'to'; render(true); }
      else if (a === 'prev' && ui.journey) nav.goStep(ui.journey.step - 1);
      else if (a === 'next' && ui.journey) {
        if (ui.journey.step >= ui.journey.count - 1) finish(); else nav.goStep(ui.journey.step + 1);
      } else if (a === 'end') { nav.stopJourney(); ui.journey = null; render(); }
      else if (a === 'north') nav.resetHeading();
      return;
    }
    const row = e.target.closest('.nav-field');
    if (row && ui.editing !== row.dataset.field) { ui.editing = row.dataset.field; render(true); }
  }
  [card, bottom, banner, compass].forEach(box => box.addEventListener('click', onClick));

  card.addEventListener('input', e => {
    const f = e.target.dataset.input;
    if (!f) return;
    ui.text[f] = e.target.value;
    // تعديل الاسم بعد اختياره يعني بحثًا جديدًا
    if (ui[f] && ui[f].name !== ui.text[f]) { ui[f] = null; nav.clearRoute(); ui.route = null; ui.failed = false; renderBottom(); }
    const box = card.querySelector('.nav-results');
    if (box) box.outerHTML = results(); else card.insertAdjacentHTML('beforeend', results());
  });
  card.addEventListener('focusin', e => {
    const f = e.target.dataset.input;
    if (f && ui.editing !== f) { ui.editing = f; render(); }
  });
  card.addEventListener('keydown', e => {
    const f = e.target.dataset.input;
    if (!f) return;
    if (e.key === 'Enter') { const first = matches(f)[0]; if (first) pick(f, first); }
    if (e.key === 'ArrowDown') { const first = card.querySelector('.nav-place'); if (first) { e.preventDefault(); first.focus(); } }
  });
  card.addEventListener('keydown', e => {
    if (!e.target.classList.contains('nav-place') || (e.key !== 'ArrowDown' && e.key !== 'ArrowUp')) return;
    e.preventDefault();
    const list = [...card.querySelectorAll('.nav-place')], i = list.indexOf(e.target);
    const next = list[i + (e.key === 'ArrowDown' ? 1 : -1)];
    if (next) next.focus(); else if (e.key === 'ArrowUp') card.querySelector('[data-input="' + ui.editing + '"]').focus();
  });

  // الضغط على جناح يصل من طبقة الإرشاد كوجهة (map:directions)، فلا نعترض النقرة هنا:
  // اعتراضها كان يحجب «رفع الزر» عن تحكّم الخريطة فتبقى ممسوكة بعد كل نقرة.
  // نقرة على أرضية فارغة تُغلق الحقل المفتوح فقط.
  const cvs = venue.renderer.domElement;
  let down = null;
  cvs.addEventListener('pointerdown', e => { down = e.button === 0 ? { x: e.clientX, y: e.clientY } : null; });
  cvs.addEventListener('pointerup', e => {
    if (!down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 6) return;
    down = null;
    if (ui.editing && venue.tables.pick(e.clientX, e.clientY) < 0) closeResults();
  });
  // وأي ضغطة خارج بطاقة الاتجاهات (الشريط السفلي، الأزرار، الرموز…) تُغلق قائمة النتائج كذلك؛
  // الخريطة نفسها لها ما فوقها: الجناح يملأ الحقل، والأرضية الفارغة تُغلق
  function closeResults() {
    ui.editing = null;
    if (document.activeElement && card.contains(document.activeElement)) document.activeElement.blur();
    render();
  }
  document.addEventListener('pointerdown', e => {
    if (ui.editing && !card.contains(e.target) && e.target !== cvs) closeResults();
  });

  document.addEventListener('map:directions', e => open(e.detail && e.detail.to));
  // ضغطة على جناح والحقل مفتوح: يمتلئ به (بطاقة الجناح تظهر في wayfinding.js)
  document.addEventListener('map:pick', e => {
    const place = e.detail && nav.place(e.detail.place);
    if (place && ui.editing && !ui.journey) { nav.reindex(); pick(ui.editing, place); }
  });
  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape' || !ui.open || document.body.classList.contains('at-screen')) return;
    e.preventDefault(); e.stopImmediatePropagation();
    if (ui.journey) { nav.stopJourney(); ui.journey = null; render(); }
    else if (ui.editing) { ui.editing = null; render(); if (document.activeElement && card.contains(document.activeElement)) document.activeElement.blur(); }
    else if (ui.from || ui.to || ADMIN) close();
  }, true);
  // زرّ الاتجاهات عند المشرف: يفتح البطاقة أو يطويها
  document.addEventListener('map:directions-toggle', () => { if (ui.open) close(); else open(); });
  addEventListener('resize', applyInsets);
  document.addEventListener('map:turn', e => nav.refit(e.detail.theta));

  renderCompass();
  if (site.here) setPlace('from', nav.place('here'));
  // رابط بمسار (?from=…&to=…): يُرسم الطريق كما كان — ومن رمز شاشة الإرشاد (&go) يبدأ التوجيه مباشرة
  const params = new URLSearchParams(location.search);
  const linked = [params.get('from'), params.get('to')].map(id => id && nav.place(id));
  if (!site.here && (linked[0] || linked[1])) {
    if (linked[0]) setPlace('from', linked[0]);
    if (linked[1]) setPlace('to', linked[1]);
    ui.open = true;
    ui.autostart = !!(linked[0] && linked[1] && params.has('go'));
    routeIfReady();
  }
  render();
  // عودة شاشة الإرشاد لوضعها الافتراضي: لا رحلة، لا طريق، «من» موقعك الحالي، القائمة مغلقة
  document.addEventListener('map:reset', () => {
    if (ui.journey) nav.stopJourney();
    close();
    ui.editing = null;
    if (document.activeElement && card.contains(document.activeElement)) document.activeElement.blur();
    render();
  });
  return { open, close };
}
