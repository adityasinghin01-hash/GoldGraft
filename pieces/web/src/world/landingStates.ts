import { drawMark } from './mark';
import type { StateDef } from './states';

// Every picture the dust becomes on the landing page, in story order.
// Photos live in /public/world (generated for GoldGraft, see CREDITS.md).
// Layout: cx, cy in -1..1 of the viewport (0,0 = centre); h = share of viewport height.

const img = (name: string) => `/world/${name}.jpg`;

/** Growth rings around the feature panel: a soft frame of light, brightest on one ring,
    with fainter, slightly uneven rings inside and out, like the rings of a tree. */
function stageRings(c: CanvasRenderingContext2D, w: number, h: number) {
  let seed = 7;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const cx = w / 2, cy = h / 2;
  for (let i = 0; i < 16; i++) {
    const k = 0.86 + i * 0.022 + (rnd() - 0.5) * 0.01;
    const main = i === 6;
    const lum = main ? 255 : Math.round(200 - Math.abs(i - 6) * 14 - rnd() * 30);
    c.strokeStyle = `rgb(${lum},${lum},${lum})`;
    c.lineWidth = main ? 2.6 : 0.6 + rnd() * 1.1;
    const a0 = rnd() * Math.PI * 2;
    const sweep = main ? Math.PI * 2 : Math.PI * (0.9 + rnd() * 1.1);
    c.beginPath(); c.ellipse(cx, cy, w * 0.42 * k, h * 0.42 * k, 0, a0, a0 + sweep); c.stroke();
  }
}

export const LANDING_STATES: StateDef[] = [
  { id: 'cloud', source: { kind: 'cloud' }, layout: { cx: 0, cy: 0, h: 1 }, motion: { drift: 1.4, swirl: 0.25, flow: 0, fall: 0 }, silk: { intensity: 0.75, warm: 0.1, pointer: 0.5 } },

  // 1 Hero — the graft union, the shop as a living tree
  { id: 'graft', source: { kind: 'image', src: img('01-graft-union'), threshold: 0.075, gamma: 1.1, depth: 0.9 },
    layout: { cx: 0.56, cy: 0.12, h: 0.7 }, layoutNarrow: { cx: 0.15, cy: 0.38, h: 0.62 },
    motion: { drift: 1, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 1, warm: 0.15, pointer: 0.8 } },

  // 2 Proof — the tree rings: time is running out
  { id: 'rings', source: { kind: 'image', src: img('02-tree-rings'), threshold: 0.06, gamma: 1.2, depth: 0.5 },
    layout: { cx: -0.5, cy: 0, h: 0.85 }, layoutNarrow: { cx: 0, cy: 0.35, h: 0.55 },
    motion: { drift: 0.6, swirl: 0.55, flow: 0, fall: 0 }, silk: { intensity: 0.8, warm: 0.05, pointer: 0.6 } },

  // 3 Problem — the old branch dying, ash falling
  { id: 'dying', source: { kind: 'image', src: img('03-dying-branch'), threshold: 0.07, gamma: 1.05, depth: 0.6 },
    layout: { cx: 0.56, cy: 0.05, h: 0.62 }, layoutNarrow: { cx: 0.1, cy: 0.4, h: 0.6 },
    motion: { drift: 0.8, swirl: 0, flow: 0, fall: 1 }, silk: { intensity: 0.55, warm: 0, pointer: 0.45 } },

  // 4 Graft — the cut is bound and sealed
  { id: 'binding', source: { kind: 'image', src: img('04-binding'), threshold: 0.07, gamma: 1.15, depth: 0.8 },
    layout: { cx: 0.4, cy: 0, h: 0.95 }, layoutNarrow: { cx: 0, cy: 0.25, h: 0.7 },
    motion: { drift: 0.7, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 1.1, warm: 0.35, pointer: 0.8 } },

  // 5 Features — one ring of light behind the working panel (cols 7–12), same for all seven
  { id: 'stage', source: { kind: 'draw', aspect: 1.45, draw: stageRings, depth: 0.12 },
    layout: { cx: 0.467, cy: -0.07, h: 0.74 }, motion: { drift: 0.35, swirl: 0.05, flow: 0, fall: 0 }, silk: { intensity: 0.8, warm: 0.25, pointer: 0.5 } },

  // 6 Steps — a sapling grows
  { id: 'sapling', source: { kind: 'image', src: img('06-sapling'), threshold: 0.07, gamma: 1.1, depth: 0.6 },
    layout: { cx: -0.5, cy: 0, h: 0.92 }, layoutNarrow: { cx: 0, cy: 0.35, h: 0.6 },
    motion: { drift: 0.9, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 0.75, warm: 0.1, pointer: 0.6 } },

  // 7 FAQ — shade under the canopy: sparse and slow
  { id: 'canopy', source: { kind: 'cloud' }, layout: { cx: 0, cy: 0, h: 1 }, motion: { drift: 0.5, swirl: 0.08, flow: 0, fall: 0 }, silk: { intensity: 0.4, warm: 0, pointer: 0.3 } },

  // 8 Final — the reveal: all the dust gathers into the healed graft, in bloom
  { id: 'bloom', source: { kind: 'image', src: img('05-bloom'), threshold: 0.07, gamma: 1.05, depth: 0.8 },
    layout: { cx: 0.55, cy: 0.02, h: 0.8 }, layoutNarrow: { cx: 0, cy: 0.3, h: 0.55 },
    motion: { drift: 0.5, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 1.15, warm: 0.45, pointer: 0.9 } },
  { id: 'mark', source: { kind: 'draw', aspect: 1, draw: drawMark, depth: 0.3 },
    layout: { cx: 0, cy: 0.1, h: 0.66 }, layoutNarrow: { cx: 0, cy: 0.3, h: 0.5 },
    motion: { drift: 0.35, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 1.15, warm: 0.45, pointer: 0.9 } },

  // 9 Footer — roots
  { id: 'roots', source: { kind: 'image', src: img('07-roots'), threshold: 0.06, gamma: 1.1, depth: 0.5 },
    layout: { cx: 0, cy: -0.85, h: 0.5 }, motion: { drift: 0.6, swirl: 0, flow: 0, fall: 0 }, silk: { intensity: 0.55, warm: 0.1, pointer: 0.5 } },
];
