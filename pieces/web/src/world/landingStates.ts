import { drawMark } from './mark';
import type { StateDef } from './states';

// Every picture the dust becomes on the landing page, in story order.
// Photos live in /public/world (generated for GoldGraft, see CREDITS.md).
// Layout: cx, cy in -1..1 of the viewport (0,0 = centre); h = share of viewport height.

const img = (name: string) => `/world/${name}.jpg`;

function codeLines(ctx: CanvasRenderingContext2D, w: number, h: number, seed: number, hot: number[], tidy: boolean) {
  let s = seed;
  const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
  const rows = 14;
  const lh = h / (rows + 1);
  ctx.lineCap = 'round';
  for (let i = 0; i < rows; i++) {
    const y = lh * (i + 0.8);
    let x = w * 0.08 + (tidy ? (i % 4 === 0 ? 0 : w * 0.05) : rnd() * w * 0.12);
    const isHot = hot.includes(i);
    const segs = 1 + Math.floor(rnd() * 3);
    for (let k = 0; k < segs; k++) {
      const len = w * (0.06 + rnd() * (tidy ? 0.2 : 0.26));
      if (x + len > w * 0.92) break;
      ctx.strokeStyle = isHot ? 'rgb(255,255,255)' : tidy ? 'rgb(170,170,170)' : 'rgb(110,110,110)';
      ctx.lineWidth = isHot ? 3.2 : 1.6;
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + len, y); ctx.stroke();
      if (isHot) { ctx.lineWidth = 1; ctx.strokeStyle = 'rgb(200,200,200)'; ctx.strokeRect(x - 8, y - lh * 0.36, len + 16, lh * 0.72); }
      x += len + w * 0.025;
    }
  }
}

function ring(c: CanvasRenderingContext2D, x: number, y: number, r: number, lw: number, color: string) {
  c.strokeStyle = color; c.lineWidth = lw; c.beginPath(); c.arc(x, y, r, 0, Math.PI * 2); c.stroke();
}

function pill(c: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, color: string, lw = 1.6) {
  c.strokeStyle = color; c.lineWidth = lw; c.beginPath(); c.roundRect(x, y, w, h, h / 2); c.stroke();
}

export const LANDING_STATES: StateDef[] = [
  { id: 'cloud', source: { kind: 'cloud' }, layout: { cx: 0, cy: 0, h: 1 }, motion: { drift: 1.4, swirl: 0.25, flow: 0, fall: 0 }, silk: { intensity: 0.75, warm: 0.1, pointer: 0.5 } },

  // 1 Hero — the graft union, the shop as a living tree
  { id: 'graft', source: { kind: 'image', src: img('01-graft-union'), threshold: 0.075, gamma: 1.1, depth: 0.9 },
    layout: { cx: 0.5, cy: -0.16, h: 0.86 }, layoutNarrow: { cx: 0.15, cy: 0.38, h: 0.62 },
    motion: { drift: 1, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 1, warm: 0.15, pointer: 0.8 } },

  // 2 Proof — the tree rings: time is running out
  { id: 'rings', source: { kind: 'image', src: img('02-tree-rings'), threshold: 0.06, gamma: 1.2, depth: 0.5 },
    layout: { cx: -0.5, cy: 0, h: 0.95 }, layoutNarrow: { cx: 0, cy: 0.35, h: 0.55 },
    motion: { drift: 0.6, swirl: 0.55, flow: 0, fall: 0 }, silk: { intensity: 0.8, warm: 0.05, pointer: 0.6 } },

  // 3 Problem — the old branch dying, ash falling
  { id: 'dying', source: { kind: 'image', src: img('03-dying-branch'), threshold: 0.07, gamma: 1.05, depth: 0.6 },
    layout: { cx: 0.38, cy: 0.12, h: 0.92 }, layoutNarrow: { cx: 0.1, cy: 0.4, h: 0.6 },
    motion: { drift: 0.8, swirl: 0, flow: 0, fall: 1 }, silk: { intensity: 0.55, warm: 0, pointer: 0.45 } },

  // 4 Graft — the cut is bound and sealed
  { id: 'binding', source: { kind: 'image', src: img('04-binding'), threshold: 0.07, gamma: 1.15, depth: 0.8 },
    layout: { cx: 0, cy: 0.02, h: 1.0 }, layoutNarrow: { cx: 0, cy: 0.25, h: 0.7 },
    motion: { drift: 0.7, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 1.1, warm: 0.35, pointer: 0.8 } },

  // 5 Features — the dust acts out what GoldGraft does
  { id: 'f-find', source: { kind: 'draw', aspect: 1.3, draw: (c, w, h) => codeLines(c, w, h, 11, [3, 8, 11], false) },
    layout: { cx: 0.44, cy: 0.3, h: 0.46 }, motion: { drift: 0.4, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 0.65, warm: 0, pointer: 0.4 } },
  { id: 'f-write', source: { kind: 'draw', aspect: 1.3, draw: (c, w, h) => codeLines(c, w, h, 29, [2, 3, 4, 8, 9, 12, 13], true) },
    layout: { cx: 0.44, cy: 0.3, h: 0.46 }, motion: { drift: 0.4, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 0.7, warm: 0.2, pointer: 0.4 } },
  { id: 'f-prove', source: { kind: 'draw', aspect: 1.35, draw: (c, w, h) => {
      for (let col = 0; col < 3; col++) for (let row = 0; row < 6; row++) {
        const x = w * (0.08 + col * 0.3), y = h * (0.1 + row * 0.14);
        pill(c, x, y, w * 0.24, h * 0.08, col === 2 ? 'rgb(255,255,255)' : 'rgb(170,170,170)', col === 2 ? 2.4 : 1.6);
        if (row < 5) { c.strokeStyle = 'rgb(90,90,90)'; c.lineWidth = 1; c.setLineDash([2, 5]); c.beginPath(); c.moveTo(x + w * 0.12, y + h * 0.08); c.lineTo(x + w * 0.12, y + h * 0.14); c.stroke(); c.setLineDash([]); }
      }
    } }, layout: { cx: 0.44, cy: 0.3, h: 0.46 }, motion: { drift: 0.3, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 0.7, warm: 0.1, pointer: 0.4 } },
  { id: 'f-bugs', source: { kind: 'draw', aspect: 1.33, draw: (c, w, h) => {
      for (let i = 0; i < 12; i++) {
        const cx = w * (0.17 + (i % 4) * 0.22), cy = h * (0.2 + Math.floor(i / 4) * 0.3), r = h * 0.1;
        ring(c, cx, cy, r, 1.8, 'rgb(210,210,210)');
        ring(c, cx, cy, r * 0.62, 1, 'rgb(120,120,120)');
        c.fillStyle = 'rgb(255,255,255)'; c.beginPath(); c.arc(cx, cy, r * 0.16, 0, Math.PI * 2); c.fill();
      }
    } }, layout: { cx: 0.44, cy: 0.3, h: 0.44 }, motion: { drift: 0.3, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 0.7, warm: 0.15, pointer: 0.4 } },
  { id: 'f-oldbug', source: { kind: 'draw', aspect: 1.35, draw: (c, w, h) => {
      for (let col = 0; col < 2; col++) for (let row = 0; row < 6; row++) {
        const x = w * (0.12 + col * 0.44), y = h * (0.1 + row * 0.14);
        const hot = row === 3;
        pill(c, x, y, w * 0.32, h * 0.08, hot ? 'rgb(255,255,255)' : 'rgb(95,95,95)', hot ? 2.6 : 1.3);
      }
      c.strokeStyle = 'rgb(255,255,255)'; c.lineWidth = 2;
      c.beginPath(); c.moveTo(w * 0.46, h * 0.56); c.lineTo(w * 0.54, h * 0.56); c.lineTo(w * 0.515, h * 0.535); c.moveTo(w * 0.54, h * 0.56); c.lineTo(w * 0.515, h * 0.585); c.stroke();
    } }, layout: { cx: 0.44, cy: 0.3, h: 0.46 }, motion: { drift: 0.3, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 0.7, warm: 0.25, pointer: 0.4 } },
  { id: 'f-golive', source: { kind: 'draw', aspect: 2.2, draw: (c, w, h) => {
      c.lineCap = 'round';
      for (let i = 0; i < 9; i++) {
        const y = h * (0.22 + i * 0.07);
        const hot = i >= 3 && i <= 5;
        c.strokeStyle = hot ? 'rgb(240,240,240)' : 'rgb(100,100,100)'; c.lineWidth = hot ? 2.2 : 1.2;
        c.setLineDash(hot ? [w * 0.05, w * 0.02] : [w * 0.02, w * 0.03]);
        c.beginPath(); c.moveTo(w * 0.02, y); c.lineTo(w * 0.98, y); c.stroke();
      }
      c.setLineDash([]);
    } }, layout: { cx: 0.44, cy: 0.3, h: 0.36 }, motion: { drift: 0.2, swirl: 0, flow: 1, fall: 0 }, silk: { intensity: 0.75, warm: 0.2, pointer: 0.4 } },
  { id: 'f-cert', source: { kind: 'draw', aspect: 1, draw: drawMark, depth: 0.25 },
    layout: { cx: 0.44, cy: 0.3, h: 0.46 }, motion: { drift: 0.25, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 0.85, warm: 0.4, pointer: 0.5 } },

  // 6 Steps — a sapling grows
  { id: 'sapling', source: { kind: 'image', src: img('06-sapling'), threshold: 0.07, gamma: 1.1, depth: 0.6 },
    layout: { cx: -0.55, cy: -0.05, h: 0.95 }, layoutNarrow: { cx: 0, cy: 0.35, h: 0.6 },
    motion: { drift: 0.9, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 0.75, warm: 0.1, pointer: 0.6 } },

  // 7 FAQ — shade under the canopy: sparse and slow
  { id: 'canopy', source: { kind: 'cloud' }, layout: { cx: 0, cy: 0, h: 1 }, motion: { drift: 0.5, swirl: 0.08, flow: 0, fall: 0 }, silk: { intensity: 0.4, warm: 0, pointer: 0.3 } },

  // 8 Final — the reveal: all the dust gathers into the healed graft, in bloom
  { id: 'bloom', source: { kind: 'image', src: img('05-bloom'), threshold: 0.07, gamma: 1.05, depth: 0.8 },
    layout: { cx: 0.02, cy: 0.2, h: 0.82 }, layoutNarrow: { cx: 0, cy: 0.3, h: 0.55 },
    motion: { drift: 0.5, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 1.15, warm: 0.45, pointer: 0.9 } },
  { id: 'mark', source: { kind: 'draw', aspect: 1, draw: drawMark, depth: 0.3 },
    layout: { cx: 0, cy: 0.1, h: 0.66 }, layoutNarrow: { cx: 0, cy: 0.3, h: 0.5 },
    motion: { drift: 0.35, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 1.15, warm: 0.45, pointer: 0.9 } },

  // 9 Footer — roots
  { id: 'roots', source: { kind: 'image', src: img('07-roots'), threshold: 0.06, gamma: 1.1, depth: 0.5 },
    layout: { cx: 0, cy: -0.42, h: 0.7 }, motion: { drift: 0.6, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 0.55, warm: 0.1, pointer: 0.5 } },
];
