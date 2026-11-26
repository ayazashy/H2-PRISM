/* =========================================================
   موقع معرض سيف — القاعة 4
   المقاسات من آخر مخطط للموقع (sef-plan.js)، والشكل مبسّط على
   طابع المحرّك المحايد: جدران بيضاء، أرضيات رمادية فاتحة، حواف مستديرة.
     · غرب القاعة: منصة الإعلانات وشاشتها، صفّا كبار الشخصيات، ومقاعد الجمهور.
     · وسطها: استراحة المحكّمين وفريق سيف، وقاعات الجهات (الكراج، موهبة، علم، تحكم، وزارة التعليم، طويق).
     · شرقها: 1200 جناح في أربع شرائح، والمركز الإعلامي في وسط الأولى.
     · جنوبها: المداخل الأربعة عبر شريط الخدمات إلى الممر الخارجي.
   ========================================================= */
import { U, ux, uz, HALL, COLUMNS, BAND, CONCOURSE, SOUTH, BAND_ROOMS, SOUTH_ROOMS, AIRLOCKS, ATM, ENTRANCES, ENTRANCE_W, EXITS, FOYERS, CHECKPOINTS,
  STAGE, STAGE_ZONE, VVIP, SEATS, FOH, ROOMS, MEDIA, STRIPS, BANDS, ZONES, KIOSKS, PODS, AREAS, OUTSIDE, FOOD_TRUCKS, stripSkipped, booths, areaOf, nameOf,
  NORTH, CAFES, SCREENS, WALL_BOOTHS, PRAYERS, NORTH_WC, NORTH_ROOMS, EAST_GATES, EAST_BOOTHS } from './sef-plan.js';
import { sefNav, LABELS } from './sef-nav.js';
import { teamOf } from './sef-teams.js';
import { tr } from '../i18n.js';

const WALL_H = 9 * U, CUT_H = 1.4 * U, ROOM_H = 2.6 * U, STAGE_H = 1.2 * U;
const m = v => v * U;                                   // طول بالمتر ← وحدات
const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

// الأجنحة بترتيب أرقامها: موضعها في المشهد، وشريحتها، وعمودها، وطرف الشريط
const BOOTHS = booths();

export default {
  id: 'sef',
  label: tr('موقع معرض سيف ثلاثي الأبعاد: القاعة 4 بالمسرح والقاعات و1200 بوث والمداخل', 'SAIF exhibition in 3D: Hall 4 with the stage, rooms, 1,200 booths and entrances'),
  center: [ux(HALL.x0 + HALL.w / 2), uz(HALL.d / 2 + 4)],
  extent: [m(HALL.w + 8), m(HALL.d - HALL.z0 + 18)],
  perspectiveScale: 1.02,
  polar: .8,
  bounds: [ux(CONCOURSE.x0), uz(NORTH_WC.z0 - 2), ux(CONCOURSE.x1), uz(SOUTH.z1 + 4)],
  sun: [-400, 3200, 1400],
  shadow: [m(HALL.w / 2 + 12), m(HALL.d / 2 + 20)],
  minDistance: 20,
  shadowMap: 1024,
  maxDpr: 1.25,
  moveDpr: .9,
  anchorLift: 10,
  // الجناح صغير (1 × 2 م): هامش الالتقاط وحلقة الإبراز بمقاسه
  pick: [m(.5), m(1)],
  ring: m(1.25),
  labels: LABELS,
  // زر «أجندة المعرض» معلّق فوق المنصّة الدائرية في مقدّمة المسرح
  agendaAnchor: [ux((STAGE.x0 + STAGE.x1) / 2), m(4.5), uz(STAGE.z1 + 1)],
  // المسرح على المخطط [x0, z0, x1, z1] — المنصّة ومقدّمتها الدائرية: الضغط عليه يفتح الأجندة كزرّها
  stageRect: (() => { const xs = [ux(STAGE.x0), ux(STAGE.x1)], zs = [uz(STAGE.z0), uz(STAGE.z1 + 4)];
    return [Math.min(...xs), Math.min(...zs), Math.max(...xs), Math.max(...zs)]; })(),
  // بطاقة الأجندة في الجوال (?agenda): نظرة جانبية على المسرح ومقدّمة المقاعد
  // (من الجنوب الشرقي، مرتفعة قليلًا)
  stageView: {
    target: [ux((STAGE.x0 + STAGE.x1) / 2 + 2), m(2.5), uz(STAGE.z1 + 4)],
    position: [ux((STAGE.x0 + STAGE.x1) / 2 + 24), m(15), uz(STAGE.z1 + 30)]
  },
  // التنقّل: من أين يبدأ من لم يحدّد مكانه، وما يُقترح قبل الكتابة
  start: 'entrance:1',
  suggest: ['entrance:1', 'entrance:2', 'entrance:3', 'entrance:4', 'stage', 'media', 'svc:reception-e', 'svc:info', 'svc:wc-w', 'svc:wc-m', 'svc:cafe'],
  hint: tr('اكتب كود بوث (مثل C3-12) أو اسم فريق أو منطقة أو خدمة — أو اضغط على بوث في الخريطة',
    'Type a team name or ID, a booth code (like C3-12), a zone or a service — or tap a booth on the map'),
  // باك اند تحكيم (api/tahkeem.js): الفرق على طاولاتها والأجندة المنشورة، من نقطتين عامّتين.
  // space: معرّف المساحة · event: معرّف الفعالية (UUID فقط). وحتى يُملآ تبقى الفرق والأجندة التجريبية
  // (للتجربة: ?space=…&event=… في الرابط)
  api: { base: 'https://tahkeem-api.tuwaiq.edu.sa', space: 'a8ae6cb4-a14d-491f-b025-aec137800758', event: '3b95c0f8-a0bb-4726-848a-a6f4b2ce5883' },
  // بيانات الخريطة: الأجنحة كـ«طاولات» يلتقطها المحرّك ويبحث فيها التنقّل
  data(tables) {
    return {
      tables: tables.map((t, i) => {
        const f = teamOf(BOOTHS[i].n);
        // exhibitor: اسم الفريق — يظهر في التلميح ويُبحث به، والدولة والقائد في بطاقة الجناح
        return { ...t, ...BOOTHS[i], x: t.x, z: t.z, code: BOOTHS[i].code, team: null,
          exhibitor: f && f.team, teamCode: f && f.code, track: f && f.track, country: f && f.country, flag: f && f.flag, leader: f && f.leader };
      }),
      zones: ZONES.map((z, i) => ({ id: i, letter: z.letter, name: tr('المنطقة ', 'Zone ') + z.letter }))
    };
  },
  // شاشة الإرشاد التي تعمل عليها الصفحة — تُضبط من الرابط قبل بناء المشهد (map.js)
  here: null,
  kiosks: KIOSKS.map(k => ({ ...k, x: ux(k.x), z: uz(k.z) })),
  nav(H) { return sefNav(H, this.here); },

  build(k) {
    const here = this.here;
    const { THREE, add, rgeo, block, instanced, canvasTexture, screenTexture, glow, mat, tone, frame, mainScreen, toneHex } = k;
    const wall = mat(93), cap = mat(96), low = mat(91);
    const R = (x0, z0, x1, z1) => [ux(x0), uz(z0), m(x1 - x0), m(z1 - z0)];

    /* ---------- الأرضيات ---------- */
    const HX0 = HALL.x0, HX1 = HALL.x0 + HALL.w;
    block(...R(HX0, HALL.z0, HX1, HALL.d), 0, .8, mat(95), .4, false);
    block(...R(STAGE_ZONE.x0, STAGE_ZONE.z0, STAGE_ZONE.x1, STAGE_ZONE.z1), .8, .3, mat(92), .2, false);       // سجّاد المسرح
    block(...R(CONCOURSE.x0, BAND.z0, CONCOURSE.x1, SOUTH.z1), 0, .8, mat(96), .4, false);
    block(...R(OUTSIDE.x0, HALL.z0 - .9, OUTSIDE.x1, BAND.z0), 0, .8, mat(94), .4, false);                  // ساحة الفود تراكس شرقًا

    /* ---------- الجدران: عالية شمالًا وغربًا وشرقًا، ومقطوعة جنوبًا لترى الكاميرا الداخل ---------- */
    const wallSeg = (x0, z0, x1, z1, h, material = wall) => {
      block(x0, z0, x1 - x0, z1 - z0, 0, h, material, 1.2);
      block(x0 - .5, z0 - .5, x1 - x0 + 1, z1 - z0 + 1, h, 2, cap, .8, false);
    };
    wallSeg(ux(HX0 - .9), uz(HALL.z0 - .9), ux(HX1 + .9), uz(HALL.z0), WALL_H);
    // الأعمدة الإنشائية الكبيرة على الجدار الشمالي (كل 12 م، بارزة 5.7 م)
    COLUMNS.xs.forEach(x => block(...R(x - COLUMNS.w / 2, COLUMNS.z0, x + COLUMNS.w / 2, COLUMNS.z1), 0, WALL_H, wall, 1.2));
    // الجداران الجانبيان بفتحات أبواب الطوارئ (الغربي زجاجي بغرف عزل)
    [['west', HX0 - .9, HX0], ['east', HX1, HX1 + .9]].forEach(([side, a, b]) => {
      let z = HALL.z0 - .9;
      EXITS[side].forEach(ez => { wallSeg(ux(a), uz(z), ux(b), uz(ez - 1), WALL_H); z = ez + 1; });
      wallSeg(ux(a), uz(z), ux(b), uz(HALL.d + .3), WALL_H);
    });
    // الجنوبي: فتحات المداخل الأربعة
    const west2east = ENTRANCES.slice().sort((p, q) => p.x - q.x);
    let cursor = HX0 - .9;
    west2east.forEach(e => {
      wallSeg(ux(cursor), uz(HALL.d - .3), ux(e.x - ENTRANCE_W / 2), uz(HALL.d + .3), CUT_H);
      cursor = e.x + ENTRANCE_W / 2;
    });
    wallSeg(ux(cursor), uz(HALL.d - .3), ux(HX1 + .9), uz(HALL.d + .3), CUT_H);

    /* ---------- بوابات المداخل: إطار بلافتة رقمه، يُرى من الممر ومن داخل القاعة ---------- */
    const font = getComputedStyle(document.body).fontFamily;
    // الخط بأكبر مقاس يسعه عرض اللافتة (النص الإنجليزي أطول)
    const fitText = (g, text, size, max) => {
      g.font = '700 ' + size + 'px ' + font;
      const wd = g.measureText(text).width;
      if (wd > max) g.font = '700 ' + Math.floor(size * max / wd) + 'px ' + font;
    };
    const sign = text => glow(canvasTexture(512, 160, (g, w, h) => {
      g.fillStyle = css('--brand'); g.fillRect(0, 0, w, h);
      g.fillStyle = toneHex(100); g.textAlign = 'center'; g.textBaseline = 'middle';
      fitText(g, text, 64, w * .9); g.fillText(text, w / 2, h / 2 + 4);
    }));
    // البوابة كما في العرض: إطار عنابي بحافة ذهبية داخلية، بارتفاع ~6 م
    const brand = name => new THREE.MeshStandardMaterial({ color: css(name), roughness: .8, metalness: 0 });
    const gateMat = brand('--sef-maroon'), gold = brand('--sef-gold');
    ENTRANCES.forEach(e => {
      const x0 = ux(e.x - ENTRANCE_W / 2), x1 = ux(e.x + ENTRANCE_W / 2), z = uz(HALL.d + 2.5), h = m(5);
      block(x0 - 14, z - 8, 14, 16, 0, h, gateMat, 2);
      block(x1, z - 8, 14, 16, 0, h, gateMat, 2);
      block(x0 - 14, z - 8, x1 - x0 + 28, 16, h, 14, gateMat, 2);
      // الحافة الذهبية داخل الفتحة ملاصقة للعمود لا داخله — وجهان في موضع واحد يومضان (z-fighting)
      block(x0 + .1, z - 9, 1.6, 18, 0, h - .1, gold, .6); block(x1 - 1.7, z - 9, 1.6, 18, 0, h - .1, gold, .6);
      const face = sign(tr('مدخل ', 'Entrance ') + e.n), board = new THREE.Mesh(rgeo(m(5), m(1.4), 2, .8), [frame, frame, frame, frame, face, face]);
      board.position.set((x0 + x1) / 2, h + 7, z); add(board);
    });

    /* ---------- منصة الإعلانات — كما في ريندر المسرح (العرض الفني، صفحات 27–30) ----------
       منصّة خضراء داكنة بحواف ذهبية وثلاث درجات بعرضها كله، منصّة دائرية برتقالية بطبقتين
       تبرز نحو الجمهور، شاشة رئيسية عريضة خلفها جدار أخضر بأعلى متدرّج، وشاشتان جانبيتان
       مائلتان نحو الوسط بإطار مربعات بألوان سيف. */
    const backdrop = brand('--sef-green'), orange = brand('--sef-orange');
    const scx = ux((STAGE.x0 + STAGE.x1) / 2), cxm = (STAGE.x0 + STAGE.x1) / 2;
    // حافة ذهبية رفيعة على وجه كل درجة — سطحها أخفض من سطح الدرجة، فلا سطحان في موضع واحد
    const nose = (z, top) => block(...R(STAGE.x0, z - .06, STAGE.x1, z + .04), top - 1, .8, gold, .2, false);
    block(...R(STAGE.x0, STAGE.z0, STAGE.x1, STAGE.z1), 0, STAGE_H, backdrop, 1.2);
    nose(STAGE.z1, STAGE_H);
    [3 / 4, 1 / 2, 1 / 4].forEach((k, i) => {
      const z0 = STAGE.z1 + i * .5, z1 = z0 + .5;
      block(...R(STAGE.x0, z0, STAGE.x1, z1), 0, STAGE_H * k, backdrop, .5);
      nose(z1, STAGE_H * k);
    });
    // المنصّة الدائرية: طبقة سفلى عريضة بين الدرجات، وعليا أعلى من سطح المنصّة قليلًا
    [[2.9, STAGE_H * .62], [2.1, STAGE_H + 2]].forEach(([r, h]) => {
      const disc = new THREE.Mesh(new THREE.CylinderGeometry(m(r), m(r), h, 64), orange);
      disc.position.set(scx, h / 2, uz(STAGE.z1)); add(disc);
      const rim = new THREE.Mesh(new THREE.TorusGeometry(m(r), .45, 6, 64), gold);
      rim.rotation.x = Math.PI / 2; rim.position.set(scx, h - .2, uz(STAGE.z1)); add(rim, false);
    });
    // المنبر على يسار المنصّة
    block(...R(STAGE.x0 + 3.5, STAGE.z1 - 2.4, STAGE.x0 + 4.3, STAGE.z1 - 1.8), STAGE_H, m(1.15), orange, 1);

    // الشاشة الرئيسية وجدارها الأخضر بأعلى متدرّج كأفق المدينة
    const sw = m(20), sh = m(6.5);
    mainScreen({ x: scx, z: uz(STAGE.z0) + 2, w: sw, h: sh, y: STAGE_H + m(1.2), depth: 4, r: 1.2, idle: screenTexture([tr('سيف', 'SAIF'), tr('منصة الإعلانات', 'Announcements Stage')]) });
    const wallTop = STAGE_H + m(1.2) + sh + 6;
    block(ux(STAGE.x0), uz(STAGE.z0) - 4, m(STAGE.x1 - STAGE.x0), 4, 0, wallTop, backdrop, 1);
    [[.0, .14, 1.6], [.14, .3, .8], [.7, .86, .8], [.86, 1, 1.6]].forEach(([a, b, up]) =>
      block(ux(STAGE.x0 + (STAGE.x1 - STAGE.x0) * a), uz(STAGE.z0) - 4, m((STAGE.x1 - STAGE.x0) * (b - a)), 4, wallTop, m(up), backdrop, 1));
    block(ux(STAGE.x0), uz(STAGE.z0) - 1.2, m(STAGE.x1 - STAGE.x0), 1.4, wallTop - 1.4, 1.4, gold, .3, false);

    // الشاشتان الجانبيتان: على طرفي المنصّة (بعرض منطقة المسرح كلها)، مائلتان نحو الوسط، وعلى حافتهما الخارجية مربعات سيف
    const side = glow(screenTexture([tr('سيف', 'SAIF')]));
    const pixel = ['--sef-maroon', '--sef-teal', '--sef-orange', '--sef-coral'].map(brand);
    [[STAGE.x0 + 4, .38, -1], [STAGE.x1 - 4, -.38, 1]].forEach(([x, rot, out]) => {
      const g = new THREE.Group();
      const scr = new THREE.Mesh(rgeo(m(6.4), m(4.2), 3, .8), [frame, frame, frame, frame, side, frame]);
      scr.position.y = m(1.2) + m(2.1);
      g.add(scr);
      for (let k = 0; k < 4; k++) {
        const cube = new THREE.Mesh(rgeo(m(1), m(1.05), m(.4), .4), pixel[k]);
        cube.position.set(out * m(3.55), m(1.2) + m(.55) + k * m(1.05), 0);
        g.add(cube);
      }
      const leg = new THREE.Mesh(rgeo(m(1.2), m(1.2), m(.4), .4), backdrop);
      leg.position.y = m(.6); g.add(leg);
      g.position.set(ux(x), STAGE_H, uz(STAGE.z0 + 3.2)); g.rotation.y = rot;          // قائمتان على المنصّة نفسها
      g.traverse(o => { o.castShadow = true; o.receiveShadow = true; });
      add(g);
    });

    /* ---------- الجلوس: صفّا كبار الشخصيات (أرائك)، ثم مقاعد الجمهور بممرّين عرضيين ---------- */
    const sofas = [], chairs = [], backs = [];
    SEATS.blocks.forEach(([a, b]) => {
      for (let x = a + .9; x < b - .8; x += 2.1) [VVIP.z0 + .7, VVIP.z1 - .8].forEach(z => sofas.push([ux(x), m(.25), uz(z)]));
      for (let x = a + .45; x < b; x += SEATS.dx) for (let z = SEATS.z0 + .4; z < SEATS.z1; z += SEATS.dz) {
        if (SEATS.cross.some(([c0, c1]) => z > c0 - .3 && z < c1 + .3)) continue;
        chairs.push([ux(x), m(.23), uz(z)]); backs.push([ux(x), m(.5), uz(z + .26)]);
      }
    });
    instanced(rgeo(m(1.9), m(.5), m(.85), 1.5), mat(84), sofas);
    instanced(new THREE.BoxGeometry(m(.5), m(.46), m(.5)), mat(82), chairs, false);
    instanced(new THREE.BoxGeometry(m(.52), m(.55), m(.08)), mat(80), backs, false);
    block(...R(FOH.x0, FOH.z0, FOH.x1, FOH.z1), 0, m(1.1), mat(86), 1.5);                                 // غرفة التحكم

    /* ---------- سياج الجمهور وبواباته: حاجز أخضر منخفض بحافة ذهبية حول المقاعد،
       وأقواس متدرّجة خضراء عند مداخل الممرّات (ريندر المسرح، صفحة 30) ---------- */
    const fence = (x0, z0, x1, z1) => {
      block(...R(x0, z0, x1, z1), 0, m(1.1), backdrop, .6);
      block(...R(x0, z0, x1, z1), m(1.1), 1, gold, .3, false);
    };
    const EAST = STAGE_ZONE.x1 - .3, FENCE_S = 63.4, GAP = 1.6;
    // شرقًا: فتحات عند الممرّات العرضية (الأمامي والوسطيان)؛ جنوبًا: عند الممر الأوسط
    [[14.4, 32.1 - GAP], [32.1 + GAP, 48.1 - GAP], [48.1 + GAP, FENCE_S]].forEach(([a, b]) => fence(EAST - .25, a, EAST, b));
    [[3.8, 21.6 - GAP], [21.6 + GAP, 39.2]].forEach(([a, b]) => fence(a, FENCE_S - .25, b, FENCE_S));
    const arch = (c, at, axis) => {
      const open = GAP * 2, ph = 3.4, pw = .6, d = .6;
      const piece = (u0, u1, y0, h, material) => axis === 'x'
        ? block(...R(c + u0, at - d / 2, c + u1, at + d / 2), m(y0), m(h), material, .8)
        : block(...R(at - d / 2, c + u0, at + d / 2, c + u1), m(y0), m(h), material, .8);
      piece(-open / 2 - pw, -open / 2, 0, ph, backdrop); piece(open / 2, open / 2 + pw, 0, ph, backdrop);
      piece(-open / 2 - pw, open / 2 + pw, ph, .7, backdrop);
      piece(-1.1, .4, ph + .7, .7, backdrop);                         // درجة الأفق فوق القوس
      piece(-.35, .35, ph + 1.4, .7, gold);                           // المكعّب الذهبي
    };
    [32.1, 48.1].forEach(z => arch(z, EAST - .12, 'z'));
    arch(21.6, FENCE_S - .12, 'x');

    /* ---------- الغرف: جدران بباب على الممر، وأرضية أفتح، وسقف مسطّح يغطّيها ---------- */
    const roomWall = mat(97), roomFloor = mat(98), roomRoof = mat(100);
    const room = (x0, z0, x1, z1, door) => {
      block(...R(x0, z0, x1, z1), .8, .3, roomFloor, .3, false);
      const t = .15, sides = { n: [x0, z0, x1, z0 + t], s: [x0, z1 - t, x1, z1], w: [x0, z0, x0 + t, z1], e: [x1 - t, z0, x1, z1] };
      Object.entries(sides).forEach(([key, [a, b, c, d]]) => {
        if (key !== door) { block(...R(a, b, c, d), 0, ROOM_H, roomWall, .6); return; }
        const horizontal = key === 'n' || key === 's', mid = horizontal ? (a + c) / 2 : (b + d) / 2, gap = 1.1;
        if (horizontal) { block(...R(a, b, mid - gap, d), 0, ROOM_H, roomWall, .6); block(...R(mid + gap, b, c, d), 0, ROOM_H, roomWall, .6); }
        else { block(...R(a, b, c, mid - gap), 0, ROOM_H, roomWall, .6); block(...R(a, mid + gap, c, d), 0, ROOM_H, roomWall, .6); }
      });
      // السقف فوق الجدران مباشرة، أعرض منها قليلًا فيغطّي حوافها — الغرفة كتلة واحدة من الأعلى
      block(...R(x0 - .1, z0 - .1, x1 + .1, z1 + .1), ROOM_H, m(.18), roomRoof, .5);
    };
    // باب كل غرفة على الممر الذي يصلها (door في المخطط)
    ROOMS.forEach(r => room(r.x0, r.z0, r.x1, r.z1, r.door));
    // غرفتان متلاصقتان (المقهى ووزارة التعليم، المحكّمين وفريق سيف): سقفاهما يلتقيان،
    // فيُرسم الجدار المشترك خطًّا أغمق فوقهما — يُقرأان غرفتين من الأعلى
    const seam = mat(88);
    ROOMS.forEach(r => ROOMS.forEach(q => {
      const a = Math.max(r.x0, q.x0), b = Math.min(r.x1, q.x1);
      if (r !== q && Math.abs(r.z1 - q.z0) < .05 && b - a > 1) block(...R(a, r.z1 - .12, b, r.z1 + .12), ROOM_H, m(.18) + 1.2, seam, .2, false);
    }));
    // الكتل الخضراء في المخطط (بلا اسم): كتلة خضراء داكنة منخفضة كما رُسمت
    PODS.forEach(p => block(...R(p.x0, p.z0, p.x1, p.z1), 0, m(1.2), backdrop, .8));
    /* ---------- الفود تراكس خارج الجدار الشرقي: كاونتر طولي يواجه الجدار، وخلفه 4 عربات ----------
       العربة: صندوق أبيض بنافذة بيع غربًا تحت مظلّة ذهبية، وقمرة القيادة شرقًا */
    const truckBody = mat(99), truckCab = mat(88), counterMat = mat(90), awning = brand('--sef-gold');
    const [c0, c1] = FOOD_TRUCKS.counter, [t0, t1] = FOOD_TRUCKS.body, CAB = 1.1;
    FOOD_TRUCKS.groups.forEach(([z0, z1]) => {
      block(...R(c0, z0, c1, z1), 0, m(1.05), counterMat, .5);
      const slot = (z1 - z0) / FOOD_TRUCKS.per;
      for (let i = 0; i < FOOD_TRUCKS.per; i++) {
        const a = z0 + i * slot + .15, b = z0 + (i + 1) * slot - .15;
        block(...R(t0, a, t1 - CAB, b), m(.25), m(2.3), truckBody, 1);
        block(...R(t1 - CAB, a + .1, t1, b - .1), m(.25), m(1.6), truckCab, 1);
        block(...R(t0 - .45, a + .1, t0, b - .1), m(2.05), m(.12), awning, .3);
      }
    });
    /* ---------- شمال القاعة وشرقها (ملاحظات «مخطط الموقع 250») ---------- */
    // بوثات الجدار (بلا ظهر) بنفس بنية البوث العادي: طاولته (0.55 × 1.6 م) وفاصله الأبيض (عمق جناح ~0.95 م، ارتفاع 1.8 م)،
    // وفوقها شريط الواجهة بلون منطقتها كباقي الأجنحة (رمادي في خريطة المشرف كالأجنحة قبل الحضور)
    // مرتّبة على شكل نصف مستطيل كما في الموقع — طاولة على كل طرف متعامدة مع الجدار، والبقية في الوسط
    // along: 'x' على الجدار الشمالي (الواجهة جنوبًا)، 'z' على الشرقي (الواجهة غربًا)
    // فسحة بين الجدار والطاولة يقف فيها أصحاب البوث؛ عمق الـU كله U_DEPTH
    const counters = [], boothDividers = [], U_DEPTH = 2.1, DESK = 1.25;
    // منطقة الصفّ: منطقة أقرب جناح إليه
    const zoneNear = x => BOOTHS.filter(b => !b.wall).reduce((p, b) => Math.abs(b.x - x) < Math.abs(p.x - x) ? b : p).zone;
    // teams: صفوف المنطقة K — طاولاتها طاولات فرق (تُلتقط وتُلوَّن، أدناه)، وفي خريطة المشرف لكل جناح شريطه
    const wallRow = (a0, a1, per, along, back, front, teams = false) => {
      const dir = Math.sign(front - back);
      const zone = zoneNear(along === 'x' ? (a0 + a1) / 2 : back);
      const face = document.body.classList.contains('is-admin') ? mat(88) : brand('--sef-area-' + areaOf(zone));
      // شريط الواجهة على شكل الـU كله: على الجدار، ويمتد على الطرفين فوق الطاولتين الجانبيتين
      const bar = (u0, u1, d0, d1) => {
        const [z0, z1] = [back + dir * d0, back + dir * d1].sort((p, q) => p - q);
        if (along === 'x') block(...R(u0, z0, u1, z1), m(2.65) - m(.225), m(.45), face, .6, false);
        else block(...R(z0, u0, z1, u1), m(2.65) - m(.225), m(.45), face, .6, false);
      };
      if (!(teams && document.body.classList.contains('is-admin'))) {
        bar(a0 + .1, a1 - .1, 0, .4);
        [[a0 + .1, a0 + .5], [a1 - .5, a1 - .1]].forEach(([u0, u1]) => bar(u0, u1, .4, U_DEPTH));
      }
      // turn: 0 = الطاولة/الفاصل بطوله على الجدار، π/2 = متعامد معه
      const P = (a, d, y, turn) => along === 'x' ? [ux(a), y, uz(back + dir * d), turn] : [ux(back + dir * d), y, uz(a), turn + Math.PI / 2];
      const mid = per - 2, i0 = a0 + .65, i1 = a1 - .65, step = (i1 - i0) / mid;
      if (!teams) {
        for (let i = 0; i < mid; i++) counters.push(P(i0 + (i + .5) * step, DESK, m(.45), Math.PI / 2));
        [a0 + .3, a1 - .3].forEach(a => counters.push(P(a, U_DEPTH - .8, m(.45), 0)));
      }
      for (let i = 0; i <= mid; i++) boothDividers.push(P(i0 + i * step, (DESK + .275) / 2, m(.9), Math.PI / 2));
    };
    WALL_BOOTHS.forEach(b => wallRow(b.x0, b.x1, b.per, 'x', NORTH.z0, NORTH.z0 + 2, true));
    // المنطقة K: طاولات الجدار أجنحة فرق في الخريطتين (sef-plan.js)
    EAST_BOOTHS.blocks.forEach(([z0, z1]) => wallRow(z0, z1, EAST_BOOTHS.per, 'z', EAST_BOOTHS.x1, EAST_BOOTHS.x0, true));
    // نفس مقاسات البوث العادي (طاولة الفريق وفاصل الأجنحة أدناه)
    instanced(rgeo(m(.55), m(.9), m(1.6), 1.2, 1), mat(100), counters);
    instanced(new THREE.BoxGeometry(m(DESK + .275), m(1.8), m(.06)), mat(96), boothDividers, false);

    // البوابات الشرقية: دهليز مسقوف بين الجدار والممر عند كل باب
    EXITS.east.forEach(z => {
      const { x0, x1, half } = EAST_GATES;
      [z - half, z + half - .2].forEach(a => block(...R(x0, a, x1, a + .2), 0, ROOM_H, roomWall, .6));
      block(...R(x0 - .1, z - half - .1, x1, z + half + .1), ROOM_H, m(.18), roomRoof, .5);
      block(...R(x0 - .1, z - half, x0 + .25, z + half), ROOM_H - m(.5), m(.5), gateMat, .4);      // عتبة عنابية على الواجهة
    });

    // الشاشات: شاشة LED عريضة على هيكل أسود بقائمتين وقاعدتين، تواجه القاعة
    // وجه الشاشة: صورة الرعاية المعروضة عليها في الموقع (assets/img/saif-patronage.jpg، 5:3)،
    // وحتى تُحمَّل لون عنابي بلون خلفيتها
    const rig = brand('--sef-screen-rig'), patronage = new Image();
    const ledTex = canvasTexture(1600, 960, (g, w, h) => {
      if (patronage.complete && patronage.naturalWidth) g.drawImage(patronage, 0, 0, w, h);
      else { g.fillStyle = css('--sef-maroon'); g.fillRect(0, 0, w, h); }
    });
    patronage.onload = () => { ledTex.userData.repaint(); if (this.redraw) this.redraw(); };
    patronage.src = 'assets/img/saif-patronage.jpg';
    const led = glow(ledTex);
    SCREENS.forEach(({ x, w, h, y }) => {
      const zf = NORTH.z1 - 1.4;
      [x - w / 2 - .25, x + w / 2 + .25].forEach(lx => {
        block(...R(lx - .3, zf - .2, lx + .3, zf + .4), 0, m(y + h + .2), rig, .4);              // القائمة الأمامية
        block(...R(lx - .3, zf - 2.2, lx + .3, zf - 1.6), 0, m(y + h - .6), rig, .4);            // الخلفية
        block(...R(lx - .4, zf - 2.3, lx + .4, zf + .6), 0, m(.5), rig, .4);                    // القاعدة
        block(...R(lx - .25, zf - 2.2, lx + .25, zf + .2), m(y + h - .9), m(.4), rig, .3);       // الوصلة العلوية
      });
      block(...R(x - w / 2 - .55, zf - .1, x + w / 2 + .55, zf + .3), m(y + h), m(.3), rig, .3);  // العارضة
      const scr = new THREE.Mesh(rgeo(m(w), m(h), m(.3), .6), [rig, rig, rig, rig, led, rig]);
      scr.position.set(ux(x), m(y + h / 2), uz(zf + .25)); add(scr);
    });

    /* ---------- المقاهي الثلاث بين عمودين، كما في صور الموقع ----------
       (من الغرب للشرق) MAPS · دانكن على الجدار · BREW92، وثلاجة مياه ورفّ وجبات أمام كل عمود */
    const cafeSign = (text, bg, ink, wd = 512) => glow(canvasTexture(wd, 128, (g, w, h) => {
      g.fillStyle = css(bg); g.fillRect(0, 0, w, h);
      g.fillStyle = css(ink); g.textAlign = 'center'; g.textBaseline = 'middle';
      fitText(g, text, 76, w * .8); g.fillText(text, w / 2, h / 2 + 3);
    }));
    // صندوق بلافتة على وجه أو أكثر: faces = { s: جنوبًا (+z)، w: غربًا (-x) }
    const signed = (x0, z0, x1, z1, y0, h, body, faces, r = .4) => {
      const mats = [body, faces.w || body, body, body, faces.s || body, body];
      const mesh = new THREE.Mesh(rgeo(m(x1 - x0), m(h), m(z1 - z0), r), mats);
      mesh.position.set(ux((x0 + x1) / 2), m(y0 + h / 2), uz((z0 + z1) / 2)); return add(mesh);
    };
    const pole = (x, z, y0, h, material, w = .07) => block(...R(x - w, z - w, x + w, z + w), m(y0), m(h), material, .05, false);
    const steel = mat(88), cafeWhite = mat(100);

    // MAPS: كاونتر أزرق بحواف مستديرة (2.4 × 0.8 م) بشعاره، وقطعة جانبية متعامدة على يمينه،
    // ومظلّة زرقاء بطوله على قائمتين رفيعتين من وسط الكاونتر
    const mapsBlue = brand('--sef-cafe-maps');
    const mapsFace = cafeSign('MAPS', '--sef-cafe-maps', '--venue-100');
    signed(72.6, -4.4, 75, -3.6, 0, 1, mapsBlue, { s: mapsFace }, 1.6);
    signed(75.05, -5.5, 75.8, -3.6, 0, 1, mapsBlue, { s: mapsFace }, 1.2);
    [73.4, 74.2].forEach(x => pole(x, -4.05, 1, 1.25, mapsBlue, .04));
    signed(72.55, -4.45, 75.05, -3.55, 2.25, .38, mapsBlue, { s: mapsFace }, 1.4);

    // دانكن على الجدار: خزانة عرض زجاجية بقاعدة وغطاء خشبيين يسارًا، كاونتر بشرائح خشبية وسطحه داكن،
    // وامتداد أقصر يمينًا؛ ولافتة بنّية بإطار خشبي على قائمتين معدنيتين خلف الكاونتر
    const wood = brand('--sef-cafe-dunkin'), brown = brand('--sef-cafe-dunkin-sign');
    const dunkinFace = cafeSign('DUNKIN’ دانكن', '--sef-cafe-dunkin-sign', '--sef-cafe-dunkin-ink', 1024);
    block(...R(75.95, -6, 76.85, -5.3), 0, m(.45), wood, .3);
    block(...R(76, -5.95, 76.8, -5.35), m(.45), m(1.15), new THREE.MeshStandardMaterial({ color: tone(96), roughness: .2, transparent: true, opacity: .5 }), .2, false);
    block(...R(75.95, -6, 76.85, -5.3), m(1.6), m(.4), wood, .3);
    block(...R(76.95, -5.8, 78.95, -5.1), 0, m(.98), wood, .3);
    block(...R(78.95, -5.8, 79.6, -5.1), 0, m(.92), wood, .3);
    block(...R(76.9, -5.85, 79.65, -5.05), m(.98), m(.05), brown, .1, false);           // السطح الداكن
    [77.15, 78.75].forEach(x => pole(x, -5.7, 0, 2.25, steel));
    block(...R(76.75, -5.95, 79.15, -5.6), m(2.25), m(.6), wood, .3);                  // الإطار الخشبي
    signed(76.85, -5.62, 79.05, -5.58, 2.31, .48, brown, { s: dunkinFace }, .02);

    // BREW92: هيكل أزرق على شكل L — واجهة على الممر (2.2 م) وجانب غربي يرجع إلى الجدار —
    // كاونتر بلوحات زرقاء داكنة وسطح أبيض، وقوائم رفيعة تحمل لوحات بيضاء بإطار أزرق حول أعلاه
    const brewBlue = brand('--sef-cafe-brew'), brewPanel = brand('--sef-cafe-brew-panel');
    const brewFace = cafeSign('BREW92°', '--sef-cafe-brew-panel', '--venue-100'), brewBoard = cafeSign('BREW92°', '--venue-100', '--sef-cafe-brew');
    const BX0 = 79.85, BX1 = 82, BZ0 = -6.6, BZ1 = -3.3, T = .6;
    signed(BX0, BZ1 - T, BX1, BZ1, 0, .95, brewPanel, { s: brewFace }, .1);            // الواجهة
    signed(BX0, BZ0, BX0 + T, BZ1 - T, 0, .95, brewPanel, { w: brewFace }, .1);         // الجانب
    block(...R(BX0 - .03, BZ1 - T - .03, BX1 + .03, BZ1 + .03), m(.95), m(.05), cafeWhite, .05, false);
    block(...R(BX0 - .03, BZ0, BX0 + T + .03, BZ1 - T), m(.95), m(.05), cafeWhite, .05, false);
    [[BX0, BZ1], [BX1, BZ1], [(BX0 + BX1) / 2, BZ1], [BX0, BZ0], [BX0, (BZ0 + BZ1) / 2], [BX0 + T, BZ1 - T], [BX1, BZ1 - T], [BX0 + T, BZ0]]
      .forEach(([x, z]) => pole(x, z, 0, 2.5, brewBlue, .05));
    signed(BX0, BZ1 - .1, BX1, BZ1 + .02, 2.1, .4, brewBlue, { s: brewBoard }, .02);    // اللوحات العليا
    signed(BX0 - .02, BZ0, BX0 + .1, BZ1, 2.1, .4, brewBlue, { w: brewBoard }, .02);
    block(...R(BX0, BZ0, BX1, BZ0 + .1), m(2.1), m(.4), brewBlue, .02, false);
    block(...R(BX1 - .1, BZ0, BX1, BZ1), m(2.1), m(.4), brewBlue, .02, false);

    // ثلاجة مياه بيضاء ورفّ وجبات خفيفة أبيض أمام كل عمود من عمودي الخانة
    const fridge = mat(97), glassDoor = new THREE.MeshStandardMaterial({ color: tone(96), roughness: .25, emissive: tone(100), emissiveIntensity: .25 });
    [[CAFES.x0 - 2, 1], [CAFES.x1 + .2, 1]].forEach(([x]) => {
      signed(x, -1.1, x + .65, -.45, 0, 1.95, fridge, { s: glassDoor }, .3);
      block(...R(x + .8, -1.05, x + 1.45, -.65), 0, m(1.75), cafeWhite, .2);
    });

    // مصلى الرجال: مساحة مفتوحة على الأرض بفرشها، والأيقونة عليها؛ مصلى النساء: غرفة مسقوفة بأيقونتها
    const prayerFloor = mat(100);   // بلون أرضية الأيقونة: تُقرأ مرسومة على الفرش
    PRAYERS.forEach(p => {
      if (p.closed) { room(p.x0, NORTH.z0, p.x1, NORTH.z1, 's'); return; }
      block(...R(p.x0, NORTH.z0 + .2, p.x1, NORTH.z1), .8, .4, prayerFloor, .3, false);
    });
    // دورات المياه خلف الجدار الشمالي، وأبوابها على القاعة
    NORTH_ROOMS.forEach(r => {
      room(r.x0 + .1, NORTH_WC.z0, r.x1 - .1, NORTH_WC.z1, 's');
      block(...R(r.door - .8, HALL.z0 - .08, r.door + .8, HALL.z0 + .05), 0, m(2.4), mat(84), .2, false);
    });

    // المركز الإعلامي: جناح زجاجي بطابقين، شريط واجهة أخضر، وسطح علوي مفتوح بدرج جانبي
    const glass = new THREE.MeshStandardMaterial({ color: tone(100), roughness: .2, metalness: 0, transparent: true, opacity: .55 });
    block(...R(MEDIA.x0, MEDIA.z0, MEDIA.x1, MEDIA.z1), 0, m(4.2), glass, 1.5);
    block(...R(MEDIA.x0 - .2, MEDIA.z0 - .2, MEDIA.x1 + .2, MEDIA.z1 + .2), m(4.2), m(.6), backdrop, 1);
    block(...R(MEDIA.x0 + 1, MEDIA.z0 + 1, MEDIA.x1 - 1, MEDIA.z1 - 1), m(4.8), m(.9), glass, 1);
    block(...R(MEDIA.x1 + .2, MEDIA.z0 + 2, MEDIA.x1 + 1.4, MEDIA.z1 - 1), 0, m(2.4), mat(90), 1);

    /* ---------- الأجنحة: جدار فاصل في وسط كل شريط، وكاونتر لكل جناح على ممرّه ---------- */
    const spines = [], dividers = [], fascias = Object.fromEntries(AREAS.map(a => [a.id, []]));
    BANDS.forEach((z0, band) => STRIPS.forEach(sx => {
      if (stripSkipped(band, sx)) return;
      spines.push([ux(sx + 1), m(1.25), uz(z0 + 6)]);
      for (let r = 1; r < 6; r++) dividers.push([ux(sx + 1), m(.9), uz(z0 + r * 2)]);
    }));
    // على خطّ الجدار الخلفي (لا فوق الأجنحة نفسها): يبقى كل جناح ظاهرًا من الأعلى
    const fasciaX = b => ux(b.wall ? EAST_BOOTHS.x1 - .25 : b.col === 'east' ? b.sx + 1.2 : b.sx + .8);
    const ADMIN = document.body.classList.contains('is-admin');
    instanced(rgeo(m(.12), m(2.5), m(12), .4, 1), mat(97), spines);
    let strip = null;
    // خريطة المشرف: حركات ناعمة بإطارات متتالية (حضور فريق) — redraw يضبطه map.js
    const tweens = new Set();
    const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    const still = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
    const tick = now => {
      tweens.forEach(tw => {
        if (tw.t0 === null) tw.t0 = now;
        const k = Math.min(1, (now - tw.t0) / tw.ms);
        tw.step(ease(k), k);
        if (k === 1) { tweens.delete(tw); if (tw.done) tw.done(); }
      });
      if (this.redraw) this.redraw();
      if (tweens.size) requestAnimationFrame(tick);
    };
    const tween = (ms, step, done) => {
      if (still()) { step(1, 1); if (done) done(); if (this.redraw) this.redraw(); return null; }
      const tw = { t0: null, ms, step, done };
      if (!tweens.size) requestAnimationFrame(tick);
      tweens.add(tw);
      return tw;
    };
    /* ---------- خريطة المشرف: شخصية لو بولي تمشي بين الأجنحة ----------
       ثوب أبيض، شماغ أبيض وعقال أسود، لحية سوداء، وسمّاعة رأس بمايك — أوجه مسطّحة (flatShading) بأضلاع قليلة.
       تمشي حلقة ثابتة على الممرات (بداية وعودة لنفس النقطة) بدورة مشي: خطوات القدمين تحت الثوب، تأرجح الذراعين، وارتفاع الجسم */
    const walker = () => {
      const low = (name, extra) => new THREE.MeshStandardMaterial(Object.assign({ color: css(name), roughness: .9, flatShading: true }, extra));
      const white = new THREE.MeshStandardMaterial({ color: tone(100), roughness: .9, flatShading: true });
      const shemagh = new THREE.MeshStandardMaterial({ color: tone(98), roughness: .95, flatShading: true, side: THREE.DoubleSide });
      const skin = low('--sef-skin'), hair = low('--sef-beard'), black = low('--sef-screen-rig');
      const fig = new THREE.Group(), body = new THREE.Group();
      const put = (geo, material, x, y, z, parent = body) => { const o = new THREE.Mesh(geo, material); o.position.set(m(x), m(y), m(z)); o.castShadow = true; parent.add(o); return o; };
      // الثوب: مخروط مقطوع بثمانية أضلاع، كتفان، وياقة
      put(new THREE.CylinderGeometry(m(.2), m(.26), m(1.2), 8), white, 0, .68, 0);
      put(new THREE.CylinderGeometry(m(.13), m(.2), m(.12), 8), white, 0, 1.34, 0);
      put(new THREE.CylinderGeometry(m(.065), m(.07), m(.06), 6), white, 0, 1.42, 0);
      put(new THREE.BoxGeometry(m(.06), m(.08), m(.012)), black, .09, 1.16, .2).rotation.y = .3;               // بطاقة الاسم
      // القدمان: حذاء أسود يخطو تحت الذيل
      const feet = [-1, 1].map(side => put(new THREE.BoxGeometry(m(.09), m(.06), m(.2)), black, .075 * side, .03, .03, fig));
      // الرأس والوجه
      put(new THREE.CylinderGeometry(m(.05), m(.055), m(.08), 6), skin, 0, 1.48, 0);
      const head = put(new THREE.IcosahedronGeometry(m(.1), 1), skin, 0, 1.6, 0); head.scale.set(.92, 1.1, .98);
      [-.033, .033].forEach(x => put(new THREE.BoxGeometry(m(.022), m(.012), m(.01)), hair, x, 1.63, .092));    // العينان
      [-.034, .034].forEach(x => put(new THREE.BoxGeometry(m(.04), m(.01), m(.01)), hair, x, 1.655, .094));     // الحاجبان
      put(new THREE.ConeGeometry(m(.016), m(.04), 4), skin, 0, 1.6, .1).rotation.x = Math.PI / 2.3;              // الأنف
      // اللحية السوداء: كتلة لو بولي على الفك والذقن، وشارب
      const beard = put(new THREE.DodecahedronGeometry(m(.095), 0), hair, 0, 1.53, .035); beard.scale.set(1, .95, .8);
      [-1, 1].forEach(sd => { const c = put(new THREE.BoxGeometry(m(.03), m(.09), m(.07)), hair, .082 * sd, 1.575, .02); c.rotation.y = .3 * sd; });   // السوالف
      put(new THREE.BoxGeometry(m(.065), m(.016), m(.014)), hair, 0, 1.578, .1);
      // الشماغ الأبيض: غطاء على الرأس، إطار حول الوجه مفتوح من الأمام، وذيل على الظهر
      put(new THREE.CylinderGeometry(m(.105), m(.118), m(.1), 8), shemagh, 0, 1.69, -.005);
      put(new THREE.ConeGeometry(m(.105), m(.05), 8), shemagh, 0, 1.765, -.005);
      put(new THREE.CylinderGeometry(m(.118), m(.2), m(.28), 8, 1, true, .9, Math.PI * 2 - 1.8), shemagh, 0, 1.52, -.01);
      put(new THREE.CylinderGeometry(m(.2), m(.24), m(.45), 8, 1, true, Math.PI * .65, Math.PI * .7), shemagh, 0, 1.17, -.012);
      // العقال: حلقتان سوداوان بأضلاع قليلة
      [[1.705, .112], [1.735, .106]].forEach(([y, r]) => put(new THREE.TorusGeometry(m(r), m(.016), 5, 12), black, 0, y, -.006).rotation.x = Math.PI / 2);
      // السمّاعة: قطعة على الأذن اليمنى وذراع مايك نحو الفم
      put(new THREE.BoxGeometry(m(.025), m(.04), m(.03)), black, -.096, 1.6, .02);
      const boom = put(new THREE.CylinderGeometry(m(.006), m(.006), m(.12), 4), black, -.07, 1.565, .07);
      boom.rotation.set(Math.PI / 2, 0, -.5); boom.rotation.order = 'YXZ'; boom.rotation.y = -.55;
      put(new THREE.IcosahedronGeometry(m(.014), 0), black, -.03, 1.555, .11);
      // الذراعان: كمّ أبيض بستة أضلاع ويد
      const arms = [-1, 1].map(side => {
        const g = new THREE.Group(); g.position.set(m(.215 * side), m(1.32), 0);
        put(new THREE.CylinderGeometry(m(.05), m(.058), m(.58), 6), white, 0, -.3, 0, g);
        put(new THREE.IcosahedronGeometry(m(.042), 0), skin, 0, -.63, 0, g);
        g.rotation.z = side * .08; body.add(g); return g;
      });
      fig.add(body); fig.scale.setScalar(1.8); add(fig, false);   // أكبر من الحقيقي قليلًا ليُرى من نظرة القاعة

      // الحلقة: مستطيل على الممرات بين الأشرطة — يبدأ وينتهي عند النقطة نفسها (بالمتر)
      const LOOP = [[139.6, 48.7], [139.6, 18.7], [93.75, 18.7], [93.75, 48.7]];
      const legs = LOOP.map((p, i) => { const q = LOOP[(i + 1) % LOOP.length]; return { p, q, len: Math.hypot(q[0] - p[0], q[1] - p[1]) }; });
      const TOTAL = legs.reduce((a, l) => a + l.len, 0), SPEED = 1.25;   // م/ث
      let dist = 0, last = performance.now(), heading = Math.atan2(legs[0].q[0] - legs[0].p[0], legs[0].q[1] - legs[0].p[1]);
      const frame = now => {
        const dt = Math.min(.1, (now - last) / 1000); last = now;
        if (!document.hidden) {
          dist = (dist + dt * SPEED) % TOTAL;
          let d = dist, leg = legs[0];
          for (const l of legs) { if (d <= l.len) { leg = l; break; } d -= l.len; }
          const k = d / leg.len, x = leg.p[0] + (leg.q[0] - leg.p[0]) * k, z = leg.p[1] + (leg.q[1] - leg.p[1]) * k;
          const want = Math.atan2(leg.q[0] - leg.p[0], leg.q[1] - leg.p[1]);
          let turn = want - heading; turn = Math.atan2(Math.sin(turn), Math.cos(turn)); heading += turn * Math.min(1, dt * 6);   // التفاتة ناعمة عند الزوايا
          fig.position.set(ux(x), 0, uz(z)); fig.rotation.y = heading;
          // دورة المشي: خطوة كل ~0.55 م
          const ph = dist / .55 * Math.PI, sw = Math.sin(ph);
          feet[0].position.z = m(.03 + .11 * sw); feet[1].position.z = m(.03 - .11 * sw);
          feet[0].position.y = m(.03 + Math.max(0, Math.cos(ph)) * .02); feet[1].position.y = m(.03 + Math.max(0, -Math.cos(ph)) * .02);
          arms[0].rotation.x = -sw * .5; arms[1].rotation.x = sw * .5;
          body.position.y = Math.abs(Math.cos(ph)) * m(.022);
          body.rotation.y = sw * .04;   // لفّة خفيفة للكتفين مع الخطوة
          if (this.redraw) this.redraw();
        }
        requestAnimationFrame(frame);
      };
      requestAnimationFrame(frame);
    };
    const stripAt = BOOTHS.map(b => b.wall === 'north' ? [ux(b.x), m(2.65), uz(NORTH.z0 + .25), Math.PI / 2] : [fasciaX(b), m(2.65), uz(b.z), 0]);
    strip = instanced(rgeo(m(.4), m(.45), m(1.9), .6, 1), mat(100), stripAt, false);
    const areaColors = Object.fromEntries(AREAS.map(a => [a.id, new THREE.Color(css('--sef-area-' + a.id))]));
    const neutralFascia = tone(88);
    const stripObj = new THREE.Object3D();
    BOOTHS.forEach((b, i) => strip.setColorAt(i, areaColors[b.area || areaOf(b.zone)]));
    strip.instanceColor.needsUpdate = true;

    this.paintChecklist = (payload, venue) => {
      if (!payload) return;
      const { records = {}, evalById, prefs = {}, ui = {}, boothToProjects, colorForBooth } = payload;
      const myTable = (prefs.myBooth || '').toUpperCase();
      const hideUnmatched = !!ui.hideFilteredOnMap;
      const hideIgnored = !!ui.hideIgnoredOnMap;
      const mode = ui.mapColor || 'status';
      const tableColors = new Array(BOOTHS.length);
      const col = new THREE.Color();

      for (let i = 0; i < BOOTHS.length; i++) {
        const b = BOOTHS[i];
        const projs = boothToProjects ? boothToProjects.get(b.code) || [] : [];
        let anyMatches = false, allIgnored = projs.length > 0;
        let anyFav = false, anyVis = false, maxRat = 0, maxScore = 0;
        for (let j = 0; j < projs.length; j++) {
          const p = projs[j];
          const r = records[p.id] || {};
          const ev = evalById ? evalById.get(p.id) : null;
          if (!ev || ev.matches) anyMatches = true;
          if (!ev || !ev.isIgnored) allIgnored = false;
          if (r.fav) anyFav = true;
          if (r.vis) anyVis = true;
          if ((r.rat || 0) > maxRat) maxRat = r.rat || 0;
          const sc = ev ? ev.matchScore : (p._score || 0);
          if (sc > maxScore) maxScore = sc;
        }
        const isMe = b.code === myTable;
        const hidden = !isMe && ((allIgnored && hideIgnored) || (!anyMatches && projs.length > 0 && hideUnmatched));
        const dimmed = !isMe && projs.length > 0 && (!anyMatches || allIgnored);

        let hexFascia = null, hexTable = null, lift = 0, grow = 1;
        if (isMe) {
          hexFascia = '#d946ef'; hexTable = '#d946ef'; lift = m(0.32); grow = 1.75;
        } else if (hidden || dimmed) {
          hexFascia = '#d8d8de'; hexTable = '#e6e6ec'; lift = 0; grow = 0.8;
        } else if (mode === 'status') {
          if (anyFav && anyVis) { hexFascia = '#0d9488'; hexTable = '#14b8a6'; lift = m(0.28); grow = 1.65; }
          else if (anyFav) { hexFascia = '#d97706'; hexTable = '#f59e0b'; lift = m(0.28); grow = 1.65; }
          else if (anyVis) { hexFascia = '#059669'; hexTable = '#10b981'; lift = m(0.24); grow = 1.5; }
          else if (maxRat > 0) { hexFascia = '#7c3aed'; hexTable = '#8b5cf6'; lift = m(0.20); grow = 1.45; }
          else if (maxScore >= 65) { hexFascia = '#0284c7'; hexTable = '#38bdf8'; lift = m(0.08); grow = 1.15; }
        } else if (colorForBooth) {
          const customHex = colorForBooth(projs, records, mode);
          if (customHex) { hexFascia = customHex; hexTable = customHex; }
          if (anyFav || anyVis || maxRat > 0) { lift = m(0.24); grow = 1.5; }
        }

        if (hexFascia) col.set(hexFascia);
        else col.copy(areaColors[b.area || areaOf(b.zone)] || neutralFascia);
        strip.setColorAt(i, col);

        stripObj.position.set(stripAt[i][0], stripAt[i][1] + lift, stripAt[i][2]);
        stripObj.rotation.set(0, stripAt[i][3], 0);
        stripObj.scale.set(1, grow, 1);
        stripObj.updateMatrix();
        strip.setMatrixAt(i, stripObj.matrix);

        tableColors[i] = hexTable;
      }

      strip.instanceColor.needsUpdate = true;
      strip.instanceMatrix.needsUpdate = true;
      if (venue && venue.tables && venue.tables.paint) venue.tables.paint(tableColors, false);
      if (venue && venue.invalidate) venue.invalidate();
    };
    instanced(new THREE.BoxGeometry(m(1.9), m(1.8), m(.06)), mat(96), dividers, false);
    k.teamTables(rgeo(m(.55), m(.9), m(1.6), 1.2, 1),
      // المنطقة K: طاولات الجدار الشرقي في مواضعها من الـU (الجانبية مدارة)
      BOOTHS.map(b => b.wall ? { x: ux(b.x), y: m(.45), z: uz(b.z), r: b.r }
        : { x: ux(b.col === 'east' ? b.sx + 1.6 : b.sx + .4), y: m(.45), z: uz(b.z) }));

    /* ---------- شاشات الإرشاد: عمود قائم بوجه شاشة، والتي أنت عندها بوجه بنفسجي ---------- */
    const kioskBody = mat(97), kioskFace = mat(84), hereFace = new THREE.MeshStandardMaterial({ color: css('--brand'), roughness: .5, emissive: css('--brand'), emissiveIntensity: .35 });
    KIOSKS.forEach(kk => {
      const g = new THREE.Group();
      const body = new THREE.Mesh(rgeo(m(.9), m(1.9), m(.28), 1.2), kioskBody);
      body.position.y = m(.95); body.castShadow = true;
      const face = new THREE.Mesh(rgeo(m(.75), m(1.15), m(.04), .6), kk.id === here ? hereFace : kioskFace);
      face.position.set(0, m(1.25), m(.16));
      g.add(body, face);
      g.position.set(ux(kk.x), 0, uz(kk.z)); g.rotation.y = kk.face;
      add(g);
    });

    /* ---------- الممر الخارجي كما في المخطط ----------
       شريط الخدمات شمالًا (غرف بين خانات المداخل، بابها على الممر)، والصفّ الجنوبي
       (دورات المياه والمقهى والمطعم والدرج والمصاعد والمكاتب) بممرّاته المفتوحة إلى خارج المبنى */
    // الاستقبال ليس غرفة مسقوفة: جناح مفتوح على الممر كما في الريندر (يُبنى أدناه)
    BAND_ROOMS.filter(r => r.kind !== 'registration').forEach(r => room(r.x0 + .15, BAND.z0 + .4, r.x1 - .15, BAND.z1, 's'));
    SOUTH_ROOMS.filter(r => !r.passage).forEach(r => room(r.x0 + .15, SOUTH.z0, r.x1 - .15, SOUTH.z1 - .3, 'n'));
    /* ---------- أيقونات السقف: كل غرفة في الممر برمزها ----------
       مسطّحة بروح رموز آبل (أشكال مصمتة بحواف مستديرة وشقوق رفيعة)، بلون فاتح قريب من السقف،
       بمقاس واحد للجميع. الأيقونة جزء من السقف: تكبر وتصغر وتدور معه.
       تُرسم على أرضية معتمة بلون السقف (لا شفافية: الحواف الشفافة تظهر كحدّ داكن)، والشقّ بلونه أيضًا */
    const ROOF = toneHex(100), INK = toneHex(93);
    const glyph = draw => canvasTexture(512, 512, (g, w, h) => {
      g.fillStyle = ROOF; g.fillRect(0, 0, w, h);
      g.save(); g.scale(w / 24, h / 24); g.fillStyle = INK;
      const fill = shape => { g.beginPath(); shape(); g.fill(); };
      const cut = shape => { g.fillStyle = ROOF; fill(shape); g.fillStyle = INK; };
      const pill = (x, y, w, h) => g.roundRect(x, y, w, h, Math.min(w, h) / 2);
      const poly = pts => { g.moveTo(...pts[0]); pts.slice(1).forEach(p => g.lineTo(...p)); g.closePath(); };
      draw({ g, fill, cut, pill, poly });
      g.restore();
    });
    // شخص: رأس، وجذع بذراعين تفصلهما شقوق، وساقان — أو فستان
    const person = ({ g, fill, cut, poly }, cx, female) => {
      fill(() => g.arc(cx, 3.5, 2.25, 0, Math.PI * 2));
      if (!female) {
        fill(() => g.roundRect(cx - 4.1, 6.7, 8.2, 7.6, [3.2, 3.2, 1.1, 1.1]));
        cut(() => g.roundRect(cx - 2.85, 9.3, .5, 6, .25)); cut(() => g.roundRect(cx + 2.35, 9.3, .5, 6, .25));
        fill(() => g.roundRect(cx - 2.35, 13.5, 4.7, 9.6, [0, 0, 1.2, 1.2]));
        cut(() => g.roundRect(cx - .24, 16.1, .48, 8, .24));
        return;
      }
      fill(() => g.roundRect(cx - 3.9, 6.7, 7.8, 6.4, [3.1, 3.1, 1.05, 1.05]));
      cut(() => g.roundRect(cx - 2.75, 9.3, .5, 5, .25)); cut(() => g.roundRect(cx + 2.25, 9.3, .5, 5, .25));
      fill(() => {
        g.moveTo(cx - 2.25, 12.1); g.lineTo(cx + 2.25, 12.1); g.lineTo(cx + 4.05, 16.5);
        g.quadraticCurveTo(cx + 4.4, 17.4, cx + 3.4, 17.4); g.lineTo(cx - 3.4, 17.4);
        g.quadraticCurveTo(cx - 4.4, 17.4, cx - 4.05, 16.5); g.closePath();
      });
      fill(() => g.roundRect(cx - 1.95, 16.9, 3.9, 6.2, [0, 0, 1.05, 1.05]));
      cut(() => g.roundRect(cx - .24, 18.3, .48, 6, .24));
    };
    const ICONS = {
      toilet: k => { person(k, 6.6, false); person(k, 17.4, true); },
      'toilet-f': k => person(k, 12, true),
      'toilet-m': k => person(k, 12, false),
      // فنجان على صحن، وثلاثة خيوط بخار
      cafe: ({ g, fill, cut, pill }) => {
        fill(() => g.arc(17.6, 12.4, 3, 0, Math.PI * 2)); cut(() => g.arc(17.6, 12.4, 1.6, 0, Math.PI * 2));
        fill(() => { g.moveTo(4.2, 8.6); g.lineTo(18.2, 8.6); g.lineTo(17, 15.8); g.quadraticCurveTo(16.4, 18.6, 13.4, 18.6);
          g.lineTo(9, 18.6); g.quadraticCurveTo(6, 18.6, 5.4, 15.8); g.closePath(); });
        fill(() => pill(2.4, 19.6, 17.6, 1.8));
        [7.6, 11.2, 14.8].forEach(x => fill(() => pill(x - .55, 2.4, 1.1, 4.4)));
      },
      // شوكة وسكين
      food: ({ g, fill, pill }) => {
        [5.4, 7.4, 9.4].forEach(x => fill(() => pill(x - .5, 1.8, 1, 6.8)));
        fill(() => g.roundRect(4.9, 7.4, 5, 3.2, [0, 0, 2.2, 2.2]));
        fill(() => pill(6.5, 9.4, 1.8, 13));
        fill(() => { g.moveTo(15.6, 1.8); g.quadraticCurveTo(19.4, 3.4, 19.4, 10); g.lineTo(19.4, 13.4); g.lineTo(15.6, 13.4); g.closePath(); });
        fill(() => pill(15.6, 11.6, 2.2, 10.8));
      },
      // مسجد: قبّة بهلال، مئذنتان، وباب مقوّس
      prayer: ({ g, fill, cut, pill, poly }) => {
        fill(() => g.arc(12, 12.4, 5.4, Math.PI, 0)); fill(() => g.rect(6.6, 12.2, 10.8, 8.4));
        fill(() => pill(11.55, 5.4, .9, 2.2));
        fill(() => g.arc(12, 3.6, 1.9, 0, Math.PI * 2)); cut(() => g.arc(12.85, 3.1, 1.55, 0, Math.PI * 2));
        [[2.4, 4.6], [19.4, 21.6]].forEach(([a, b]) => { fill(() => g.rect(a, 8.6, b - a, 12)); fill(() => poly([[a, 8.8], [(a + b) / 2, 5.2], [b, 8.8]])); });
        fill(() => g.roundRect(1.6, 20, 20.8, 1.8, .5));
        cut(() => g.roundRect(10.3, 15.2, 3.4, 4.8, [1.7, 1.7, 0, 0]));
      },
      // صليب الإسعاف في مربّع مستدير
      firstaid: ({ g, fill, cut }) => {
        fill(() => g.roundRect(2.6, 2.6, 18.8, 18.8, 4.4));
        cut(() => g.roundRect(10.2, 6.4, 3.6, 11.2, .7)); cut(() => g.roundRect(6.4, 10.2, 11.2, 3.6, .7));
      },
      info: ({ g, fill, cut }) => {
        fill(() => g.arc(12, 12, 9.6, 0, Math.PI * 2));
        cut(() => g.arc(12, 7.3, 1.5, 0, Math.PI * 2)); cut(() => g.roundRect(10.75, 10.1, 2.5, 8, 1.25));
      },
      elevator: ({ g, fill, cut, poly }) => {
        fill(() => g.roundRect(4.4, 2, 15.2, 20, 3.2));
        cut(() => poly([[12, 5.4], [15.6, 9.8], [8.4, 9.8]])); cut(() => poly([[8.4, 14.2], [15.6, 14.2], [12, 18.6]]));
      },
      stairs: ({ fill, poly }) => fill(() => poly([[2.5, 21.5], [2.5, 16.8], [7.2, 16.8], [7.2, 12.2], [11.8, 12.2], [11.8, 7.6], [16.4, 7.6], [16.4, 3], [21.5, 3], [21.5, 21.5]])),
      // حقيبة عمل
      office: ({ g, fill, cut }) => {
        fill(() => g.roundRect(8.2, 3.2, 7.6, 6, 2)); cut(() => g.roundRect(9.9, 4.9, 4.2, 5, 1));
        fill(() => g.roundRect(2.4, 7.4, 19.2, 13.6, 2.8));
        cut(() => g.rect(2.4, 13, 19.2, .8)); fill(() => g.roundRect(10.6, 12, 2.8, 2.8, .7));
      },
      // حقيبة تسوّق
      shop: ({ g, fill, cut }) => {
        fill(() => g.roundRect(7.6, 2.4, 8.8, 10, 4.4)); cut(() => g.roundRect(9.3, 4.1, 5.4, 10, 2.7));
        fill(() => g.roundRect(3.6, 8.2, 16.8, 13.6, [1.6, 1.6, 3.2, 3.2]));
      },
      // حقيبة سفر بعجلتين (الفنادق والنقل والسفر)
      travel: ({ g, fill, cut, pill }) => {
        fill(() => g.roundRect(9, 1.8, 6, 5, 1.6)); cut(() => g.roundRect(10.5, 3.3, 3, 4, .6));
        fill(() => g.roundRect(5.6, 5.6, 12.8, 14.4, 2.8));
        cut(() => pill(8.9, 8.6, 1.2, 8.4)); cut(() => pill(13.9, 8.6, 1.2, 8.4));
        fill(() => g.arc(8.6, 21.3, 1.5, 0, Math.PI * 2)); fill(() => g.arc(15.4, 21.3, 1.5, 0, Math.PI * 2));
      },
      // علّاقة ملابس (الأمانات)
      cloak: ({ g }) => {
        g.strokeStyle = INK; g.lineWidth = 1.9; g.lineCap = 'round'; g.lineJoin = 'round';
        g.beginPath(); g.arc(12, 5.6, 2.4, Math.PI * 1.05, Math.PI * .55, false); g.lineTo(12, 10);
        g.lineTo(2.6, 17.4); g.quadraticCurveTo(1.6, 18.8, 3.4, 18.8); g.lineTo(20.6, 18.8); g.quadraticCurveTo(22.4, 18.8, 21.4, 17.4); g.lineTo(12, 10);
        g.stroke();
      },
      // مفتاح ربط (الخدمات الفنية)
      tools: ({ g, fill, cut }) => {
        g.save(); g.translate(12, 12); g.rotate(-Math.PI / 4);
        fill(() => g.roundRect(-1.5, -3, 3, 13.4, 1.5));
        fill(() => g.arc(0, -5.6, 4.2, 0, Math.PI * 2)); cut(() => g.roundRect(-1.3, -11, 2.6, 6, .6));
        g.restore();
      },
      // صاعقة (غرف الخدمة والكهرباء)
      bolt: ({ fill, poly }) => fill(() => poly([[13.6, 1.8], [4.8, 13.4], [11, 13.4], [9.6, 22.2], [19.2, 9.8], [12.8, 9.8]])),
      vip: ({ fill, poly }) => fill(() => poly(Array.from({ length: 10 }, (_, i) => {
        const a = -Math.PI / 2 + i * Math.PI / 5, r = i % 2 ? 4.4 : 10;
        return [12 + Math.cos(a) * r, 12.8 + Math.sin(a) * r];
      }))),
      // قاعة: لوح عرض على حامل
      hall: ({ g, fill, cut, pill }) => {
        fill(() => g.roundRect(2.4, 2.6, 19.2, 12.4, 2)); cut(() => g.roundRect(4.4, 4.6, 15.2, 8.4, .8));
        fill(() => pill(11, 14, 2, 7.6)); fill(() => pill(5.6, 20.4, 12.8, 1.8));
      }
    };
    const ICON_OF = { 'wc-w': 'toilet-f', 'wc-m': 'toilet-m', cafe: 'cafe', restaurant: 'food', hotel: 'travel', cloak: 'cloak', techservice: 'tools',
      utility: 'bolt', market: 'shop', g105: 'hall' };
    const iconOf = r => r.icon || ICON_OF[r.id] || r.kind;
    const roofMats = {};
    // بمادّة السقف نفسها (خشونة .9) فلا يظهر للمربّع حدّ على السطح
    const roofMat = key => roofMats[key] || (roofMats[key] = new THREE.MeshStandardMaterial({ map: glyph(ICONS[key]), roughness: .9,
      metalness: 0, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
    const roofTop = ROOM_H + m(.18), ICON = m(2.6);   // مقاس واحد — يسعه أضيق سقف (2.7 م)
    const iconGeo = new THREE.PlaneGeometry(ICON, ICON);
    [...BAND_ROOMS.filter(r => r.kind !== 'registration').map(r => [r, BAND.z0 + .4, BAND.z1]),
      ...SOUTH_ROOMS.filter(r => !r.passage).map(r => [r, SOUTH.z0, SOUTH.z1 - .3]),
      ...NORTH_ROOMS.map(r => [r, NORTH_WC.z0, NORTH_WC.z1]),
      // المصلّيان: النساء على السقف، والرجال على الأرض المفتوحة (y)
      ...PRAYERS.map(p => [{ ...p, kind: 'prayer' }, NORTH.z0, NORTH.z1, p.closed ? roofTop : 1.2 + .05])]
      .filter(([r]) => ICONS[iconOf(r)]).forEach(([r, z0, z1, y = roofTop]) => {
        const decal = new THREE.Mesh(iconGeo, roofMat(iconOf(r)));
        decal.rotation.x = -Math.PI / 2;
        decal.position.set(ux((r.x0 + r.x1) / 2), y + .05, uz((z0 + z1) / 2));
        decal.renderOrder = 2;
        add(decal, false);
      });
    // الجدار الخارجي للمبنى جنوب الصفّ، مفتوح عند الممرّات
    let edge = CONCOURSE.x0;
    SOUTH_ROOMS.filter(r => r.passage).forEach(r => { wallSeg(ux(edge), uz(SOUTH.z1 - .3), ux(r.x0), uz(SOUTH.z1 + .3), CUT_H); edge = r.x1; });
    wallSeg(ux(edge), uz(SOUTH.z1 - .3), ux(CONCOURSE.x1), uz(SOUTH.z1 + .3), CUT_H);
    // بوابات «مدخل الزوار»: إطار عنابي بلافتة بيضاء عند فم كل ممرّ على الممر
    const visitSign = text => glow(canvasTexture(512, 128, (g, w, h) => {
      g.fillStyle = toneHex(100); g.fillRect(0, 0, w, h);
      g.fillStyle = css('--sef-maroon'); g.textAlign = 'center'; g.textBaseline = 'middle';
      fitText(g, text, 54, w * .9); g.fillText(text, w / 2, h / 2 + 3);
    }));
    const visitFace = visitSign(tr('مدخل الزوار', 'Visitor Entrance'));
    SOUTH_ROOMS.filter(r => r.passage).forEach(r => {
      const x0 = ux(r.x0 + .2), x1 = ux(r.x1 - .2), z = uz(SOUTH.z0 + .2), h = m(3.6);
      block(x0, z - 4, 8, 8, 0, h, gateMat, 1.5);
      block(x1 - 8, z - 4, 8, 8, 0, h, gateMat, 1.5);
      block(x0, z - 4, x1 - x0, 8, h, 8, gateMat, 1.5);
      const board = new THREE.Mesh(rgeo(Math.min(x1 - x0 - 4, m(4)), m(.9), 2, .6), [frame, frame, frame, frame, visitFace, visitFace]);
      board.position.set((x0 + x1) / 2, h + 4, z - 5); board.rotation.y = Math.PI; add(board);
    });
    /* ---------- الاستقبال كما في الريندر ----------
       جناح مفتوح على الممر: عمودان عنابيان بأعلى مائل نحو الممر، لافتة خضراء عريضة بينهما
       (شعار سيف واسم المعرض، ومربعات ألوان سيف على نصفها الأيمن)، جدار خلفي دافئ بخطوط ذهبية
       رأسية، ومكتب أبيض بواجهة خضراء تحمل الشعار ودرجات مربعات على طرفه، ونبتتان في أصيصين أبيضين */
    const logo = new Image();
    const mosaic = [['--sef-maroon', '--sef-pink', '--sef-teal', '--sef-green', '--sef-pink', '--sef-coral', '--sef-teal', '--sef-pink'],
      ['--sef-orange', '--sef-pink', '--sef-teal', '--sef-green', null, '--sef-green', '--sef-coral', null]];
    const ink = name => name ? css(name) : toneHex(100);
    // الشعار وسطر الاسم: الشعار الأبيض، فاصل رفيع، ثم الاسم بالعربية وتحته بالإنجليزية
    const brandLine = (g, x, y, hgt) => {
      if (logo.complete && logo.naturalWidth) g.drawImage(logo, x, y, hgt * logo.naturalWidth / logo.naturalHeight, hgt);
      const lx = x + hgt * (logo.naturalWidth ? logo.naturalWidth / logo.naturalHeight : 1.1) + hgt * .22;
      g.fillStyle = toneHex(100); g.fillRect(lx, y + hgt * .05, Math.max(2, hgt * .025), hgt * .9);
      g.textAlign = 'left'; g.textBaseline = 'middle';
      g.font = '700 ' + Math.round(hgt * .2) + 'px ' + font; g.fillText('معرض ومسابقة الأمن', lx + hgt * .16, y + hgt * .2);
      g.fillText('والابتكار العالمية', lx + hgt * .16, y + hgt * .45);
      g.font = '600 ' + Math.round(hgt * .14) + 'px ' + font; g.fillText('Security & Innovation Fair', lx + hgt * .16, y + hgt * .76);
    };
    const fasciaTex = canvasTexture(2048, 256, (g, w, h) => {
      g.fillStyle = css('--sef-green'); g.fillRect(0, 0, w, h);
      brandLine(g, w * .08, h * .14, h * .72);
      const cell = h / 2;
      mosaic.forEach((row, ri) => row.forEach((c, ci) => { g.fillStyle = ink(c); g.fillRect(w - cell * (row.length - ci), ri * cell, cell, cell); }));
    });
    const deskTex = canvasTexture(1536, 216, (g, w, h) => {
      g.fillStyle = css('--sef-green'); g.fillRect(0, 0, w, h);
      brandLine(g, w * .3, h * .16, h * .68);
      // درجات المربعات على الطرف الأيمن
      const c = h / 3;
      [['--sef-pink', 0, 0], ['--sef-pink', 1, 1], ['--sef-teal', 0, 1], ['--sef-coral', 1, 2], ['--sef-orange', 0, 2]]
        .forEach(([name, col, row]) => { g.fillStyle = css(name); g.fillRect(w - c * (col + 1), row * c, c, c); });
    });
    logo.onload = () => { fasciaTex.userData.repaint(); deskTex.userData.repaint(); };
    logo.src = 'assets/img/saif-logo-white.png';
    const fasciaFace = new THREE.MeshStandardMaterial({ map: fasciaTex, roughness: .6, emissive: tone(100), emissiveMap: fasciaTex, emissiveIntensity: .12 });
    const deskFace = new THREE.MeshStandardMaterial({ map: deskTex, roughness: .6, emissive: tone(100), emissiveMap: deskTex, emissiveIntensity: .1 });
    const warmWall = mat(97), white = mat(100), plant = brand('--ok-fg');
    const leafGeo = new THREE.SphereGeometry(1, 10, 6); leafGeo.scale(m(.1), m(.34), m(.03));
    // لوح بواجهة واحدة نحو الممر (+z)، وبقية أوجهه بخضرة سيف
    const panel = (w, h, d, face, x, y, z) => {
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), [backdrop, backdrop, backdrop, backdrop, face, backdrop]);
      mesh.position.set(x, y, z); add(mesh);
    };
    BAND_ROOMS.filter(r => r.kind === 'registration').forEach(r => {
      const X0 = r.x0 + .15, X1 = r.x1 - .15, Zb = BAND.z0 + .4, Zf = BAND.z1, cx = (X0 + X1) / 2;
      block(...R(X0, Zb, X1, Zf), .8, .3, roomFloor, .3, false);
      // الجدار الخلفي الدافئ وخطوطه الذهبية، والجداران الجانبيان الأبيضان
      block(...R(X0, Zb, X1, Zb + .25), 0, m(3.4), warmWall, .6);
      [1.6, 1.85, 2.1].forEach(o => [X0 + o, X1 - o].forEach(x => block(...R(x - .03, Zb + .26, x + .03, Zb + .32), 0, m(3.2), gold, .1, false)));
      [[X0, X0 + .3], [X1 - .3, X1]].forEach(([a, b]) => block(...R(a, Zb, b, Zf - .9), 0, m(3.4), white, .6));
      // العمودان العنابيان، وأعلاهما يميل نحو الممر فوق اللافتة
      [[X0, X0 + .7], [X1 - .7, X1]].forEach(([a, b]) => {
        block(...R(a, Zf - .9, b, Zf), 0, m(4.3), gateMat, 1);
        block(...R(a, Zf - .9, b, Zf + .5), m(4.3), m(.5), gateMat, 1);
      });
      // اللافتة العريضة بين العمودين
      panel(m(X1 - X0 - 1.4), m(1.3), m(.3), fasciaFace, ux(cx), m(3.7), uz(Zf - .3));
      // المكتب: جسم أبيض، واجهة خضراء، طرف داكن يسارًا، وشاشتان
      const zc = Zb + 2.4;
      block(...R(cx - 3.2, zc - .4, cx + 3.2, zc + .4), 0, m(1.05), white, .6);
      block(...R(cx - 3.6, zc - .4, cx - 3.2, zc + .3), 0, m(1), backdrop, .3);
      panel(m(6.1), m(.82), 2, deskFace, ux(cx + .05), m(.52), uz(zc + .4) + 1);
      [-1.6, 1.6].forEach(o => block(...R(cx + o - .3, zc - .25, cx + o + .3, zc - .2), m(1.05), m(.38), mat(88), .2));
      // نبتتان في أصيصين أبيضين عند طرفي الجناح
      [X0 + 1.3, X1 - 1.3].forEach(x => {
        const pot = new THREE.Mesh(new THREE.CylinderGeometry(m(.32), m(.22), m(.85), 24), white);
        pot.position.set(ux(x), m(.425), uz(Zf - 1.8)); add(pot);
        // سعف نخلة صغيرة: أوراق طويلة تنحني من الوسط إلى الخارج
        for (let i = 0; i < 9; i++) {
          const leaf = new THREE.Mesh(leafGeo, plant), a = i / 9 * Math.PI * 2, tilt = .55 + (i % 3) * .25;
          leaf.position.set(ux(x) + Math.sin(a) * m(.28) * Math.sin(tilt), m(1.05) + Math.cos(tilt) * m(.32), uz(Zf - 1.8) + Math.cos(a) * m(.28) * Math.sin(tilt));
          leaf.rotation.set(0, a, 0); leaf.rotateX(tilt);
          add(leaf, false);
        }
      });
    });
    // الصرّاف الآلي في البهو الشرقي
    block(...R(ATM.x - .5, ATM.z - .3, ATM.x + .5, ATM.z + .3), 0, m(1.8), mat(88), 1);
    // نقطتا التفتيش: بوّابتا كشف معادن عبر الممر
    CHECKPOINTS.forEach(x => [CONCOURSE.z0 + 3, CONCOURSE.z1 - 3].forEach(z => {
      block(...R(x - .4, z - .5, x - .25, z + .5), 0, m(2.2), mat(88), .3);
      block(...R(x + .25, z - .5, x + .4, z + .5), 0, m(2.2), mat(88), .3);
      block(...R(x - .4, z - .5, x + .4, z + .5), m(2.2), m(.2), mat(88), .3);
    }));
    // غرفتا العزل عند طرفي الممر: حاجزان زجاجيان بباب أوسط
    const pane = new THREE.MeshStandardMaterial({ color: tone(100), roughness: .2, metalness: 0, transparent: true, opacity: .45 });
    const midZ = (CONCOURSE.z0 + CONCOURSE.z1) / 2;
    AIRLOCKS.flat().forEach(x => {
      block(...R(x - .1, CONCOURSE.z0, x + .1, midZ - 2), 0, m(2.8), pane, .3, false);
      block(...R(x - .1, midZ + 2, x + .1, CONCOURSE.z1), 0, m(2.8), pane, .3, false);
    });
    // جلسات بيضاء في الممر بين المداخل، بعيدًا عن الأبواب
    const doors = [...BAND_ROOMS, ...SOUTH_ROOMS].map(r => (r.x0 + r.x1) / 2);
    const seat = mat(100);
    [44, 86, 113, 150].filter(x => doors.every(d => Math.abs(d - x) > 2.4)).forEach(x => [-1.3, 1.3].forEach(o => {
      block(...R(x + o - .9, 83.6, x + o + .9, 84.6), 0, m(.45), seat, 1.5);
      block(...R(x + o - .9, 84.4, x + o + .9, 84.6), m(.45), m(.4), seat, .3);
    }));
  }
};
