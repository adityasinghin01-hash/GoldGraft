import { useEffect, useRef } from 'react';
import { gsap, reducedMotion } from '../motion/scroll';
import s from './vine.module.css';

/**
 * The gold graft line. It leaves the hero's Check box, grows down the left margin lane as you
 * scroll (a leaf opens at each chapter, [data-vine]) and ends in the final Check button:
 * the page starts and ends at the same action.
 */
export function Vine({ rootRef }: { rootRef: React.RefObject<HTMLElement | null> }) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const root = rootRef.current;
    const svg = svgRef.current;
    if (!root || !svg) return;
    const path = svg.querySelector<SVGPathElement>('[data-v="stem"]')!;
    const glow = svg.querySelector<SVGPathElement>('[data-v="glow"]')!;
    const tip = svg.querySelector<SVGCircleElement>('[data-v="tip"]')!;
    const leavesG = svg.querySelector<SVGGElement>('[data-v="leaves"]')!;
    const halo = svg.querySelector<SVGCircleElement>('[data-v="halo"]')!;
    const sap = [...svg.querySelectorAll<SVGCircleElement>('[data-v="sap"] circle')];
    const still = reducedMotion();

    let total = 1;
    let lookup: { y: number; len: number }[] = [];
    let leaves: { len: number; el: SVGGElement }[] = [];
    let shown = 0;
    let target = 0;

    const build = () => {
      const rootBox = root.getBoundingClientRect();
      const W = root.clientWidth;
      const H = root.scrollHeight;
      svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
      svg.style.height = `${H}px`;
      const margin = parseFloat(getComputedStyle(root).getPropertyValue('--gg-margin')) || 60;
      // the stem lives in the left margin lane only: it never crosses a picture or a line of text
      const lane = Math.max(10, margin * 0.5);
      const els = [...root.querySelectorAll<HTMLElement>('[data-vine]')];
      if (els.length < 2) return;
      const box = (el: HTMLElement) => {
        const r = el.getBoundingClientRect();
        return { x: r.left - rootBox.left, y: r.top - rootBox.top, h: r.height };
      };
      const first = box(els[0]);
      const last = box(els[els.length - 1]);
      // start: out of the Check box's left edge, at the field's middle; end: into the final button
      const sx = first.x - 6, sy = first.y + 52;
      const ex = last.x - 6, ey = last.y + 24;
      let d = `M ${sx} ${sy} C ${sx - 18} ${sy}, ${lane} ${sy + 6}, ${lane} ${sy + 46}`;
      let y = sy + 46;
      const stops = els.slice(1, -1).map((el) => box(el).y + 18).filter((v) => v > y + 40 && v < ey - 80);
      stops.push(ey - 52);
      stops.forEach((to, i) => {
        const dy = to - y;
        const sway = (i % 2 ? 1 : -1) * Math.min(6, margin * 0.12);
        d += ` C ${lane + sway} ${y + dy * 0.33}, ${lane - sway} ${y + dy * 0.66}, ${lane} ${to}`;
        y = to;
      });
      d += ` C ${lane} ${ey - 12}, ${ex - 18} ${ey}, ${ex} ${ey}`;
      path.setAttribute('d', d);
      glow.setAttribute('d', d);
      total = path.getTotalLength();
      lookup = [];
      for (let l = 0; l <= total; l += 16) lookup.push({ y: path.getPointAtLength(l).y, len: l });
      lookup.push({ y: path.getPointAtLength(total).y, len: total });
      const lenAt = (yy: number) => {
        let best = 0, bestD = Infinity;
        for (const k of lookup) { const dd = Math.abs(k.y - yy); if (dd < bestD) { bestD = dd; best = k.len; } }
        return best;
      };

      // a small leaf at each chapter, opening toward the text; a seal node where the stem ends
      leavesG.replaceChildren();
      const marks = [...stops.slice(0, -1).map((yy) => ({ y: yy, end: false })), { y: ey, end: true }];
      leaves = marks.map((m, i) => {
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        const at = m.end ? { x: ex, y: ey } : { x: lane, y: m.y };
        g.setAttribute('transform', `translate(${at.x} ${at.y})`);
        const inner = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        inner.setAttribute('class', s.leaf);
        const up = i % 2 ? -1 : 1;
        inner.innerHTML = m.end
          ? `<circle r="4.5" class="${s.node}"/>`
          : `<circle r="2.6" class="${s.node}"/><path class="${s.leafShape}" d="M0 0 C 6 ${-8 * up}, 15 ${-9 * up}, 19 ${-3 * up} C 13 ${2 * up}, 6 ${3 * up}, 0 0 Z"/>`;
        g.appendChild(inner);
        leavesG.appendChild(g);
        return { len: m.end ? total : lenAt(m.y), el: inner };
      });
      path.style.strokeDasharray = `${total}`;
      glow.style.strokeDasharray = `${total}`;
      if (still) { shown = total; target = total; }
      paint();
    };

    const lenAtY = (y: number) => {
      if (!lookup.length) return 0;
      if (y <= lookup[0].y) return 0;
      for (let i = 1; i < lookup.length; i++) {
        if (lookup[i].y >= y) {
          const a = lookup[i - 1], b = lookup[i];
          return a.len + ((y - a.y) / Math.max(1, b.y - a.y)) * (b.len - a.len);
        }
      }
      return total;
    };

    const paint = () => {
      path.style.strokeDashoffset = `${total - shown}`;
      glow.style.strokeDashoffset = `${total - shown}`;
      const p = path.getPointAtLength(Math.max(0, shown));
      tip.setAttribute('cx', `${p.x}`);
      tip.setAttribute('cy', `${p.y}`);
      halo.setAttribute('cx', `${p.x}`);
      halo.setAttribute('cy', `${p.y}`);
      const tipOn = shown > 4 && shown < total - 4 ? '1' : '0';
      tip.style.opacity = tipOn;
      halo.style.opacity = tipOn;
      for (const l of leaves) l.el.toggleAttribute('data-on', shown >= l.len - 2);
    };

    // sap: drops of light run down the grown part of the vine, toward the tip
    let sapT = 0;
    const flowSap = () => {
      if (shown < 40) { sap.forEach((c) => (c.style.opacity = '0')); return; }
      sapT += 1;
      sap.forEach((c, i) => {
        const span = Math.min(shown, 1400);
        const off = ((sapT * (2.2 + (i % 3) * 0.6) + i * (span / sap.length)) % span);
        const at = Math.max(0, shown - span + off);
        const q = path.getPointAtLength(at);
        c.setAttribute('cx', `${q.x}`);
        c.setAttribute('cy', `${q.y}`);
        const fade = Math.min(1, off / 120, (span - off) / 120);
        c.style.opacity = String(Math.max(0, fade) * 0.9);
      });
    };

    const tick = () => {
      if (still) return;
      flowSap();
      const rootTop = root.getBoundingClientRect().top + window.scrollY;
      target = lenAtY(window.scrollY + window.innerHeight * 0.72 - rootTop);
      const next = shown + (target - shown) * 0.12;
      if (Math.abs(next - shown) > 0.05) { shown = next; paint(); }
    };

    build();
    const ro = new ResizeObserver(() => build());
    ro.observe(root);
    gsap.ticker.add(tick);
    return () => { ro.disconnect(); gsap.ticker.remove(tick); };
  }, [rootRef]);

  return (
    <svg ref={svgRef} className={s.vine} aria-hidden preserveAspectRatio="none">
      <defs>
        <linearGradient id="vineGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#e9dfc6" />
          <stop offset="0.5" stopColor="#cdbe9c" />
          <stop offset="1" stopColor="#9c8c68" />
        </linearGradient>
      </defs>
      <path data-v="glow" className={s.glow} />
      <path data-v="stem" className={s.stem} stroke="url(#vineGrad)" />
      <g data-v="leaves" />
      <g data-v="sap">{[0, 1, 2, 3, 4, 5].map((i) => <circle key={i} r={i % 2 ? 1.6 : 2.2} className={s.sap} />)}</g>
      <circle data-v="tip" r="4" className={s.tip} />
      <circle data-v="halo" r="14" className={s.halo} />
    </svg>
  );
}
