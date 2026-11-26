/* =========================================================
   لغة الخريطة — العربية (الأصل) والإنجليزية
   اللغة من الرابط (?lang=en) ثم من اختيار الزائر المحفوظ، وإلا العربية.
   التبديل يعيد تحميل الصفحة باللغة الجديدة: المشهد والبحث والتعليمات
   كلها تُبنى مرة واحدة باللغة الصحيحة، بلا نصّ عالق باللغة الأخرى.
   ========================================================= */
const KEY = 'saif-map-lang';
const param = new URLSearchParams(location.search).get('lang');
let stored = null;
try { stored = localStorage.getItem(KEY); } catch { /* التخزين غير متاح */ }

export const lang = param === 'en' || param === 'ar' ? param : stored === 'en' ? 'en' : 'ar';
export const EN = lang === 'en';
// النص باللغة الحالية: tr('مدخل', 'Entrance')
export const tr = (ar, en) => (EN ? en : ar);

document.documentElement.lang = lang;
document.documentElement.dir = EN ? 'ltr' : 'rtl';

export function setLang(next) {
  try { localStorage.setItem(KEY, next); } catch { /* لا بأس */ }
  const url = new URL(location.href);
  url.searchParams.set('lang', next);
  url.hash = '';
  location.replace(url.toString());
}

