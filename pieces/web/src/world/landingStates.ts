import { drawMark } from './mark';
import type { StateDef } from './states';

// Every picture the dust becomes on the landing page, in story order.
// Photos live in /public/world (generated for GoldGraft, see CREDITS.md).
// Layout: cx, cy in -1..1 of the viewport (0,0 = centre); h = share of viewport height.

const img = (name: string) => `/world/${name}.webp`;

function codeLines(ctx: CanvasRenderingContext2D, w: number, h: number, seed: number, hot: number[], tidy: boolean) {
  let s = seed;
  const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
  const rows = 15;
  const lh = h / (rows + 1);
  for (let i = 0; i < rows; i++) {
    const y = lh * (i + 0.6);
    let x = w * 0.08 + (tidy ? (i % 4 === 0 ? 0 : w * 0.05) : rnd() * w * 0.12);
    const isHot = hot.includes(i);
    const segs = 1 + Math.floor(rnd() * 3);
    for (let k = 0; k < segs; k++) {
      const len = w * (0.06 + rnd() * (tidy ? 0.2 : 0.26));
      if (x + len > w * 0.92) break;
      ctx.fillStyle = isHot ? 'rgb(255,255,255)' : tidy ? 'rgb(150,150,150)' : 'rgb(92,92,92)';
      ctx.beginPath();
      ctx.roundRect(x, y, len, lh * 0.36, lh * 0.18);
      ctx.fill();
      x += len + w * 0.025;
    }
  }
}

export const LANDING_STATES: StateDef[] = [
  { id: 'cloud', source: { kind: 'cloud' }, layout: { cx: 0, cy: 0, h: 1 }, motion: { drift: 1.4, swirl: 0.25, flow: 0, fall: 0 }, silk: { intensity: 0.75, warm: 0.1, pointer: 0.5 } },

  // 1 Hero — the graft union, the shop as a living tree
  { id: 'graft', source: { kind: 'image', src: img('01-graft-union'), threshold: 0.075, gamma: 1.1, depth: 0.9 },
    layout: { cx: 0.42, cy: -0.02, h: 1.05 }, layoutNarrow: { cx: 0.15, cy: 0.38, h: 0.62 },
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
        const x = w * (0.1 + col * 0.29), y = h * (0.1 + row * 0.14);
        c.fillStyle = col === 2 ? 'rgb(255,255,255)' : 'rgb(160,160,160)';
        c.beginPath(); c.roundRect(x, y, w * 0.22, h * 0.07, h * 0.035); c.fill();
      }
    } }, layout: { cx: 0.44, cy: 0.3, h: 0.46 }, motion: { drift: 0.3, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 0.7, warm: 0.1, pointer: 0.4 } },
  { id: 'f-bugs', source: { kind: 'draw', aspect: 1.33, draw: (c, w, h) => {
      for (let i = 0; i < 12; i++) {
        const cx = w * (0.17 + (i % 4) * 0.22), cy = h * (0.2 + Math.floor(i / 4) * 0.3), r = h * 0.1;
        c.strokeStyle = 'rgb(200,200,200)'; c.lineWidth = h * 0.012; c.beginPath(); c.arc(cx, cy, r, 0, Math.PI * 2); c.stroke();
        c.fillStyle = i === 7 ? 'rgb(90,90,90)' : 'rgb(255,255,255)'; c.beginPath(); c.arc(cx, cy, r * 0.32, 0, Math.PI * 2); c.fill();
      }
    } }, layout: { cx: 0.44, cy: 0.3, h: 0.44 }, motion: { drift: 0.3, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 0.7, warm: 0.15, pointer: 0.4 } },
  { id: 'f-oldbug', source: { kind: 'draw', aspect: 1.35, draw: (c, w, h) => {
      for (let col = 0; col < 2; col++) for (let row = 0; row < 6; row++) {
        const x = w * (0.16 + col * 0.42), y = h * (0.1 + row * 0.14);
        const hot = row === 3;
        c.fillStyle = hot ? (col === 0 ? 'rgb(255,255,255)' : 'rgb(235,235,235)') : 'rgb(80,80,80)';
        c.beginPath(); c.roundRect(x, y, w * 0.3, h * 0.07, h * 0.035); c.fill();
      }
      c.strokeStyle = 'rgb(255,255,255)'; c.lineWidth = h * 0.01;
      c.beginPath(); c.moveTo(w * 0.47, h * 0.555); c.lineTo(w * 0.57, h * 0.555); c.stroke();
    } }, layout: { cx: 0.44, cy: 0.3, h: 0.46 }, motion: { drift: 0.3, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 0.7, warm: 0.25, pointer: 0.4 } },
  { id: 'f-golive', source: { kind: 'draw', aspect: 2.2, draw: (c, w, h) => {
      const g = c.createLinearGradient(0, 0, w, 0);
      g.addColorStop(0, 'rgb(120,120,120)'); g.addColorStop(0.5, 'rgb(230,230,230)'); g.addColorStop(1, 'rgb(120,120,120)');
      c.fillStyle = g; c.fillRect(0, h * 0.38, w, h * 0.24);
      c.fillStyle = 'rgb(70,70,70)'; c.fillRect(0, h * 0.2, w, h * 0.08); c.fillRect(0, h * 0.72, w, h * 0.08);
    } }, layout: { cx: 0.44, cy: 0.3, h: 0.36 }, motion: { drift: 0.2, swirl: 0, flow: 1, fall: 0 }, silk: { intensity: 0.75, warm: 0.2, pointer: 0.4 } },
  { id: 'f-cert', source: { kind: 'draw', aspect: 1, draw: drawMark, depth: 0.25 },
    layout: { cx: 0.44, cy: 0.3, h: 0.46 }, motion: { drift: 0.25, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 0.85, warm: 0.4, pointer: 0.5 } },

  // 6 Steps — a sapling grows
  { id: 'sapling', source: { kind: 'image', src: img('06-sapling'), threshold: 0.07, gamma: 1.1, depth: 0.6 },
    layout: { cx: -0.55, cy: -0.05, h: 0.95 }, layoutNarrow: { cx: 0, cy: 0.35, h: 0.6 },
    motion: { drift: 0.9, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 0.75, warm: 0.1, pointer: 0.6 } },

  // 7 FAQ — shade under the canopy: sparse and slow
  { id: 'canopy', source: { kind: 'cloud' }, layout: { cx: 0, cy: 0, h: 1 }, motion: { drift: 0.5, swirl: 0.08, flow: 0, fall: 0 }, silk: { intensity: 0.4, warm: 0, pointer: 0.3 } },

  // 8 Final — the reveal: all the dust becomes the GoldGraft mark
  { id: 'mark', source: { kind: 'draw', aspect: 1, draw: drawMark, depth: 0.3 },
    layout: { cx: 0, cy: 0.1, h: 0.66 }, layoutNarrow: { cx: 0, cy: 0.3, h: 0.5 },
    motion: { drift: 0.35, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 1.15, warm: 0.45, pointer: 0.9 } },

  // 9 Footer — roots
  { id: 'roots', source: { kind: 'image', src: img('07-roots'), threshold: 0.06, gamma: 1.1, depth: 0.5 },
    layout: { cx: 0, cy: -0.42, h: 0.7 }, motion: { drift: 0.6, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 0.55, warm: 0.1, pointer: 0.5 } },
];
