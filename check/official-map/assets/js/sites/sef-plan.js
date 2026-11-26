/* =========================================================
   مخطط معرض سيف — القاعة 4 (من «مخطط الموقع 1999-Model»، تصدير أوتوكاد —
   آخر تحديث: المسرح بعرض 38 م، وقاعات الجهات بين المسرح والأجنحة، وشرائح الأجنحة؛
   ثم «مخطط الموقع 250»: الفود تراكس شرقًا، ووزارة الداخلية بجانب طويق)
   كل المقاسات بالمتر، مقيسة من الرسم نفسه: مقياسه من المسرح المكتوب
   عليه 40 × 67 م (2680 م²). الأصل: الركن الشمالي الغربي من داخل القاعة،
   X شرقًا (يمين الرسم) و Z جنوبًا (أسفله، نحو الممر والمداخل).
   الوحدة في المشهد: المتر = 11 وحدة — نفس مقياس محرّك التنقّل.
   ========================================================= */
import { tr } from '../i18n.js';

export const U = 11;
export const X0 = 100, Z0 = 200;
export const ux = m => X0 + m * U;           // متر ← وحدة مشهد
export const uz = m => Z0 + m * U;

// داخل القاعة (الجدار الغربي زجاجي، وشمالًا صفّ أعمدة إنشائية)، ثم شريط الغرف الخدمية،
// ثم الممر (Concourse) خارج المعرض
// الجدار الشرقي عند 193.5 م (المخطط الأصلي): بين آخر الأجنحة (188) والجدار صفّ بوثات وبوابات
export const HALL = { x0: -3.9, w: 197.4, z0: -6.9, d: 68 };
// أعمدة إنشائية كبيرة على الجدار الشمالي (المخطط الأصلي): كل 12 م على شبكة الشريط الخدمي،
// كتلة 2.2 × 5.7 م بارزة من الجدار — بينها «خانات» فيها المقاهي والشاشات والبوثات والمصليات
export const COLUMNS = { z0: -6.9, z1: -1.2, w: 2.2, xs: Array.from({ length: 17 }, (_, i) => -0.85 + i * 12) };
// الخانة بين العمودين اللذين مركزاهما c و c+12 (من وجه العمود إلى وجه الآخر)
const bay = c => ({ x0: c + COLUMNS.w / 2, x1: c + 12 - COLUMNS.w / 2 });
// شريط الخدمات (بين القاعة والممر) والممر الخارجي (Concourse) وصفّه الجنوبي — مقيسة من نصّ
// المخطط وخطوطه: الشريط مقسوم على شبكة الأعمدة كل 12 م، والمداخل الأربعة تعبره في أربع من خاناته
export const BAND = { z0: 68.1, z1: 74.2 };
export const CONCOURSE = { z0: 74.2, z1: 86, x0: -12, x1: 203 };
export const SOUTH = { z0: 86, z1: 92 };

// مداخل المعرض من الممر (ENTRANCE TO EXHIBITION 4 … 1 من الغرب للشرق)
export const ENTRANCES = [
  { n: 4, x: 29.1 }, { n: 3, x: 64.9 }, { n: 2, x: 101.1 }, { n: 1, x: 136.9 }
];
export const ENTRANCE_W = 4;                     // بوابة دخول وخروج بعرض 3 م تقريبًا
// غرف العزل (Air Lock) على الجدار الغربي الزجاجي، وأبواب الجدار الشرقي — مخارج طوارئ
// الشرقية الأربعة (مخطط الموقع 250): بين مجموعات الفود تراكس خارج الجدار
export const EXITS = { west: [10.4, 22.1, 43.1, 55.4], east: [11.4, 26.05, 41.2, 56.15] };
/* ---------- خارج الجدار الشرقي: ساحة الفود تراكس (مخطط الموقع 250) ----------
   ثلاث مجموعات بين أبواب الطوارئ، في كل مجموعة 4 عربات خلف كاونتر طولي يواجه الجدار.
   groups: امتداد كل مجموعة شمالًا وجنوبًا (z) */
export const OUTSIDE = { x0: 194.4, x1: 203 };
export const FOOD_TRUCKS = { counter: [196.4, 196.8], body: [197.2, 201.2], groups: [[14, 22], [29.3, 37.4], [44, 52.1]], per: 4 };

/* ---------- ملاحظات «مخطط الموقع 250» على الجدارين الشمالي والشرقي ---------- */
// الشرقي: البوابات الأربع (دهليز بين الجدار والممر عند كل باب)، وبينها 4 صفوف من 6 بوثات على الجدار
export const EAST_GATES = { x0: 190.8, x1: 193.5, half: 2.4 };
// والصفّ الخامس شمال البوابة الأولى، بين العمود الركني والبوابة
export const EAST_BOOTHS = { x0: 191.5, x1: 193.5, per: 6, blocks: [[-0.9, 8.7], [14.2, 23.4], [29.2, 38.7], [44.5, 53.5], [59.2, 67.6]] };
// الشمالي، في الخانات بين الأعمدة (من الغرب للشرق)
export const NORTH = { z0: HALL.z0, z1: COLUMNS.z1 };
export const CAFES = { ...bay(71.15), list: [
  { id: 'maps', name: 'MAPS', en: 'MAPS', color: '--sef-cafe-maps', x: 73.8, z: -3.1, aliases: ['ماپس', 'مابس', 'maps', 'roastery', 'مقهى', 'المقاهي', 'مقاهي', 'كوفي'] },
  { id: 'dunkin', name: 'دانكن', en: 'Dunkin', color: '--sef-cafe-dunkin', x: 77.9, z: -4.6, aliases: ['دانكن', 'دنكن', 'dunkin', 'donuts', 'دونات', 'مقهى', 'المقاهي', 'مقاهي', 'كوفي'] },
  { id: 'brew92', name: 'BREW92', en: 'BREW92', color: '--sef-cafe-brew', x: 81, z: -2.8, aliases: ['برو', 'برو92', 'brew', 'brew92', 'brew 92', 'مقهى', 'المقاهي', 'مقاهي', 'كوفي'] }
] };
// المقاهي كما في صور الموقع (من الغرب للشرق): MAPS كاونتر أزرق مستدير بمظلّة على قائمتين وقطعة جانبية،
// ودانكن على الجدار (خزانة عرض زجاجية، كاونتر خشبي، لافتة على قائمتين)، وBREW92 هيكل أزرق على شكل L بلوحات بيضاء أعلاه؛
// ثلاجة مياه ورفّ وجبات خفيفة أمام كل عمود. x, z: مكان الوقوف أمام كل مقهى (للبحث والتنقّل)
// الشاشات: شاشة LED على هيكل أسود كما في الموقع
export const SCREENS = [89.15, 125.15, 161.15].map(x => ({ x, w: 5.6, h: 3.36, y: 2.6 }));   // بنسبة صورتها 5:3
// صفّا البوثات الملاصقة للجدار (7 بوثات، بلا ظهر)
export const WALL_BOOTHS = [{ ...bay(107.15), per: 7 }, { ...bay(143.15), per: 7 }];
// المصلّيان: النساء غرفة مغلقة مسقوفة، والرجال مساحة مفتوحة على الأرض (بممرّ لباب دورات المياه بجانبها)
export const PRAYERS = [
  { id: 'prayer-m', name: 'مصلى الرجال', en: "Men's Prayer Area", x0: 170.3, x1: bay(167.15).x1, closed: false, aliases: ['رجال', 'الرجال', 'men'] },
  { id: 'prayer-w', name: 'مصلى النساء', en: "Women's Prayer Room", ...bay(179.15), closed: true, aliases: ['نساء', 'النساء', 'نسائي', 'women', 'ladies'] }
];
// دورات المياه خلف الجدار الشمالي (المخطط الأصلي)، وأبوابها على القاعة
export const NORTH_WC = { z0: -11, z1: HALL.z0 - .9 };
export const NORTH_ROOMS = [
  { id: 'wc-n1', x0: 82.4, x1: 96.7, door: 85.4, name: 'دورات مياه الرجال', en: "Men's Restrooms", kind: 'toilet', icon: 'toilet-m', aliases: ['رجال', 'الرجال', 'men'] },
  { id: 'wc-n2', x0: 104.6, x1: 112, door: 105.2, name: 'دورات مياه النساء', en: "Women's Restrooms", kind: 'toilet', icon: 'toilet-f', aliases: ['نساء', 'النساء', 'سيدات', 'women', 'ladies'] },
  { id: 'wc-n3', x0: 141.4, x1: 157.6, door: 141.2, name: 'دورات مياه الرجال', en: "Men's Restrooms", kind: 'toilet', icon: 'toilet-m', aliases: ['رجال', 'الرجال', 'men'] },
  { id: 'wc-n4', x0: 157.6, x1: 169.4, door: 169.3, name: 'دورات مياه الرجال', en: "Men's Restrooms", kind: 'toilet', icon: 'toilet-m', aliases: ['رجال', 'الرجال', 'men'] }
];
/* ---------- شريط الخدمات: الغرف بين خانات المداخل (الاسم كما في المخطط) ---------- */
export const BAND_ROOMS = [
  { id: 'org1', x0: -3.9, x1: 5.1, name: 'مكتب المنظّمين 1', en: "Organizers' Office 1", kind: 'office' },
  { id: 'sup4', x0: 5.1, x1: 11.1, name: 'مشرف القاعة 4', en: "Hall 4 Supervisor", kind: 'office' },
  { id: 'reception-w', x0: 11.1, x1: 23.1, name: 'منطقة الاستقبال الغربية', en: "West Reception Area", kind: 'registration' },
  { id: 'hotel', x0: 35.1, x1: 47.1, name: 'خدمات الفنادق والنقل ووكالة السفر', en: "Hotel, Transport & Travel Services", kind: 'service' },
  { id: 'org', x0: 47.1, x1: 53.9, name: 'مكتب المنظّمين', en: "Organizers' Office", kind: 'office' },
  { id: 'sup3', x0: 53.9, x1: 59.1, name: 'مشرف القاعة 3', en: "Hall 3 Supervisor", kind: 'office' },
  { id: 'techservice', x0: 71.2, x1: 83.2, name: 'الخدمات الفنية للعارضين', en: "Exhibitor Technical Services", kind: 'service' },
  { id: 'firstaid', x0: 83.2, x1: 95.2, name: 'الإسعافات الأولية', en: "First Aid", kind: 'firstaid' },
  { id: 'sup2', x0: 107.2, x1: 114, name: 'مشرف القاعة 2', en: "Hall 2 Supervisor", kind: 'office' },
  { id: 'org3', x0: 114, x1: 119.2, name: 'مكتب المنظّمين 3', en: "Organizers' Office 3", kind: 'office' },
  { id: 'market', x0: 119.2, x1: 131.2, name: 'البقالة والمكتبة', en: "Mini Market & Bookshop", kind: 'shop' },
  { id: 'sup1', x0: 143.2, x1: 149.2, name: 'مشرف القاعة 1', en: "Hall 1 Supervisor", kind: 'office' },
  { id: 'org4', x0: 149.2, x1: 155.2, name: 'مكتب المنظّمين 4', en: "Organizers' Office 4", kind: 'office' },
  { id: 'cloak', x0: 155.2, x1: 161.2, name: 'غرفة الأمانات', en: "Cloakroom", kind: 'service' },
  { id: 'info', x0: 161.2, x1: 167.2, name: 'الاستعلامات', en: "Information", kind: 'info' },
  { id: 'reception-e', x0: 167.2, x1: 179.2, name: 'منطقة الاستقبال الشرقية', en: "East Reception Area", kind: 'registration' },
  { id: 'lift89', x0: 179.2, x1: 191.2, name: 'المصاعد 8 و9', en: "Elevators 8 & 9", kind: 'elevator' }
];

/* ---------- الصفّ الجنوبي للممر: الغرف والممرّات المفتوحة (passage) إلى خارج المبنى ---------- */
export const SOUTH_ROOMS = [
  { id: 'vip-hall2', x0: 7.3, x1: 18.3, name: 'قاعة الاستقبال 2', en: "Reception Hall 2", kind: 'vip' },
  { id: 'wc-vip1', x0: 18.3, x1: 21.3, name: 'دورة مياه كبار الزوار', en: "VIP Restroom", kind: 'toilet' },
  { id: 'vip-entry', x0: 21.3, x1: 26.4, name: 'دخول كبار الشخصيات', en: "VIP Entrance", kind: 'vip', passage: true },
  { id: 'vip-hall3', x0: 26.4, x1: 31, name: 'قاعة الاستقبال 3', en: "Reception Hall 3", kind: 'vip' },
  { id: 'wc-vip2', x0: 31, x1: 35, name: 'دورة مياه', en: "Restroom", kind: 'toilet' },
  { id: 'offices-w', x0: 35, x1: 50.1, name: 'مكاتب', en: "Offices", kind: 'office' },
  { id: 'exit1', x0: 50.1, x1: 56, name: 'المدخل الرئيسي — ممر الخروج 1', en: "Main Entrance · Exit Corridor 1", kind: 'door', passage: true },
  // مقابل مدخل 3: للنساء · مقابل مدخل 1: للرجال
  { id: 'wc-w', x0: 57.5, x1: 63.3, name: 'دورات مياه النساء', en: "Women's Restrooms", kind: 'toilet', aliases: ['نساء', 'النساء', 'نسائية', 'سيدات', 'women', 'ladies'] },
  { id: 'stair-w', x0: 63.4, x1: 67.8, name: 'الدرج', en: "Stairs", kind: 'stairs' },
  { id: 'g105', x0: 67.8, x1: 93.8, name: 'القاعة G105', en: "Hall G105", kind: 'room' },
  { id: 'exit2', x0: 98.4, x1: 104, name: 'المدخل الرئيسي — ممر الخروج 2', en: "Main Entrance · Exit Corridor 2", kind: 'door', passage: true },
  { id: 'offices', x0: 104.3, x1: 121.1, name: 'المكاتب الإدارية', en: "Administrative Offices", kind: 'office' },
  { id: 'access', x0: 121.7, x1: 128.1, name: 'مدخل إلى المعرض', en: "Exhibition Access", kind: 'door', passage: true },
  { id: 'wc-m', x0: 128.1, x1: 134.1, name: 'دورات مياه الرجال', en: "Men's Restrooms", kind: 'toilet', aliases: ['رجال', 'الرجال', 'رجالية', 'men', 'gents'] },
  { id: 'main-e', x0: 134.1, x1: 141.5, name: 'المدخل الرئيسي', en: "Main Entrance", kind: 'door', passage: true },
  { id: 'stair1', x0: 141.8, x1: 146, name: 'الدرج 1', en: "Stairs 1", kind: 'stairs' },
  { id: 'wc3', x0: 146, x1: 149.2, name: 'دورات المياه', en: "Restrooms", kind: 'toilet' },
  { id: 'utility', x0: 149.2, x1: 152.2, name: 'غرف الخدمة', en: "Service Rooms", kind: 'service' },
  { id: 'cafe', x0: 152.4, x1: 162, name: 'المقهى', en: "Café", kind: 'food' },
  { id: 'restaurant', x0: 162, x1: 180.4, name: 'المطعم وجلسات العائلات', en: "Restaurant & Family Seating", kind: 'food' },
  { id: 'lift67', x0: 180.6, x1: 189.8, name: 'المصاعد 6 و7', en: "Elevators 6 & 7", kind: 'elevator' }
];
// المداخل الرئيسية للمبنى = الممرّات المفتوحة في الصفّ الجنوبي
export const MAIN_DOORS = SOUTH_ROOMS.filter(r => r.passage).map(r => (r.x0 + r.x1) / 2);
// المدخلان العامّان عند طرفي الممر، وغرفتا العزل الزجاجيتان قبلهما، ونقطتا التفتيش قبل البوابات
export const PUBLIC_ACCESS = [{ name: tr('المدخل العام الغربي', 'West Public Entrance'), x: -10.5 }, { name: tr('المدخل العام الشرقي', 'East Public Entrance'), x: 197 }];
export const AIRLOCKS = [[7.5, 12.1], [180.6, 189.9]];
export const CHECKPOINTS = [21.3, 172.3];
// مكتبا الاستقبال في البهوين (RECEPTION FOYER 2 و1) والصرّاف في البهو الشرقي
export const FOYERS = [{ name: tr('بهو الاستقبال الغربي', 'West Reception Foyer'), x: 13.9, z: 80.5 }, { name: tr('بهو الاستقبال الشرقي', 'East Reception Foyer'), x: 175.5, z: 78.3 }];
export const ATM = { x: 181.1, z: 75.4 };
// الخدمات للبحث: كل غرفة مسمّاة في الشريط والصفّ الجنوبي (عدا الممرّات — لها أماكنها كمداخل)
export const SERVICES = [
  ...BAND_ROOMS.map(r => ({ ...r, x: (r.x0 + r.x1) / 2, z: (BAND.z0 + BAND.z1) / 2, side: 'band' })),
  ...SOUTH_ROOMS.filter(r => !r.passage).map(r => ({ ...r, x: (r.x0 + r.x1) / 2, z: (SOUTH.z0 + SOUTH.z1) / 2, side: 'south' })),
  { id: 'atm', name: 'صرّاف آلي', en: "ATM", kind: 'service', x: ATM.x, z: ATM.z, side: 'concourse' },
  // داخل القاعة شمالًا: المكان عند الباب نفسه
  ...NORTH_ROOMS.map(r => ({ ...r, x: r.door, z: HALL.z0, side: 'north' })),
  ...PRAYERS.map(r => ({ ...r, kind: 'prayer', x: (r.x0 + r.x1) / 2, z: r.closed ? NORTH.z1 : (NORTH.z0 + NORTH.z1) / 2, side: 'north' })),
  ...CAFES.list.map(c => ({ ...c, kind: 'food', side: 'north' }))
];

/* ---------- منطقة المسرح (غرب القاعة) ---------- */
export const STAGE_ZONE = { x0: 1.5, x1: 41.5, z0: 1.1, z1: 67.9 };
export const STAGE = { x0: 2.9, x1: 40.9, z0: 1.7, z1: 9.7 };           // منصّة الإعلانات 38 × 8 م
export const VVIP = { z0: 14.2, z1: 17.5 };
export const SEATS = { blocks: [[3.9, 20.6], [22.6, 39.3]], z0: 19.1, z1: 62, cross: [[31.1, 33.1], [47.1, 49.1]], dx: .9, dz: .8 };
export const FOH = { x0: -3.6, x1: 1.4, z0: 14.1, z1: 20.6 };

/* ---------- الغرف بين المسرح والأجنحة: استراحة المحكّمين وقاعات الجهات ----------
   door: جهة الباب — على الممر الذي يصل الغرفة (n · s · w · e) */
export const ROOMS = [
  { id: 'judges', name: 'استراحة المحكّمين', en: "Judges' Lounge", x0: 44.5, x1: 65.5, z0: 1.2, z1: 8.1, door: 'e', aliases: ['محكمين', 'المحكمين', 'judges'] },
  { id: 'saif-team', name: 'فريق سيف', en: 'SAIF Team', x0: 44.5, x1: 65.5, z0: 8.1, z1: 15.1, door: 's', aliases: ['فريق سيف', 'سيف', 'saif team', 'المنظمين'] },
  { id: 'garage', name: 'الكراج', en: 'The Garage', x0: 49, x1: 61, z0: 16.7, z1: 22.7, door: 's', aliases: ['كراج', 'الكراج', 'garage'] },
  { id: 'mawhiba', name: 'موهبة', en: 'Mawhiba', x0: 44.5, x1: 50.5, z0: 24.8, z1: 34.8, door: 'w', aliases: ['موهبه', 'موهبة', 'mawhiba'] },
  { id: 'coffee', name: 'مقهى', en: 'Café', x0: 53.5, x1: 65.5, z0: 25.8, z1: 29.8, door: 'e', aliases: ['مقهى', 'القهوة', 'قهوة', 'كوفي', 'كافيه', 'coffee', 'cafe'] },
  { id: 'moe', name: 'وزارة التعليم', en: 'Ministry of Education', x0: 53.5, x1: 65.5, z0: 29.8, z1: 34.8, door: 'e', aliases: ['التعليم', 'وزارة التعليم', 'moe', 'education'] },
  { id: 'elm', name: 'علم', en: 'Elm', x0: 44.5, x1: 50.5, z0: 37.1, z1: 49.1, door: 'w', aliases: ['علم', 'elm'] },
  { id: 'tahakom', name: 'تحكم', en: 'Tahakom', x0: 53.5, x1: 65.5, z0: 38.1, z1: 48.1, door: 'e', aliases: ['تحكم', 'tahakom'] },
  // البوث الكبير جنوبًا مقسوم بوثين 9 × 12 م بينهما ممر 3 م (مخطط الموقع 250)
  { id: 'moi', name: 'وزارة الداخلية', en: 'Ministry of Interior', x0: 44.5, x1: 53.5, z0: 52.1, z1: 64.1, door: 's', aliases: ['الداخلية', 'وزارة الداخلية', 'moi', 'interior', 'ministry of interior'] },
  { id: 'tuwaiq', name: 'طويق', en: 'Tuwaiq', x0: 56.5, x1: 65.5, z0: 52.1, z1: 64.1, door: 's', aliases: ['طويق', 'اكاديمية طويق', 'tuwaiq', 'tuwaiq academy'] }
];
// المركز الإعلامي: جناح زجاجي بطابقين (15 × 9 م) في فجوة الشريحة الأولى
export const MEDIA = { name: tr('المركز الإعلامي وصالة كبار الزوار', 'Media Center & VIP Lounge'), x0: 120.5, x1: 135.5, z0: 5.1, z1: 14.1 };
export const MEDIA_GAP = { x0: 115, x1: 141.1 };

/* ---------- الأجنحة: 1200 جناح بمقاس 1 × 2 م ----------
   شريط = عمودان × 6 أجنحة (2 × 12 م). أربع شرائح أفقية من الشمال للجنوب؛
   الأولى 22 شريطًا (المركز الإعلامي في وسطها) والبقية 26.
   n تسلسل داخلي (يرتّب الأجنحة)؛ ما يراه الناس الكود الرسمي في booths() أدناه. */
export const STRIPS = [68, 72.5, 77, 81.5, 86, 90.5, 95, 99.5, 104, 108.5, 113, 118.07, 122.6,
  131.6, 136.1, 141.1, 145.6, 150.1, 154.6, 159.1, 163.6, 168, 172.6, 177, 181.6, 186];
export const BANDS = [5.2, 20.2, 35.2, 50.2];             // بداية كل شريحة؛ عمقها 12 م، وبينها ممرات 3 م
export const BOOTH = { w: 1, d: 2, rows: 6 };
// الشريحة الأولى بلا الشرائط التي مكانها المركز الإعلامي
const skip = (band, x) => band === 0 && x > MEDIA_GAP.x0 && x < MEDIA_GAP.x1;
export const stripSkipped = skip;

/* ---------- كتل خضراء في المخطط بلا اسم ----------
   ثلاث (2 × 3 م) في الممر العريض جنوب المركز الإعلامي، وثلاث (4 × 3 م) في الممر الخارجي.
   مرسومة كما في المخطط، ومسارات المشي تمرّ بجانبها لا من خلالها. */
export const PODS = [
  { x0: 126.4, x1: 128.3, z0: 25, z1: 28 }, { x0: 126.4, x1: 128.3, z0: 39.4, z1: 42.4 }, { x0: 126.4, x1: 128.3, z0: 54.3, z1: 57.3 },
  { x0: 76, x1: 80, z0: 78, z1: 81 }, { x0: 113.9, x1: 117.9, z0: 78, z1: 81 }, { x0: 145.6, x1: 149.6, z0: 78, z1: 81 }
];

/* ---------- مناطق الأجنحة A–J (لوحة المناطق في العرض الفني، صفحة 5) ----------
   تُعدّ بالأعمدة المفردة من الشرق للغرب: A وB وC وD خمسة أعمدة لكلٍّ،
   ثم E (102 جناح) وF (90) حول المركز الإعلامي، ثم G وH وI خمسة، وJ سبعة.
   لون الأجنحة بالمناطق الثلاث — AREAS أدناه */
export const ZONES = [
  { letter: 'A', cols: 5 }, { letter: 'B', cols: 5 }, { letter: 'C', cols: 5 }, { letter: 'D', cols: 5 },
  { letter: 'E', cols: 5 }, { letter: 'F', cols: 5 }, { letter: 'G', cols: 5 }, { letter: 'H', cols: 5 },
  { letter: 'I', cols: 5 }, { letter: 'J', cols: 7 },
  // K: بوثات الجدار (ليست في شبكة الأعمدة) — الشرقي من الجنوب شمالًا ثم الشمالي من الشرق غربًا، wallBooths() أدناه
  { letter: 'K', cols: 4, wall: true }
];
// العمود المفرد رقم c من الشرق ← منطقته
export function zoneOfColumn(c) {
  let acc = 0;
  for (let i = 0; i < ZONES.length; i++) { acc += ZONES[i].cols; if (c < acc) return i; }
  return ZONES.length - 1;
}

// أول عمود مفرد (من الشرق) في المنطقة i
const zoneStart = i => ZONES.slice(0, i).reduce((a, z) => a + z.cols, 0);

/* ---------- المناطق الثلاث (ترقيم البوثات، سيف 2026): الزرقاء A–C، الحمراء D–G، البرتقالية H–J ----------
   كل أجنحة المنطقة بلونها — توكن --sef-area-* */
export const AREAS = [
  { id: 'blue', zones: [0, 1, 2, 10] },   // K بجانب A على الجدار الشرقي
  { id: 'red', zones: [3, 4, 5, 6] },
  { id: 'orange', zones: [7, 8, 9] }
];
export const areaOf = zone => AREAS.find(a => a.zones.includes(zone)).id;

// اسم الغرفة باللغة الحالية — en اسمها الإنجليزي المعروض
export const nameOf = r => tr(r.name, r.en || r.name);

// الكود كما يكتبه الناس ← الصيغة الرسمية: «c3-12» و«C3 12» و«s-c3-12» كلها S-C3-12
export function boothCode(text) {
  const m = String(text || '').trim().toUpperCase().match(/^(?:S\s*-?\s*)?([A-K])\s*(\d)\s*-?\s*(\d{1,2})$/);
  return m ? 'S-' + m[1] + m[2] + '-' + m[3].padStart(2, '0') : null;
}

export function booths() {
  const list = [];
  let n = 0;
  const desc = STRIPS.slice().reverse();
  const colIndex = (sx, col) => desc.indexOf(sx) * 2 + (col === 'east' ? 0 : 1);
  BANDS.forEach((z0, band) => {
    const strips = STRIPS.filter(x => !skip(band, x)).slice().reverse();     // من الشرق للغرب
    strips.forEach(sx => {
      ['east', 'west'].forEach(col => {
        const zone = zoneOfColumn(colIndex(sx, col));
        // الكود الرسمي (ترقيم البوثات للتركيب، سيف 2026): S-{المنطقة}{العمود}-{الجناح} —
        // العمود 1 أقرب أعمدة المنطقة للشرق، والجناح 01 أقربها للمداخل (الجنوب) صعودًا حتى 24 شمالًا
        const zc = colIndex(sx, col) - zoneStart(zone) + 1;
        for (let r = 0; r < 6; r++) {
          const num = (BANDS.length - 1 - band) * 6 + (6 - r);
          list.push({
            n: col === 'east' ? n + 1 + r : n + 12 - r, band, col, sx, zone, x: sx + (col === 'east' ? 1.5 : .5), z: z0 + r * 2 + 1,
            code: 'S-' + ZONES[zone].letter + zc + '-' + String(num).padStart(2, '0'),
            end: r === 0 ? 'north' : r === 5 ? 'south' : null
          });
        }
      });
      n += 12;
    });
  });
  // بعد أجنحة الشبكة (أرقامها بعد 1200): ترتيب الشبكة كما هو، فلا تتغيّر أرقام طاولاتها
  list.sort((a, b) => a.n - b.n);
  return list.concat(wallBooths(list));
}

/* ---------- المنطقة K: بوثات الجدار الشرقي ----------
   تبدأ من أقصى الجنوب (عند الممر) وتصعد شمالًا: كل صفّ 6 بوثات بين بوابتين، وكل عمود (K1، K2) صفّان.
   في الصفّ: الطاولة الجانبية الجنوبية أولًا، ثم الأربع على الجدار، ثم الشمالية — شكل U (sef.js).
   x, z: مكان الطاولة · r: دورانها (الجانبية متعامدة مع الجدار) · wall: لا شريط ولا عمود في الشبكة */
export const WALL_U = { depth: 2.1, desk: 1.25, side: .3, inset: .65 };
export function wallRowSlots(a0, a1, per) {
  // مواضع الطاولات على طول الصفّ (a) وعمقها من الجدار (d) — بترتيب الصفّ من a0 إلى a1
  const mid = per - 2, i0 = a0 + WALL_U.inset, i1 = a1 - WALL_U.inset, step = (i1 - i0) / mid;
  return [{ a: a0 + WALL_U.side, d: WALL_U.depth - .8, side: true },
    ...Array.from({ length: mid }, (_, i) => ({ a: i0 + (i + .5) * step, d: WALL_U.desk, side: false })),
    { a: a1 - WALL_U.side, d: WALL_U.depth - .8, side: true }];
}
function wallBooths(grid) {
  const K = ZONES.findIndex(z => z.letter === 'K'), list = [], start = grid.length;
  // لون الجناح لون موضعه (كما يظهر الآن): منطقة أقرب جناح في الشبكة — الشرقي أزرق، والشمالي أحمر
  const areaNear = (x, z) => areaOf(grid.reduce((p, b) => Math.hypot(b.x - x, b.z - z) < Math.hypot(p.x - x, p.z - z) ? b : p).zone);
  const push = (code, x, z, r, side) => list.push({ n: start + list.length + 1, band: null, col: 'wall', sx: null, zone: K, wall: side,
    x, z, r, area: areaNear(x, z), code, end: null });
  // الجدار الشرقي: الصفوف من الجنوب إلى الشمال، وفي كل صفّ من الجنوب إلى الشمال (z تنقص شمالًا) —
  // كل عمود صفّان: K1، K2، ثم K3 يبدأ بالصفّ الشمالي (شمال البوابة الأولى)
  const east = EAST_BOOTHS.blocks.slice().sort((p, q) => q[0] - p[0]);
  let col = 1, num = 0;
  const next = () => { if (num === 12) { col++; num = 0; } return 'S-K' + col + '-' + String(++num).padStart(2, '0'); };
  east.forEach(([z0, z1]) => wallRowSlots(z0, z1, EAST_BOOTHS.per).reverse().forEach(slot =>
    push(next(), EAST_BOOTHS.x1 - slot.d, slot.a, slot.side ? Math.PI / 2 : 0, 'east')));
  // الجدار الشمالي: من الشرق إلى الغرب — صفّه الشرقي يكمل K3 (K3-07…13)، والغربي K4 (K4-01…07)
  const north = WALL_BOOTHS.slice().sort((p, q) => q.x0 - p.x0);
  north.forEach((row, i) => {
    if (i === 1) { col++; num = 0; }
    wallRowSlots(row.x0, row.x1, row.per).reverse().forEach(slot =>
      push('S-K' + col + '-' + String(++num).padStart(2, '0'), slot.a, NORTH.z0 + slot.d, slot.side ? 0 : Math.PI / 2, 'north'));
  });
  return list;
}

/* ---------- شاشات الإرشاد (الكيوسك) ----------
   مواقع مؤقتة مقترحة حتى يصل مخطط أماكن الشاشات الفعلي: عند المداخل
   من الداخل، وفي الممر العريض جنوب المركز الإعلامي، وفي الممر الخارجي.
   الصفحة تُفتح على الشاشة بـ ?kiosk=k1 … فتعرف موقعها. face: اتجاه وجهها (π = نحو الشمال، داخل القاعة). */
export const KIOSKS = [
  { id: 'k1', name: tr('شاشة الإرشاد 1', 'Info Kiosk 1'), x: 133.5, z: 67.2, face: Math.PI },
  { id: 'k2', name: tr('شاشة الإرشاد 2', 'Info Kiosk 2'), x: 97.5, z: 67.2, face: Math.PI },
  { id: 'k3', name: tr('شاشة الإرشاد 3', 'Info Kiosk 3'), x: 61.5, z: 67.2, face: Math.PI },
  { id: 'k4', name: tr('شاشة الإرشاد 4', 'Info Kiosk 4'), x: 126.2, z: 18.4, face: 0 },
  { id: 'k5', name: tr('شاشة الإرشاد 5', 'Info Kiosk 5'), x: 170, z: 77.2, face: 0 }
];
