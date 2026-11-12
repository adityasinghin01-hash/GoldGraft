// The GoldGraft mark: an older rootstock rising from the lower left, a young scion
// continuing to the upper right, joined at a diagonal cut sealed by a line of light,
// inside a thin seal ring. Shared by the header logo, the favicon and the world's
// final "reveal" state, so the shape the dust gathers into is the brand itself.

export const MARK_VIEWBOX = 64;
export const MARK = {
  ring: { cx: 32, cy: 32, r: 29 },
  root: 'M20.5 53.5 C 22.6 46.4, 25.8 40.4, 30.3 35.7',
  scion: 'M33.6 32.4 C 37.4 27.9, 40.2 21.6, 41.6 13.2',
  leaf: 'M41.3 18.4 C 45.6 14.9, 50.2 15.4, 52.6 18.9 C 48.6 21.4, 44.4 21.4, 41.3 18.4 Z',
  seam: 'M27.4 37.9 L 36.9 30.1',
} as const;

export function drawMark(ctx: CanvasRenderingContext2D, w: number, h: number) {
  const s = Math.min(w, h) / MARK_VIEWBOX;
  ctx.save();
  ctx.translate((w - MARK_VIEWBOX * s) / 2, (h - MARK_VIEWBOX * s) / 2);
  ctx.scale(s, s);
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.strokeStyle = 'rgb(150,150,150)';
  ctx.lineWidth = 1.1;
  ctx.beginPath();
  ctx.arc(MARK.ring.cx, MARK.ring.cy, MARK.ring.r, 0, Math.PI * 2);
  ctx.stroke();
  ctx.strokeStyle = 'rgb(210,210,210)';
  ctx.lineWidth = 5.2;
  ctx.stroke(new Path2D(MARK.root));
  ctx.lineWidth = 3.4;
  ctx.stroke(new Path2D(MARK.scion));
  ctx.fillStyle = 'rgb(190,190,190)';
  ctx.fill(new Path2D(MARK.leaf));
  ctx.strokeStyle = '#fff';
  ctx.lineWidth = 1.8;
  ctx.shadowColor = '#fff';
  ctx.shadowBlur = 6;
  ctx.stroke(new Path2D(MARK.seam));
  ctx.restore();
}
