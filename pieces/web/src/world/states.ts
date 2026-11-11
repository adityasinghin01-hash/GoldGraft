// A "state" is one picture made of dust: N points (x, y, z, brightness) plus a colour each,
// in state space where y spans -1..1 and x spans -aspect..aspect of the source picture.
// Photos are sampled by brightness AND edges, so silhouettes and details (bark, binding,
// petals, ring lines) carry the most dust and the picture stays recognisable.

export type Motion = { drift: number; swirl: number; flow: number; fall: number };
export type Layout = { cx: number; cy: number; h: number }; // cx, cy in -1..1 of the viewport; h = share of viewport height

export type StateDef = {
  id: string;
  source: { kind: 'image'; src: string; threshold?: number; gamma?: number; depth?: number; plate?: number }
        | { kind: 'draw'; aspect: number; draw: (ctx: CanvasRenderingContext2D, w: number, h: number) => void; depth?: number }
        | { kind: 'cloud' };
  layout: Layout;
  layoutNarrow?: Layout;
  motion: Motion;
  silk: { intensity: number; warm: number; pointer: number };
};

export type PointState = { data: Float32Array; color: Float32Array; aspect: number };

const SAMPLE_W = 720;
const GOLD = [0.80, 0.745, 0.61];

function sampleCanvas(canvas: HTMLCanvasElement, n: number, threshold: number, gamma: number, depth: number, photo: boolean): PointState {
  const ctx = canvas.getContext('2d', { willReadFrequently: true })!;
  const { width: w, height: h } = canvas;
  const px = ctx.getImageData(0, 0, w, h).data;
  const lum = new Float32Array(w * h);
  for (let i = 0; i < w * h; i++) lum[i] = (0.2126 * px[i * 4] + 0.7152 * px[i * 4 + 1] + 0.0722 * px[i * 4 + 2]) / 255;

  // weight = brightness term + edge term (Sobel-ish), only on the subject
  const weights = new Float32Array(w * h);
  let total = 0;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const i = y * w + x;
      const L = lum[i];
      let v = 0;
      if (L > threshold) {
        v = Math.pow((L - threshold) / (1 - threshold), gamma) * 0.55;
        if (x > 0 && y > 0 && x < w - 1 && y < h - 1) {
          const gx = lum[i + 1] - lum[i - 1];
          const gy = lum[i + w] - lum[i - w];
          v += Math.min(1, Math.sqrt(gx * gx + gy * gy) * 4) * (photo ? 0.9 : 0.4);
        }
      }
      total += v;
      weights[i] = total;
    }
  }
  const aspect = w / h;
  const out = new Float32Array(n * 4);
  const col = new Float32Array(n * 3);
  if (total <= 0) return { data: out, color: col.fill(0.6), aspect };
  for (let k = 0; k < n; k++) {
    const target = Math.random() * total;
    let lo = 0, hi = weights.length - 1;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (weights[mid] < target) lo = mid + 1; else hi = mid; }
    const x = lo % w, y = (lo / w) | 0;
    const L = lum[lo];
    out[k * 4] = ((x + Math.random()) / w - 0.5) * 2 * aspect;
    out[k * 4 + 1] = -((y + Math.random()) / h - 0.5) * 2;
    out[k * 4 + 2] = (L - 0.45) * depth + (Math.random() - 0.5) * depth * 0.3;
    out[k * 4 + 3] = Math.min(1, 0.18 + L * 1.1);
    if (photo) {
      // the photo's own colour, lifted a little so dark bark still glows
      const lift = 1.15 + (1 - L) * 0.5;
      col[k * 3] = Math.min(1, (px[lo * 4] / 255) * lift);
      col[k * 3 + 1] = Math.min(1, (px[lo * 4 + 1] / 255) * lift);
      col[k * 3 + 2] = Math.min(1, (px[lo * 4 + 2] / 255) * lift);
    } else {
      const t = 0.55 + L * 0.45;
      col[k * 3] = GOLD[0] * t; col[k * 3 + 1] = GOLD[1] * t; col[k * 3 + 2] = GOLD[2] * t;
    }
  }
  return { data: out, color: col, aspect };
}

async function loadImage(src: string): Promise<HTMLCanvasElement> {
  const img = new Image();
  img.decoding = 'async';
  img.src = src;
  await img.decode();
  const w = SAMPLE_W;
  const h = Math.round((img.naturalHeight / img.naturalWidth) * w);
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  c.getContext('2d')!.drawImage(img, 0, 0, w, h);
  return c;
}

function cloud(n: number): PointState {
  const out = new Float32Array(n * 4);
  const col = new Float32Array(n * 3);
  for (let k = 0; k < n; k++) {
    out[k * 4] = (Math.random() * 2 - 1) * 2.2;
    out[k * 4 + 1] = (Math.random() * 2 - 1) * 1.15;
    out[k * 4 + 2] = (Math.random() * 2 - 1) * 1.6;
    out[k * 4 + 3] = Math.pow(Math.random(), 3.2) * 0.75;
    col[k * 3] = GOLD[0]; col[k * 3 + 1] = GOLD[1]; col[k * 3 + 2] = GOLD[2];
  }
  return { data: out, color: col, aspect: 2.2 };
}

export async function buildState(def: StateDef, n: number): Promise<PointState> {
  const s = def.source;
  if (s.kind === 'cloud') return cloud(n);
  if (s.kind === 'image') {
    try {
      const c = await loadImage(s.src);
      return sampleCanvas(c, n, s.threshold ?? 0.09, s.gamma ?? 1.15, s.depth ?? 0.5, true);
    } catch {
      return cloud(n); // picture missing: stay as calm dust rather than break the page
    }
  }
  const h = 420;
  const w = Math.round(h * s.aspect);
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const ctx = c.getContext('2d', { willReadFrequently: true })!;
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, w, h);
  s.draw(ctx, w, h);
  return sampleCanvas(c, n, 0.06, 1.0, s.depth ?? 0.35, false);
}
