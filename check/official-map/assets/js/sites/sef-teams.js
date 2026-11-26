/* =========================================================
   فرق معرض سيف على الأجنحة — بيانات تجريبية ثابتة البذرة
   تظهر حتى يصل باك اند تحكيم (api/tahkeem.js)، وحين يصل تحلّ بياناته محلّها
   بالكامل: الجناح بلا فريق هناك يبقى بلا فريق هنا.
   ========================================================= */
import { EN } from '../i18n.js';
import { countryOf, getCountryFlag } from '../countries.js';
const PREFIX = ['درع', 'حصن', 'رادار', 'شيفرة', 'بصمة', 'أفق', 'نبض', 'سحابة', 'جسر', 'منارة', 'سهم', 'مدار',
  'حارس', 'ومضة', 'بوابة', 'نواة', 'مرصد', 'رمز', 'صقر', 'يقظة'];
const SUFFIX = ['الأمان', 'الرقمي', 'الذكي', 'المستقبل', 'الابتكار', 'الحماية', 'الشبكة', 'البيانات', 'السيبراني', 'الهوية',
  'الثقة', 'المدينة', 'الرصد', 'الدفاع', 'التشفير'];
// الدول بأسمائها الإنجليزية كما يرسلها تحكيم (countries.js يعطي الاسم بالعربية والعلم)
const NATIONS = ['Saudi Arabia', 'Saudi Arabia', 'Saudi Arabia', 'United Arab Emirates', 'Egypt', 'Jordan',
  'Bahrain', 'Kuwait', 'Oman', 'Qatar', 'Morocco', 'Tunisia', 'India',
  'South Korea', 'Japan', 'Germany', 'United Kingdom', 'United States',
  'Singapore', 'Spain'];
// المسارات كما في تحكيم (event_path_name)
const TRACKS = EN
  ? ['AI & Security Forecasting', 'Cybersecurity', 'Smart Cities & Safety', 'Digital Identity', 'National & Border Security']
  : ['الذكاء الاصطناعي والتنبؤ الأمني', 'الأمن السيبراني', 'المدن الذكية والسلامة', 'الهوية الرقمية', 'الأمن الوطني والحدود'];
const FIRST = ['محمد', 'عبدالله', 'سارة', 'نورة', 'فهد', 'ريم', 'خالد', 'لمى', 'عبدالرحمن', 'هيا', 'سلطان', 'جود',
  'يوسف', 'دانة', 'تركي', 'شهد', 'عمر', 'مها', 'فيصل', 'رهف', 'أحمد', 'لين', 'ماجد', 'غلا'];
const FAMILY = ['العتيبي', 'القحطاني', 'الشهري', 'الحربي', 'الدوسري', 'الزهراني', 'المطيري', 'الغامدي', 'السبيعي', 'العنزي',
  'الشمري', 'الرشيد', 'الخالدي', 'البلوي', 'العمري', 'السلمي', 'الجهني', 'الأحمدي'];

let seed = 7311;
const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
const pick = list => list[Math.floor(rnd() * list.length)];

// رقم الجناح ← فريقه؛ الاسم لا يتكرّر (تكراره يُرقَّم)
const TEAMS = (() => {
  const seen = {}, out = {};
  for (let n = 1; n <= 1200; n++) {
    let name = pick(PREFIX) + ' ' + pick(SUFFIX);
    seen[name] = (seen[name] || 0) + 1;
    if (seen[name] > 1) name += ' ' + seen[name];
    const nation = pick(NATIONS), c = countryOf(nation), country = EN ? c.nameEn : c.nameAr, flag = getCountryFlag(nation);
    out[n] = { team: name, code: 'SAIF-' + String(n).padStart(4, '0'), track: pick(TRACKS), country, flag, leader: pick(FIRST) + ' ' + pick(FAMILY) };
  }
  return out;
})();

export const teamOf = n => TEAMS[n] || null;
