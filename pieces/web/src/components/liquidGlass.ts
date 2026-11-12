import { useEffect, type RefObject } from 'react';

// Liquid glass refraction (Chromium only): the backdrop bends at the rim of a rounded shape,
// like the edge of a thick lens. A displacement map is drawn for the element's real size and
// radius, and the element's backdrop-filter runs it through an SVG filter:
//   blur → bend at the rim (feDisplacementMap) → richer colour.
// Other browsers keep the plain CSS blur from .gg-lg, which already reads as glass.

const SVG_NS = 'http://www.w3.org/2000/svg';
let host: SVGSVGElement | null = null;
let seq = 0;

export function refractionSupported(): boolean {
  if (typeof navigator === 'undefined') return false;
  const brands = (navigator as Navigator & { userAgentData?: { brands: { brand: string }[] } }).userAgentData?.brands ?? [];
  return brands.some((b) => /Chromium|Google Chrome|Microsoft Edge/.test(b.brand));
}

function defs(): SVGDefsElement {
  if (!host) {
    host = document.createElementNS(SVG_NS, 'svg');
    host.setAttribute('aria-hidden', 'true');
    host.setAttribute('width', '0');
    host.setAttribute('height', '0');
    host.style.cssText = 'position:absolute;width:0;height:0;overflow:hidden;pointer-events:none';
    host.appendChild(document.createElementNS(SVG_NS, 'defs'));
    document.body.appendChild(host);
  }
  return host.firstChild as SVGDefsElement;
}

/** R/G = how far to look outward at each pixel; strongest on the rim, zero in the middle. */
function displacementMap(w: number, h: number, r: number, band: number): string {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const ctx = c.getContext('2d')!;
  const img = ctx.createImageData(w, h);
  const d = img.data;
  const hw = w / 2, hh = h / 2;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      // signed distance to a rounded rectangle (negative inside)
      const px = Math.abs(x + 0.5 - hw) - (hw - r);
      const py = Math.abs(y + 0.5 - hh) - (hh - r);
      const ox = Math.max(px, 0), oy = Math.max(py, 0);
      const dist = Math.hypot(ox, oy) + Math.min(Math.max(px, py), 0) - r;
      const inside = -dist;
      let nx = 0, ny = 0, m = 0;
      if (inside > 0 && inside < band) {
        // outward normal of the nearest edge
        if (px > 0 && py > 0) { const l = Math.hypot(ox, oy) || 1; nx = ox / l; ny = oy / l; }
        else if (px > py) nx = 1; else ny = 1;
        nx *= Math.sign(x + 0.5 - hw) || 1;
        ny *= Math.sign(y + 0.5 - hh) || 1;
        const t = 1 - inside / band;
        m = t * t * (3 - 2 * t); // smooth: full bend at the rim, none past the band
      }
      const i = (y * w + x) * 4;
      d[i] = 128 + nx * m * 127;
      d[i + 1] = 128 + ny * m * 127;
      d[i + 2] = 128;
      d[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  return c.toDataURL();
}

type Opts = { blur?: number; bend?: number; band?: number; saturate?: number };

/** Give one element bending-glass refraction. Returns a cleanup function. */
export function applyLiquidGlass(el: HTMLElement, opts: Opts = {}): () => void {
  if (!refractionSupported() || window.matchMedia('(prefers-reduced-transparency: reduce)').matches) return () => {};
  const id = `gg-lg-${++seq}`;
  const filter = document.createElementNS(SVG_NS, 'filter');
  filter.setAttribute('id', id);
  filter.setAttribute('color-interpolation-filters', 'sRGB');
  for (const [k, v] of [['x', '0%'], ['y', '0%'], ['width', '100%'], ['height', '100%']]) filter.setAttribute(k, v);
  defs().appendChild(filter);
  const blur = opts.blur ?? 7;
  const bend = opts.bend ?? 28;
  const sat = opts.saturate ?? 1.6;

  let lastKey = '';
  const build = () => {
    const w = Math.round(el.offsetWidth), h = Math.round(el.offsetHeight);
    if (w < 4 || h < 4) return;
    const r = Math.min(parseFloat(getComputedStyle(el).borderTopLeftRadius) || 0, h / 2, w / 2);
    const band = Math.min(opts.band ?? 16, h / 2);
    const key = `${w}x${h}x${r}`;
    if (key === lastKey) return;
    lastKey = key;
    filter.innerHTML = `
      <feGaussianBlur in="SourceGraphic" stdDeviation="${blur}" result="soft"/>
      <feImage href="${displacementMap(w, h, r, band)}" x="0" y="0" width="${w}" height="${h}" preserveAspectRatio="none" result="map"/>
      <feDisplacementMap in="soft" in2="map" scale="${bend}" xChannelSelector="R" yChannelSelector="G" result="bent"/>
      <feColorMatrix in="bent" type="saturate" values="${sat}"/>`;
    el.style.setProperty('backdrop-filter', `url(#${id}) brightness(0.92)`);
    el.style.setProperty('-webkit-backdrop-filter', `url(#${id}) brightness(0.92)`);
  };
  build();
  let raf = 0;
  const ro = new ResizeObserver(() => { cancelAnimationFrame(raf); raf = requestAnimationFrame(build); });
  ro.observe(el);
  return () => {
    ro.disconnect();
    cancelAnimationFrame(raf);
    filter.remove();
    el.style.removeProperty('backdrop-filter');
    el.style.removeProperty('-webkit-backdrop-filter');
  };
}


export function useLiquidGlass(ref: RefObject<HTMLElement | null>, opts: Opts = {}) {
  const { blur, bend, band, saturate } = opts;
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    return applyLiquidGlass(el, { blur, bend, band, saturate });
  }, [ref, blur, bend, band, saturate]);
}
