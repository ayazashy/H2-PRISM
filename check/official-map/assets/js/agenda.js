/* =========================================================
   أجندة المعرض — بهوية سيف
     · mountAgenda: نسخة الشاشة الرئيسية للمسرح (نسيج ثلاثي الأبعاد يرسمه
       paintDisplay: خلفيات وحدود وصور ونص سطرًا واحدًا، بلا SVG ولا التفاف).
     · mountAgendaPanel: البطاقة الكبيرة على الصفحة — الجارية الآن وكم بقي لها،
       والتالية ومتى تبدأ، والقائمة كاملة؛ ولكل جلسة «أضف للتقويم» (ملف ics).
     · mountSessionPop: تفاصيل جلسة عند الضغط عليها — في الشاشة أو في البطاقة:
       وقتها ومدتها ومكانها، من يقدّمها، ومحاورها، و«أضف للتقويم».
   الحالة (انتهت / الآن / قادمة) تُحسب من الساعة الفعلية وتتحدّث كل نصف دقيقة.
   ========================================================= */
import { button, iconButton, pressable, icon, esc } from '../primitives/ui.js';
import { tr, EN } from './i18n.js';

// تاريخ المعرض 'YYYY-MM-DD' — فارغ = وضع تجريبي: الجلسات تُزاح حول الساعة الآن
// (الجلسة الثالثة جارية) فيظهر «الآن» و«التالي» وكم بقي في أي وقت تُفتح فيه الصفحة
export const EVENT_DATE = null;
// جلسات تجريبية حتى تصل أجندة سيف الفعلية — البداية، المدة بالدقائق، العنوان، المكان،
// النوع، نبذة، المقدّمون (الاسم · الصفة)، والمحاور
export const SESSIONS = [
  { time: '09:00', mins: 30, title: 'الافتتاح الرسمي للمعرض', where: 'منصة الإعلانات', kind: 'افتتاح',
    about: 'كلمة الترحيب وإطلاق النسخة الأولى من معرض ومسابقة الأمن والابتكار.',
    hosts: [['م. عبدالله الرشيد', 'رئيس اللجنة المنظمة']], topics: ['رؤية المعرض', 'مسارات المسابقة', 'جدول الأيام'] },
  { time: '09:30', mins: 45, title: 'كلمة راعي المعرض', where: 'منصة الإعلانات', kind: 'كلمة',
    about: 'كلمة الراعي الرسمي عن الشراكة في بناء القدرات الوطنية في الأمن والابتكار.',
    hosts: [['د. سارة القحطاني', 'الراعي الرسمي']], topics: ['الشراكة', 'بناء القدرات', 'الفرص للمشاركين'] },
  { time: '10:15', mins: 75, title: 'جلسة حوارية: مستقبل الأمن السيبراني', where: 'منصة الإعلانات', kind: 'جلسة حوارية',
    about: 'حوار مع خبراء الأمن عن التهديدات القادمة وكيف يستعد لها الجيل القادم من المختصين.',
    hosts: [['د. فهد الدوسري', 'خبير الأمن السيبراني'], ['م. ريم الحربي', 'باحثة في الذكاء الاصطناعي'], ['خالد العتيبي', 'مدير الحوار']],
    topics: ['الذكاء الاصطناعي في الهجوم والدفاع', 'حماية البنى التحتية الحيوية', 'المهارات المطلوبة 2030'] },
  { time: '11:30', mins: 90, title: 'إعلان المشاريع المتأهلة', where: 'منصة الإعلانات', kind: 'إعلان',
    about: 'إعلان الفرق المتأهلة للمرحلة النهائية بعد تقييم لجان التحكيم.',
    hosts: [['م. نورة الشهري', 'رئيسة لجنة التحكيم']], topics: ['معايير التقييم', 'الفرق المتأهلة', 'خطوات المرحلة النهائية'] },
  { time: '13:00', mins: 120, title: 'ورشة: الابتكار في الحماية الرقمية', where: 'منطقة العمل', kind: 'ورشة عمل',
    about: 'ورشة تطبيقية لبناء نموذج أولي لحل حماية رقمية خلال ساعتين، بفرق صغيرة.',
    hosts: [['م. تركي الغامدي', 'مهندس حلول أمنية'], ['لمى الزهراني', 'مصممة تجربة المستخدم']],
    topics: ['تحديد المشكلة', 'تصميم الحل', 'نمذجة سريعة', 'عرض النتائج'] },
  { time: '15:00', mins: 60, title: 'تكريم الفائزين وختام اليوم', where: 'منصة الإعلانات', kind: 'حفل',
    about: 'تكريم الفرق الفائزة في مسارات المسابقة وختام اليوم الأول.',
    hosts: [['م. عبدالله الرشيد', 'رئيس اللجنة المنظمة']], topics: ['الجوائز', 'كلمة الختام'] }
];

// النسخة الإنجليزية: النصوص نفسها، والأوقات والمدد من النسخة العربية
const SESSIONS_EN = [
  { title: 'Official Opening', where: 'Announcements Stage', kind: 'Opening',
    about: 'Welcome remarks and the launch of the first edition of the Security & Innovation Fair and Competition.',
    hosts: [['Eng. Abdullah Al-Rasheed', 'Chair, Organizing Committee']], topics: ['The fair\'s vision', 'Competition tracks', 'Schedule of the days'] },
  { title: 'Sponsor Keynote', where: 'Announcements Stage', kind: 'Keynote',
    about: 'The official sponsor on partnering to build national capabilities in security and innovation.',
    hosts: [['Dr. Sarah Al-Qahtani', 'Official Sponsor']], topics: ['Partnership', 'Capacity building', 'Opportunities for participants'] },
  { title: 'Panel: The Future of Cybersecurity', where: 'Announcements Stage', kind: 'Panel',
    about: 'Security experts discuss the threats ahead and how the next generation of specialists can prepare.',
    hosts: [['Dr. Fahad Al-Dosari', 'Cybersecurity Expert'], ['Eng. Reem Al-Harbi', 'AI Researcher'], ['Khalid Al-Otaibi', 'Moderator']],
    topics: ['AI in attack and defense', 'Protecting critical infrastructure', 'Skills needed for 2030'] },
  { title: 'Finalists Announcement', where: 'Announcements Stage', kind: 'Announcement',
    about: 'Announcing the teams that qualified for the final round after the judging panels\' review.',
    hosts: [['Eng. Noura Al-Shehri', 'Head of the Judging Panel']], topics: ['Evaluation criteria', 'Qualified teams', 'Final-round steps'] },
  { title: 'Workshop: Innovation in Digital Protection', where: 'Workspace', kind: 'Workshop',
    about: 'A hands-on workshop to prototype a digital-protection solution in two hours, in small teams.',
    hosts: [['Eng. Turki Al-Ghamdi', 'Security Solutions Engineer'], ['Lama Al-Zahrani', 'UX Designer']],
    topics: ['Defining the problem', 'Designing the solution', 'Rapid prototyping', 'Presenting results'] },
  { title: 'Awards & Closing', where: 'Announcements Stage', kind: 'Ceremony',
    about: 'Honoring the winning teams across the competition tracks and closing day one.',
    hosts: [['Eng. Abdullah Al-Rasheed', 'Chair, Organizing Committee']], topics: ['Awards', 'Closing remarks'] }
];

const I = {
  close: icon('<path d="M18 6L6 18M6 6l12 12"/>', 18),
  cal: icon('<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18M12 14v4M10 16h4"/>', 16)
};

/* ---------- الوقت ---------- */
function day() {
  if (EVENT_DATE) { const [y, mo, d] = EVENT_DATE.split('-').map(Number); return new Date(y, mo - 1, d); }
  const t = new Date(); return new Date(t.getFullYear(), t.getMonth(), t.getDate());
}
const pad = n => String(n).padStart(2, '0');
function demoShift() {
  if (EVENT_DATE) return 0;
  // بداية الجلسة الثالثة قبل نصف ساعة من الآن (مقرّبة لربع ساعة)
  const [h, mi] = SESSIONS[2].time.split(':').map(Number), now = new Date();
  const anchor = new Date(day()); anchor.setHours(h, mi, 0, 0);
  const want = new Date(now.getTime() - 30 * 60000); want.setMinutes(Math.floor(want.getMinutes() / 15) * 15, 0, 0);
  return want - anchor;
}
/* ---------- الأجندة الفعلية من تحكيم (api/tahkeem.js · loadTimeline) ---------- */
// نوع المرحلة ← اسمه المعروض (OTHER يُعرض بـ type_other)
const KINDS = {
  OPENING: ['افتتاح', 'Opening'], SPEECH: ['كلمة', 'Speech'], PANEL: ['جلسة حوارية', 'Panel'], WORKSHOP: ['ورشة عمل', 'Workshop'],
  ANNOUNCEMENT: ['إعلان', 'Announcement'], CEREMONY: ['حفل', 'Ceremony'], BREAK: ['استراحة', 'Break']
};
const hm = d => pad(d.getHours()) + ':' + pad(d.getMinutes());
let remote = null;   // null = لا باك اند بعد (تبقى التجريبية) · [] = لا جلسات منشورة
// يعيد true إن تغيّرت الأجندة (فيُعاد رسم الشاشة والبطاقة)
export function setStages(stages) {
  if (!stages) return false;
  const next = stages.map((st, i) => {
    // تاريخ بلا وقت (مراحل قديمة) يُقرأ بالتوقيت المحلي لا UTC
    const when = v => new Date(/^\d{4}-\d{2}-\d{2}$/.test(v) ? v + 'T00:00' : v);
    const start = when(st.date_start), end = when(st.date_end);
    const pick = (ar, en) => (EN && st[en]) || st[ar] || st[en] || '';
    const kind = st.type === 'OTHER' ? st.type_other : KINDS[st.type] ? KINDS[st.type][EN ? 1 : 0] : '';
    const hosts = [];
    if (pick('moderator', 'moderator_en')) hosts.push([pick('moderator', 'moderator_en'), tr('مدير الحوار', 'Moderator')]);
    (st.guests || []).forEach(g => g && hosts.push([g, tr('ضيف', 'Guest')]));
    return { i, start, end, time: hm(start), until: hm(end), title: pick('title', 'title_en'), where: pick('location', 'location_en'),
      kind: kind || '', about: pick('description', 'description_en'), hosts, topics: st.topics || [] };
  }).filter(s => !isNaN(s.start) && !isNaN(s.end)).map((s, i) => ({ ...s, i }));
  const changed = JSON.stringify(next) !== JSON.stringify(remote);
  remote = next;
  return changed;
}
const sessions = () => {
  if (remote) return remote;
  const shift = demoShift();
  return SESSIONS.map((d0, i) => {
    const d = EN ? { ...d0, ...SESSIONS_EN[i] } : d0;
    const [h, mi] = d.time.split(':').map(Number), start = new Date(day()); start.setHours(h, mi, 0, 0);
    start.setTime(start.getTime() + shift);
    const end = new Date(start.getTime() + d.mins * 60000);
    return { ...d, i, time: pad(start.getHours()) + ':' + pad(start.getMinutes()), until: pad(end.getHours()) + ':' + pad(end.getMinutes()), start, end };
  });
};
// المدة بالعربية: 45 د · ساعة و10 د · ساعتان
function span(ms) {
  const total = Math.max(1, Math.round(ms / 60000)), h = Math.floor(total / 60), m = total % 60;
  if (EN) return (h ? h + ' h' : '') + (h && m ? ' ' : '') + (m || !h ? m + ' min' : '');
  const hours = h === 0 ? '' : h === 1 ? 'ساعة' : h === 2 ? 'ساعتان' : h + ' ساعات';
  if (!hours) return m + ' د';
  return m ? hours + ' و' + m + ' د' : hours;
}
export function agendaState(now = new Date()) {
  const list = sessions();
  const current = list.find(s => now >= s.start && now < s.end) || null;
  const next = list.find(s => s.start > now) || null;
  return { list, current, next, now };
}

/* ---------- نسخة الشاشة الرئيسية (نسيج) ---------- */
export function mountAgenda(host) {
  const { list, current, next, now } = agendaState();
  const live = current || next;
  host.innerHTML =
    '<div class="agenda">' +
      '<div class="agenda__head">' +
        '<img class="agenda__logo" src="assets/img/saif-logo-white.png" alt="' + tr('سيف — معرض ومسابقة الأمن والابتكار العالمية', 'SAIF — Security & Innovation Fair') + '">' +
        '<div class="agenda__title"><b>' + tr('أجندة المعرض', 'Exhibition Agenda') + '</b><span>' + tr('اليوم الأول', 'Day One') + '</span></div>' +
        '<div class="agenda__partners">' +
          '<img class="agenda__moi" src="assets/img/moi-logo-white.svg" alt="' + tr('وزارة الداخلية', 'Ministry of Interior') + '">' +
          '<img class="agenda__partner" src="assets/img/tuwaiq-logo-white-stacked.svg" alt="' + tr('أكاديمية طويق', 'Tuwaiq Academy') + '">' +
        '</div>' +
      '</div>' +
      // كل جلسة تُضغط عند الوقوف أمام الشاشة فتفتح تفاصيلها (mountSessionPop)
      '<div class="agenda__list">' + list.map(s => pressable(
          '<span class="agenda__time">' + esc(s.time) + '</span>' +
          '<span class="agenda__text"><b>' + esc(s.title) + '</b>' + (s.where ? '<span>' + esc(s.where) + '</span>' : '') + '</span>' +
          (live && s.i === live.i ? '<span class="agenda__now">' + (current ? tr('الآن', 'Now') : tr('التالي', 'Next')) + '</span>' : ''),
          'agenda__row' + (live && s.i === live.i ? ' is-now' : s.end <= now ? ' is-past' : ''),
          { 'data-session': s.i, 'aria-label': tr('تفاصيل ', 'Details: ') + s.title })).join('') +
      '</div>' +
      '<div class="agenda__bar"><i></i><i></i><i></i><i></i><i></i></div>' +
    '</div>';
  return host.querySelector('.agenda__logo');
}

/* ---------- التقويم: ملف ics لجلسة أو للأجندة كلها ---------- */
const icsTime = d => d.getFullYear() + String(d.getMonth() + 1).padStart(2, '0') + String(d.getDate()).padStart(2, '0') +
  'T' + String(d.getHours()).padStart(2, '0') + String(d.getMinutes()).padStart(2, '0') + '00';
const icsText = v => String(v).replace(/[\\;,]/g, c => '\\' + c);
function downloadIcs(list, name) {
  const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//SAIF//Agenda//AR', 'CALSCALE:GREGORIAN'];
  list.forEach(s => lines.push('BEGIN:VEVENT', 'UID:saif-' + icsTime(s.start) + '-' + s.i + '@saif',
    'DTSTAMP:' + icsTime(new Date()), 'DTSTART:' + icsTime(s.start), 'DTEND:' + icsTime(s.end),
    'SUMMARY:' + icsText(s.title + tr(' — معرض سيف', ' — SAIF')), 'LOCATION:' + icsText((s.where ? s.where + ' · ' : '') + tr('القاعة 4', 'Hall 4')), 'END:VEVENT'));
  lines.push('END:VCALENDAR');
  const url = URL.createObjectURL(new Blob([lines.join('\r\n')], { type: 'text/calendar;charset=utf-8' }));
  const a = document.createElement('a'); a.href = url; a.download = name + '.ics';
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}

/* ---------- البطاقة الكبيرة على الصفحة ---------- */
// details: بطاقة تفاصيل الجلسة (mountSessionPop) — تُفتح بالضغط على أي جلسة في القائمة
export function mountAgendaPanel({ onClose, details } = {}) {
  const panel = document.createElement('section');
  panel.className = 'agenda-panel';
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-label', tr('أجندة المعرض', 'Exhibition Agenda'));
  panel.hidden = true;
  document.body.appendChild(panel);

  function render() {
    const { list, current, next, now } = agendaState();
    const hero = s => '<div class="ap-hero' + (s === current ? ' is-now' : '') + '">' +
      '<span class="ap-hero__tag">' + (s === current ? tr('الآن', 'Now') : tr('التالي', 'Next')) + '</span>' +
      '<b class="ap-hero__title">' + esc(s.title) + '</b>' +
      '<span class="ap-hero__meta">' + esc(s.time) + (s.where ? ' · ' + esc(s.where) : '') + '</span>' +
      '<span class="ap-hero__count">' + (s === current ? tr('ينتهي بعد ', 'Ends in ') + span(s.end - now) : tr('يبدأ بعد ', 'Starts in ') + span(s.start - now)) + '</span>' +
    '</div>';
    panel.innerHTML =
      '<header class="ap-head">' +
        '<img class="ap-head__logo" src="assets/img/saif-logo-green.png" alt="' + tr('سيف', 'SAIF') + '">' +
        '<div class="ap-head__title"><h2>' + tr('أجندة المعرض', 'Exhibition Agenda') + '</h2><span>' + tr('اليوم الأول · منصة الإعلانات', 'Day One · Announcements Stage') + '</span></div>' +
        iconButton(I.close, tr('إغلاق الأجندة', 'Close agenda'), { 'data-ap': 'close' }, 'ap-head__close') +
      '</header>' +
      '<div class="ap-heroes">' + (current ? hero(current) : '') + (next ? hero(next) : '') +
        (!current && !next ? '<p class="ap-done">' + (list.length ? tr('انتهت جلسات اليوم — نراكم غدًا', 'Today\'s sessions are over — see you tomorrow')
          : tr('لم تُنشر الأجندة بعد', 'The agenda has not been published yet')) + '</p>' : '') + '</div>' +
      '<ol class="ap-list">' + list.map(s => {
        const state = s === current ? 'is-now' : s.end <= now ? 'is-past' : '';
        return '<li class="ap-row ' + state + '">' +
          pressable('<span class="ap-row__time">' + esc(s.time) + '</span>' +
            '<span class="ap-row__text"><b>' + esc(s.title) + '</b>' + (s.where ? '<span>' + esc(s.where) + '</span>' : '') + '</span>',
            'ap-row__open', { 'data-session': s.i, 'aria-label': tr('تفاصيل ', 'Details: ') + s.title }) +
          (s.end > now ? iconButton(I.cal, tr('أضف «' + s.title + '» للتقويم', 'Add “' + s.title + '” to calendar'), { 'data-ap': 'ics', 'data-i': s.i }, 'ap-row__cal') : '<span class="ap-row__done">' + tr('انتهت', 'Ended') + '</span>') +
        '</li>';
      }).join('') + '</ol>' +
      '<footer class="ap-foot">' + button(tr('أضف الأجندة كاملة للتقويم', 'Add the full agenda to calendar'), { variant: 'soft', icon: I.cal, attrs: { 'data-ap': 'ics-all' }, cls: 'ui-btn--block' }) + '</footer>';
  }

  panel.addEventListener('click', e => {
    const row = e.target.closest('[data-session]');
    if (row && details) { details.open(+row.dataset.session, row); return; }
    const b = e.target.closest('[data-ap]');
    if (!b) return;
    const list = agendaState().list;
    if (b.dataset.ap === 'close') { close(); if (onClose) onClose(); }
    else if (b.dataset.ap === 'ics') { const s = list[+b.dataset.i]; downloadIcs([s], 'saif-' + s.time.replace(':', '')); }
    else if (b.dataset.ap === 'ics-all') downloadIcs(list.filter(s => s.end > new Date()), 'saif-agenda');
  });

  let timer = 0;
  function open() {
    render();
    panel.hidden = false;
    clearInterval(timer);
    timer = setInterval(render, 30000);
    const btn = panel.querySelector('.ap-head__close');
    if (btn) btn.focus({ preventScroll: true });
  }
  function close() { panel.hidden = true; clearInterval(timer); }
  return { open, close, get isOpen() { return !panel.hidden; } };
}

/* ---------- تفاصيل جلسة: فوق الجلسة المضغوطة (أو من الأسفل على الشاشة الضيقة) ---------- */
// أول حرف من الاسم وحده (بعد اللقب: د. م. أ.)
const initials = name => name.replace(/^(د|م|أ|Dr|Eng)\.\s*/, '').trim().charAt(0);
// onClose: يُنادى حين تُغلق البطاقة (لإرجاع ما أزاحه المشهد لأجلها)
export function mountSessionPop({ onClose } = {}) {
  const pop = document.createElement('section');
  pop.className = 'session-pop';
  pop.setAttribute('role', 'dialog');
  pop.hidden = true;
  document.body.appendChild(pop);
  let at = -1;

  // fit(h, w): لعرضها عريضة في مساحة فارغة — يُعطى ارتفاعها المطلوب ويعيد المساحة {x, y, w, h}
  // (وقد يزيح المشهد ليوسّعها). بدونه تُعرض بجانب الجلسة.
  function open(i, anchor, fit) {
    const s = agendaState().list[i], now = new Date();
    if (!s) return;
    at = i;
    const state = now >= s.start && now < s.end ? [tr('الآن', 'Now'), 'is-now'] : s.end <= now ? [tr('انتهت', 'Ended'), 'is-past'] : [tr('قادمة', 'Upcoming'), ''];
    pop.setAttribute('aria-label', s.title);
    pop.innerHTML =
      '<header class="sp-head">' + (s.kind ? '<span class="sp-kind">' + esc(s.kind) + '</span>' : '') + '<span class="sp-state ' + state[1] + '">' + state[0] + '</span>' +
        // التقويم أيقونة في الرأس في العرض العريض (يوفّر سطرًا كاملًا)، وزرّ كامل أسفل البطاقة في غيره
        (s.end > now ? iconButton(I.cal, tr('أضف للتقويم', 'Add to calendar'), { 'data-sp': 'ics' }, 'sp-cal') : '') +
        iconButton(I.close, tr('إغلاق التفاصيل', 'Close details'), { 'data-sp': 'close' }, 'sp-close') + '</header>' +
      '<h3 class="sp-title">' + esc(s.title) + '</h3>' +
      // سطر واحد للوقت والمدة والمكان — يحلّ محلّ صفوفها في العرض العريض المختصر
      '<p class="sp-meta"><b dir="ltr">' + esc(s.time) + ' – ' + esc(s.until) + '</b> · ' + esc(span(s.end - s.start)) + (s.where ? ' · ' + esc(s.where) : '') + '</p>' +
      // عمودان في العرض العريض: النبذة والوقت والمكان، ثم المتحدّثون والمحاور — فوق بعض في غيره
      '<div class="sp-cols"><div class="sp-col">' +
      (s.about ? '<p class="sp-about">' + esc(s.about) + '</p>' : '') +
      // الوقت والمكان بروح «من / إلى»: صفوف رمادية بعنوان صغير وقيمة واضحة
      '<div class="sp-facts">' +
        '<div class="sp-fact"><span>' + tr('الوقت', 'Time') + '</span><b dir="ltr">' + esc(s.time) + ' – ' + esc(s.until) + '</b></div>' +
        '<div class="sp-fact"><span>' + tr('المدة', 'Duration') + '</span><b>' + esc(span(s.end - s.start)) + '</b></div>' +
        (s.where ? '<div class="sp-fact"><span>' + tr('المكان', 'Location') + '</span><b>' + esc(s.where) + '</b></div>' : '') +
      '</div>' +
      (s.topics.length ? '<p class="sp-label">' + tr('المحاور', 'Topics') + '</p>' +
      '<ol class="sp-topics">' + s.topics.map(t => '<li>' + esc(t) + '</li>').join('') + '</ol>' : '') +
      '</div><div class="sp-col">' +
      (s.hosts.length ? '<p class="sp-label">' + (s.hosts.length > 1 ? tr('المتحدّثون', 'Speakers') : tr('يقدّمها', 'Presented by')) + '</p>' +
      '<div class="sp-hosts">' + s.hosts.map(([name, role]) =>
        '<div class="sp-host"><span class="sp-host__avatar" aria-hidden="true">' + esc(initials(name)) + '</span>' +
        '<span class="sp-host__text"><b>' + esc(name) + '</b><span>' + esc(role) + '</span></span></div>').join('') + '</div>' : '') +
      '</div></div>' +
      (s.end > now ? button(tr('أضف للتقويم', 'Add to calendar'), { variant: 'primary', icon: I.cal, attrs: { 'data-sp': 'ics' }, cls: 'ui-btn--block' }) : '');
    pop.hidden = false;
    place(anchor, fit);
    const c = pop.querySelector('.sp-close'); if (c) c.focus({ preventScroll: true });
  }
  // في المساحة الفارغة إن أُعطيت واتّسعت؛ وإلا بجانب الجلسة (تحتها أو فوقها)؛ وعلى الشاشة الضيقة شيت سفلي
  function place(anchor, fit) {
    pop.classList.remove('is-sheet', 'is-wide');
    pop.style.left = pop.style.top = pop.style.width = pop.style.maxHeight = '';
    if (fit && innerWidth >= 520) {
      pop.classList.add('is-wide');
      // بلا تمرير أبدًا: تتّسع البطاقة أولًا فيقصر نصّها، وإن بقيت أطول من المساحة الفارغة
      // تمتدّ فوق أعلى الشاشة بطولها كاملًا (لا يحدّها إلا طول النافذة)
      let w = Math.min(600, innerWidth - 48);
      pop.style.width = w + 'px';
      let h = pop.offsetHeight;
      const region = fit(h, w);
      for (const wider of [720, 860]) {
        const next = Math.min(wider, innerWidth - 48, region.w - 48);
        if (h <= region.h || next <= w) break;
        w = next; pop.style.width = w + 'px'; h = pop.offsetHeight;
      }
      pop.style.maxHeight = (innerHeight - 32) + 'px';
      pop.style.left = (region.x + (region.w - w) / 2) + 'px';
      pop.style.top = (h <= region.h ? region.y + (region.h - h) / 2 : Math.max(16, Math.min(region.y, innerHeight - 16 - h))) + 'px';
      return;
    }
    if (!anchor || innerWidth < 700) { pop.classList.add('is-sheet'); return; }
    const r = anchor.getBoundingClientRect(), w = pop.offsetWidth, h = pop.offsetHeight, gap = 12;
    const x = Math.max(16, Math.min(innerWidth - w - 16, r.left + r.width / 2 - w / 2));
    const below = r.bottom + gap + h < innerHeight - 16;
    const y = below ? r.bottom + gap : Math.max(16, r.top - gap - h);
    pop.style.left = x + 'px'; pop.style.top = y + 'px';
  }
  function close() {
    if (pop.hidden) return;
    pop.hidden = true; at = -1;
    if (onClose) onClose();
  }
  pop.addEventListener('click', e => {
    const b = e.target.closest('[data-sp]');
    if (!b) return;
    if (b.dataset.sp === 'close') close();
    else if (b.dataset.sp === 'ics') { const s = agendaState().list[at]; downloadIcs([s], 'saif-' + s.time.replace(':', '')); }
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !pop.hidden) { e.stopImmediatePropagation(); close(); } }, true);
  document.addEventListener('pointerdown', e => { if (!pop.hidden && !pop.contains(e.target) && !e.target.closest('[data-session]')) close(); });
  return { open, close, get isOpen() { return !pop.hidden; } };
}

