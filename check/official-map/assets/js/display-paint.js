/* يرسم محتوى شاشة العرض الحيّ (صناديق، صور، نصوص) على canvas
   ليُستعمل نسيجًا على الشاشة ثلاثية الأبعاد. يقرأ التخطيط الفعلي
   للودجتات بدل نسخة ثانية من الأرقام؛ ليس رسّامًا عامًّا لأي HTML —
   يكفي لأنواع ودجتات الشاشة (خلفيات مسطّحة، حدود، صور، نص). */
function roundedRect(ctx, x, y, w, h, r) {
  ctx.beginPath(); ctx.roundRect(x, y, w, h, Math.max(0, Math.min(r, w / 2, h / 2)));
}

export function paintDisplay(screen, width = 2048) {
  const box = screen.getBoundingClientRect();
  if (!box.width || !box.height) return null;
  const scale = width / box.width;
  const out = document.createElement('canvas');
  out.width = width; out.height = Math.round(box.height * scale);
  const ctx = out.getContext('2d');
  ctx.scale(scale, scale);
  ctx.fillStyle = getComputedStyle(screen).backgroundColor;
  ctx.fillRect(0, 0, box.width, box.height);

  function visit(el) {
    const s = getComputedStyle(el), b = el.getBoundingClientRect();
    if (s.display === 'none' || s.visibility === 'hidden' || +s.opacity === 0 || !b.width || !b.height) return;
    if (el.tagName.toLowerCase() === 'svg') return;
    ctx.save();
    ctx.globalAlpha *= +s.opacity;
    const x = b.left - box.left, y = b.top - box.top, radius = parseFloat(s.borderTopLeftRadius) || 0;
    roundedRect(ctx, x, y, b.width, b.height, radius);
    ctx.fillStyle = s.backgroundColor; ctx.fill();
    const border = parseFloat(s.borderTopWidth) || 0;
    if (border && s.borderTopStyle !== 'none') {
      roundedRect(ctx, x + border / 2, y + border / 2, b.width - border, b.height - border, radius);
      ctx.strokeStyle = s.borderTopColor; ctx.lineWidth = border; ctx.stroke();
    }
    if (el.tagName === 'IMG' && el.complete && el.naturalWidth) ctx.drawImage(el, x, y, b.width, b.height);
    for (let node = el.firstChild; node; node = node.nextSibling) {
      if (node.nodeType === 1) visit(node);
      else if (node.nodeType === 3 && node.textContent.trim()) {
        const range = document.createRange(); range.selectNodeContents(node);
        const t = range.getBoundingClientRect();
        if (!t.width) continue;
        ctx.font = s.fontStyle + ' ' + s.fontWeight + ' ' + s.fontSize + ' ' + s.fontFamily;
        ctx.fillStyle = s.color; ctx.textBaseline = 'middle'; ctx.direction = s.direction;
        ctx.textAlign = s.direction === 'rtl' ? 'right' : 'left';
        ctx.fillText(node.textContent.trim(), (s.direction === 'rtl' ? t.right : t.left) - box.left, t.top - box.top + t.height / 2);
      }
    }
    ctx.restore();
  }
  Array.from(screen.children).forEach(visit);
  return out;
}
