/* Paint the existing, flat room geometry into a small backdrop texture.
   This adapter owns only the room's rectangles, not arbitrary page HTML. */
export function splitGradientParts(value) {
  const parts = []; let depth = 0, start = 0;
  for (let i = 0; i < value.length; i++) {
    if (value[i] === '(') depth++;
    if (value[i] === ')') depth--;
    if (value[i] === ',' && depth === 0) { parts.push(value.slice(start, i).trim()); start = i + 1; }
  }
  parts.push(value.slice(start).trim()); return parts;
}
export function intersects(a, b) {
  return a.right > b.left && a.left < b.right && a.bottom > b.top && a.top < b.bottom;
}
function roundedRect(ctx, rect, radius) {
  ctx.beginPath(); ctx.roundRect(rect.left, rect.top, rect.width, rect.height, Math.max(0, radius));
}
function paintBox(ctx, node, bounds) {
  const style = getComputedStyle(node);
  const scale = bounds.width / (parseFloat(style.width) || bounds.width);
  const radius = Math.min(parseFloat(style.borderTopLeftRadius) * scale || 0, bounds.width / 2, bounds.height / 2);
  roundedRect(ctx, bounds, radius);
  ctx.fillStyle = style.backgroundColor; ctx.fill();
  // Chairs use a horizontal gradient, with computed CSS colors and alpha intact.
  if (style.backgroundImage.startsWith('linear-gradient(90deg,')) {
    const parts = splitGradientParts(style.backgroundImage.slice(16, -1)).slice(1);
    const gradient = ctx.createLinearGradient(bounds.left, bounds.top, bounds.right, bounds.top);
    for (const part of parts) {
      const match = part.match(/^(.*)\s+([\d.]+)%$/);
      if (match) gradient.addColorStop(Number(match[2]) / 100, match[1]);
    }
    ctx.fillStyle = gradient; ctx.fill();
  }
  const border = parseFloat(style.borderTopWidth) * scale;
  if (border > 0 && style.borderTopStyle !== 'none') {
    const inner = {left:bounds.left + border / 2, top:bounds.top + border / 2, width:bounds.width - border, height:bounds.height - border};
    roundedRect(ctx, inner, Math.max(0, radius - border / 2));
    ctx.strokeStyle = style.borderTopColor; ctx.lineWidth = border; ctx.stroke();
  }
}
export function paintRoomBackdrop(ctx, room, region, dpr, washOpacity) {
  ctx.setTransform(dpr, 0, 0, dpr, -region.left * dpr, -region.top * dpr);
  ctx.fillStyle = getComputedStyle(document.body).backgroundColor;
  ctx.fillRect(region.left, region.top, region.width, region.height);
  // المشهد ثلاثي الأبعاد: آخر إطار مرسوم (preserveDrawingBuffer) في موضعه على الشاشة
  const venue = room.querySelector('canvas.venue-3d');
  if (venue) {
    const b = venue.getBoundingClientRect();
    if (intersects(b, region)) ctx.drawImage(venue, b.left, b.top, b.width, b.height);
  }
  for (const booth of room.querySelectorAll('.booth')) {
    const bounds = booth.getBoundingClientRect();
    if (!intersects(bounds, region)) continue;
    paintBox(ctx, booth, bounds);
    for (const shape of booth.querySelectorAll('i')) {
      const shapeBounds = shape.getBoundingClientRect();
      if (!intersects(shapeBounds, region)) continue;
      const asset = shape.querySelector('img');
      if (asset && asset.complete && asset.naturalWidth) {
        ctx.save();
        ctx.globalAlpha = parseFloat(getComputedStyle(shape).opacity);
        const flipped = shape.classList.contains('b-seat--flipped');
        ctx.translate(flipped ? shapeBounds.right : shapeBounds.left, shapeBounds.top);
        ctx.scale(flipped ? -1 : 1, 1);
        ctx.drawImage(asset, 0, 0, shapeBounds.width, shapeBounds.height);
        ctx.restore();
      } else paintBox(ctx, shape, shapeBounds);
    }
  }
  if (washOpacity > 0) {
    const mobile = window.matchMedia('(max-width:680px)').matches;
    const rx = mobile ? 440 : 636, ry = mobile ? 460 : 596;
    const stops = mobile ? [[0,1],[.24,.97],[.44,.78],[.64,.4],[.82,.1],[1,0]]
      : [[0,1],[.2,.99],[.34,.94],[.47,.78],[.6,.5],[.73,.23],[.86,.06],[.95,.008],[1,0]];
    ctx.save(); ctx.translate(innerWidth, innerHeight); ctx.scale(rx, ry);
    const gradient = ctx.createRadialGradient(0, 0, 0, 0, 0, 1);
    for (const [stop, alpha] of stops) gradient.addColorStop(stop, `rgba(250,250,250,${alpha * washOpacity})`);
    ctx.fillStyle = gradient; ctx.fillRect(-innerWidth / rx, -innerHeight / ry, innerWidth / rx, innerHeight / ry); ctx.restore();
  }
}
