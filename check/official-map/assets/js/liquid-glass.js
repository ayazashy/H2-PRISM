/* Progressive enhancement of the existing accessible 52px button.
   Liquid DOM receives an app-owned room texture; no HTML-in-Canvas flags needed. */
import { intersects, paintRoomBackdrop } from './room-backdrop.js';

const button = document.querySelector('.participant-actions__toggle');
const room = document.querySelector('#canvas');
const actions = button?.closest('.participant-actions');
const transparency = matchMedia('(prefers-reduced-transparency: reduce)');
const forcedColors = matchMedia('(forced-colors: active)');
let dispose = () => {};

async function enhance() {
  dispose();
  if (!button || !room) return;
  button.dataset.glass = 'fallback';
  if (!isSecureContext || !navigator.gpu || transparency.matches || forcedColors.matches) {
    button.dataset.glassReason = !navigator.gpu ? 'webgpu-unavailable' : 'environment-preference';
    return;
  }
  let disposed = false, device, core, context, texture, frame = 0, observer;
  let drawing = false, ready = false, warmUntil = 0, pixelSize = 0, dpr = 1;
  const controller = new AbortController();
  const output = document.createElement('canvas');
  output.className = 'participant-actions__glass'; output.setAttribute('aria-hidden', 'true');
  const source = document.createElement('canvas');
  const ctx = source.getContext('2d', { alpha: false });
  function destroy(reason = 'disposed') {
    if (disposed) return;
    disposed = true; cancelAnimationFrame(frame); observer?.disconnect(); controller.abort();
    button.classList.remove('has-liquid-glass'); button.dataset.glass = 'fallback'; button.dataset.glassReason = reason;
    core?.destroy(); texture?.destroy(); context?.unconfigure(); device?.destroy(); output.remove();
  }
  dispose = destroy;
  button.dataset.glass = 'loading';
  try {
    const [{ Container, Glass, Scene, WebGpuGlassCore }, adapter] = await Promise.all([
      import('../vendor/liquid-dom/core.mjs'), navigator.gpu.requestAdapter()
    ]);
    if (disposed) return;
    if (!adapter || !ctx) { destroy('adapter-unavailable'); return; }
    device = await adapter.requestDevice();
    if (disposed) { device.destroy(); return; }
    device.lost.then(() => destroy('device-lost'));
    device.addEventListener('uncapturederror', () => destroy('gpu-error'), { signal: controller.signal });
    context = output.getContext('webgpu');
    if (!context) { destroy('canvas-unavailable'); return; }
    const format = navigator.gpu.getPreferredCanvasFormat();
    device.pushErrorScope('validation');
    core = new WebGpuGlassCore({ device, format });
    const scene = new Scene();
    const optics = new Container({
      blur: 1, bezelWidth: 8, thickness: 14, ior: 1.45, displacementFactor: 1.5,
      displacementBlur: .65, surfaceProfile: 'convex', spacing: 0,
      tint: { r: 73 / 255, g: 49 / 255, b: 175 / 255, a: .2 },
      specularWidth: 'hairline', specularStrength: .75, oppositeSpecularStrength: .4,
      specularOpacity: .32, reflectionOffset: 5,
      shadowColor: {r:0,g:0,b:0,a:0}, shadowBlur:0,
    });
    const glass = new Glass({ width:52, height:52, cornerRadius:26, cornerSmoothing:0 });
    optics.add(glass); scene.add(optics);
    button.prepend(output);

    function overlapsForeignSurface(region) {
      // The adapter captures the flat room. Keep CSS glass if other UI covers it.
      return Array.from(document.querySelectorAll('.pop, .ev-sheet:not([hidden]), .canvas-screen'))
        .some(el => intersects(el.getBoundingClientRect(), region));
    }
    function draw() {
      if (disposed || document.hidden) return false;
      if (document.body.classList.contains('is-lifting')) {
        button.classList.remove('has-liquid-glass'); return false;
      }
      const rect = button.getBoundingClientRect(), padding = 38;
      const size = rect.width + padding * 2;
      const region = {left:rect.left-padding,top:rect.top-padding,width:size,height:size,right:rect.right+padding,bottom:rect.bottom+padding};
      if (overlapsForeignSurface(region)) {
        button.classList.remove('has-liquid-glass'); button.dataset.glass = 'fallback';
        button.dataset.glassReason = 'overlapping-content'; return false;
      }
      const nextDpr = Math.min(devicePixelRatio || 1, 2);
      const nextSize = Math.round(size * nextDpr);
      if (pixelSize !== nextSize || dpr !== nextDpr) {
        dpr = nextDpr; pixelSize = nextSize;
        source.width = source.height = output.width = output.height = pixelSize;
        Object.assign(output.style, { width:size+'px',height:size+'px',left:-padding+'px',top:-padding+'px' });
        texture?.destroy();
        texture = device.createTexture({size:[pixelSize,pixelSize],format:'rgba8unorm',usage:GPUTextureUsage.COPY_DST|GPUTextureUsage.TEXTURE_BINDING|GPUTextureUsage.RENDER_ATTACHMENT});
        context.configure({device,format,alphaMode:'opaque'});
      }
      glass.x = glass.y = padding; glass.width = rect.width; glass.height = rect.height; glass.cornerRadius = rect.width / 2;
      const washOpacity = parseFloat(getComputedStyle(actions.querySelector('.participant-actions__wash')).opacity) || 0;
      paintRoomBackdrop(ctx, room, region, dpr, washOpacity);
      device.queue.copyExternalImageToTexture({source},{texture},[pixelSize,pixelSize]);
      core.render({scene,width:pixelSize,height:pixelSize,dpr,outputTexture:context.getCurrentTexture(),backdropTexture:texture});
      if (ready) {
        button.classList.add('has-liquid-glass'); button.dataset.glass = 'webgpu'; delete button.dataset.glassReason;
      }
      return true;
    }
    const firstPaint = draw();
    const validationError = await device.popErrorScope();
    if (validationError) throw validationError;
    await device.queue.onSubmittedWorkDone();
    if (disposed) return;
    ready = true;
    if (firstPaint) { button.classList.add('has-liquid-glass'); button.dataset.glass = 'webgpu'; delete button.dataset.glassReason; }
    function tick(now) {
      frame = 0; if (disposed || document.hidden) return;
      try { drawing = true; draw(); } catch (_) { destroy('render-error'); return; } finally { drawing = false; }
      if (now < warmUntil) frame = requestAnimationFrame(tick);
    }
    function invalidate() {
      if (disposed || drawing) return;
      warmUntil = performance.now() + 360;
      if (!frame && !document.hidden) frame = requestAnimationFrame(tick);
    }
    observer = new MutationObserver(invalidate);
    observer.observe(room, {subtree:true,childList:true,attributes:true,attributeFilter:['style','class']});
    room.addEventListener('load', invalidate, {capture:true,signal:controller.signal});
    observer.observe(actions, {attributes:true,attributeFilter:['class']});
    observer.observe(document.body, {attributes:true,attributeFilter:['class']});
    const sheet = document.querySelector('.ev-sheet');
    if (sheet) observer.observe(sheet,{attributes:true,attributeFilter:['hidden','style']});
    for (const type of ['resize', 'scroll']) window.addEventListener(type, invalidate, {passive:true,signal:controller.signal});
    for (const type of ['pointerover','pointerout']) room.addEventListener(type,invalidate,{passive:true,signal:controller.signal});
    document.addEventListener('visibilitychange',invalidate,{signal:controller.signal});
    invalidate();
  } catch (_) { destroy('initialization-failed'); }
}
transparency.addEventListener('change', enhance);
forcedColors.addEventListener('change', enhance);
window.addEventListener('pagehide', () => dispose());
window.addEventListener('pageshow', e => { if (e.persisted) enhance(); });
enhance();
