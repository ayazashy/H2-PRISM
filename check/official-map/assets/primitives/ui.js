/* =========================================================
   مكوّنات التحكّم الأولية — المكان الوحيد الذي تُكتب فيه عناصر
   HTML التفاعلية الخام. كل واجهة أخرى تبني منها نصوصًا جاهزة
   (القوالب نصية لأن طبقات الصفحة كلها تُرسم بـ innerHTML).
   ========================================================= */
export const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

const attrs = a => Object.entries(a || {})
  .filter(([, v]) => v !== false && v != null)
  .map(([k, v]) => v === true ? ' ' + k : ' ' + k + '="' + esc(v) + '"').join('');

export const icon = (d, size = 18, width = 2) =>
  '<svg width="' + size + '" height="' + size + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
  'stroke-width="' + width + '" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + d + '</svg>';

/* زر نصّي — variant: primary | soft | quiet | danger | ghost */
export function button(label, opts = {}) {
  const cls = ['ui-btn', 'ui-btn--' + (opts.variant || 'quiet'), opts.size === 'lg' ? 'ui-btn--lg' : '', opts.cls || '']
    .filter(Boolean).join(' ');
  return '<button type="button" class="' + cls + '"' + attrs(opts.attrs) + '>' +
    (opts.icon || '') + '<span>' + esc(label) + '</span>' + (opts.tail || '') + '</button>';
}

/* زر أيقونة — الاسم المقروء إلزامي */
export const iconButton = (svg, label, a = {}, cls = '') =>
  '<button type="button" class="ui-icon-btn ' + cls + '" aria-label="' + esc(label) + '" title="' + esc(label) + '"' +
  attrs(a) + '>' + svg + '</button>';

/* زر حرّ بمحتوى مركّب (صفوف قابلة للنقر، شرائح، دبابيس) */
export const pressable = (inner, cls, a = {}) =>
  '<button type="button" class="' + cls + '"' + attrs(a) + '>' + inner + '</button>';

/* مفتاح تشغيل — checkbox بدور switch حتى يُقرأ كحالة لا كاختيار */
export const toggle = (name, label, on, sub = '', a = {}) =>
  '<label class="ui-toggle">' +
    '<span class="ui-toggle__text"><span class="ui-toggle__label">' + esc(label) + '</span>' +
    (sub ? '<span class="ui-toggle__sub">' + esc(sub) + '</span>' : '') + '</span>' +
    '<input type="checkbox" role="switch" data-toggle="' + esc(name) + '"' + (on ? ' checked' : '') + attrs(a) + '>' +
    '<span class="ui-toggle__track" aria-hidden="true"><i></i></span>' +
  '</label>';

/* حقل بحث بأيقونة في الطرف */
export const search = (placeholder, a = {}) =>
  '<div class="shx-search">' + icon('<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>', 16) +
  '<input type="search" placeholder="' + esc(placeholder) + '" aria-label="' + esc(placeholder) + '"' + attrs(a) + '></div>';

/* حقل نصّي سطري */
export const field = (placeholder, a = {}) =>
  '<input type="text" class="ui-field" placeholder="' + esc(placeholder) + '" aria-label="' + esc(placeholder) + '"' + attrs(a) + '>';

/* اختيار ملف: الحقل الأصلي مخفي، والملصق كله سطح النقر */
export const filePicker = (inner, accept, a = {}) =>
  '<label class="ctl-import">' + inner + '<input type="file" accept="' + esc(accept) + '" hidden' + attrs(a) + '></label>';

/* ستيبر رقمي «− قيمة +» */
export const stepper = (value, label, a = {}) =>
  '<span class="ui-stepper" role="group" aria-label="' + esc(label) + '">' +
    '<button type="button" data-step="-5"' + attrs(a) + ' aria-label="إنقاص ' + esc(label) + '">−</button>' +
    '<b>' + esc(value) + '</b>' +
    '<button type="button" data-step="5"' + attrs(a) + ' aria-label="زيادة ' + esc(label) + '">+</button>' +
  '</span>';
