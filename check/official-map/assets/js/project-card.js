/* =========================================================
   بطاقة الجناح: البوب أوفر الصغير فوق الجناح، والبوب أب الكبير بتفاصيل المشروع
   هما بطاقة واحدة بحجمين — بالعناصر نفسها (الشارة، الاسم، الكود، صفوف الدولة والمسار والقائد،
   زر الاتجاهات). «تفاصيل المشروع» يكبّر البطاقة إلى وسط الشاشة: كل عنصر ينتقل من مكانه في الصغيرة
   إلى مكانه في الكبيرة (View Transitions بأسماء مشتركة pv-*)، وزر التفاصيل نفسه يتفتّح إلى قسم الفكرة.
   «رجوع» يعكس الحركة. بلا دعم للانتقالات أو مع تقليل الحركة: تبدّل مباشر.
   وخريطة المشرف: البوب أوفر نفسه بصفوف القائد والأعضاء وحدهم (teamRows) بلا تفاصيل المشروع.
   ========================================================= */
import { button, iconButton, icon, esc } from '../primitives/ui.js';
import { tr, EN } from './i18n.js';

const I = {
  close: icon('<path d="M18 6L6 18M6 6l12 12"/>', 18),
  chev: icon('<path d="M6 9l6 6 6-6"/>', 18),
  link: icon('<path d="M10 14a4 4 0 005.66 0l3-3a4 4 0 00-5.66-5.66l-1 1"/><path d="M14 10a4 4 0 00-5.66 0l-3 3a4 4 0 005.66 5.66l1-1"/>', 14),
  route: icon('<circle cx="6" cy="19" r="2.5"/><circle cx="18" cy="5" r="2.5"/><path d="M8.5 19H16a3.5 3.5 0 000-7H8a3.5 3.5 0 010-7h7.5"/>', 16)
};
const BOOTH = code => tr('بوث ', 'Booth ') + code;
const calm = matchMedia('(prefers-reduced-motion: reduce)');

/* ---------- العناصر المشتركة: تُرسم بالدالة نفسها في البطاقتين حتى تتطابق تمامًا ---------- */
// الشارة والمنطقة (extra: زر الإغلاق في الكبيرة)
export const cardHead = (t, zone, extra = '') =>
  '<div class="bp-head"><span class="bp-chip">' + tr('بوث', 'Booth') + ' <bdi dir="ltr">' + esc(t.code) + '</bdi></span>' +
    (zone ? '<span class="bp-zone">' + esc(zone) + '</span>' : '') + extra + '</div>' +
  '<h3 class="booth-pop__team">' + esc(t.exhibitor || BOOTH(t.code)) + '</h3>' +
  (t.teamCode ? '<span class="bp-code" dir="ltr">' + esc(t.teamCode) + '</span>' : '');
// صفوف الدولة (بعلمها إلا على شاشات الإرشاد) والمسار والقائد (بأول حرف من اسمه)
// صفّ القائد بأول حرف من اسمه — هو نفسه في البطاقتين
const leaderRow = (t, extra = '') => !t.leader ? '' :
  '<div class="bp-row bp-row--leader"><span class="bp-avatar" aria-hidden="true">' + esc(t.leader.trim().charAt(0)) + '</span>' +
    '<span class="bp-row__stack"><span class="bp-row__label">' + tr('قائد الفريق', 'Team leader') + '</span><b class="bp-row__value">' + esc(t.leader) + '</b></span>' + extra + '</div>';
export function cardRows(t, noFlags) {
  return '<div class="bp-rows">' +
    (t.country ? '<div class="bp-row bp-row--country">' +
      (t.flag && !noFlags ? '<span class="bp-flag" aria-hidden="true">' + esc(t.flag) + '</span>' : '') +
      '<span class="bp-row__label">' + tr('الدولة', 'Country') + '</span><b class="bp-row__value">' + esc(t.country) + '</b></div>' : '') +
    (t.track ? '<div class="bp-row bp-row--track"><span class="bp-row__label">' + tr('المسار', 'Track') + '</span><b class="bp-row__value">' + esc(t.track) + '</b></div>' : '') +
    leaderRow(t) +
  '</div>';
}
// خريطة المشرف: البوب أوفر نفسه — الحضور (هل حضر، ووقته، وكم حضر من أعضائه) والتحكيمات،
// ثم القائد وأعضاء الفريق، بجانب كلٍّ حضوره اليوم (بلا الدولة والمسار والفكرة)
const clock = d => d.toLocaleTimeString(EN ? 'en-GB' : 'ar-SA-u-nu-latn', { hour: 'numeric', minute: '2-digit' });
// «تحكيم واحد · تحكيمان · 3 تحكيمات · 11 تحكيمًا»
const evals = n => EN ? n + (n === 1 ? ' evaluation' : ' evaluations')
  : n === 1 ? 'تحكيم واحد' : n === 2 ? 'تحكيمان' : n % 100 >= 3 && n % 100 <= 10 ? n + ' تحكيمات' : n + ' تحكيمًا';
const presence = m => !m || m.checkedIn === null || m.checkedIn === undefined ? '' :
  '<span class="bp-in' + (m.checkedIn ? ' is-in' : '') + '">' +
    (m.checkedIn ? tr('حضر', 'In') + (m.checkedInAt ? ' · ' + clock(m.checkedInAt) : '') : tr('لم يحضر', 'Not in')) + '</span>';
export function teamRows(t) {
  const d = t.details || { members: [] }, a = t.admin, others = d.members.filter(m => m.role !== 'leader');
  const lead = d.members.find(m => m.role === 'leader');
  const attend = !a ? '' : '<div class="ts-attend bp-attend ts-attend--' + (a.checkedIn ? 'in' : 'out') + '">' +
      '<i class="ts-attend__dot" aria-hidden="true"></i>' +
      '<span class="ts-attend__text"><b>' + (a.checkedIn ? tr('حضر الفريق اليوم', 'Team checked in today') : tr('لم يحضر الفريق بعد', 'Team not checked in yet')) + '</b>' +
        (a.checkedIn && a.leaderCheckedInAt ? '<span>' + tr('الساعة ', 'At ') + clock(a.leaderCheckedInAt) + '</span>' : '') + '</span>' +
      '<span class="ts-attend__count">' + tr(a.checkedInCount + ' من ' + a.membersCount, a.checkedInCount + ' of ' + a.membersCount) + '</span></div>';
  const judged = !a || a.evaluations === null ? '' : '<div class="bp-row"><span class="bp-row__label">' + tr('التحكيمات', 'Evaluations') + '</span>' +
    '<b class="bp-row__value">' + (a.evaluations ? evals(a.evaluations) : tr('لم يُحكَّم بعد', 'Not evaluated yet')) + '</b></div>';
  // الفريق قائمة مضغوطة في صندوق واحد: القائد أولًا بشارة صغيرة، والأعضاء تحته سطرًا سطرًا (الاسم وحضوره فقط)
  const crew = [lead || (t.leader ? { name: t.leader, role: 'leader', checkedIn: null } : null), ...others].filter(Boolean);
  const line = m => '<li class="bp-crew__row' + (m.role === 'leader' ? ' is-lead' : '') + '">' +
    '<span class="bp-crew__dot" aria-hidden="true">' + esc(m.name.trim().charAt(0)) + '</span>' +
    '<span class="bp-crew__name">' + esc(m.name) + '</span>' +
    (m.role === 'leader' ? '<span class="bp-crew__lead">' + tr('القائد', 'Leader') + '</span>' : '') + presence(m) + '</li>';
  return '<div class="bp-rows">' + attend + judged +
    (crew.length ? '<ul class="bp-crew" aria-label="' + tr('أعضاء الفريق', 'Team members') + '">' + crew.map(line).join('') + '</ul>' : '') + '</div>';
}
// العضو بشكل صفّ القائد: أول حرف من اسمه، واسمه أولًا ثم دوره وتخصّصه تحته بخطّ أخفّ (extra: حضوره للمشرف)
function member(m, extra = '') {
  const meta = [tr('عضو', 'Member'), m.specialty].filter(Boolean).map(esc).join(' · ');
  return '<li class="bp-row pc-member"><span class="bp-avatar" aria-hidden="true">' + esc(m.name.trim().charAt(0)) + '</span>' +
    '<span class="bp-row__stack"><b class="bp-row__value">' + esc(m.name) + '</b><span class="bp-row__label">' + meta + '</span></span>' +
    (m.linkedin ? '<a class="ts-member__link pc-member__link" href="' + esc(m.linkedin) + '" target="_blank" rel="noopener noreferrer">' + I.link + 'LinkedIn</a>' : '') + extra +
  '</li>';
}
export const goButton = i =>
  button(tr('الاتجاهات', 'Directions'), { variant: 'primary', icon: I.route, attrs: { 'data-go': 'table:' + i }, cls: 'bp-go' });
export const detailsButton = () =>
  button(tr('تفاصيل المشروع', 'Project details'), { variant: 'soft', attrs: { 'data-pop': 'details' }, cls: 'bp-details' });

// onGo(placeId): الاتجاهات إلى الجناح · onBack: عادت البطاقة الصغيرة · noFlags: شاشات الإرشاد
export function mountProjectCard({ onGo, onBack, noFlags = false }) {
  const root = document.createElement('div');
  root.className = 'project-card';
  root.hidden = true;
  root.innerHTML = '<div class="pc-scrim" data-pc="back"></div>' +
    '<section class="pc-card" role="dialog" aria-modal="true"></section>';
  document.body.appendChild(root);
  const card = root.querySelector('.pc-card');
  let current = null, html = '', busy = null, membersOpen = false;

  // الترتيب نفسه في الصغيرة: الرأس ثم الصفوف — ثم ما تضيفه الكبيرة: فكرة المشروع (مكان زر التفاصيل) والأعضاء
  function render() {
    const { t, i, zone } = current, d = t.details || { description: null, members: [], membersCount: 0 };
    const others = d.members.filter(m => m.role !== 'leader');
    // pc-grab: مقبض الشيت السفلي (الجوال) · pc-edge: حافة التمرير العلوية — تدرّج خفيف وتمويه متدرّج كشيت iOS
    const next =
      '<div class="pc-grab" aria-hidden="true"></div>' +
      '<div class="pc-scroll">' +
        cardHead(t, zone, iconButton(I.close, tr('رجوع إلى الخريطة', 'Back to map'), { 'data-pc': 'back' }, 'pc-close')) +
        cardRows(t, noFlags) +
        // تحت صفّ القائد: «أعضاء الفريق» نصًّا مجرّدًا بعددهم وسهم — يُضغط فتنسدل صفوف الأعضاء بشكل صفّ القائد
        (others.length ? '<div class="pc-team' + (membersOpen ? ' is-open' : '') + '">' +
          '<button type="button" class="pc-team__toggle" data-pc="members" aria-expanded="' + membersOpen + '" aria-controls="pc-team-list">' +
            tr('أعضاء الفريق', 'Team members') + ' <span class="pc-team__count">' + others.length + '</span>' +
            '<span class="pc-team__chev">' + I.chev + '</span></button>' +
          '<div class="pc-team__body" id="pc-team-list"><div class="pc-team__clip">' +
            '<ul class="pc-team__list">' + others.map(member).join('') + '</ul></div></div>' +
        '</div>' : '') +
        '<section class="pc-idea"><h4>' + tr('فكرة المشروع', 'Project idea') + '</h4>' +
          (d.description ? '<p class="pc-idea__text">' + esc(d.description) + '</p>'
            : '<p class="pc-idea__text is-empty">' + tr('لم يُضف الفريق وصفًا لمشروعه بعد.', 'The team has not added a project description yet.') + '</p>') +
        '</section>' +
      '</div>' +
      '<div class="pc-edge" aria-hidden="true"><i></i><i></i><i></i></div>' +
      '<div class="pc-foot">' + goButton(i) + '</div>';
    if (next === html) return;
    const scroll = card.querySelector('.pc-scroll'), top = scroll ? scroll.scrollTop : 0;
    card.innerHTML = html = next;
    if (scroll) card.querySelector('.pc-scroll').scrollTop = top;
    card.classList.toggle('is-scrolled', top > 2);
  }

  // قسم الفكرة طويل ويتمرّر داخل البطاقة؛ لقطة الانتقال تأخذه كاملًا فتفيض تحت البطاقة.
  // أثناء الانتقال وحده يُقصّ بقدر ما يظهر منه، ثم يعود كما كان (المرئي هو نفسه)
  function capIdea() {
    const sc = card.querySelector('.pc-scroll'), idea = card.querySelector('.pc-idea');
    if (!sc || !idea) return () => {};
    const vis = Math.floor(sc.getBoundingClientRect().bottom - idea.getBoundingClientRect().top);
    if (vis >= idea.offsetHeight) return () => {};
    idea.style.maxHeight = Math.max(0, vis) + 'px';
    idea.style.overflow = 'hidden';
    return () => { idea.style.maxHeight = idea.style.overflow = ''; };
  }

  // update: تبديل الـDOM من حالة لأخرى — داخل انتقال إن أمكن. dir: اتجاه الحركة (للتوقيت في CSS)
  function transition(dir, update) {
    if (!document.startViewTransition || calm.matches) { update(); return Promise.resolve(); }
    document.documentElement.dataset.pv = dir;
    const vt = document.startViewTransition(update);
    return vt.finished.catch(() => {}).finally(() => { delete document.documentElement.dataset.pv; });
  }

  // hideFrom: يخفي البطاقة الصغيرة حين تحلّ الكبيرة محلّها
  function open(t, i, zone, hideFrom) {
    if (busy) return;
    current = { t, i, zone }; html = ''; membersOpen = false;
    card.setAttribute('aria-label', t.exhibitor || BOOTH(t.code));
    render();
    let uncap = () => {};
    busy = transition('grow', () => {
      hideFrom();
      root.hidden = false;
      document.body.classList.add('is-project-card');
      uncap = capIdea();
    }).then(() => { uncap(); busy = null; });
    card.querySelector('.pc-close').focus({ preventScroll: true });
  }
  // instant: إغلاق بلا رجوع للبطاقة الصغيرة (جناح آخر، إعادة ضبط الخريطة، الاتجاهات)
  function close(instant) {
    if (!current) return;
    const done = () => {
      card.style.transform = '';
      root.hidden = true;
      document.body.classList.remove('is-project-card');
      current = null; html = '';
    };
    if (instant) { done(); return; }
    // أعضاء الفريق يُطوون فورًا والصفوف في مكانها: تعود البطاقة إلى الصغيرة بلا قفزة ولا فيض
    const team = card.querySelector('.pc-team');
    if (team) { team.querySelector('.pc-team__body').style.transition = 'none'; team.classList.remove('is-open'); }
    card.querySelector('.pc-scroll').scrollTop = 0;
    capIdea();   // تُغلق البطاقة بعده فلا حاجة لإعادته
    busy = transition('shrink', () => { done(); if (onBack) onBack(); }).then(() => { busy = null; });
  }

  // حافة التمرير: تظهر حين يمرّ المحتوى تحت رأس الشيت، وتختفي في أعلاه
  card.addEventListener('scroll', e => {
    if (e.target.classList && e.target.classList.contains('pc-scroll')) card.classList.toggle('is-scrolled', e.target.scrollTop > 2);
  }, true);

  /* ---- الجوال (شيت سفلي): سحبه للأسفل من مقبضه أو رأسه — والمحتوى في أعلاه — يرجعه إلى البوب أوفر ---- */
  const phone = matchMedia('(max-width: 600px)');
  let drag = null;
  card.addEventListener('pointerdown', e => {
    if (!phone.matches || !e.isPrimary || busy || !current || e.target.closest('button, a')) return;
    const sc = card.querySelector('.pc-scroll');
    const onGrab = e.target.closest('.pc-grab') || (e.target.closest('.bp-head, .booth-pop__team, .bp-code') && sc.scrollTop <= 0);
    if (!onGrab) return;
    drag = { y: e.clientY, t: performance.now(), dy: 0, id: e.pointerId };
    try { card.setPointerCapture(e.pointerId); } catch { /* مؤشر غير نشط */ }
    card.style.transition = 'none';
  });
  card.addEventListener('pointermove', e => {
    if (!drag || e.pointerId !== drag.id) return;
    drag.dy = Math.max(0, e.clientY - drag.y);
    card.style.transform = 'translateY(' + drag.dy + 'px)';
  });
  const release = e => {
    if (!drag || e.pointerId !== drag.id) return;
    const { dy, t } = drag, fast = dy / Math.max(1, performance.now() - t) > .6;
    drag = null;
    if (dy > 110 || (fast && dy > 30)) {
      // يعود من حيث أفلته الإصبع: الانتقال يبدأ من الشيت المسحوب وينتهي بالبوب أوفر
      card.style.transition = '';
      close();   // الإزاحة تُزال داخل الانتقال (done) بعد أخذ لقطة الشيت المسحوب
    } else {
      card.style.transition = 'transform .32s cubic-bezier(.32,.72,0,1)';
      card.style.transform = '';
      setTimeout(() => { card.style.transition = ''; }, 320);
    }
  };
  card.addEventListener('pointerup', release);
  card.addEventListener('pointercancel', release);

  root.addEventListener('click', e => {
    const go = e.target.closest('[data-go]');
    if (go) { const to = go.dataset.go; close(true); onGo(to); return; }
    // أعضاء الفريق: يُفتح ويُطوى في مكانه — الكلاس وحده يحرّك الارتفاع والسهم
    const team = e.target.closest('[data-pc="members"]');
    if (team) {
      membersOpen = !membersOpen;
      team.setAttribute('aria-expanded', membersOpen);
      team.parentElement.classList.toggle('is-open', membersOpen);
      html = '';   // الرسم القادم (تحديث البيانات) يحفظ الحالة الجديدة
      return;
    }
    if (e.target.closest('[data-pc="back"]') && !busy) close();
  });
  // فوق بطاقة الجناح: Esc يرجع خطوة واحدة (إلى البطاقة الصغيرة) لا يغلق كل شيء
  addEventListener('keydown', e => { if (e.key === 'Escape' && current) { e.stopImmediatePropagation(); if (!busy) close(); } }, true);

  return {
    open, close,
    get isOpen() { return !!current; },
    refresh() { if (current) render(); }
  };
}
