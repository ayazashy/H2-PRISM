/* =========================================================
   خريطة معرض سيف — المنتج
   خريطة إرشاد فقط: مشهد القاعة ثلاثي الأبعاد بأسماء المناطق، وفوقه التنقّل
   داخل القاعة: «من / إلى»، البحث، الطريق، والرحلة بمراحل
   (wayfinding.js · venue-nav.js · nav-ui.js).
   سحب للتحريك، زر أيمن (أو Ctrl + سحب) للتدوير، عجلة للتقريب حول المؤشر.
   «أجندة المعرض» معلّق فوق المسرح: يطير بالكاميرا إلى شاشة المسرح وهي تعرض الأجندة،
   والضغط على أي جلسة فيها يفتح تفاصيلها. رابط ?agenda (رمز الجوال) يفتح بطاقة الأجندة.
   على شاشة إرشاد (?kiosk=k1 …): «من» موقعك الحالي، والعرض متمركز على الشاشة،
   وشريط آمن أسفل الشاشة بهوية سيف خارج حسبة الخريطة.
   ========================================================= */
import { tr, EN, setLang } from './i18n.js';
import { createVenue3D } from './venue-3d.js';
import { paintDisplay } from './display-paint.js';
import site from './sites/sef.js';
import { mountAgenda, mountAgendaPanel, mountSessionPop, setStages } from './agenda.js';

// شاشة الإرشاد: ?kiosk=k3 لشاشة بعينها، و?kiosk وحدها للأولى.
// وبلا رابط: شاشة عمودية طويلة (الكيوسك 1080 × 1920) تُعرف وحدها — الجوال أقصر بكثير.
// ?kiosk=off يطفئها، ورابط المسار من رمز QR (from/to) لا يُعامل ككيوسك أبدًا.
const query = new URLSearchParams(location.search);
const EMBED = query.has('embed') || window.self !== window.top;
if (EMBED) document.body.classList.add('is-embed');
const ADMIN = document.body.classList.contains('is-admin');
const tallPortrait = !EMBED && matchMedia('(orientation: portrait) and (min-height: 1400px)').matches;
const kioskParam = EMBED ? null : (query.get('kiosk') ?? (tallPortrait && !query.has('to') ? '' : null));
if (kioskParam !== null && kioskParam !== 'off') {
  site.here = site.kiosks.some(k => k.id === kioskParam) ? kioskParam : site.kiosks[0].id;
  document.body.classList.add('is-kiosk');
  // الشريط الآمن: جزء الشاشة السفلي خارج الخريطة — المشهد كله يتكيّف فيما فوقه (map.css)
  const safe = document.createElement('footer');
  safe.className = 'safe-area';
  // الشعاران في المنتصف بينهما خط فاصل، ورمز QR للجوال في الطرف (kiosk-qr.js)
  safe.innerHTML = '<span class="safe-area__brand">' +
    '<img class="safe-area__saif" src="assets/img/saif-logo-green.png" alt="' + tr('سيف', 'SAIF') + '">' +
    '<i class="safe-area__rule" aria-hidden="true"></i>' +
    '<img class="safe-area__tuwaiq" src="assets/img/tuwaiq-logo.svg" alt="' + tr('أكاديمية طويق', 'Tuwaiq Academy') + '"></span>';
  safe.setAttribute('aria-label', tr('معرض سيف بالشراكة مع أكاديمية طويق', 'SAIF in partnership with Tuwaiq Academy'));
  document.body.appendChild(safe);
  import('./kiosk-qr.js').then(m => m.mountQR(safe, site));
}

const canvas = document.getElementById('canvas');
const world = document.getElementById('world');
const wall = document.getElementById('wall');
const screenBtn = document.querySelector('.screen-btn');
const backBtn = document.getElementById('backToPlan');
const screenToolbar = document.querySelector('.scr-bar');
const viewSwitch = document.querySelector('.view-switch');

// نصوص الصفحة الثابتة (index.html) باللغة الإنجليزية
if (EN) {
  document.title = ADMIN ? 'SAIF Exhibition Map · Admin' : 'SAIF Exhibition Map';
  if (screenBtn) screenBtn.lastChild.textContent = ' Exhibition Agenda';
  if (viewSwitch) {
    viewSwitch.setAttribute('aria-label', 'Viewing angle');
    const [p3, p2] = viewSwitch.querySelectorAll('button');
    p3.setAttribute('aria-label', '3D view'); p3.title = '3D view';
    p2.setAttribute('aria-label', 'Flat top-down view'); p2.title = 'Flat top-down view';
  }
  if (backBtn) backBtn.setAttribute('aria-label', 'Back to the map');
}

if (canvas && wall) {
  // موقع مسطّح ← محرّك SVG بالواجهة نفسها؛ الباقي ثلاثي الأبعاد
  // الجوال (لا الكيوسك): القاعة بالطول افتراضيًا — تملأ الشاشة العمودية بدل شريط عريض في وسطها
  site.startTall = matchMedia('(max-width: 600px)').matches && !document.body.classList.contains('is-kiosk');
  if (site.startTall) site.tallZoom = 1.12;   // وأبعد قليلًا من الملء التام
  const venue = createVenue3D(canvas, site);
  // حركات الموقع المتدرّجة (حضور الفرق والتركيز على فريق في خريطة المشرف) ترسم المشهد مع كل إطار
  site.redraw = () => venue.invalidate();
  // على شاشة الإرشاد: نظرة واسعة على القاعة لكن مركزها الشاشة نفسها — في المنظور والعلوي معًا
  const spot = site.here && site.kiosks.find(k => k.id === site.here);
  if (spot) {
    ['perspective', 'top'].forEach(name => {
      const base = venue.views[name];
      venue.views[name] = () => {
        // أقرب من النظرة الكاملة: موقع الشاشة وما حوله واضحان، وبقية القاعة على الأطراف
        const v = base(), offset = v.position.clone().sub(v.target).multiplyScalar(.5);
        v.target.set(spot.x, v.target.y, spot.z);
        v.position.copy(v.target).add(offset);
        return v;
      };
    });
    venue.fly(venue.views.perspective(), null, true);
  }
  // زرّا 3D/2D في الزاوية، والبوصلة تنضمّ إليهما حين يدور المشهد
  const dock = document.createElement('div');
  dock.className = 'map-dock';
  const mapBar = document.createElement('nav');
  mapBar.className = 'map-bar';
  mapBar.setAttribute('aria-label', tr('عرض الخريطة', 'Map view'));
  if (viewSwitch) mapBar.appendChild(viewSwitch);
  // فوق 3D/2D: تدوير زاوية النظر بين القاعة بالعرض والقاعة بالطول
  const turnBtn = document.createElement('button');
  turnBtn.type = 'button';
  turnBtn.className = 'map-turn';
  const paintTurn = () => {
    const tall = venue.orient.tall;
    turnBtn.setAttribute('aria-pressed', String(tall));
    turnBtn.setAttribute('aria-label', tall ? tr('عرض القاعة بالعرض', 'Show the hall landscape') : tr('عرض القاعة بالطول', 'Show the hall portrait'));
    turnBtn.title = turnBtn.getAttribute('aria-label');
  };
  // مستطيل الشاشة يدور: أفقي ← رأسي
  turnBtn.innerHTML = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<rect x="8" y="3" width="8" height="14" rx="1.5"/><path d="M3 13a9 9 0 0 0 8 8M3 13l-1 2.5M3 13l2.5 1"/></svg>';
  paintTurn();
  turnBtn.addEventListener('click', () => {
    if (document.body.classList.contains('is-lifting')) return;
    venue.orient.tall = !venue.orient.tall;
    paintTurn();
    const active = viewSwitch && viewSwitch.querySelector('[aria-pressed="true"]');
    const view = venue.views[active ? active.dataset.view : 'perspective']();
    // مسار معروض: يُعاد تأطيره بالاتجاه الجديد (طرفاه ظاهران)، لا القاعة كلها
    if (document.body.classList.contains('has-route')) {
      const o = view.position.clone().sub(view.target);
      document.dispatchEvent(new CustomEvent('map:turn', { detail: { theta: Math.atan2(o.x, o.z) } }));
      return;
    }
    venue.fly(view);
  });
  // إعادة الضبط ترجع إلى اتجاه البداية (بالطول في الجوال، بالعرض في غيره)
  document.addEventListener('map:reset', () => { if (venue.orient.tall !== !!site.startTall) { venue.orient.tall = !!site.startTall; paintTurn(); } });
  // اللغة: زرّ بحرف اللغة الأخرى فوق زرّ التدوير — يعيد فتح الخريطة بها
  const langBtn = document.createElement('button');
  langBtn.type = 'button';
  langBtn.className = 'map-turn map-lang';
  langBtn.lang = EN ? 'ar' : 'en';
  langBtn.textContent = EN ? 'ع' : 'EN';
  langBtn.setAttribute('aria-label', EN ? 'العربية' : 'English');
  langBtn.title = langBtn.getAttribute('aria-label');
  langBtn.addEventListener('click', () => setLang(EN ? 'ar' : 'en'));
  // المشرف: زرّ حسابه أعلى الزاوية — اسمه، حضور اليوم، الخروج (admin-ui.js)
  if (ADMIN) import('./admin-ui.js').then(m => m.mountAdminUI(dock, site));
  dock.appendChild(langBtn);
  dock.appendChild(turnBtn);
  dock.appendChild(mapBar);
  document.body.appendChild(dock);
  let wfCtrl = null, navCtrl = null, latestChecklist = null;
  Promise.all([import('./wayfinding.js'), import('./venue-nav.js'), import('./nav-ui.js')])
    .then(([way, engine, ui]) => {
      wfCtrl = way.mountWayfinding(venue, site);
      ui.mountNavUI(venue, wfCtrl, engine.mountNav, site);
      syncTeams(wfCtrl.state);
      const bridge = {
        syncChecklist(payload) {
          latestChecklist = payload;
          if (site.paintChecklist) site.paintChecklist(payload, venue);
          if (wfCtrl) wfCtrl.setChecklistState(payload);
        },
        focusBooth(code, openCard = true) {
          return wfCtrl ? wfCtrl.focusBooth(code, openCard) : false;
        },
        focusZone(zoneLetter) {
          const matches = wfCtrl ? wfCtrl.state.tables.filter((t) => wfCtrl.state.zones[t.zone]?.letter === zoneLetter) : [];
          if (!matches.length) return false;
          const cx = matches.reduce((s, t) => s + t.x, 0) / matches.length;
          const cz = matches.reduce((s, t) => s + t.z, 0) / matches.length;
          venue.focus(cx, cz, 850);
          return true;
        },
        setViewMode(mode) {
          const key = mode === 'top' ? 'top' : 'perspective';
          if (viewSwitch) viewSwitch.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.view === key)));
          venue.fly(venue.views[key]());
        },
        resetView() {
          const active = viewSwitch && viewSwitch.querySelector('[aria-pressed="true"]');
          venue.fly(venue.views[active ? active.dataset.view : 'perspective']());
        },
      };
      window.saifOfficialMap = bridge;
      if (latestChecklist) bridge.syncChecklist(latestChecklist);
      try {
        if (window.parent && window.parent !== window && window.parent.onOfficialMapReady) {
          window.parent.onOfficialMapReady(bridge);
        }
      } catch (_) {}
    });

  function syncTeams(state) {
    const applyData = raw => {
      if (!raw || !Array.isArray(raw.projects)) return;
      const pathMap = new Map((raw.meta?.paths || []).map(p => [p.id, p]));
      const countryMap = raw.meta?.countries || {};
      const byBooth = new Map();
      for (const p of raw.projects) {
        if (p.table && !byBooth.has(p.table)) byBooth.set(p.table, p);
      }
      state.tables.forEach(t => {
        const p = byBooth.get(t.code);
        if (!p) return;
        const pathObj = pathMap.get(p.path);
        const nat = p.nat || (p.members?.[0]?.nat) || '';
        const cInfo = countryMap[nat];
        const flag = cInfo ? cInfo[0] : '';
        const country = cInfo ? tr(cInfo[2] || nat, nat) : nat;
        const leaderMem = (p.members && p.members.find(m => m.l === 1)) || (p.members && p.members[0]);
        const leaderName = leaderMem ? (EN ? (leaderMem.n || leaderMem.ar) : (leaderMem.ar || leaderMem.n)) : '';
        Object.assign(t, {
          projectId: p.id,
          catId: p.cat,
          tags: p.tags || [],
          exhibitor: p.title,
          teamCode: p.code,
          track: pathObj ? tr(pathObj.ar, pathObj.en) : null,
          country: country || null,
          flag: flag || null,
          leader: leaderName || null,
          details: {
            description: p.desc || null,
            members: (p.members || []).map(m => ({
              name: EN ? (m.n || m.ar || '') : (m.ar || m.n || ''),
              role: m.l === 1 ? 'leader' : 'member',
              specialty: '',
              linkedin: m.li || '',
            })),
            membersCount: (p.members || []).length,
          },
        });
      });
      document.dispatchEvent(new CustomEvent('map:data', { detail: { teams: raw.projects } }));
      if (latestChecklist) window.saifOfficialMap?.syncChecklist(latestChecklist);
    };
    let localObj = window.__SAIF_LOCAL_DATA__;
    try {
      if (!localObj && window.parent && window.parent !== window) {
        localObj = window.parent.__SAIF_RAW_DATA__;
      }
    } catch (_) {}
    if (localObj) {
      applyData(localObj);
    } else {
      fetch('../data.json').then(r => r.json()).then(applyData).catch(() => {});
    }
  }

  /* ---- «أجندة المعرض» راسٍ دائمًا في أعلى الخريطة (تحت بطاقة الاتجاهات على الشاشات الضيقة):
          مكان ثابت سهل الوصول لا يغطّي تفاصيل القاعة. كان معلّقًا فوق المسرح يتبعه، فيحجب ما حوله ---- */
  function updateScreenAnchor() {
    if (!screenBtn || document.body.classList.contains('is-lifting') || document.body.classList.contains('is-agenda')) return;
    const box = canvas.getBoundingClientRect();
    let dockTop = parseFloat(getComputedStyle(screenBtn).getPropertyValue('--screen-dock-top')) || 128;
    // بطاقة الاتجاهات بعرض الشاشة (الشاشات الضيقة): الزر يرسو تحتها لا تحتها مخفيًّا
    // صندوق الحقلين وحده — لا قائمة النتائج تحته، فلا يقفز الزر إلى أسفلها حين تُفتح
    const card = document.querySelector('.nav-card:not([hidden]) .nav-card__box');
    if (card) {
      const c = card.getBoundingClientRect();
      if (c.left < box.width / 2 && c.right > box.width / 2) dockTop = Math.max(dockTop, c.bottom + 12);
    }
    screenBtn.style.left = box.width / 2 + 'px';
    screenBtn.style.setProperty('--screen-position-top', dockTop + 'px');
    screenBtn.dataset.position = 'docked';
  }
  addEventListener('resize', updateScreenAnchor);
  if (document.fonts) document.fonts.ready.then(updateScreenAnchor);
  // كل رسم جديد للمشهد يحرّك الزر مع المسرح، ويُعلم زر الزجاج السائل (يراقب style على الكانفس)
  let frameNo = 0;
  venue.onRender(() => {
    updateScreenAnchor();
    canvas.style.setProperty('--venue-frame', String(++frameNo % 1000));
  });

  /* ---- مؤشر السحب ---- */
  // السحب على المشهد لا يبدأ تحديد نص في الصفحة
  venue.renderer.domElement.addEventListener('mousedown', e => e.preventDefault());
  venue.controls.addEventListener('start', () => { canvas.classList.add('is-panning'); document.body.classList.add('is-panning'); });
  venue.controls.addEventListener('end', () => { canvas.classList.remove('is-panning'); document.body.classList.remove('is-panning'); });

  /* ---- منظور / علوي ---- */
  if (viewSwitch) viewSwitch.addEventListener('click', e => {
    const btn = e.target.closest('button[data-view]');
    if (!btn || document.body.classList.contains('is-lifting')) return;
    viewSwitch.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b === btn)));
    venue.fly(venue.views[btn.dataset.view]());
  });

  const reduced = matchMedia('(prefers-reduced-motion: reduce)');

  /* ---- الأجندة على الشاشة ثلاثية الأبعاد ---- */
  const display = wall.querySelector('.scene__screen');
  // مع باك اند مُعدّ لا تظهر الأجندة التجريبية ولو لحظة: فارغة حتى تصل الفعلية
  if (site.api && site.api.space && site.api.event) setStages([]);
  if (display) mountAgenda(display);
  // الطبقة مخفية (visibility) خارج وضع الشاشة؛ نُظهرها لحظة الرسم وهي شفافة أصلًا
  const paintScreen = () => {
    if (!display) return;
    const was = wall.style.visibility;
    wall.style.visibility = 'visible';
    const image = paintDisplay(display);
    wall.style.visibility = was;
    if (image) venue.setScreenImage(image);
  };
  // نرسم بعد تحميل الخط وشعارَي الأجندة؛ الطبقة مخفية لكنها مُخطَّطة فتُقرأ أبعادها
  const logos = display ? Array.from(display.querySelectorAll('img')) : [];
  Promise.all([document.fonts ? document.fonts.ready : null,
    ...logos.map(img => img.complete ? null : new Promise(r => { img.onload = img.onerror = r; }))]).then(paintScreen);
  // تتبع الجلسة الجارية كل دقيقة — إلا والزائر أمام الشاشة يتصفّحها
  setInterval(() => { if (display && !atScreen) { mountAgenda(display); paintScreen(); } }, 60000);
  // الأجندة المحلية دون طلبات شبكة خارجية
  if (setStages([]) && display) { mountAgenda(display); paintScreen(); }
  // يطابق المحتوى التفاعلي على وجه الشاشة في موضعه الحالي على الصفحة
  function placeDisplay() {
    const r = venue.screenRect();
    Object.assign(display.style, { left: r.x + 'px', top: r.y + 'px', width: r.width + 'px', height: r.height + 'px' });
  }
  /* ---- الضغط على جلسة في الشاشة: بطاقة تفاصيلها مختصرة في المساحة الفارغة فوق الشاشة،
          تحت زر الرجوع — بلا أي حركة للمشهد ---- */
  const details = mountSessionPop();
  wall.addEventListener('click', e => {
    const row = e.target.closest('[data-session]');
    if (!row || !atScreen) return;
    details.open(+row.dataset.session, row, () => {
      const bar = screenToolbar ? screenToolbar.getBoundingClientRect() : null;
      const top = (bar ? bar.bottom : 0) + 12;
      return { x: 0, y: top, w: canvas.clientWidth, h: venue.screenRect().y - top - 12 };
    });
  });

  /* ---- «أجندة المعرض»: الطيران إلى شاشة المسرح والعودة — بلا مغادرة المشهد ---- */
  let atScreen = false, saved = null;
  const setPlanInert = value => {
    dock.inert = value;
    if (screenBtn) screenBtn.inert = value;
    venue.controls.enabled = !value;
  };
  wall.inert = true;
  if (screenToolbar) screenToolbar.inert = true;
  wall.style.opacity = '0';
  const fade = (to, done) => {
    const from = parseFloat(wall.style.opacity) || 0;
    wall.style.opacity = String(to);
    if (reduced.matches) { done && done(); return; }
    wall.animate([{ opacity: from }, { opacity: to }], { duration: 260, easing: 'ease' }).finished.then(() => done && done());
  };
  function goScreen(push) {
    if (atScreen) return;
    atScreen = true;
    // مسار الصفحة صريحًا: '#screen' وحدها تُحَلّ على <base href="/"> في خريطة المشرف فتخرج من /admin
    if (push !== false) history.pushState({ v: 'screen' }, '', location.pathname + location.search + '#screen');
    saved = venue.current();
    setPlanInert(true);
    document.body.classList.add('is-lifting');
    venue.fly(venue.views.screen(), () => {
      if (!atScreen) return;
      venue.controls.enabled = false;
      placeDisplay();
      document.body.classList.add('at-screen');
      fade(1);
      wall.inert = false;
      if (screenToolbar) screenToolbar.inert = false;
      if (backBtn) backBtn.focus({ preventScroll: true });
    });
  }
  function goPlan(push) {
    if (!atScreen) return;
    atScreen = false;
    details.close();
    if (push !== false && location.hash === '#screen') history.pushState({}, '', location.pathname + location.search);
    paintScreen();
    document.body.classList.remove('at-screen');
    wall.inert = true;
    if (screenToolbar) screenToolbar.inert = true;
    fade(0, () => {
      venue.fly(saved || venue.views.perspective(), () => {
        if (atScreen) return;
        document.body.classList.remove('is-lifting');
        setPlanInert(false);
        updateScreenAnchor();
        if (screenBtn) screenBtn.focus({ preventScroll: true });
      });
    });
  }
  // تغيير حجم النافذة أثناء الوقوف أمام الشاشة: نعيد الإطار فورًا
  addEventListener('resize', () => {
    if (!atScreen || !document.body.classList.contains('at-screen')) return;
    venue.fly(venue.views.screen(), placeDisplay, true);
  });
  if (screenBtn) screenBtn.addEventListener('click', () => goScreen());
  // الضغط على المسرح في الخريطة (wayfinding.js) يفعل ما يفعله الزر
  document.addEventListener('map:stage', () => { if (location.hash !== '#screen') goScreen(); });
  if (backBtn) backBtn.addEventListener('click', () => goPlan());
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && atScreen) goPlan(); });

  /* ---- رمز الأجندة في الجوال (?agenda): البطاقة الكبيرة ونظرة جانبية على المسرح ---- */
  const panel = mountAgendaPanel({ onClose: () => closeAgenda(), details });
  function stagePose() {
    const v = venue.current(), sv = site.stageView;
    v.target.set(...sv.target);
    v.position.set(...sv.position);
    const aspect = canvas.clientWidth / Math.max(1, canvas.clientHeight);
    if (aspect < 1.2) v.position.sub(v.target).multiplyScalar(Math.min(2.2, 1.2 / aspect)).add(v.target);
    return v;
  }
  // المسرح في الجزء الظاهر من الشاشة: تحت البطاقة إن غطّت العرض، وبجانبها إن كانت في الطرف
  function frameBesidePanel() {
    const el = document.querySelector('.agenda-panel'), cam = venue.camera;
    const W = canvas.clientWidth, H = canvas.clientHeight;
    if (!el || el.hidden) { cam.clearViewOffset(); cam.updateProjectionMatrix(); venue.invalidate(); return; }
    const r = el.getBoundingClientRect();
    let x = 0, y = 0;
    if (r.width > W * .6) y = -Math.min(r.bottom, H * .7) / 2;
    else x = r.left > W / 2 ? (W - r.left) / 2 : -r.right / 2;
    cam.setViewOffset(W, H, x, y, W, H);
    cam.updateProjectionMatrix();
    venue.invalidate();
  }
  function openAgenda() {
    if (panel.isOpen) return;
    saved = venue.current();
    document.body.classList.add('is-agenda');
    panel.open();
    frameBesidePanel();
    if (site.stageView) venue.fly(stagePose());
  }
  function closeAgenda() {
    if (!document.body.classList.contains('is-agenda')) return;
    panel.close(); details.close();
    document.body.classList.remove('is-agenda');
    frameBesidePanel();
    dispatchEvent(new Event('resize'));          // طبقة التنقّل تعيد إزاحتها هي إن كان طريق مرسوم
    venue.fly(saved || venue.views.perspective(), updateScreenAnchor);
  }
  // بعد طبقة التنقّل (تعيد إزاحتها هي عند تغيّر الحجم) — فتبقى إزاحة الأجندة الأخيرة
  addEventListener('resize', () => { if (panel.isOpen) setTimeout(frameBesidePanel); });
  addEventListener('popstate', () => { if (location.hash === '#screen') goScreen(false); else goPlan(false); });
  if (location.hash === '#screen') requestAnimationFrame(() => goScreen(false));
  if (new URLSearchParams(location.search).has('agenda')) requestAnimationFrame(() => openAgenda());
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && panel.isOpen && !atScreen) closeAgenda(); });

  /* ---- شاشة الإرشاد: تعود لوضعها الافتراضي بعد دقيقة بلا لمس، وتُعيد تحميل الصفحة
          كل بضع ساعات وهي خاملة (تلتقط آخر نسخة منشورة وتبدأ نظيفة) ---- */
  if (site.here) {
    const IDLE_MS = 60 * 1000, RELOAD_MS = 4 * 60 * 60 * 1000, loadedAt = Date.now();
    let lastTouch = Date.now(), atRest = true;
    ['pointerdown', 'keydown', 'wheel', 'input'].forEach(type =>
      addEventListener(type, () => { lastTouch = Date.now(); atRest = false; }, { capture: true, passive: true }));
    function resetKiosk() {
      atRest = true;
      // الشاشة تعود للعربية لزائرها التالي
      if (EN) { setLang('ar'); return; }
      if (atScreen) goPlan();
      if (panel.isOpen) closeAgenda();
      details.close();
      // التنقّل (يمسح الطريق ويعيد «من» لموقعك الحالي) وبطاقة الجناح يستمعان لهذا الحدث
      document.dispatchEvent(new CustomEvent('map:reset'));
      if (viewSwitch) viewSwitch.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.view === 'perspective')));
      if (!atScreen) venue.fly(venue.views.perspective());
      if (document.activeElement && document.activeElement !== document.body) document.activeElement.blur();
    }
    setInterval(() => {
      const idle = Date.now() - lastTouch;
      if (idle < IDLE_MS) return;
      if (Date.now() - loadedAt > RELOAD_MS) { location.reload(); return; }
      if (!atRest) resetKiosk();
    }, 5000);
  }
}
