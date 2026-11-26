/* =========================================================
   التنقّل في معرض سيف — أماكن القاعة 4 وشبكة ممراتها
   الخطوط تمشي في وسط كل ممر حقيقي على المخطط:
     · أربعة ممرات عرضية بين شرائح الأجنحة + ممر شمالي وآخر جنوبي.
     · ممر طولي بين كل شريطي أجنحة (2.5 م)، وممرّا الغرف (3 م).
     · ممرات الجمهور أمام المسرح: الأمامي والأوسط والجانبيان والعرضيان.
     · المداخل الأربعة عبر شريط الخدمات إلى الممر الخارجي والمداخل الرئيسية.
   ========================================================= */
import { ux, uz, HALL, BAND, CONCOURSE, SOUTH, SOUTH_ROOMS, ENTRANCES, EXITS, MAIN_DOORS, FOYERS, PUBLIC_ACCESS, SERVICES, STAGE, STAGE_ZONE, FOH,
  ROOMS, MEDIA, MEDIA_GAP, STRIPS, BANDS, ZONES, KIOSKS, PODS, OUTSIDE, FOOD_TRUCKS, EAST_BOOTHS, CAFES, booths, nameOf } from './sef-plan.js';
import { tr, EN } from '../i18n.js';

// خطوط الممرات (بالمتر)
const H_NORTH = 3.15, H_SOUTH = 66;
const LANES = [H_NORTH, 18.7, 33.7, 48.7, H_SOUTH];                    // حدود الشرائح الأربع (ممرات 3 م بينها)
// EAST_LANE: منتصف الفجوة بين آخر شريط (186–188) وواجهة بوثات الجدار الشرقي (191.5)
const WEST_LANE = 66.75, EAST_LANE = (188 + EAST_BOOTHS.x0) / 2;
// ممر طولي في منتصف كل فجوة بين شريطين، وعلى طرفي الأجنحة
// الممر العريض جنوب المركز الإعلامي (7 م) في وسطه كتل خضراء: خطّه على جانبها الشرقي
const MID_AISLE = 129.95;
const AISLES = [WEST_LANE, ...STRIPS.slice(1).map((x, i) => (STRIPS[i] + 2 + x) / 2), EAST_LANE]
  .map(x => PODS.some(p => p.z0 < HALL.d && x > p.x0 - .5 && x < p.x1 + .5) ? MID_AISLE : x);
// الشريحة الأولى: فجوة المركز الإعلامي بلا ممرات بين الأشرطة، ممرّان على جانبي الجناح الزجاجي
const inMedia = x => x > MEDIA_GAP.x0 && x < MEDIA_GAP.x1;
const MEDIA_SIDES = [(MEDIA_GAP.x0 + MEDIA.x0) / 2, (MEDIA.x1 + MEDIA_GAP.x1) / 2];
const ROOM_GAPS = [15.9, 23.75, 35.95, 50.6];                          // بين الغرف عرضيًا
const COL_A = 42.95, COL_B = 52;                                       // ممرّا الغرف طوليًا
const SEAT_X = [2.7, 21.6, 40.4], SEAT_Z = [13.4, 32.1, 48.1, H_SOUTH];
// الممر الخارجي: خطّه الرئيسي جنوب الكتل الخضراء، وخطّ شمالي يصل أبواب غرف الشريط
const IN_Z = 71.2, CON_Z = 83, CON_N = 76.6;
// عتبة باب غرف الشريط (شمال الممر) وغرف الصفّ الجنوبي
const DOOR_N = BAND.z1 - .8, DOOR_S = SOUTH.z0 + .8;
// خارج الجدار الشرقي: ممشى بين الجدار (191) وكاونترات الفود تراكس (194.6)، تصله أبواب الطوارئ الشرقية
const OUT_LANE = (OUTSIDE.x0 + FOOD_TRUCKS.counter[0]) / 2;
const TRUCK_MID = (([a, b]) => (a + b) / 2)(FOOD_TRUCKS.groups[1]);
const TRUCKS_NAME = tr('عربات الطعام', 'Food Trucks');

const ADMIN_ROOMS = ['judges', 'saif-team'];
const adminX = A => (Math.min(...A.map(r => r.x0)) + Math.max(...A.map(r => r.x1))) / 2;
const adminZ = A => (Math.min(...A.map(r => r.z0)) + Math.max(...A.map(r => r.z1))) / 2;
const ROOM_NAME = r => r.name ? nameOf(r) : tr('القاعة ', 'Room ') + r.id;
// اسم الجناح وحده: «جناح S-C3-12» · «Booth S-C3-12»
const BOOTH = code => tr('بوث ', 'Booth ') + code;
const ZONE = letter => tr('المنطقة ', 'Zone ') + letter;
// الخدمات في الإنجليزية: مكانها على الممر بدل اسمها الإنجليزي المكرّر
const SIDE = { band: 'Concourse · hall side', south: 'Concourse · outer side', concourse: 'Concourse', north: 'Hall · north wall' };

// باب الغرفة (منتصف جهة door) وأقرب نقطة له على ممرّه
function roomDoor(r) {
  const cx = (r.x0 + r.x1) / 2, cz = (r.z0 + r.z1) / 2;
  if (r.door === 'e') return { at: [r.x1, cz], lane: [WEST_LANE, cz] };
  if (r.door === 'w') return { at: [r.x0, cz], lane: [COL_A, cz] };
  return { at: [cx, r.z1], lane: [cx, Math.min(...[...ROOM_GAPS, H_SOUTH].filter(z => z > r.z1))] };
}

// here: معرّف شاشة الإرشاد التي تعمل عليها الصفحة (?kiosk=…) — يصير «موقعك الحالي»
export function sefNav(H, here) {
  const nodes = {}, edges = [];
  const key = (x, z) => x.toFixed(2) + ',' + z.toFixed(2);
  const node = (x, z) => { const k = key(x, z); if (!nodes[k]) nodes[k] = [ux(x), uz(z)]; return k; };
  // خطّ من نقاط متتالية؛ w عرض الممر بالوحدات (للرسم)
  const line = (pts, w) => pts.slice(1).forEach((p, i) => edges.push([node(...pts[i]), node(...p), w]));
  const span = (fixed, list, horizontal, w) => {
    const sorted = [...new Set(list)].sort((a, b) => a - b);
    line(sorted.map(v => horizontal ? [v, fixed] : [fixed, v]), w);
  };

  /* ---------- الأجنحة ---------- */
  LANES.forEach((z, li) => {
    const xs = AISLES.filter(x => !(li === 0 && inMedia(x))).concat(li < 2 ? MEDIA_SIDES : []);
    span(z, li === LANES.length - 1 ? [...xs, ...ENTRANCES.map(e => e.x)] : xs, true, li === 0 || li === 4 ? 30 : 46);
  });
  AISLES.forEach(x => LANES.slice(0, -1).forEach((z, b) => {
    if (b === 0 && inMedia(x)) return;
    line([[x, z], [x, LANES[b + 1]]], 26);
  }));
  MEDIA_SIDES.forEach(x => line([[x, LANES[0]], [x, LANES[1]]], 40));

  /* ---------- الغرف بين المسرح والأجنحة ---------- */
  span(COL_A, [...ROOM_GAPS, ...SEAT_Z, H_SOUTH], false, 30);
  // الممر الأوسط بين صفّي الغرف: بين الكراج (شمالًا) وطويق (جنوبًا) — كلاهما يعبره
  span(COL_B, ROOM_GAPS.slice(1), false, 30);
  ROOM_GAPS.forEach(z => line([[COL_A, z], [COL_B, z], [WEST_LANE, z]], z === ROOM_GAPS[0] ? 18 : 30));
  // باب كل غرفة إلى ممرّه
  ROOMS.forEach(r => { const d = roomDoor(r); line([d.at, d.lane], 20); });

  /* ---------- منطقة المسرح ---------- */
  SEAT_Z.forEach(z => span(z, [...SEAT_X, COL_A, ...(z === H_SOUTH ? [ENTRANCES[0].x] : [])], true, z === SEAT_Z[0] ? 34 : 22));
  SEAT_X.forEach(x => span(x, SEAT_Z, false, x === SEAT_X[1] ? 22 : 24));

  /* ---------- الجنوب: المداخل، شريط الخدمات، الممر الخارجي ---------- */
  span(H_SOUTH, [SEAT_X[2], COL_A, COL_B, WEST_LANE, ...ENTRANCES.map(e => e.x)], true, 30);
  ENTRANCES.forEach(e => line([[e.x, H_SOUTH], [e.x, IN_Z], [e.x, CON_Z]], 60));
  const bandXs = SERVICES.filter(v => v.side === 'band').map(v => v.x);
  span(CON_Z, [PUBLIC_ACCESS[0].x, FOYERS[0].x, ...ENTRANCES.map(e => e.x), ...MAIN_DOORS, ...SERVICES.filter(v => v.side !== 'band').map(v => v.x), FOYERS[1].x, PUBLIC_ACCESS[1].x], true, 60);
  // الخطّ الشمالي: بين غرف الشريط والكتل الخضراء، يلتقي بالرئيسي عند المداخل وطرفي الممر
  span(CON_N, [...bandXs, ...ENTRANCES.map(e => e.x)], true, 24);
  [Math.min(...bandXs), Math.max(...bandXs)].forEach(x => line([[x, CON_N], [x, CON_Z]], 24));
  // من الممر إلى باب كل غرفة: شمالًا لغرف الشريط، وجنوبًا لغرف الصفّ الجنوبي
  // وداخل القاعة شمالًا: من الممر الشمالي إلى الباب أو المكان عند الجدار
  SERVICES.forEach(v => v.side === 'band' ? line([[v.x, CON_N], [v.x, DOOR_N]], 24)
    : v.side === 'south' ? line([[v.x, CON_Z], [v.x, DOOR_S]], 24)
    : v.side === 'north' ? line([[v.x, H_NORTH], [v.x, v.z]], 20) : line([[v.x, CON_Z], [v.x, v.z]], 24));
  // الممرّات المفتوحة في الصفّ الجنوبي: إلى خارج المبنى
  MAIN_DOORS.forEach(x => line([[x, CON_Z], [x, SOUTH.z1 - .5]], 40));

  /* ---------- الفود تراكس: من الممر الشرقي عبر أبواب الطوارئ إلى الممشى الخارجي ---------- */
  EXITS.east.forEach(z => line([[EAST_LANE, z], [OUT_LANE, z]], 30));
  span(OUT_LANE, [...EXITS.east, ...FOOD_TRUCKS.groups.map(([a, b]) => (a + b) / 2)], false, 30);

  /* ---------- اللحام: كل عقدة تقع على ممر تقسمه، فتلتقي الخطوط حيث تتقاطع ---------- */
  (function weld() {
    const ids = Object.keys(nodes);
    for (let i = 0; i < edges.length; i++) {
      const [a, b, w] = edges[i], A = nodes[a], B = nodes[b];
      const dx = B[0] - A[0], dz = B[1] - A[1], L2 = dx * dx + dz * dz;
      let cut = null, best = 1;
      ids.forEach(k => {
        if (k === a || k === b) return;
        const P = nodes[k], t = ((P[0] - A[0]) * dx + (P[1] - A[1]) * dz) / L2;
        if (t <= .001 || t >= .999 || t >= best) return;
        const qx = A[0] + dx * t, qz = A[1] + dz * t;
        if (Math.hypot(P[0] - qx, P[1] - qz) < .05) { cut = k; best = t; }
      });
      if (cut) { edges[i] = [a, cut, w]; edges.push([cut, b, w]); i--; }
    }
  })();

  /* ---------- الأماكن ---------- */
  const fixed = [];
  const at = (x, z) => ({ x: ux(x), z: uz(z) });
  ENTRANCES.forEach(e => fixed.push({ id: 'entrance:' + e.n, kind: 'entrance', name: tr('مدخل المعرض ', 'Exhibition Entrance ') + e.n, sub: tr('من الممر الرئيسي', 'From the main concourse'),
    aliases: ['entrance ' + e.n, 'gate ' + e.n, 'بوابة ' + e.n, 'دخول ' + e.n, 'باب ' + e.n], node: node(e.x, IN_Z), ...at(e.x, IN_Z) }));
  SOUTH_ROOMS.filter(r => r.passage).forEach((r, i) => fixed.push({ id: 'door:' + i, kind: r.kind === 'vip' ? 'vip' : 'door', name: nameOf(r), sub: EN ? 'Building entrance' : r.en,
    aliases: ['main entrance', 'خارج', 'مخرج المبنى', 'مدخل الزوار', 'مدخل رئيسي'], node: node(MAIN_DOORS[i], SOUTH.z1 - .5), ...at(MAIN_DOORS[i], SOUTH.z1 - .5) }));
  FOYERS.forEach((f, i) => fixed.push({ id: 'foyer:' + i, kind: 'registration', name: f.name, sub: tr('بهو الاستقبال والتسجيل', 'Reception & registration foyer'),
    aliases: ['reception', 'تسجيل', 'استقبال'], node: node(f.x, CON_Z), ...at(f.x, CON_Z) }));
  PUBLIC_ACCESS.forEach((a, i) => fixed.push({ id: 'public:' + i, kind: 'door', name: a.name, sub: tr('دخول الجمهور إلى الممر الرئيسي', 'Public access to the main concourse'),
    aliases: ['public', 'main access', 'دخول', 'مدخل عام'], node: node(a.x, CON_Z), ...at(a.x, CON_Z) }));
  // كل غرفة بنوعها؛ الكلمات الدارجة تجد دورات المياه والمقهى والمطعم بأيّ صيغة
  const SAYS = { toilet: ['حمام', 'حمامات', 'دورة مياه', 'wc', 'toilet', 'restroom'], food: ['أكل', 'مطعم', 'كافيه', 'قهوة', 'coffee', 'cafe', 'food', 'restaurant', 'eat'],
    elevator: ['مصعد', 'اسانسير', 'lift', 'elevator'], stairs: ['درج', 'سلم', 'stairs'], firstaid: ['إسعاف', 'طبي', 'عيادة', 'clinic', 'first aid', 'medical'],
    info: ['استفسار', 'مساعدة', 'help', 'information', 'info'], registration: ['تسجيل', 'استقبال', 'بادج', 'badge', 'reception', 'registration'], office: ['إدارة', 'office'], shop: ['بقالة', 'shop', 'market'], prayer: ['مصلى', 'مصليات', 'صلاة', 'مسجد', 'prayer', 'mosque'], vip: ['vip', 'كبار الشخصيات'] };
  SERVICES.forEach(v => {
    const at0 = v.side === 'band' ? DOOR_N : v.side === 'south' ? DOOR_S : v.z;
    fixed.push({ id: 'svc:' + v.id, kind: v.kind, name: nameOf(v), sub: v.side === 'north' ? tr('شمال القاعة', 'Hall · north wall') : EN ? SIDE[v.side] : v.en,
      aliases: [v.en, v.name, ...(SAYS[v.kind] || []), ...(v.aliases || [])], node: node(v.x, at0), ...at(v.x, v.z) });
  });
  ZONES.forEach((z, i) => {
    const mine = H.tables.filter(t => t.zone === i), xs = mine.map(t => t.x);
    fixed.push({ id: 'zone:' + i, kind: 'zone', name: ZONE(z.letter), sub: mine.length + tr(' بوث · ', ' booths · ') + z.letter + '1–' + z.letter + z.cols,
      aliases: ['zone ' + z.letter, 'منطقه ' + z.letter, z.letter], x: z.wall ? Math.max(...xs) : (Math.min(...xs) + Math.max(...xs)) / 2, z: uz(LANES[2]),
      node: null });
  });
  KIOSKS.forEach(k => {
    fixed.push({ id: 'kiosk:' + k.id, kind: 'kiosk', name: k.name, sub: tr('شاشة إرشاد تفاعلية', 'Interactive info kiosk'),
      aliases: ['kiosk', 'شاشة', 'screen', k.id], ...at(k.x, k.z) });
    if (k.id === here) fixed.push({ id: 'here', kind: 'here', name: tr('موقعك الحالي', 'Your location'), sub: tr('عند ', 'At ') + k.name,
      aliases: ['انا هنا', 'هنا', 'موقعي', 'here', 'my location', 'you are here'], ...at(k.x, k.z) });
  });
  fixed.push({ id: 'stage', kind: 'stage', name: tr('منصة الإعلانات', 'Announcements Stage'), sub: tr('المسرح الرئيسي والشاشة', 'Main stage and screen'),
    aliases: ['المسرح', 'stage', 'announcement', 'الشاشة الرئيسية'], node: node(SEAT_X[1], SEAT_Z[0]), ...at(SEAT_X[1], SEAT_Z[0]) });
  fixed.push({ id: 'vvip', kind: 'vip', name: tr('مقاعد كبار الشخصيات', 'VIP Seating'), sub: tr('الصف الأول أمام المسرح', 'Front row facing the stage'),
    aliases: ['vvip', 'vip', 'كبار الزوار'], ...at(SEAT_X[1], 15.8) });
  fixed.push({ id: 'audience', kind: 'seats', name: tr('مقاعد الجمهور', 'Audience Seating'), sub: tr('أمام منصة الإعلانات', 'Facing the Announcements Stage'),
    aliases: ['الجمهور', 'كراسي', 'جلوس', 'seats', 'audience'], node: node(SEAT_X[1], SEAT_Z[1]), ...at(SEAT_X[1], SEAT_Z[1]) });
  fixed.push({ id: 'foh', kind: 'service', name: tr('غرفة التحكم', 'Control Room'), sub: 'FOH / VVIP Control Room',
    aliases: ['foh', 'control', 'تحكم', 'الصوت'], ...at((FOH.x0 + FOH.x1) / 2, (FOH.z0 + FOH.z1) / 2) });
  ROOMS.forEach(r => fixed.push({ id: 'room:' + r.id, kind: 'room', name: ROOM_NAME(r), sub: (EN ? null : r.en) || tr('قاعة ', 'Room · ') + Math.round((r.x1 - r.x0) * (r.z1 - r.z0)) + tr(' م²', ' m²'),
    aliases: [r.id, r.en || '', r.name, ...(r.aliases || [])], node: node(...roomDoor(r).at), ...at((r.x0 + r.x1) / 2, (r.z0 + r.z1) / 2) }));
  // مبنى الإدارة: استراحة المحكّمين وفريق سيف في مبنى واحد، بشارة واحدة — بابه باب فريق سيف جنوبًا
  const ADMIN = ROOMS.filter(r => ADMIN_ROOMS.includes(r.id)), adminDoor = roomDoor(ROOMS.find(r => r.id === 'saif-team')).at;
  fixed.push({ id: 'room:admin', kind: 'room', name: tr('سيف', 'SAIF'), sub: ADMIN.map(nameOf).join(' · '),
    aliases: ['سيف', 'saif', 'الإدارة', 'الاداره', 'مبنى الإدارة', 'admin', 'administration'], node: node(...adminDoor), ...at(adminX(ADMIN), adminZ(ADMIN)) });
  fixed.push({ id: 'media', kind: 'vip', name: MEDIA.name, sub: tr('Media Center & VIP Lounge', 'Glass pavilion, two floors'),
    aliases: ['media', 'الإعلام', 'المنطقة الإعلامية', 'كبار الزوار', 'vip lounge', 'صالة', 'مجلس'], node: node(MID_AISLE, LANES[1]), ...at((MEDIA.x0 + MEDIA.x1) / 2, (MEDIA.z0 + MEDIA.z1) / 2) });
  fixed.push({ id: 'trucks', kind: 'food', name: TRUCKS_NAME, sub: tr('خارج الجدار الشرقي · ' + FOOD_TRUCKS.groups.length * FOOD_TRUCKS.per + ' عربة', 'Outside the east wall · ' + FOOD_TRUCKS.groups.length * FOOD_TRUCKS.per + ' trucks'),
    aliases: ['فود ترك', 'فود تراك', 'فود تراكس', 'فودترك', 'عربات الطعام', 'عربة طعام', 'food truck', 'food trucks', 'trucks', ...SAYS.food], node: node(OUT_LANE, TRUCK_MID), ...at(FOOD_TRUCKS.body[0], TRUCK_MID) });
  EXITS.west.forEach((z, i) => fixed.push({ id: 'exit:w' + i, kind: 'exit', name: tr('مخرج الطوارئ غربًا ', 'West Emergency Exit ') + (i + 1), sub: tr('الجدار الغربي', 'West wall'),
    aliases: ['طوارئ', 'emergency', 'exit', 'مخرج'], ...at(HALL.x0, z) }));
  // بوابات الجدار الشرقي (مخطط الموقع 250) — إلى عربات الطعام خارجه
  EXITS.east.forEach((z, i) => fixed.push({ id: 'exit:e' + i, kind: 'exit', name: tr('البوابة الشرقية ', 'East Gate ') + (i + 1), sub: tr('الجدار الشرقي · إلى عربات الطعام', 'East wall · to the food trucks'),
    aliases: ['بوابة', 'بوابه', 'gate', 'طوارئ', 'emergency', 'exit', 'مخرج'], node: node(EAST_LANE, z), ...at(HALL.x0 + HALL.w, z) }));

    function places() {
    const list = fixed.slice();
    H.tables.forEach((t, i) => list.push({
      // اسم الفريق هو العنوان، والجناح ومنطقته تحته؛ الجناح بلا فريق يُعنون بكوده
      id: 'table:' + i, kind: 'booth', name: t.exhibitor || BOOTH(t.code),
      sub: (t.exhibitor ? BOOTH(t.code) + ' · ' : '') + ZONE(ZONES[t.zone].letter),
      // الكود يُبحث بصيغه كلها: S-C3-12 و C3-12 و C312 و «C3 12»
      code: t.code, n: i + 1, aliases: ['بوث ' + t.code, 'جناح ' + t.code, t.code, t.code.slice(2), t.code.slice(2).replace('-', ''), t.code.slice(2).replace('-', ' '),
        'booth ' + t.code.slice(2), 'بوث ' + t.code.slice(2), t.exhibitor || '', t.teamCode || '', t.track || '',
        t.leader || '', t.country || ''], x: t.x, z: t.z, table: i
    }));
    return list;
  }

  // الجناح مفتوح على ممرّه: العمود الشرقي على الممر شرق الشريط، والغربي غربه
  function approach(p, { project }) {
    if (p.kind !== 'booth') return null;
    const t = H.tables[p.table];
    // أقرب ممر طولي على جهة واجهته (الممر الشرقي الأخير أعرض من غيره)؛ بوثات الجدار الشرقي (K) على الممر الشرقي
    // بوثات الجدار الشمالي (K): على الممر الشمالي أمامها
    // بوثات الجدار (K): الطريق يدخل من الممر إلى داخل الـU وينتهي أمام طاولة الفريق نفسها —
    // دبّوس الوجهة على الجناح لا على الممر (الجانبية متعامدة مع الجدار: أمام طرفها)
    const off = ((t.r && t.wall === 'east') || (!t.r && t.wall === 'north') ? 1 : .55) * (ux(1) - ux(0));   // بالوحدات
    if (t.wall === 'north') {
      const gz = uz(H_NORTH), q = project({ x: t.x, z: gz }, (e, A, B) => Math.abs(A.z - gz) < 1 && Math.abs(B.z - gz) < 1);
      return q && q.d < 10 ? [{ at: q, tail: [], end: { x: t.x, z: t.z + off }, table: t }] : null;
    }
    if (t.wall === 'east') {
      const gx = ux(EAST_LANE), q = project({ x: gx, z: t.z }, (e, A, B) => Math.abs(A.x - gx) < 1 && Math.abs(B.x - gx) < 1);
      if (!q || q.d > 50) return null;
      // الصفّ الشمالي يتجاوز نهاية الممر الشرقي: يكمل على الممر نفسه حتى يحاذي الجناح ثم يدخل
      const tail = Math.abs(q.z - t.z) > 1 ? [{ x: q.x, z: t.z }] : [];
      return [{ at: q, tail, end: { x: t.x - off, z: t.z }, table: t }];
    }
    const ax = t.col === 'east' ? AISLES.find(x => x > t.sx + 2) : AISLES.filter(x => x < t.sx).pop();
    if (ax === undefined) return null;
    const gx = ux(ax);
    const q = project({ x: gx, z: t.z }, (e, A, B) => Math.abs(A.x - gx) < 1 && Math.abs(B.x - gx) < 1);
    if (!q || q.d > 4) return null;
    return [{ at: q, tail: [], end: { x: q.x, z: q.z }, table: t }];
  }

  // المعالم: أطراف كل شريط برقم جناحه، الغرف، المسرح، المداخل
  const landmarks = [];
  H.tables.forEach(t => {
    if (t.end) landmarks.push({ x: t.x, z: t.z + (t.end === 'north' ? -11 : 11), name: tr('البوث ', 'booth ') + t.code });
  });
  ROOMS.forEach(r => landmarks.push({ ...at((r.x0 + r.x1) / 2, r.z1), name: ROOM_NAME(r) }));
  const media = tr('المركز الإعلامي', 'the Media Center');
  landmarks.push({ ...at(MEDIA.x0, MEDIA.z1), name: media }, { ...at(MEDIA.x1, MEDIA.z1), name: media });
  landmarks.push({ ...at(SEAT_X[1], SEAT_Z[0]), name: tr('منصة الإعلانات', 'the Announcements Stage') });
  landmarks.push({ ...at(OUT_LANE, TRUCK_MID), name: TRUCKS_NAME });
  ENTRANCES.forEach(e => landmarks.push({ ...at(e.x, H_SOUTH), name: tr('مدخل المعرض ', 'Exhibition Entrance ') + e.n }));

  return { places, nodes, edges, approach, landmarks, landmarkReach: 40 };
}

// ما يُكتب على الخريطة: أسماء المناطق وحدها، والضغط عليها يجعلها وجهتك
export const LABELS = [
  { place: 'media', name: tr('المركز الإعلامي', 'Media Center'), x: ux((MEDIA.x0 + MEDIA.x1) / 2), z: uz(MEDIA.z0) },
  // شارة كل منطقة فوق أعمدتها عند الطرف الشمالي، حيث تُعلّق لوحتها
  ...ZONES.map((z, i) => {
    const xs = booths().filter(b => b.zone === i).map(b => b.x);
    // K على جدارين: شارتها عند الجدار الشرقي (بدايتها) لا في منتصف القاعة
    return { place: 'zone:' + i, name: ZONE(z.letter), short: z.letter, x: ux(z.wall ? Math.max(...xs) : (Math.min(...xs) + Math.max(...xs)) / 2), z: uz(BANDS[0]) };
  }),
  { place: 'svc:dunkin', name: tr('المقاهي', 'Cafés'), x: ux((CAFES.x0 + CAFES.x1) / 2), z: uz(-4) },
  { place: 'trucks', name: TRUCKS_NAME, x: ux((FOOD_TRUCKS.body[0] + FOOD_TRUCKS.body[1]) / 2), z: uz(TRUCK_MID) },
  ...ENTRANCES.map(e => ({ place: 'entrance:' + e.n, name: tr('مدخل ', 'Entrance ') + e.n, x: ux(e.x), z: uz(HALL.d) })),
  // الممر الخارجي: الاستقبال ودورات المياه والطعام والإسعاف
  ...[['reception-w', 'الاستقبال', 'Reception'], ['reception-e', 'الاستقبال', 'Reception'], ['firstaid', 'الإسعاف', 'First Aid'],
    ['info', 'الاستعلامات', 'Information'], ['wc-w', 'دورات مياه النساء', "Women's Restrooms"], ['wc-m', 'دورات مياه الرجال', "Men's Restrooms"],
    ['cafe', 'المقهى', 'Café'], ['restaurant', 'المطعم', 'Restaurant'],
    // شمال القاعة: المصلّيان ودورات المياه خلف الجدار، والمقاهي
    ['prayer-m', 'مصلى الرجال', "Men's Prayer"], ['prayer-w', 'مصلى النساء', "Women's Prayer"],
    ['wc-n1', 'دورات مياه الرجال', "Men's Restrooms"], ['wc-n2', 'دورات مياه النساء', "Women's Restrooms"],
    ['wc-n3', 'دورات مياه الرجال', "Men's Restrooms"], ['wc-n4', 'دورات مياه الرجال', "Men's Restrooms"]]
    .map(([id, ar, en]) => tr([id, ar], [id, en])).map(([id, name]) => { const v = SERVICES.find(s => s.id === id); return { place: 'svc:' + id, name, x: ux(v.x), z: uz(v.z) }; }),
  // الغرف بين المسرح والأجنحة: اسم كل جهة فوق غرفتها — آخر القائمة، فتظهر كلها حين يكفي التقريب
  // مبنى الإدارة بشارة واحدة بدل شارتَي غرفتيه
  ...(A => [{ place: 'room:admin', name: tr('سيف', 'SAIF'), x: ux(adminX(A)), z: uz(adminZ(A)) }])(ROOMS.filter(r => ADMIN_ROOMS.includes(r.id))),
  ...ROOMS.filter(r => !ADMIN_ROOMS.includes(r.id)).map(r => ({ place: 'room:' + r.id, name: nameOf(r), x: ux((r.x0 + r.x1) / 2), z: uz((r.z0 + r.z1) / 2) }))
];
export { STAGE_ZONE, BANDS };
