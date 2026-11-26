/* =========================================================
   خريطة الإرشاد — ما تحت التنقّل
   الخريطة للوصول والتنقّل فقط: لا طبقات ولا شيتات ولا بيانات عن الفرق
   أو المناطق. ما يبقى على المشهد:
     · شارة كل منطقة باسمها وحده (site.labels) — والضغط عليها يجعلها وجهتك.
     · تلميح فوق الجناح: رقمه ومنطقته، كلافتة في القاعة.
     · الضغط على جناح يفتح بطاقته فوقه: اسم الفريق، دولته، مساره، قائده — وزرّا الاتجاهات وتفاصيل المشروع
       (التفاصيل تكبر من البطاقة نفسها إلى وسط الشاشة — project-card.js). خريطة المشرف: البوب أوفر نفسه بالقائد والأعضاء
       (وإن كان حقل «من / إلى» مفتوحًا يمتلئ به أيضًا — map:pick في nav-ui.js).
   ========================================================= */
import { pressable, esc } from '../primitives/ui.js';
import { mountProjectCard, cardHead, cardRows, teamRows, detailsButton, goButton } from './project-card.js';
import { tr } from './i18n.js';

const BOOTH = code => tr('بوث ', 'Booth ') + code;

export function mountWayfinding(venue, site) {
  // بيانات الموقع: الأجنحة («طاولات» المحرّك) ومناطقها — للقراءة فقط
  const S = site.data(venue.tables.list);
  const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const go = to => document.dispatchEvent(new CustomEvent('map:directions', { detail: { to } }));

  /* ---------- شارات المناطق: الاسم وحده ---------- */
  const overlay = document.createElement('div');
  overlay.className = 'map-overlay';
  document.body.appendChild(overlay);
  const labels = site.labels || [];
  const chips = labels.map(l => {
    const wrap = document.createElement('div');
    wrap.className = 'map-anchor';
    // المنطقة بحرفها وحده في دائرة (عشر شارات متجاورة)، والأماكن المسمّاة باسمها
    wrap.innerHTML = pressable(l.short ? '<b>' + esc(l.short) + '</b>' : '<span>' + esc(l.name) + '</span>', 'zone-chip zone-chip--name' + (l.short ? ' zone-chip--letter' : ''),
      { 'data-place': l.place, 'aria-label': tr('الاتجاهات إلى ', 'Directions to ') + l.name, title: l.name });
    overlay.appendChild(wrap);
    return wrap;
  });
  overlay.addEventListener('click', e => {
    const chip = e.target.closest('[data-place]');
    if (chip) go(chip.dataset.place);
  });

  // شاشة الإرشاد التي تعمل عليها الصفحة: «أنت هنا» بنقطة نابضة فوق موقعها
  const hereSpot = site.here && (site.kiosks || []).find(k => k.id === site.here);
  let hereEl = null;
  if (hereSpot) {
    hereEl = document.createElement('div');
    hereEl.className = 'map-anchor';
    hereEl.innerHTML = '<span class="here-pin" role="img" aria-label="' + tr('أنت هنا', 'You are here') + '"><i></i><b>' + tr('أنت هنا', 'You are here') + '</b></span>';
    overlay.appendChild(hereEl);
  }

  const tip = document.createElement('div');
  tip.className = 'table-tip';
  tip.hidden = true;
  tip.setAttribute('aria-hidden', 'true');
  overlay.appendChild(tip);

  function place() {
    const W = innerWidth, H = innerHeight;
    const shown = chips.map((c, i) => {
      const p = venue.projectXZ(labels[i].x, labels[i].z, 30);
      const ok = p.visible && p.x > -40 && p.x < W + 40 && p.y > 0 && p.y < H;
      if (ok) c.style.transform = 'translate(' + p.x.toFixed(1) + 'px,' + p.y.toFixed(1) + 'px)';
      return ok;
    });
    // الشارات المتراكبة: تبقى الأسبق في القائمة (الأهم)، وتختفي التي تغطّيها حتى يكفي التقريب لها
    const taken = [];
    // طرفا المسار المعروض (علامة البداية والدبوس بارتفاعه): لا تغطّيهما شارة
    (venue.routeEnds || []).forEach(e => {
      const g = venue.projectXZ(e.x, e.z, 0), t = venue.projectXZ(e.x, e.z, e.h);
      if (!g.visible) return;
      taken.push({ left: Math.min(g.x, t.x) - 18, right: Math.max(g.x, t.x) + 18, top: Math.min(g.y, t.y) - 18, bottom: Math.max(g.y, t.y) + 14 });
    });
    chips.forEach((c, i) => {
      let ok = shown[i];
      if (ok) {
        const r = c.firstElementChild.getBoundingClientRect();
        ok = !taken.some(t => r.left < t.right + 4 && r.right > t.left - 4 && r.top < t.bottom + 2 && r.bottom > t.top - 2);
        if (ok) taken.push(r);
      }
      c.style.visibility = ok ? '' : 'hidden';
    });
  }
  if (hereEl) {
    const placeHere = () => {
      const p = venue.projectXZ(hereSpot.x, hereSpot.z, 2);
      hereEl.style.visibility = p.visible ? '' : 'hidden';
      hereEl.style.transform = 'translate(' + p.x.toFixed(1) + 'px,' + p.y.toFixed(1) + 'px)';
    };
    venue.onRender(placeHere);
  }
  venue.onRender(place);
  addEventListener('resize', place);

  /* ---------- الطاولات: تلميح عند المرور، ووجهة عند الضغط ---------- */
  const cvs = venue.renderer.domElement;
  let down = null, hoverFrame = 0, hovered = -1;
  cvs.addEventListener('pointerdown', e => { down = e.button === 0 ? { x: e.clientX, y: e.clientY, t: performance.now() } : null; });
  // خريطة المشرف: البوب أوفر نفسه، بصفوف القائد والأعضاء وحدهم
  const ADMIN = document.body.classList.contains('is-admin');

  /* ---------- بطاقة الجناح (الخريطة العامة): فوقه بسهم صغير، وتتبعه مع حركة الخريطة ---------- */
  const pop = document.createElement('div');
  pop.className = 'map-anchor booth-pop';
  pop.hidden = true;
  pop.setAttribute('role', 'dialog');
  overlay.appendChild(pop);
  let popAt = -1, popHtml = '';
  const zoneOf = t => S.zones[t.zone] ? S.zones[t.zone].name : null;
  // تفاصيل المشروع: تكبر من البطاقة إلى وسط الشاشة، والرجوع يعيدها إلى الجناح
  const details = mountProjectCard({ onGo: to => { closePop(); go(to); }, noFlags: !!site.here,
    // البطاقة عادت بالانتقال نفسه: حركة ظهورها لا تُعاد بعده (كانت تومض لإطار حين ينتهي)
    onBack: () => { if (popAt >= 0) { pop.firstElementChild.classList.add('is-back'); pop.hidden = false; placePop(); } } });
  function placePop() {
    if (popAt < 0 || pop.hidden) return;
    const t = S.tables[popAt], p = venue.projectXZ(t.x, t.z, 26);
    pop.style.visibility = p.visible ? '' : 'hidden';
    // فوق الجناح إن اتّسع له المكان (تحت بطاقة الاتجاهات)، وإلا تحته — أو حيث المكان أوسع
    // الحدّ الأعلى: أسفل بطاقة الاتجاهات وزرّ الأجندة الراسي تحتها (يعلوان البطاقة فلا تختفي تحتهما)
    const card = pop.firstElementChild, top = document.querySelector('.nav-card:not([hidden])'), agenda = document.querySelector('.screen-btn');
    const ab = agenda && getComputedStyle(agenda).visibility !== 'hidden' ? agenda.getBoundingClientRect() : null;
    const over = ab && ab.height && ab.left < p.x + 160 && ab.right > p.x - 160 ? ab.bottom : 0;
    // وفي خريطة المشرف: أسفل عناصر الأعلى (اليوم، فلاتر الفئات، حضور اليوم)
    const bar = ADMIN ? Math.max(0, ...[...document.querySelectorAll('.admin-day, .admin-ages, .admin-in')]
      .filter(el => !el.hidden && getComputedStyle(el).visibility !== 'hidden').map(el => el.getBoundingClientRect().bottom)) : 0;
    const limit = Math.max(top ? top.getBoundingClientRect().bottom : 0, over, bar) + 8, floor = innerHeight - 8, gap = 14;
    const h = card ? card.offsetHeight : 200, above = p.y - gap - limit, below = floor - p.y - gap;
    const isBelow = h > above && below > above;
    pop.classList.toggle('is-below', isBelow);
    // لا تتّسع لها أيّ جهة (التفاصيل مفتوحة): تنزاح عموديًا لتبقى كاملة على الشاشة، ويختفي السهم
    const y0 = isBelow ? p.y + gap : p.y - gap - h;
    const dy = y0 < limit ? limit - y0 : y0 + h > floor ? Math.max(limit - y0, floor - (y0 + h)) : 0;
    pop.style.setProperty('--pop-dy', dy.toFixed(1) + 'px');
    pop.classList.toggle('is-shifted', Math.abs(dy) > .5);
    // قرب حافة الشاشة: البطاقة تنزاح للداخل كاملة، والسهم يبقى على الجناح
    const half = (card ? card.offsetWidth : 300) / 2, edge = 12;
    const minX = edge + half, maxX = innerWidth - edge - half;
    const dx = p.x < minX ? minX - p.x : p.x > maxX ? maxX - p.x : 0;
    pop.style.setProperty('--pop-dx', Math.max(-(half - 20), Math.min(half - 20, dx)).toFixed(1) + 'px');
    pop.style.transform = 'translate(' + p.x.toFixed(1) + 'px,' + p.y.toFixed(1) + 'px)';
  }
  function openPop(i) {
    const t = S.tables[i];
    if (popAt !== i) details.close(true);
    popAt = i;
    pop.setAttribute('aria-label', t.exhibitor || BOOTH(t.code));
    const clHtml = renderChecklistBar(t);
    const html = '<div class="booth-pop__card">' +
      cardHead(t, zoneOf(t)) + (ADMIN ? teamRows(t) : cardRows(t, !!site.here)) +
      clHtml +
      '<div class="bp-actions">' + (t.exhibitor && !ADMIN ? detailsButton() : '') + goButton(i) + '</div>' +
    '</div>';
    if (html !== popHtml) { pop.innerHTML = html; popHtml = html; popSize.disconnect(); popSize.observe(pop.firstElementChild); }
    if (!details.isOpen) pop.hidden = false;
    venue.tables.mark('select', i, css('--brand'));
    placePop();
  }
  function closePop() {
    details.close(true);
    if (popAt < 0) return;
    popAt = -1;
    pop.hidden = true;
    venue.tables.mark('select', -1);
  }
  venue.onRender(placePop);
  const popSize = new ResizeObserver(placePop);
  pop.addEventListener('transitionend', placePop);
  pop.addEventListener('click', e => {
    const clBtn = e.target.closest('[data-cl-act]');
    if (clBtn) {
      const act = clBtn.dataset.clAct;
      const pid = clBtn.dataset.pid;
      if (act === 'rat') window.saifChecklistAction?.('rat', { id: pid, stars: Number(clBtn.dataset.stars) });
      else if (act === 'open') window.saifChecklistAction?.('openProject', pid);
      else window.saifChecklistAction?.(act, pid);
      return;
    }
    const b = e.target.closest('[data-go]');
    if (b) { const to = b.dataset.go; closePop(); go(to); return; }
    if (e.target.closest('[data-pop="details"]') && popAt >= 0) {
      const t = S.tables[popAt];
      details.open(t, popAt, zoneOf(t), () => { pop.hidden = true; });
    }
  });

  /* ---------- Checklist Floating Highlight Pins & Actions Layer ---------- */
  let clState = null;
  const pinsLayer = document.createElement('div');
  pinsLayer.className = 'cl-pins';
  overlay.appendChild(pinsLayer);
  let pinItems = [];
  const CL_ICO = {
    star: '<svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><polygon points="12 2 15.1 8.3 22 9.3 17 14.1 18.2 21 12 17.8 5.8 21 7 14.1 2 9.3 8.9 8.3 12 2"/></svg>',
    starOut: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polygon points="12 2 15.1 8.3 22 9.3 17 14.1 18.2 21 12 17.8 5.8 21 7 14.1 2 9.3 8.9 8.3 12 2"/></svg>',
    check: '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>',
    pin: '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
    ban: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="m4.9 4.9 14.2 14.2"/></svg>',
    expand: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m15 3 6 6M9 21l-6-6M21 3l-7 7M3 21l7-7"/></svg>',
  };

  function renderChecklistBar(t) {
    if (!clState || !clState.boothToProjects) return '';
    const projs = clState.boothToProjects.get(t.code) || [];
    if (!projs.length) return '';
    const p = projs[0];
    const rec = (clState.records && clState.records[p.id]) || {};
    const stars = [1, 2, 3, 4, 5].map(s =>
      '<button type="button" class="cl-star' + ((rec.rat || 0) >= s ? ' on' : '') + '" data-cl-act="rat" data-pid="' + esc(p.id) + '" data-stars="' + s + '">' + CL_ICO.star + '</button>'
    ).join('');
    return '<div class="cl-pop-bar">' +
      '<button type="button" class="cl-act fav' + (rec.fav ? ' on' : '') + '" data-cl-act="fav" data-pid="' + esc(p.id) + '" aria-label="Fav">' + CL_ICO.starOut + '</button>' +
      '<button type="button" class="cl-act vis' + (rec.vis ? ' on' : '') + '" data-cl-act="vis" data-pid="' + esc(p.id) + '" aria-label="Visited">' + CL_ICO.check + '</button>' +
      '<span class="cl-stars">' + stars + '</span>' +
      '<button type="button" class="cl-act ign' + (rec.ign ? ' on' : '') + '" data-cl-act="ign" data-pid="' + esc(p.id) + '" aria-label="Ignore">' + CL_ICO.ban + '</button>' +
      '<button type="button" class="cl-act" data-cl-act="open" data-pid="' + esc(p.id) + '" aria-label="Open">' + CL_ICO.expand + '</button>' +
    '</div>';
  }

  function rebuildPins() {
    pinsLayer.innerHTML = '';
    pinItems = [];
    if (!clState || !clState.boothToProjects) return;
    const { records = {}, evalById, prefs = {}, routeIndexByTable, boothToProjects } = clState;
    const myTable = (prefs.myBooth || '').toUpperCase();
    const candidates = [];

    S.tables.forEach((t, idx) => {
      const projs = boothToProjects.get(t.code) || [];
      let fav = false, vis = false, rat = 0, visible = false;
      for (const p of projs) {
        const r = records[p.id] || {};
        const ev = evalById ? evalById.get(p.id) : null;
        if (r.fav) fav = true;
        if (r.vis) vis = true;
        if ((r.rat || 0) > rat) rat = r.rat || 0;
        if (!ev || (ev.matches && !ev.isIgnored)) visible = true;
      }
      const isMe = t.code === myTable;
      const routeNum = routeIndexByTable ? routeIndexByTable.get(t.code) : null;
      if (!isMe && !routeNum && (!visible || (!fav && !vis && !rat))) return;
      const prio = isMe ? 100 : routeNum ? 90 - routeNum : fav && vis ? 70 : fav ? 60 : rat ? 50 + rat : 40;
      candidates.push({ t, idx, isMe, routeNum, fav, vis, rat, prio });
    });

    candidates.sort((a, b) => b.prio - a.prio);
    const chosen = candidates.slice(0, 120);
    for (const c of chosen) {
      const btn = document.createElement('button');
      btn.type = 'button';
      const kind = c.isMe ? 'me' : c.routeNum ? 'route' : c.fav && c.vis ? 'both' : c.fav ? 'fav' : c.vis ? 'vis' : 'rat';
      btn.className = 'map-anchor cl-pin cl-pin--' + kind;
      btn.dataset.pinIdx = String(c.idx);
      const shortLbl = c.t.code.startsWith('S-') ? c.t.code.slice(2) : c.t.code;
      const icoHtml = c.routeNum ? '<b>#' + c.routeNum + '</b>' : c.isMe ? CL_ICO.pin : c.fav ? CL_ICO.star : c.vis ? CL_ICO.check : '<b>' + c.rat + '</b>' + CL_ICO.star;
      btn.innerHTML = icoHtml + '<span>' + esc(shortLbl) + '</span>';
      btn.title = (c.t.exhibitor || c.t.code) + ' (' + shortLbl + ')';
      pinsLayer.appendChild(btn);
      pinItems.push({ el: btn, t: c.t });
    }
    placePins();
  }

  function placePins() {
    if (!pinItems.length) return;
    const W = innerWidth, H = innerHeight;
    for (let k = 0; k < pinItems.length; k++) {
      const it = pinItems[k];
      const p = venue.projectXZ(it.t.x, it.t.z, 34);
      const ok = p.visible && p.x > -30 && p.x < W + 30 && p.y > 0 && p.y < H;
      it.el.style.visibility = ok ? '' : 'hidden';
      if (ok) it.el.style.transform = 'translate(' + p.x.toFixed(1) + 'px,' + p.y.toFixed(1) + 'px)';
    }
  }
  venue.onRender(placePins);
  pinsLayer.addEventListener('click', e => {
    const b = e.target.closest('[data-pin-idx]');
    if (!b) return;
    const i = Number(b.dataset.pinIdx);
    const t = S.tables[i];
    if (!t) return;
    venue.focus(t.x, t.z, 340);
    openPop(i);
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !details.isOpen) closePop(); });
  document.addEventListener('map:reset', closePop);
  document.addEventListener('map:data', () => { if (popAt >= 0) openPop(popAt); details.refresh(); });

  /* ---------- المشرف: «+1» فوق جناح كل فريق يُحكَّم — تظهر مع كل تحكيم جديد (map.js · admin:judged) ----------
     شارة خضراء تظهر صاعدة بهدوء، تبقى ثانيتين، ثم تكمل صعودها وتتلاشى — بلا ارتداد؛ وتتبع الجناح مع حركة الخريطة */
  const pluses = new Set();
  const placePlus = el => {
    const t = S.tables[el._table], p = venue.projectXZ(t.x, t.z, 34);
    el.style.visibility = p.visible ? '' : 'hidden';
    el.style.transform = 'translate(' + p.x.toFixed(1) + 'px,' + p.y.toFixed(1) + 'px)';
  };
  if (ADMIN) {
    document.addEventListener('admin:judged', e => (e.detail.judged || []).forEach(({ table, count }) => {
      const el = document.createElement('div');
      el.className = 'map-anchor judge-plus';
      el.setAttribute('aria-hidden', 'true');
      el.innerHTML = '<span dir="ltr">+' + count + '</span>';
      el._table = table;
      overlay.appendChild(el); pluses.add(el); placePlus(el);
      el.firstElementChild.addEventListener('animationend', () => { pluses.delete(el); el.remove(); }, { once: true });
    }));
    venue.onRender(() => pluses.forEach(placePlus));
  }

  // المسرح وشاشته: ضغطة عليهما تنقل إلى الأجندة كزرّ «أجندة المعرض» — بلا أي علامة عليهما
  function onStage(x, y) {
    const r = venue.screenRect ? venue.screenRect() : null;
    if (r && x >= r.x && x <= r.x + r.width && y >= r.y && y <= r.y + r.height) return true;
    const s = site.stageRect, g = s && venue.groundPoint(x, y);
    return !!(g && g.x >= s[0] && g.x <= s[2] && g.z >= s[1] && g.z <= s[3]);
  }
  cvs.addEventListener('pointerup', e => {
    if (!down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 6 || performance.now() - down.t > 600) return;
    down = null;
    const i = venue.tables.pick(e.clientX, e.clientY);
    if (i < 0) {
      closePop();
      // لا حين تُختار نقطة «من / إلى» (قائمة النتائج مفتوحة) ولا أثناء التوجيه
      const busy = document.body.classList.contains('is-picking') || document.body.classList.contains('is-journey');
      if (!busy && onStage(e.clientX, e.clientY)) document.dispatchEvent(new CustomEvent('map:stage'));
      return;
    }
    openPop(i);
    // حقل «من / إلى» مفتوح يمتلئ بالجناح نفسه
    document.dispatchEvent(new CustomEvent('map:pick', { detail: { place: 'table:' + i } }));
  });
  cvs.addEventListener('pointermove', e => {
    if (e.buttons) { tip.hidden = true; return; }
    const x = e.clientX, y = e.clientY;
    cancelAnimationFrame(hoverFrame);
    hoverFrame = requestAnimationFrame(() => {
      const i = venue.tables.pick(x, y);
      if (i !== hovered) { hovered = i; venue.tables.mark('hover', i, css('--brand-200')); cvs.style.cursor = i >= 0 ? 'pointer' : ''; }
      if (i < 0) cvs.style.cursor = onStage(x, y) ? 'pointer' : '';   // المؤشر وحده يلمّح أن المسرح يُضغط
      // لا تلميح فوق جناح شيته مفتوح — الشيت يقول أكثر
      if (i < 0 || i === popAt) { tip.hidden = true; return; }
      const t = S.tables[i];
      tip.innerHTML = '<b>' + esc(t.exhibitor || BOOTH(t.code)) + '</b><span>' + esc((t.exhibitor ? BOOTH(t.code) + ' · ' : '') + (t.teamCode ? t.teamCode + ' · ' : '') + (S.zones[t.zone] ? S.zones[t.zone].name : '') +
        (t.admin ? ' · ' + (t.admin.checkedIn ? tr('حضر اليوم', 'Checked in') : tr('لم يحضر', 'Not in yet')) : '')) + '</span>';
      tip.hidden = false;
      tip.style.transform = 'translate(' + x + 'px,' + (y - 16) + 'px)';
    });
  });
  cvs.addEventListener('pointerleave', () => { tip.hidden = true; hovered = -1; venue.tables.mark('hover', -1); });

  return {
    state: S,
    setChecklistState(next) {
      clState = next;
      rebuildPins();
      if (popAt >= 0) openPop(popAt);
    },
    focusBooth(code, openCard = true) {
      const idx = S.tables.findIndex(t => t.code === code);
      if (idx < 0) return false;
      const t = S.tables[idx];
      venue.focus(t.x, t.z, 340);
      if (openCard) openPop(idx);
      return true;
    },
  };
}
