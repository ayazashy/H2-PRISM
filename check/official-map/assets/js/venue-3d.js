/* =========================================================
   محرّك موقع الحدث ثلاثي الأبعاد — Three.js
   مشترك بين المواقع: الكاميرا والإضاءة والتحكّم والطيران إلى الشاشة
   ومحتوى العرض الحيّ. كل موقع (assets/js/sites/*.js) يصف هندسته فقط
   بأدوات البناء هنا، بإحداثيات مخططه: X = x المخطط، Z = y، Y للأعلى.
   الطابع: سلّم --venue-* المحايد، إضاءة ناعمة، حواف مستديرة، بلا خطوط.
   ========================================================= */
import * as THREE from '../vendor/three/three.module.min.js';
import { OrbitControls } from '../vendor/three/OrbitControls.js';
import { RoundedBoxGeometry } from '../vendor/three/RoundedBoxGeometry.js';

const FALLBACK_TONES = {
  100: '#FFFFFF', 98: '#FAFAFA', 97: '#F7F7F8', 96: '#F4F4F5', 95: '#F1F1F3',
  94: '#EEEEF0', 93: '#EBEBED', 92: '#E8E8EA', 91: '#E5E5E8', 90: '#E2E2E5',
  88: '#DEDEE1', 87: '#DADADD', 85: '#D6D6DA', 83: '#D1D1D5', 81: '#CDCDD1', 80: '#C9C9CD',
};
const toneHex = n => {
  const v = getComputedStyle(document.documentElement).getPropertyValue('--venue-' + n).trim();
  return v || FALLBACK_TONES[n] || '#EAEAEF';
};
const tone = n => new THREE.Color(toneHex(n));
const mat = (n, extra) => new THREE.MeshStandardMaterial(Object.assign({ color: tone(n), roughness: .9, metalness: 0 }, extra));

export function createVenue3D(container, site) {
  /* ---------- المشهد والكاميرا ---------- */
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true });
  // دقة الرسم: كاملة عند الثبات، ومخفّضة أثناء الحركة (السحب/الطيران) لتبقى سلسة
  const restDpr = Math.min(devicePixelRatio || 1, site.maxDpr || 2), moveDpr = Math.min(restDpr, site.moveDpr || 1.25);
  renderer.setPixelRatio(restDpr);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.domElement.className = 'venue-3d';
  renderer.domElement.setAttribute('role', 'img');
  renderer.domElement.setAttribute('aria-label', site.label);
  container.prepend(renderer.domElement);

  const scene = new THREE.Scene();
  const bg = tone(98);
  scene.background = bg;
  scene.fog = new THREE.Fog(bg, 3000, 9000);

  const camera = new THREE.PerspectiveCamera(35, 1, 4, 30000);
  const CENTER = new THREE.Vector3(site.center[0], 0, site.center[1]);

  /* ---------- الإضاءة: سماء بيضاء + شمس ناعمة بظلال ---------- */
  scene.add(new THREE.HemisphereLight(tone(100), tone(88), 1.55));
  const sun = new THREE.DirectionalLight(tone(100), 1.35);
  sun.position.copy(CENTER).add(new THREE.Vector3(...site.sun));
  sun.target.position.copy(CENTER);
  sun.castShadow = true;
  sun.shadow.mapSize.set(site.shadowMap || 4096, site.shadowMap || 4096);
  const S = site.shadow;
  // ds-allow: rtl-logical-props — حدود مخروط ظل كاميرا Three.js، ليست خصائص CSS
  Object.assign(sun.shadow.camera, { left: -S[0], right: S[0], top: S[1], bottom: -S[1], near: 100, far: 8000 });
  sun.shadow.bias = -.0004;
  sun.shadow.normalBias = 1.2;
  scene.add(sun, sun.target);

  /* ---------- أدوات البناء (تُمرَّر للموقع) ---------- */
  const add = (mesh, cast = true) => { mesh.castShadow = cast; mesh.receiveShadow = true; scene.add(mesh); return mesh; };
  const rgeo = (w, h, d, r, seg = 2) => new RoundedBoxGeometry(w, h, d, seg, Math.max(.01, Math.min(r, w / 2 - .01, h / 2 - .01, d / 2 - .01)));
  // صندوق مستدير: ركنه (x0, z0) على المخطط، وقاعدته عند y0
  const block = (x0, z0, w, d, y0, h, material, r = 2, cast = true) => {
    const m = new THREE.Mesh(rgeo(w, h, d, r), material);
    m.position.set(x0 + w / 2, y0 + h / 2, z0 + d / 2);
    return add(m, cast);
  };
  // شكل مسطّح من نقاط المخطط يُرفع عموديًا
  const extrude = (pts, height, materials, y0 = 0, bevel = 1.2) => {
    const shape = new THREE.Shape(pts.map(([x, z]) => new THREE.Vector2(x, -z)));
    const g = new THREE.ExtrudeGeometry(shape, { depth: height - bevel * 2, bevelEnabled: bevel > 0, bevelSize: bevel, bevelThickness: bevel, bevelSegments: 2 });
    g.rotateX(-Math.PI / 2);
    g.translate(0, y0 + bevel, 0);
    return add(new THREE.Mesh(g, materials));
  };
  // نسخ متعدّدة لنفس الشكل (كراسي، طاولات…) في استدعاء رسم واحد: [x, y, z, دوران حول Y]
  // cast = false للقطع الصغيرة الكثيرة: تمريرة الظل تعيد رسم كل مثلّث
  const instanced = (geometry, material, transforms, cast = true) => {
    const mesh = new THREE.InstancedMesh(geometry, material, transforms.length);
    const o = new THREE.Object3D();
    transforms.forEach((t, i) => {
      o.position.set(t[0], t[1], t[2]); o.rotation.set(0, t[3] || 0, 0); o.updateMatrix();
      mesh.setMatrixAt(i, o.matrix);
    });
    return add(mesh, cast);
  };
  const textures = [];
  const canvasTexture = (w, h, paint) => {
    const c = document.createElement('canvas'); c.width = w; c.height = h;
    paint(c.getContext('2d'), w, h);
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
    t.userData.repaint = () => { paint(c.getContext('2d'), w, h); t.needsUpdate = true; };
    textures.push(t);
    return t;
  };
  // سطح شاشة محايد: تدرّج بأفق مضيء وخطوط ضوء، ونص اختياري في المنتصف
  const screenTexture = (lines) => canvasTexture(1536, 600, (g, w, h) => {
    const grad = g.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, toneHex(85)); grad.addColorStop(.5, toneHex(91)); grad.addColorStop(.6, toneHex(96));
    grad.addColorStop(.68, toneHex(90)); grad.addColorStop(1, toneHex(85));
    g.fillStyle = grad; g.fillRect(0, 0, w, h);
    let seed = 7; const rnd = () => (seed = (seed * 9301 + 49297) % 233280) / 233280;
    g.fillStyle = toneHex(100); g.globalAlpha = .55;
    for (let i = 0; i < 70; i++) { g.beginPath(); g.roundRect(rnd() * w, 40 + rnd() ** 1.6 * 230, 14 + rnd() * 50, 4, 2); g.fill(); }
    for (let i = 0; i < 9; i++) g.fillRect(0, 380 + (i / 8) ** 1.7 * 200, w, 2 + i * .4);
    g.globalAlpha = 1;
    if (!lines) return;
    g.fillStyle = toneHex(98); g.textAlign = 'center';
    const font = getComputedStyle(document.body).fontFamily || '"IBM Plex Sans Arabic", system-ui, sans-serif';
    g.font = '700 74px ' + font; g.fillText(lines[0], w / 2, 250);
    if (lines[1]) { g.font = '600 44px ' + font; g.fillText(lines[1], w / 2, 312); }
  });
  const glow = map => new THREE.MeshStandardMaterial({ map, roughness: .6, emissive: tone(100), emissiveIntensity: .08, emissiveMap: map });
  const frame = mat(90);

  // الشاشة الرئيسية: وجهها نحو +Z، ويُستبدل نسيجها بمحتوى العرض الحيّ
  const screenMat = glow(null);
  let SCREEN = null;
  function mainScreen({ x, z, w, h, y, depth = 12, r = 3, idle }) {
    screenMat.map = screenMat.emissiveMap = idle; screenMat.needsUpdate = true;
    const m = new THREE.Mesh(rgeo(w, h, depth, r), [frame, frame, frame, frame, screenMat, frame]);
    m.position.set(x, y + h / 2, z);
    SCREEN = { x, z: z + depth / 2, w, h, y };
    return add(m);
  }

  /* ---------- طاولات الفرق: نسخ تُلوَّن وتُلتقط ----------
     لون كل نسخة يضرب لون المادة؛ المادة والحياد أبيض كقماش الطاولة،
     فطبقات الأدمن تلوّن الطاولة نفسها بدل رسم شيء فوقها. */
  const NEUTRAL = tone(100);
  let teamMesh = null, teamList = [];
  function teamTables(geometry, list) {
    teamList = list;
    teamMesh = instanced(geometry, mat(100), list.map(t => [t.x, t.y, t.z, t.r || 0]));   // r: دوران الطاولة حول Y
    list.forEach((t, i) => teamMesh.setColorAt(i, NEUTRAL));
    teamMesh.instanceColor.needsUpdate = true;
    return teamMesh;
  }
  // كراسي الفرق: perTable كرسي (وظهره) لكل طاولة بترتيب الطاولات نفسه — لونها لون مسار الفريق
  const SEAT = tone(81), BACK = tone(80);
  let seatMesh = null, backMesh = null, perTable = 0;
  function teamSeats(seatGeo, seats, backGeo, backs, n) {
    perTable = n;
    seatMesh = instanced(seatGeo, mat(100), seats, false);
    backMesh = instanced(backGeo, mat(100), backs, false);
    seats.forEach((t, i) => { seatMesh.setColorAt(i, SEAT); backMesh.setColorAt(i, BACK); });
    seatMesh.instanceColor.needsUpdate = backMesh.instanceColor.needsUpdate = true;
  }
  // حلقتان على الأرض تحت الطاولة: المختارة، والتي تحت المؤشر
  const ring = (inner, outer, opacity) => {
    const m = new THREE.Mesh(new THREE.RingGeometry(inner, outer, 48),
      new THREE.MeshBasicMaterial({ color: tone(100), transparent: true, opacity, depthWrite: false }));
    m.rotation.x = -Math.PI / 2; m.visible = false; m.renderOrder = 2;
    scene.add(m); return m;
  };
  // نصف قطر الحلقة من الموقع: طاولة هاكاثون أو جناح معرض صغير
  const R = site.ring || 13.5;
  const markers = { select: ring(R, R + 3, 1), hover: ring(R, R + 1.5, .55) };

  const kit = { THREE, add, rgeo, block, extrude, instanced, canvasTexture, screenTexture, glow, mat, tone, toneHex, frame, mainScreen, teamTables, teamSeats };
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(40000, 40000), mat(97));
  ground.rotation.x = -Math.PI / 2;
  add(ground, false);
  site.build(kit);

  /* ---------- التحكّم: سحب للتحريك، زر أيمن للتدوير، عجلة للتقريب حول المؤشر ---------- */
  const controls = new OrbitControls(camera, renderer.domElement);
  Object.assign(controls, {
    enableDamping: true, dampingFactor: .09, screenSpacePanning: false, zoomToCursor: true,
    minDistance: site.minDistance || 45, maxDistance: 6000, maxPolarAngle: 1.46, rotateSpeed: .55, zoomSpeed: 1.1
  });
  controls.mouseButtons = { LEFT: THREE.MOUSE.PAN, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.ROTATE };
  controls.touches = { ONE: THREE.TOUCH.PAN, TWO: THREE.TOUCH.DOLLY_ROTATE };
  controls.listenToKeyEvents(window);
  // نقطة النظر تبقى داخل حدود الموقع أفقيًا (ارتفاعها حرّ: وقفة الشاشة تنظر لمنتصفها)
  const B = site.bounds;
  controls.addEventListener('change', () => {
    const t = controls.target;
    const cx = THREE.MathUtils.clamp(t.x, B[0], B[2]), cz = THREE.MathUtils.clamp(t.z, B[1], B[3]);
    if (cx !== t.x || cz !== t.z) {
      camera.position.add(new THREE.Vector3(cx - t.x, 0, cz - t.z));
      t.set(cx, t.y, cz);
    }
  });

  let moving = 0;
  const setMoving = on => {
    moving = Math.max(0, moving + (on ? 1 : -1));
    const dpr = moving ? moveDpr : restDpr;
    if (renderer.getPixelRatio() !== dpr) { renderer.setPixelRatio(dpr); resize(); }
  };
  controls.addEventListener('start', () => setMoving(true));
  // بعد ترك المؤشر يستمرّ التخميد قليلًا؛ نعيد الدقة بعد سكونه
  let settle = 0;
  controls.addEventListener('end', () => { clearTimeout(settle); settle = setTimeout(() => setMoving(false), 450); });

  /* ---------- الوضعيات وحركة الكاميرا ---------- */
  const tanV = () => Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
  // مسافة تُظهر مستطيلًا بعرض w وعمق h كاملًا
  const fit = (w, h) => Math.max(w / 2 / (tanV() * camera.aspect), h / 2 / tanV());
  const pose = (target, polar, azimuth, distance) =>
    ({ position: new THREE.Vector3().setFromSphericalCoords(distance, polar, azimuth).add(target), target: target.clone() });
  // اتجاه النظر: بالعرض (من الجنوب) أو بالطول (من الشرق، فتمتد القاعة رأسيًا على الشاشة)
  const orient = { tall: !!site.startTall };   // site.startTall: البداية بالطول (الجوال — map.js)
  const turnAz = () => orient.tall ? Math.PI / 2 : 0;
  const ext = () => orient.tall ? [site.extent[1], site.extent[0]] : site.extent;
  const views = {
    // site.tallZoom: مسافة إضافية للقاعة بالطول في الجوال (map.js) — تظهر بهامش أوسع حولها
    perspective: () => pose(CENTER, site.polar || .88, turnAz(), fit(...ext()) * (site.perspectiveScale || 1) * (orient.tall && site.tallZoom || 1)),
    top: () => pose(CENTER, .0001, turnAz(), fit(...ext()) * 1.05),
    screen: () => {
      const target = new THREE.Vector3(SCREEN.x, SCREEN.y + SCREEN.h / 2, SCREEN.z);
      // الشاشة بنحو 72٪ من العرض: يظهر حولها المسرح، فالوقفة داخل المشهد
      const d = Math.max(SCREEN.w / .72 / 2 / (tanV() * camera.aspect), SCREEN.h / .62 / 2 / tanV());
      return { position: target.clone().add(new THREE.Vector3(0, 0, d)), target };
    }
  };
  let flight = null, dirty = true, tween = null;
  const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  function fly(to, done, instant) {
    const from = { position: camera.position.clone(), target: controls.target.clone() };
    const distance = from.position.distanceTo(to.position) + from.target.distanceTo(to.target);
    const duration = instant || matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : Math.min(2200, 700 + 380 * Math.log1p(distance / 400));
    controls.enabled = false;
    if (duration) setMoving(true);
    const finish = done;
    done = () => { if (duration) setMoving(false); if (finish) finish(); };
    flight = { from, to, start: null, duration, done };   // البداية من أول إطار: ساعة rAF وحدها
  }
  const current = () => ({ position: camera.position.clone(), target: controls.target.clone() });

  /* ---------- الحلقة: رسم عند الحاجة فقط ---------- */
  const listeners = new Set();
  function resize() {
    const w = Math.max(1, container.clientWidth), h = Math.max(1, container.clientHeight);
    renderer.setSize(w, h);
    camera.aspect = w / h; camera.updateProjectionMatrix(); dirty = true;
  }
  addEventListener('resize', resize);
  if (typeof ResizeObserver !== 'undefined') new ResizeObserver(resize).observe(container);
  resize();
  const start = views.perspective();
  camera.position.copy(start.position); controls.target.copy(start.target); controls.update();

  function frameLoop(now) {
    requestAnimationFrame(frameLoop);
    if (tween) {
      if (tween.start === null) tween.start = now;
      const t = Math.min(1, (now - tween.start) / tween.duration), e = ease(t), c = new THREE.Color();
      tween.to.forEach((to, i) => teamMesh.setColorAt(i, c.lerpColors(tween.from[i], to, e)));
      teamMesh.instanceColor.needsUpdate = true;
      dirty = true;
      if (t === 1) tween = null;
    }
    if (flight) {
      if (flight.start === null) flight.start = now;
      const t = flight.duration ? Math.min(1, Math.max(0, (now - flight.start) / flight.duration)) : 1, e = ease(t);
      camera.position.lerpVectors(flight.from.position, flight.to.position, e);
      controls.target.lerpVectors(flight.from.target, flight.to.target, e);
      camera.lookAt(controls.target);
      camera.updateMatrixWorld();
      dirty = true;
      if (t === 1) { const done = flight.done; flight = null; controls.enabled = true; controls.update(); if (done) done(); }
    } else if (controls.update()) dirty = true;
    if (!dirty) return;
    dirty = false;
    const dist = camera.position.distanceTo(controls.target);
    scene.fog.near = dist * 1.4; scene.fog.far = dist * 4.5;
    renderer.render(scene, camera);
    listeners.forEach(fn => fn());
  }
  requestAnimationFrame(frameLoop);
  // الخط العربي يُحمَّل لاحقًا: نعيد رسم النسج التي فيها نص
  if (document.fonts) document.fonts.ready.then(() => { textures.forEach(t => t.userData.repaint()); dirty = true; });

  const api = {
    renderer, camera, controls, views, fly, current, orient,
    // المشهد مكشوف لطبقة التنقّل (venue-nav.js) لترسم الممرات والمسار فيه
    scene,
    get screenAnchor() { return new THREE.Vector3(SCREEN.x, SCREEN.y + SCREEN.h + (site.anchorLift || 24), SCREEN.z); },
    onRender: fn => listeners.add(fn),
    // محتوى العرض الحيّ على وجه الشاشة الرئيسية
    setScreenImage(image) {
      const t = new THREE.CanvasTexture(image);
      t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
      if (screenMat.userData.live) screenMat.map.dispose();
      screenMat.userData.live = true;
      screenMat.map = t; screenMat.emissiveMap = t; screenMat.emissiveIntensity = .35; screenMat.roughness = .45;
      screenMat.needsUpdate = true; dirty = true;
    },
    // مستطيل وجه الشاشة على الصفحة (بكسل CSS)
    screenRect() {
      camera.updateMatrixWorld();
      const xs = [], ys = [];
      [[-1, 0], [1, 0], [1, 1], [-1, 1]].forEach(([sx, sy]) => {
        const p = new THREE.Vector3(SCREEN.x + sx * SCREEN.w / 2, SCREEN.y + sy * SCREEN.h, SCREEN.z).project(camera);
        xs.push((p.x + 1) / 2 * container.clientWidth); ys.push((1 - p.y) / 2 * container.clientHeight);
      });
      const x = Math.min(...xs), y = Math.min(...ys);
      return { x, y, width: Math.max(...xs) - x, height: Math.max(...ys) - y };
    },
    project(v) {
      const p = v.clone().project(camera);
      return { x: (p.x + 1) / 2 * container.clientWidth, y: (1 - p.y) / 2 * container.clientHeight, visible: p.z > -1 && p.z < 1 };
    },
    // نقطة على المخطط (x, y, z) ← موضعها على الصفحة
    projectXZ(x, z, y = 0) { return this.project(new THREE.Vector3(x, y, z)); },
    // موضع المؤشر على أرضية المخطط، أو null إن لم يقع الشعاع عليها
    groundPoint(clientX, clientY, y = 3.9) {
      const r = renderer.domElement.getBoundingClientRect();
      const ray = new THREE.Raycaster();
      ray.setFromCamera(new THREE.Vector2((clientX - r.left) / r.width * 2 - 1, -(clientY - r.top) / r.height * 2 + 1), camera);
      const hit = ray.ray.intersectPlane(new THREE.Plane(new THREE.Vector3(0, 1, 0), -y), new THREE.Vector3());
      return hit ? { x: hit.x, z: hit.z } : null;
    },
    // الكاميرا تقترب من نقطة وتحافظ على زاوية النظر الحالية
    focus(x, z, distance) {
      const s = new THREE.Spherical().setFromVector3(camera.position.clone().sub(controls.target));
      s.radius = distance || Math.min(s.radius, 360);
      const target = new THREE.Vector3(x, 0, z);
      fly({ position: new THREE.Vector3().setFromSpherical(s).add(target), target });
    },
    tables: {
      get list() { return teamList; },
      // أقرب طاولة لنقطة المؤشر، ضمن هامش يسامح النقر على الكراسي حولها
      pick(clientX, clientY) {
        const p = this.ground(clientX, clientY);
        if (!p) return -1;
        let best = -1, bestD = Infinity;
        const [hx, hz] = site.pick || [13, 10];
        teamList.forEach((t, i) => {
          const dx = Math.abs(t.x - p.x), dz = Math.abs(t.z - p.z);
          if (dx < hx && dz < hz && dx + dz < bestD) { best = i; bestD = dx + dz; }
        });
        return best;
      },
      ground: null,
      // colors[i]: لون CSS أو null للحياد؛ الانتقال بين الألوان ناعم ما لم تُطلب الحركة المخفّضة
      paint(colors, animate = true) {
        if (!teamMesh) return;
        const from = [], to = [];
        teamList.forEach((t, i) => {
          const c = new THREE.Color(); teamMesh.getColorAt(i, c); from.push(c);
          to.push(colors[i] ? new THREE.Color(colors[i]) : NEUTRAL);
        });
        if (!animate || matchMedia('(prefers-reduced-motion: reduce)').matches) {
          to.forEach((c, i) => teamMesh.setColorAt(i, c));
          teamMesh.instanceColor.needsUpdate = true; tween = null; dirty = true;
          return;
        }
        tween = { from, to, start: null, duration: 420 };
      },
      // colors[i]: لون مسار فريق الطاولة i، أو null لكراسي محايدة؛ الظهر أغمق قليلًا من المقعد
      seats(colors) {
        if (!seatMesh) return;
        const c = new THREE.Color(), b = new THREE.Color();
        colors.forEach((col, i) => {
          if (col) { c.set(col); b.copy(c).multiplyScalar(.82); } else { c.copy(SEAT); b.copy(BACK); }
          for (let k = 0; k < perTable; k++) { seatMesh.setColorAt(i * perTable + k, c); backMesh.setColorAt(i * perTable + k, b); }
        });
        seatMesh.instanceColor.needsUpdate = backMesh.instanceColor.needsUpdate = true;
        dirty = true;
      },
      // kind: select | hover · index = -1 يخفي العلامة · color: لون CSS
      mark(kind, index, color) {
        const m = markers[kind], t = teamList[index];
        m.visible = !!t;
        if (t) { m.position.set(t.x, 1.2, t.z); if (color) m.material.color.set(color); }
        dirty = true;
      }
    },
    invalidate() { dirty = true; }
  };
  api.tables.ground = api.groundPoint.bind(api);
  return api;
}
