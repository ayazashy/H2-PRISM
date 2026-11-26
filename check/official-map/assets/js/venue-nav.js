/* =========================================================
   طبقة التنقّل فوق خريطة القاعة — منقولة من تطبيق تحكيم (المرشد بالتجربة الكاملة).
   ١) الكاميرا: «جهاز» من نقطة نظر + مسافة + ميل + اتجاه، فوق OrbitControls نفسه
      (الفأرة واللمس للموقع كما هما؛ هذه الطبقة تحرّك الكاميرا للمسار والرحلة فقط).
   ٢) فهرس كل ما في القاعة (فرق، طاولات، مناطق، مداخل، أعمدة…) للبحث في «من / إلى».
   ٣) شبكة ممرات القاعة، وأقصر مسار بين أي مكانين، ورحلة بكاميرا الشخص الثالث.
   الوحدة: المتر ≈ 11 وحدة مخطط. X شرقًا، Z جنوبًا.
   ========================================================= */
import * as THREE from '../vendor/three/three.module.min.js';
import { tr } from './i18n.js';

const UNITS_PER_M = 11;
const WALK_MPS = 1.3;                    // سرعة مشي مريحة في معرض
// لون المسار وما يخصّه وحده (الخط، البداية، الدبوس، الماشي) — توكن --route (مرجاني سيف)
const root = getComputedStyle(document.documentElement);
const ACCENT = new THREE.Color(root.getPropertyValue('--route').trim() || root.getPropertyValue('--brand').trim() || 'teal');

// H: حالة الهاكاثون من طبقة الأدمن — الأسماء والطاولات كما تظهر على الخريطة
export function mountNav(venue, site, H, post) {
  const cam = venue.camera, controls = venue.controls, scene = venue.scene;
  const container = venue.renderer.domElement.parentElement;

  /* =====================================================
     ١) الكاميرا: «جهاز» من نقطة نظر على الأرض + مسافة + ميل + اتجاه
     ===================================================== */
  const PHI_MIN = 0.0001, PHI_MAX = 1.2, D_MIN = site.minDistance || 45, D_MAX = 5200;
  const PHI_3D = site.polar || .82;
  const THETA_HOME = 0;                  // الشاشة أفقية: الاتجاه الأصلي لمنظور الموقع
  const B = site.bounds;
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const wrap = a => Math.atan2(Math.sin(a), Math.cos(a));
  // علامتا المسار تكبران مع بُعد الكاميرا (مقاس ثابت تقريبًا على الشاشة) — markerK مقاسهما الحالي
  const markerScale = d => clamp(d / 1000, 1, 6);
  let markerK = 1;

  function getRig() {
    const t = controls.target, o = cam.position.clone().sub(t), d = o.length();
    return { x: t.x, z: t.z, d, phi: Math.acos(clamp(o.y / d, -1, 1)), theta: Math.atan2(o.x, o.z) };
  }
  let lastSent = { pitched: null, heading: null };
  function setRig(r) {
    r.phi = clamp(r.phi, PHI_MIN, PHI_MAX);
    r.d = clamp(r.d, D_MIN, D_MAX);
    r.x = clamp(r.x, B[0], B[2]);
    r.z = clamp(r.z, B[1], B[3]);
    controls.target.set(r.x, 0, r.z);
    const s = Math.sin(r.phi) * r.d;
    cam.position.set(r.x + s * Math.sin(r.theta), r.d * Math.cos(r.phi), r.z + s * Math.cos(r.theta));
    cam.lookAt(controls.target);
    cam.updateMatrixWorld();
    venue.invalidate();
    // الحالة للتطبيق: زر 2D/3D والبوصلة — فقط عند التغيّر
    const pitched = r.phi > .12, heading = Math.round(wrap(r.theta - THETA_HOME) * 180 / Math.PI * 2) / 2;
    if (pitched !== lastSent.pitched || heading !== lastSent.heading) {
      lastSent = { pitched, heading };
      post({ type: 'camera', pitched, heading });
    }
    return r;
  }
  const ground = (sx, sy) => venue.groundPoint(sx, sy, 0);
  // يبقي نقطة الأرض G تحت نقطة الشاشة (sx, sy): إزاحة الجهاز تزيح الإصابة بالقدر نفسه
  function anchor(r, G, sx, sy) {
    if (!G) return r;
    const H = ground(sx, sy);
    if (!H || Math.hypot(H.x - r.x, H.z - r.z) > r.d * 8) return r;
    r.x += G.x - H.x; r.z += G.z - H.z;
    return setRig(r);
  }

  /* ---------- الحركات المتحرّكة ---------- */
  let anim = null, inertia = null;
  // إزاحة مركز الإسقاط (لوحة جانبية): الحالية، ومن أين وإلى أين تنزلق
  // y: رفع الصورة فوق الشيت السفلي في الجوال (لا تُزاح الكاميرا: حدود القاعة تمنع إزاحتها بما يكفي)
  const view = { x: 0, from: 0, to: 0, y: 0, yFrom: 0, yTo: 0, t0: 0, ms: 900 };
  const easeInOut = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  const easeOut = t => 1 - Math.pow(1 - t, 3);
  function animateTo(to, ms, opts = {}) {
    const from = getRig(), ease = opts.ease || easeInOut;
    const target = Object.assign({}, from, to);
    const dTheta = wrap(target.theta - from.theta);
    stopMotion();
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) ms = 0;
    anim = { start: null, step(now) {
      if (this.start === null) this.start = now;
      const k = ms ? Math.min(1, (now - this.start) / ms) : 1, e = ease(k);
      const r = {
        x: from.x + (target.x - from.x) * e,
        z: from.z + (target.z - from.z) * e,
        d: from.d * Math.pow(target.d / from.d, e),            // التقريب أُسّيّ: يبدو منتظمًا للعين
        phi: from.phi + (target.phi - from.phi) * e,
        theta: from.theta + dTheta * e
      };
      setRig(r);
      if (opts.anchor) anchor(r, opts.anchor.G, opts.anchor.sx, opts.anchor.sy);
      if (k === 1) { anim = null; if (opts.done) opts.done(); }
    } };
  }
  function stopMotion() { anim = null; inertia = null; }

  /* ---------- لمسة المستخدم توقف الحركة الآلية، والرحلة تعود لتتبّعه بعد ثلاث ثوانٍ ---------- */
  let journeyTouchedAt = 0;
  const pts = { size: 0 };
  controls.addEventListener('start', () => { stopMotion(); journeyTouchedAt = performance.now(); pts.size = 1; });
  controls.addEventListener('end', () => { journeyTouchedAt = performance.now(); pts.size = 0; });
  container.addEventListener('wheel', () => { anim = null; journeyTouchedAt = performance.now(); }, { passive: true });

  /* ---------- الضغط مرتين: تقريب سلس نحو موضع الضغطة (تبقى النقطة تحت الإصبع) ---------- */
  {
    const cvs = venue.renderer.domElement;
    let down = null, lastTap = null;
    cvs.addEventListener('pointerdown', e => { down = e.isPrimary ? { x: e.clientX, y: e.clientY, t: performance.now() } : null; });
    cvs.addEventListener('pointerup', e => {
      const now = performance.now();
      if (!down || now - down.t > 300 || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 8) { down = null; lastTap = null; return; }
      down = null;
      if (lastTap && now - lastTap.t < 320 && Math.hypot(e.clientX - lastTap.x, e.clientY - lastTap.y) < 40) {
        lastTap = null;
        if (!controls.enabled) return;
        const G = ground(e.clientX, e.clientY);
        if (!G) return;
        const sx = e.clientX, sy = e.clientY;
        animateTo({ d: Math.max(D_MIN, getRig().d * .45) }, 450, { ease: easeOut, anchor: { G, sx, sy } });
        journeyTouchedAt = now;
      } else lastTap = { x: e.clientX, y: e.clientY, t: now };
    });
    // يمنع تكبير المتصفح نفسه بالضغط مرتين على الخريطة
    cvs.addEventListener('dblclick', e => e.preventDefault());
  }

  /* =====================================================
     ٢) الفهرس وشبكة الممرات — من الموقع نفسه (site.nav)
     الموقع يعرف قاعته: أماكنه، وخطوطًا تمشي في وسط كل ممر حقيقي،
     ومعالم يراها الماشي، وكيف يُوصل لكل مكان («الأمتار الأخيرة»).
     ===================================================== */
  const spec = site.nav(H);
  let places = [];
  let placeById = {};
  function buildIndex() {
    places = spec.places();
    placeById = {};
    places.forEach(p => { placeById[p.id] = p; });
  }
  buildIndex();

  const N = {};
  Object.entries(spec.nodes).forEach(([id, [x, z]]) => { N[id] = { id, x, z }; });
  const EDGES = spec.edges.map(([a, b, w]) => ({ a, b, w: w || 14 }));
  const len = (a, b) => Math.hypot(a.x - b.x, a.z - b.z);

  // نقطة على الشبكة: أقرب إسقاط على أي ممر
  function project(p, filter) {
    let best = null;
    EDGES.forEach((e, i) => {
      if (filter && !filter(e, N[e.a], N[e.b])) return;
      const A = N[e.a], Bn = N[e.b], dx = Bn.x - A.x, dz = Bn.z - A.z, L2 = dx * dx + dz * dz;
      const t = clamp(((p.x - A.x) * dx + (p.z - A.z) * dz) / L2, 0, 1);
      const q = { x: A.x + dx * t, z: A.z + dz * t }, d = len(p, q);
      if (!best || d < best.d) best = { edge: i, t, x: q.x, z: q.z, d };
    });
    return best;
  }

  // كيف نصل لكل مكان: عقدته إن كانت له، أو ما يقترحه الموقع، أو أقرب ممر
  function approaches(id) {
    const p = placeById[id];
    if (!p) return [];
    if (p.node && N[p.node]) return [{ at: { node: p.node, x: N[p.node].x, z: N[p.node].z }, tail: [], end: N[p.node] }];
    const custom = spec.approach && spec.approach(p, { project, N });
    if (custom && custom.length) return custom;
    const q = project(p);
    return [{ at: q, tail: [], end: { x: q.x, z: q.z } }];
  }

  // أقصر طريق بين نقطتين على الشبكة (Dijkstra على شبكة صغيرة + عقدتان مؤقتتان)
  function shortest(from, to) {
    const adj = {};
    const link = (a, b, w) => { (adj[a] = adj[a] || []).push({ to: b, w }); (adj[b] = adj[b] || []).push({ to: a, w }); };
    EDGES.forEach(e => link(e.a, e.b, len(N[e.a], N[e.b])));
    const pos = Object.assign({}, N);
    const attach = (name, q) => {
      if (q.node) return q.node;
      const e = EDGES[q.edge];
      pos[name] = { id: name, x: q.x, z: q.z };
      link(name, e.a, len(q, N[e.a])); link(name, e.b, len(q, N[e.b]));
      return name;
    };
    const a = attach('$a', from), b = attach('$b', to);
    if (!from.node && !to.node && from.edge === to.edge) link(a, b, len(from, to));
    const dist = { [a]: 0 }, prev = {}, done = new Set();
    while (true) {
      let u = null;
      Object.keys(dist).forEach(k => { if (!done.has(k) && (u === null || dist[k] < dist[u])) u = k; });
      if (u === null || u === b) break;
      done.add(u);
      (adj[u] || []).forEach(({ to: v, w }) => {
        if (dist[u] + w < (dist[v] ?? Infinity)) { dist[v] = dist[u] + w; prev[v] = u; }
      });
    }
    if (dist[b] === undefined) return null;
    const path = [];
    for (let k = b; k !== undefined; k = prev[k]) path.unshift({ x: pos[k].x, z: pos[k].z });
    return { path, length: dist[b] };
  }

  function computeRoute(fromId, toId) {
    let best = null;
    approaches(fromId).forEach(A => approaches(toId).forEach(Z => {
      const mid = shortest(A.at, Z.at);
      if (!mid) return;
      const pts = [A.end, ...A.tail.slice().reverse(), ...mid.path, ...Z.tail, Z.end];
      const clean = simplify(pts);
      const total = clean.slice(1).reduce((s, p, i) => s + len(clean[i], p), 0);
      if (!best || total < best.total) best = { pts: clean, total, end: Z, start: A };
    }));
    return best;
  }

  function simplify(pts) {
    const out = [];
    pts.forEach(p => { if (!out.length || len(out[out.length - 1], p) > .5) out.push({ x: p.x, z: p.z }); });
    for (let i = out.length - 2; i > 0; i--) {
      const a = out[i - 1], b = out[i], c = out[i + 1];
      const cross = (b.x - a.x) * (c.z - b.z) - (b.z - a.z) * (c.x - b.x);
      if (Math.abs(cross) < 1e-3 * len(a, b) * len(b, c)) out.splice(i, 1);
    }
    return out;
  }

  /* ---------- التعليمات: انعطافات بمعالم يراها الماشي ---------- */
  const landmarks = spec.landmarks;
  function landmarkNear(p) {
    let best = null;
    landmarks.forEach(l => { const d = len(l, p); if (d < (spec.landmarkReach || 45) && (!best || d < best.d)) best = { d, name: l.name }; });
    return best && best.name;
  }
  const meters = u => Math.max(1, Math.round(u / UNITS_PER_M));

  function buildSteps(route, toPlace) {
    const pts = route.pts, steps = [];
    let walked = 0, lastAt = 0;
    for (let i = 1; i < pts.length - 1; i++) {
      walked += len(pts[i - 1], pts[i]);
      const a = { x: pts[i].x - pts[i - 1].x, z: pts[i].z - pts[i - 1].z };
      const b = { x: pts[i + 1].x - pts[i].x, z: pts[i + 1].z - pts[i].z };
      const turn = Math.atan2(a.x * b.z - a.z * b.x, a.x * b.x + a.z * b.z);   // موجب = يمين (X شرق، Z جنوب)
      if (Math.abs(turn) < .5) continue;
      const right = turn > 0, slight = Math.abs(turn) < 1.1;
      // ميل خفيف على مقطع قصير لا يحتاج تعليمة؛ وانعطافان متقاربان يُدمجان في الأخير
      const legAfter = len(pts[i], pts[i + 1]);
      if (slight && legAfter < 6 * UNITS_PER_M) continue;
      if (steps.length && walked - steps[steps.length - 1].at < 6 * UNITS_PER_M) {
        const prev = steps.pop();
        lastAt = prev.at - prev.meters * UNITS_PER_M;
      } else if (!steps.length && walked < 6 * UNITS_PER_M) lastAt = 0;
      const where = landmarkNear(pts[i]);
      steps.push({
        icon: (slight ? 'slight-' : '') + (right ? 'right' : 'left'),
        text: tr((slight ? 'مِل ' : 'انعطف ') + (right ? 'يمينًا' : 'يسارًا') + (where ? ' عند ' + where : ''),
          (slight ? 'Bear ' : 'Turn ') + (right ? 'right' : 'left') + (where ? ' at ' + where : '')),
        at: walked, meters: meters(walked - lastAt)
      });
      lastAt = walked;
    }
    const total = route.total;
    let arrive = tr('وصلت إلى ', 'Arrive at ') + toPlace.name;
    if (route.end.table && pts.length > 1) {
      // الطاولة عن يمين الماشي أو يساره في آخر خطوة
      const p = pts[pts.length - 2], q = pts[pts.length - 1], t = route.end.table;
      const side = (q.x - p.x) * (t.z - q.z) - (q.z - p.z) * (t.x - q.x);
      arrive = toPlace.name + (side > 0 ? tr(' على يمينك', ' on your right') : tr(' على يسارك', ' on your left'));
    }
    steps.push({ icon: 'arrive', text: arrive, at: total, meters: meters(total - lastAt) });
    // كل خطوة يضغط لها «التالي» — فلا تستحقها إلا انعطافة حقيقية بعد مسافة تُذكر.
    // الميل الخفيف والمقطع القصير يُضمّان إلى الخطوة التي بعدهما.
    const kept = [];
    let carry = 0;
    steps.forEach(st => {
      if (st.icon !== 'arrive' && (st.icon.startsWith('slight-') || st.meters < 8)) { carry += st.meters; return; }
      kept.push({ ...st, meters: st.meters + carry });
      carry = 0;
    });
    return kept;
  }

  /* =====================================================
     ٤) الرسم: ممرات بيضاء هادئة، ومسار بلون واحد بلا حدود
     ===================================================== */
  const Y_WALK = .95, Y_ROUTE = 1.6;
  // الممرات: شرائط بيضاء على الأرضية الرمادية — تقرأ القاعة كطرق دون أي خط محيط
  (function drawWalkways() {
    // من مادة الأرضية نفسها (مضاءة وتستقبل الظل) بدرجة أفتح منها بالكاد —
    // الممرات تُقرأ جزءًا من الأرض لا شرائط بيضاء فوقها
    const tone = getComputedStyle(document.documentElement).getPropertyValue('--venue-98').trim() || '#FAFAFA';
    const mat = new THREE.MeshStandardMaterial({ color: tone, roughness: .9, metalness: 0, side: THREE.DoubleSide, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -1 });
    const geos = [];
    EDGES.forEach(e => geos.push(ribbon([N[e.a], N[e.b]], e.w, Y_WALK)));
    Object.values(N).forEach(n => {
      const w = Math.max(...EDGES.filter(e => e.a === n.id || e.b === n.id).map(e => e.w));
      const c = new THREE.CircleGeometry(w / 2, 24); c.rotateX(-Math.PI / 2); c.translate(n.x, Y_WALK, n.z); geos.push(c);
    });
    geos.forEach(geo => {
      // الشرائط هندسة يدوية بلا متّجهات عمودية — بدونها تظهر المادة المضاءة سوداء
      if (!geo.attributes.normal) geo.computeVertexNormals();
      const m = new THREE.Mesh(geo, mat); m.renderOrder = 1; m.receiveShadow = true; scene.add(m);
    });
    venue.invalidate();
  })();

  function ribbon(pts, width, y) {
    const pos = [], idx = [];
    pts.forEach((p, i) => {
      const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
      let tx = b.x - a.x, tz = b.z - a.z; const l = Math.hypot(tx, tz) || 1; tx /= l; tz /= l;
      const nx = -tz * width / 2, nz = tx * width / 2;
      pos.push(p.x + nx, y, p.z + nz, p.x - nx, y, p.z - nz);
      if (i) { const k = i * 2; idx.push(k - 2, k - 1, k, k - 1, k + 1, k); }
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    geo.setIndex(idx);
    return geo;
  }

  // زوايا المسار مستديرة، ونقاطه متقاربة ليُرسم تدريجيًا ويُطوى ما مشيته
  const SPACING = 3;
  function smooth(pts) {
    const out = [pts[0]];
    for (let i = 1; i < pts.length - 1; i++) {
      const a = pts[i - 1], b = pts[i], c = pts[i + 1];
      const r = Math.min(10, len(a, b) / 2, len(b, c) / 2);
      const u = { x: (a.x - b.x) / len(a, b), z: (a.z - b.z) / len(a, b) };
      const v = { x: (c.x - b.x) / len(b, c), z: (c.z - b.z) / len(b, c) };
      const p0 = { x: b.x + u.x * r, z: b.z + u.z * r }, p2 = { x: b.x + v.x * r, z: b.z + v.z * r };
      for (let k = 0; k <= 8; k++) {
        const t = k / 8, s = 1 - t;
        out.push({ x: s * s * p0.x + 2 * s * t * b.x + t * t * p2.x, z: s * s * p0.z + 2 * s * t * b.z + t * t * p2.z });
      }
    }
    out.push(pts[pts.length - 1]);
    const dense = [out[0]];
    for (let i = 1; i < out.length; i++) {
      const a = out[i - 1], b = out[i], l = len(a, b), n = Math.max(1, Math.ceil(l / SPACING));
      for (let k = 1; k <= n; k++) dense.push({ x: a.x + (b.x - a.x) * k / n, z: a.z + (b.z - a.z) * k / n });
    }
    const cum = [0];
    for (let i = 1; i < dense.length; i++) cum.push(cum[i - 1] + len(dense[i - 1], dense[i]));
    return { pts: dense, cum };
  }

  const routeGroup = new THREE.Group();
  scene.add(routeGroup);
  const accentMat = new THREE.MeshBasicMaterial({ color: ACCENT, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2 });
  const whiteMat = new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -3 });
  // نواة العلامات فوق قرصها الأبيض: إزاحة عمق أقوى منه، وإلا غطّاها الأبيض رغم ارتفاعها
  const coreMat = new THREE.MeshBasicMaterial({ color: ACCENT, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -5 });
  let current = null;              // { line, mesh, puck, startCap, ... }

  function disc(r, mat, y) {
    const g2 = new THREE.CircleGeometry(r, 40); g2.rotateX(-Math.PI / 2);
    const m = new THREE.Mesh(g2, mat); m.position.y = y; m.renderOrder = 3; return m;
  }
  function makeStartMarker() {
    const g2 = new THREE.Group();
    g2.add(disc(7.5, whiteMat, Y_ROUTE + .05), disc(4.6, coreMat, Y_ROUTE + .1));
    return g2;
  }
  function makePin() {
    const g2 = new THREE.Group();
    const head = new THREE.Mesh(new THREE.SphereGeometry(5.2, 24, 16), new THREE.MeshStandardMaterial({ color: ACCENT, roughness: .45 }));
    head.position.y = 26;
    const stem = new THREE.Mesh(new THREE.CylinderGeometry(.7, .7, 22, 10), new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: .6 }));
    stem.position.y = 11 + Y_ROUTE;
    g2.add(stem, head, disc(4, accentMat, Y_ROUTE + .1));
    head.castShadow = true; stem.castShadow = true;
    return g2;
  }
  function makePuck() {
    // الماشي: قرص أبيض بنواة بنفسجية وسهم صغير يدل على اتجاهه
    const g2 = new THREE.Group();
    g2.add(disc(8, whiteMat, Y_ROUTE + .2), disc(5.4, coreMat, Y_ROUTE + .3));
    const s = new THREE.Shape(); s.moveTo(0, -12.5); s.lineTo(4.2, -8); s.lineTo(-4.2, -8); s.lineTo(0, -12.5);
    const arrow = new THREE.Mesh(new THREE.ShapeGeometry(s), coreMat);
    arrow.rotation.x = -Math.PI / 2; arrow.position.y = Y_ROUTE + .25; arrow.renderOrder = 3;
    g2.add(arrow);
    return g2;
  }

  /* ---------- مكان واحد في الضوء: فريق يتصفّحه المرشد قبل أن يقبل طلبه ---------- */
  let focused = null;
  function focusPlace(id) {
    const p = placeById[id];
    if (!p || p.x === undefined) return;
    unfocus();
    if (current) return;   // طريق مرسوم يبقى هو الأهم
    const pin = makePin(); pin.position.set(p.x, 0, p.z);
    focused = pin; routeGroup.add(pin);
    markerK = 0;
    // الشيت يغطي نصف الشاشة السفلي: المكان يُرفع إلى ما فوقه
    // قريب بما يكفي ليُرى مكان الطاولة بين جاراتها، بعيد بما يكفي ليُعرف موقعها من القاعة
    const r = getRig(), d = 1100, phi = r.phi > .12 ? .6 : PHI_MIN;
    const k = d * .12;
    animateTo({ x: p.x + Math.sin(r.theta) * k, z: p.z + Math.cos(r.theta) * k, d, phi }, 900);
    venue.invalidate();
  }
  // يُظهر النقطة (x, z) داخل المساحة الظاهرة free = {l, t, r, b} بجانب شيت الفريق، بهامش — ولا يتحرّك إن كانت ظاهرة:
  // أفقيًا بإزاحة الكاميرا (الشيت الجانبي)، وعموديًا برفع الصورة فوق الشيت السفلي (الجوال).
  // null: أُغلق الشيت — تعود الصورة لمكانها. يستدعيه شيت الفريق (map:reveal)
  function reveal(d) {
    const lift = y => { view.yTo = Math.max(0, y); applyInsets(); };
    if (!d) { if (view.yTo) lift(0); return; }
    const { x, z, free } = d, p = venue.projectXZ(x, z, 0);
    // الهامش يصغر مع المساحة (فوق الشيت السفلي شريط قصير): لا يتجاوز ربعها
    const M = Math.min(72, (free.r - free.l) / 4, (free.b - free.t) / 4);
    const l = free.l + M, r = Math.max(l, free.r - M), t = free.t + M, b = Math.max(t, free.b - M);
    const bottomSheet = free.b < container.clientHeight - 1;
    // شيت سفلي بطول الشاشة تقريبًا (الجوال): لا مساحة تستحق رفع الصورة إليها
    if (bottomSheet && free.b - free.t < 160) { if (view.yTo) lift(0); return; }
    if (bottomSheet && p.visible && (p.y < t || p.y > b)) lift(view.y + p.y - (t + b) / 2);
    else if (!bottomSheet && view.yTo) lift(0);
    if (!p.visible || p.x >= l && p.x <= r) return;
    const H = ground(clamp(p.x, l, r), p.y), rig = getRig();
    if (H) animateTo({ x: rig.x + x - H.x, z: rig.z + z - H.z }, 600);
  }
  document.addEventListener('map:reveal', e => reveal(e.detail));
  function unfocus() {
    if (!focused) return;
    routeGroup.remove(focused); focused = null;
    venue.invalidate();
  }

  function clearRoute() {
    unfocus();
    stopJourney(false);
    routeGroup.clear();
    current = null;
    venue.routeEnds = null;
    venue.invalidate();
  }

  function showRoute(fromId, toId) {
    clearRoute();
    const from = placeById[fromId], to = placeById[toId];
    if (!from || !to || fromId === toId) return post({ type: 'route', ok: false });
    const route = computeRoute(fromId, toId);
    if (!route) return post({ type: 'route', ok: false });
    const line = smooth(route.pts);
    const geo = ribbon(line.pts, 8, Y_ROUTE);
    const mesh = new THREE.Mesh(geo, accentMat); mesh.renderOrder = 2;
    const startMarker = makeStartMarker(); startMarker.position.set(line.pts[0].x, 0, line.pts[0].z);
    const last = line.pts[line.pts.length - 1];
    const pin = makePin(); pin.position.set(last.x, 0, last.z);
    routeGroup.add(mesh, startMarker, pin);
    const steps = buildSteps(route, to);
    current = { route, line, geo, mesh, startMarker, pin, steps, total: route.total };
    // طرفا المسار لطبقة الشارات: لا تُغطّى علامة البداية ولا الدبوس باسم مكان
    venue.routeEnds = [{ x: line.pts[0].x, z: line.pts[0].z, get h() { return 12 * markerK; }, r: 8 },
      { x: last.x, z: last.z, get h() { return PIN_TOP * markerK; }, r: 6 }];
    markerK = 0;    // العلامتان الجديدتان تأخذان مقاسهما في الإطار التالي

    // يُرسم المسار من البداية إلى النهاية في لحظة — يقرأ كاتجاه لا كخط ثابت
    const count = geo.index.count;
    geo.setDrawRange(0, 0);
    const t0 = performance.now(), ms = 650;
    (function grow(now) {
      if (!current || current.geo !== geo) return;
      const k = Math.min(1, (now - t0) / ms);
      geo.setDrawRange(0, Math.floor(easeOut(k) * count / 6) * 6);
      venue.invalidate();
      if (k < 1) requestAnimationFrame(grow);
    })(t0);

    fitRoute(line.pts);
    post({
      type: 'route', ok: true, meters: meters(route.total),
      minutes: Math.max(1, Math.round(route.total / UNITS_PER_M / WALK_MPS / 60)),
      steps: steps.map(s => ({ icon: s.icon, text: s.text, meters: s.meters }))
    });
  }

  /* نظرة عامة على المسار كاملًا: نفس الاتجاه وميل خفيف، ونقطتا البداية والنهاية ظاهرتان دائمًا.
     لا تقدير بالأبعاد: الكاميرا تُجرَّب، وتُسقط نقاط المسار (والدبوس بارتفاعه) على الشاشة فعلًا،
     ثم تُزاح وتُبعَد حتى يقع المسار كله في الجزء المكشوف — بين البطاقة أعلاه والشريط أسفله
     وأزرار الخريطة جانبه، بالعرض وبالطول وعلى أي شاشة. */
  const PIN_TOP = 32;                                     // أعلى رأس الدبوس فوق الأرض (بمقاسه الأصلي)
  const probe = new THREE.PerspectiveCamera(), ray = new THREE.Raycaster(), floor = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
  function placeProbe(r) {
    probe.copy(cam);
    setOffset(probe, view.to, view.yTo);   // الإطار يُحسب على الإزاحة التي تنتهي إليها، لا التي في منتصف انزلاقها
    const sn = Math.sin(r.phi) * r.d;
    probe.position.set(r.x + sn * Math.sin(r.theta), r.d * Math.cos(r.phi), r.z + sn * Math.cos(r.theta));
    probe.lookAt(r.x, 0, r.z);
    probe.updateMatrixWorld();
  }
  // نقطة الأرض تحت بكسل الشاشة (من الكاميرا التجريبية)
  function probeGround(px, py, W, Hh) {
    ray.setFromCamera(new THREE.Vector2(px / W * 2 - 1, 1 - py / Hh * 2), probe);
    return ray.ray.intersectPlane(floor, new THREE.Vector3());
  }
  function routePose(pts, theta, phi) {
    // هامش يبعد الطرفين عن حواف المكشوف وما حولها من أزرار
    const W = container.clientWidth, Hh = container.clientHeight, M = clamp(Math.min(W, Hh) * .11, 36, 72);
    // الجزء المكشوف من الشاشة
    const box = {
      l: Math.max(insets.left, safe.left) + M, r: W - Math.max(insets.right, safe.right) - M,
      t: safe.top + M, b: Hh - safe.bottom - M
    };
    if (box.r - box.l < 80) { box.l = M; box.r = W - M; }
    if (box.b - box.t < 80) { box.t = M; box.b = Hh - M; }
    // عيّنة من المسار، ونقطتا الطرفين بارتفاع العلامتين
    const step = Math.max(1, Math.floor(pts.length / 120));
    const sample = pts.filter((p, i) => i % step === 0).map(p => new THREE.Vector3(p.x, 0, p.z));
    const a = pts[0], z = pts[pts.length - 1];
    const startTop = new THREE.Vector3(a.x, 12, a.z), pinTop = new THREE.Vector3(z.x, PIN_TOP, z.z);
    sample.push(startTop, new THREE.Vector3(z.x, 0, z.z), pinTop);
    // العلامتان تكبران مع المسافة: ارتفاعهما في كل تجربة بمقاسهما عندها
    const lift = d => { const k = markerScale(d); startTop.y = 12 * k; pinTop.y = PIN_TOP * k; };
    let x0 = Infinity, x1 = -Infinity, z0 = Infinity, z1 = -Infinity;
    pts.forEach(p => { x0 = Math.min(x0, p.x); x1 = Math.max(x1, p.x); z0 = Math.min(z0, p.z); z1 = Math.max(z1, p.z); });
    const tanV = Math.tan(cam.fov * Math.PI / 360);
    // طريق قصير لا يقرّب حتى تضيع القاعة حوله
    const dMin = Math.max(D_MIN, 220 / 2 / (tanV * Math.min(1, visibleAspect())) * 1.5);
    const r = { x: (x0 + x1) / 2, z: (z0 + z1) / 2, d: Math.max(dMin, Math.hypot(x1 - x0, z1 - z0) / tanV), phi, theta };
    const v = new THREE.Vector3();
    for (let i = 0; i < 40; i++) {
      r.d = clamp(r.d, D_MIN, D_MAX); r.x = clamp(r.x, B[0], B[2]); r.z = clamp(r.z, B[1], B[3]);
      placeProbe(r); lift(r.d);
      let sx0 = Infinity, sx1 = -Infinity, sy0 = Infinity, sy1 = -Infinity, behind = false;
      sample.forEach(p => {
        v.copy(p).project(probe);
        if (v.z > 1) behind = true;
        const sx = (v.x + 1) / 2 * W, sy = (1 - v.y) / 2 * Hh;
        sx0 = Math.min(sx0, sx); sx1 = Math.max(sx1, sx); sy0 = Math.min(sy0, sy); sy1 = Math.max(sy1, sy);
      });
      if (behind) { r.d *= 1.5; continue; }
      // ١) الإزاحة: منتصف المسار على الشاشة ← منتصف الجزء المكشوف
      const g1 = probeGround((sx0 + sx1) / 2, (sy0 + sy1) / 2, W, Hh), g2 = probeGround((box.l + box.r) / 2, (box.t + box.b) / 2, W, Hh);
      const shift = g1 && g2 ? Math.hypot(g1.x - g2.x, g1.z - g2.z) : 0;
      if (g1 && g2) { r.x += g1.x - g2.x; r.z += g1.z - g2.z; }
      // ٢) المسافة: نسبة حجم المسار على الشاشة إلى الجزء المكشوف
      const k = Math.max((sx1 - sx0) / (box.r - box.l), (sy1 - sy0) / (box.b - box.t));
      r.d *= Math.pow(k, .85);
      if (Math.abs(k - 1) < .01 && shift < r.d * .002) break;
    }
    // تحقّق أخير: إن بقي طرف خارج المكشوف (حدود الموقع منعت الإزاحة) نبتعد حتى يظهر
    for (let i = 0; i < 12; i++) {
      r.d = clamp(Math.max(r.d, dMin), D_MIN, D_MAX); r.x = clamp(r.x, B[0], B[2]); r.z = clamp(r.z, B[1], B[3]);
      placeProbe(r); lift(r.d);
      const out = sample.some(p => {
        v.copy(p).project(probe);
        const sx = (v.x + 1) / 2 * W, sy = (1 - v.y) / 2 * Hh;
        return v.z > 1 || sx < box.l - 2 || sx > box.r + 2 || sy < box.t - 2 || sy > box.b + 2;
      });
      if (!out) break;
      r.d *= 1.08;
    }
    return r;
  }
  // الاتجاه الذي اختاره الزائر بزرّ التدوير (القاعة بالعرض أو بالطول) — لا اتجاه آخر مرحلة من الرحلة
  function chosenTheta() {
    const v = venue.views && venue.views.perspective && venue.views.perspective();
    if (!v) return getRig().theta;
    const o = v.position.clone().sub(v.target);
    return Math.atan2(o.x, o.z);
  }
  function fitRoute(pts) {
    const r = getRig();
    animateTo(routePose(pts, chosenTheta(), r.phi > .12 ? .62 : PHI_MIN), 900);
  }

  /* =====================================================
     ٥) الرحلة بمراحل: لا نعرف موقع المرشد ولا سرعته، فلا نتظاهر بتتبّعه.
     كل مرحلة مقطع بين منعطفين؛ ينتقل بينها بنفسه، والعلامة تنزلق إلى بداية المقطع.
     ===================================================== */
  let journey = null;
  function startJourney() {
    if (!current) return;
    stopJourney(false);
    const puck = makePuck();
    routeGroup.add(puck);
    current.startMarker.visible = false;
    journey = { s: 0, step: 0, glide: null, puck, heading: null, started: false };
    placePuck(0);
    // دخول سلس إلى منظور الشخص الثالث خلف بداية المرحلة الأولى
    animateTo(chasePose(0, true), 1300, { done: () => { if (journey) journey.started = true; } });
    postStep();
  }
  // بداية المرحلة i على المسار: حيث انتهت التي قبلها.
  // وبعد آخر مرحلة محطة أخيرة: العلامة عند الدبوس نفسه — هناك فقط يقول «وصلت»
  const stepStart = i => i <= 0 ? 0 : i >= current.steps.length ? current.total : current.steps[i - 1].at;
  function goStep(i) {
    if (!journey || !current) return;
    i = clamp(i, 0, current.steps.length);
    if (i === journey.step) return;
    journey.step = i;
    const to = stepStart(i), from = journey.s;
    // انزلاق بطول المقطع، بين ثانية تقريبًا وثانيتين وربع
    const ms = clamp(Math.abs(to - from) / UNITS_PER_M * 70, 900, 2200);
    journey.glide = { from, to, t0: performance.now(), ms };
    journeyTouchedAt = 0;   // الكاميرا تعود لتتبع المرحلة الجديدة فورًا
    postStep();
  }
  function postStep() {
    post({ type: 'journey', step: journey.step, count: current.steps.length + 1 });
  }
  function dirAt(s) {
    const line = current.line, cum = line.cum;
    let i = 1; while (i < cum.length - 1 && cum[i] < s + 18) i++;
    const j = Math.max(0, i - 6), a = line.pts[j], b = line.pts[i];
    const l = len(a, b) || 1;
    return { x: (b.x - a.x) / l, z: (b.z - a.z) / l };
  }
  function pointAt(s) {
    const line = current.line, cum = line.cum;
    let i = 1; while (i < cum.length - 1 && cum[i] < s) i++;
    const a = line.pts[i - 1], b = line.pts[i], seg = cum[i] - cum[i - 1] || 1, t = clamp((s - cum[i - 1]) / seg, 0, 1);
    return { x: a.x + (b.x - a.x) * t, z: a.z + (b.z - a.z) * t, i };
  }
  function chasePose(s, fresh) {
    const p = pointAt(s), f = dirAt(s);
    const theta = Math.atan2(-f.x, -f.z);
    // خلف الماشي وفوقه بزاوية ملاحة (~٤٥°): يرى ما أمامه دون أن تحجبه جدران القاعة
    return { x: p.x + f.x * 45, z: p.z + f.z * 45, d: 330, phi: .8, theta: fresh || !journey || journey.heading === null ? theta : journey.heading };
  }
  function placePuck(s) {
    const p = pointAt(s), f = dirAt(s);
    journey.puck.position.set(p.x, 0, p.z);
    journey.puck.rotation.y = Math.atan2(f.x, f.z);
    // ما مشيته يُطوى: المسار يبدأ من موضع الماشي
    current.geo.setDrawRange(Math.max(0, (p.i - 1) * 6), current.geo.index.count);
  }
  function stopJourney(refit = true) {
    if (!journey) return;
    routeGroup.remove(journey.puck);
    journey = null;
    if (current) {
      current.startMarker.visible = true;
      current.geo.setDrawRange(0, current.geo.index.count);
      if (refit) fitRoute(current.line.pts);
    }
    venue.invalidate();
  }
  function stepJourney(dt, now) {
    if (!journey || !current || !journey.started) return;
    const g = journey.glide;
    if (g) {
      const k = Math.min(1, (now - g.t0) / g.ms);
      journey.s = g.from + (g.to - g.from) * easeInOut(k);
      if (k >= 1) journey.glide = null;
      placePuck(journey.s);
    }
    // الكاميرا تتبع ما لم يلمس المرشد الخريطة؛ تعود بعد ثلاث ثوانٍ من آخر لمسة
    if (now - journeyTouchedAt > 3000 && !anim && !pts.size) {
      const want = chasePose(journey.s, true), r = getRig();
      const k = 1 - Math.exp(-dt * 3);
      journey.heading = r.theta + wrap(want.theta - r.theta) * k;
      setRig({
        x: r.x + (want.x - r.x) * k, z: r.z + (want.z - r.z) * k,
        d: r.d + (want.d - r.d) * k, phi: r.phi + (want.phi - r.phi) * k, theta: journey.heading
      });
    }
  }

  /* ---------- حلقة واحدة: الحركات، القصور الذاتي، الرحلة ---------- */
  let lastFrame = performance.now();
  (function loop(now) {
    requestAnimationFrame(loop);
    const dt = Math.min(.05, (now - lastFrame) / 1000); lastFrame = now;
    stepOffset(now);
    if (anim) anim.step(now);
    if (inertia) {
      const r = getRig();
      r.x += inertia.v.x * dt * 1000; r.z += inertia.v.z * dt * 1000;
      const decay = Math.pow(.996, dt * 1000);
      inertia.v.x *= decay; inertia.v.z *= decay;
      setRig(r);
      if (Math.hypot(inertia.v.x, inertia.v.z) * 1000 < 4) inertia = null;
    }
    stepJourney(dt, now);
    scaleMarkers();
  })(lastFrame);

  /* ---------- علامتا البداية والنهاية بمقاس ثابت على الشاشة ----------
     بمقاسهما الحقيقي تصغران حتى تختفيا حين تبعد الكاميرا لترى القاعة كلها (جوال، قاعة بالطول):
     تكبران مع المسافة كدبابيس الخرائط، فيُرى طرفا المسار دائمًا */
  function scaleMarkers() {
    const k = markerScale(cam.position.distanceTo(controls.target));
    if (Math.abs(k - markerK) < .01) return;
    markerK = k;
    [current && current.startMarker, current && current.pin, focused].forEach(o => o && o.scale.setScalar(k));
    venue.invalidate();
  }

  /* ---------- الجزء الظاهر من الشاشة ----------
     لوحة جانبية (آيفون Duo مفتوحًا) تغطي جزءًا من الخريطة: نزيح مركز الإسقاط
     فتتمركز القاعة والمسار في الجزء الظاهر، كخرائط Apple على الآيباد. */
  const insets = { left: 0, right: 0 };
  // ما يغطي الخريطة دون إزاحة المشهد (البطاقة فوق، الشريط تحت، أزرار الخريطة جانبًا): يحسبه إطار المسار فقط
  const safe = { top: 0, bottom: 0, left: 0, right: 0 };
  // الإزاحة تنزلق مع حركة الكاميرا (لا قفزة حين تظهر البطاقة أو تختفي)؛ view.to هدفها الذي يُحسب عليه الإطار
  function setOffset(cameraLike, x, y = 0) {
    const W = container.clientWidth, Hh = container.clientHeight;
    if (Math.abs(x) > .25 || Math.abs(y) > .25) cameraLike.setViewOffset(W, Hh, x, y, W, Hh);
    else cameraLike.clearViewOffset();
    cameraLike.updateProjectionMatrix();
  }
  function applyInsets(animate = true) {
    view.to = (insets.right - insets.left) / 2;
    if (!animate || matchMedia('(prefers-reduced-motion: reduce)').matches) { view.x = view.to; view.y = view.yTo; view.t0 = 0; setOffset(cam, view.x, view.y); }
    else { view.from = view.x; view.yFrom = view.y; view.t0 = performance.now(); }
    venue.invalidate();
  }
  function stepOffset(now) {
    if (!view.t0) return;
    const k = Math.min(1, (now - view.t0) / view.ms);
    view.x = view.from + (view.to - view.from) * easeInOut(k);
    view.y = view.yFrom + (view.yTo - view.yFrom) * easeInOut(k);
    if (k === 1) view.t0 = 0;
    setOffset(cam, view.x, view.y);
    venue.invalidate();
  }
  addEventListener('resize', () => applyInsets(false));
  // نسبة الجزء الظاهر لا الشاشة كلها — لحساب المسافة التي تتسع للقاعة أو للمسار
  const visibleAspect = () => {
    const W = container.clientWidth, Hh = container.clientHeight;
    return Math.max(.2, (W - insets.left - insets.right) / Hh);
  };

  /* ---------- البداية: الجوال عمودي، القاعة بطول الشاشة ---------- */
  function homePose() {
    const tanV = Math.tan(cam.fov * Math.PI / 360), aspect = visibleAspect();
    const portrait = aspect < 1;
    const [w, h] = portrait ? [site.extent[1], site.extent[0]] : site.extent;
    const d = Math.max(w / 2 / (tanV * aspect), h / 2 / tanV) * (site.perspectiveScale || 1);
    return { x: site.center[0], z: site.center[1], d, phi: PHI_3D, theta: portrait ? THETA_HOME : 0 };
  }

  const listPlaces = () => places.map(p => ({ id: p.id, kind: p.kind, name: p.name, sub: p.sub || '', aliases: p.aliases || [], code: p.code || null, n: p.n || null }));
  post({ type: 'places', items: listPlaces() });

  return {
    setPitch3D(on) {
      animateTo({ phi: on ? PHI_3D : PHI_MIN, d: getRig().d * (on ? .9 : 1.1) }, 700);
    },
    resetHeading() { animateTo({ theta: THETA_HOME }, 600); },
    // الجزء المغطّى من الشاشة بالبكسل؛ تتغيّر مع الطيّ والفتح فتعود القاعة لتملأ ما ظهر
    setInsets(left, right, cover = {}) {
      const next = { top: 0, bottom: 0, left: 0, right: 0, ...cover };
      const same = insets.left === left && insets.right === right && ['top', 'bottom', 'left', 'right'].every(k => Math.abs(safe[k] - next[k]) < 2);
      if (same) return;
      const moved = insets.left !== left || insets.right !== right;
      insets.left = left; insets.right = right; Object.assign(safe, next);
      if (moved) applyInsets();
      if (current && !journey) fitRoute(current.line.pts);
    },
    // الفرق تنتقل بين الطاولات في طبقة الأدمن: الفهرس يُعاد بناؤه قبل كل بحث
    reindex() { buildIndex(); post({ type: 'places', items: listPlaces() }); },
    place: id => placeById[id] || null,
    get busy() { return !!current; },
    route: showRoute,
    // تدوير زاوية النظر والمسار معروض: يُعاد تأطيره بالاتجاه الجديد
    refit(theta) {
      if (!current || journey) return;
      const r = getRig();
      animateTo(routePose(current.line.pts, theta, r.phi > .12 ? .62 : PHI_MIN), 900);
    },
    clearRoute,
    focus: focusPlace,
    unfocus,
    startJourney,
    goStep,
    stopJourney: () => stopJourney(true)
  };
}
