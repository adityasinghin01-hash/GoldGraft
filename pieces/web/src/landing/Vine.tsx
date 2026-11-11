import { useEffect, useRef } from 'react';
import { gsap, reducedMotion } from '../motion/scroll';
import s from './vine.module.css';

type Side = 'L' | 'R' | 'C';

/**
 * The gold graft line. It starts at the Check box and grows down the page as you
 * scroll, touching every chapter's anchor ([data-vine]) and putting out a leaf there,
 * so the sections read as one living plant instead of separate boxes.
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
      const vh = window.innerHeight;
      svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
      svg.style.height = `${H}px`;
      const margin = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--gg-margin')) || 84;
      const L = Math.max(14, margin * 0.5);
      const R = W - L;
      const lane = (side: Side) => (side === 'L' ? L : side === 'R' ? R : W * 0.7);
      type A = { y: number; side: Side; secTop: number; secBottom: number; padTop: number; padBottom: number; x0?: number };
      const anchors: A[] = [];
      root.querySelectorAll<HTMLElement>('[data-vine]').forEach((el) => {
        const r = el.getBoundingClientRect();
        const sec = (el.closest('section, footer') as HTMLElement) ?? el;
        const sr = sec.getBoundingClientRect();
        const cs = getComputedStyle(sec);
        const mid = r.left - rootBox.left + r.width / 2;
        const side: Side = el.dataset.vine === 'final' ? 'C' : mid > W * 0.55 ? 'R' : 'L';
        anchors.push({
          y: r.top - rootBox.top + Math.min(36, r.height * 0.3), side,
          secTop: sr.top - rootBox.top, secBottom: sr.bottom - rootBox.top,
          padTop: parseFloat(cs.paddingTop) || 0, padBottom: parseFloat(cs.paddingBottom) || 0,
          x0: r.left - rootBox.left,
        });
      });
      if (anchors.length < 2) return;
      const fin = anchors[anchors.length - 1];
      if (fin.side === 'C') fin.y = fin.secTop + vh * 0.42; // the mark's centre when the final chapter fills the screen

      const sway = (i: number) => (i % 2 ? 9 : -9);
      const a0 = anchors[0];
      let x = lane(a0.side), y = a0.y;
      let d = `M ${(a0.x0 ?? x) - 8} ${a0.y} C ${(a0.x0 ?? x) - 30} ${a0.y}, ${x} ${a0.y - 10}, ${x} ${a0.y + 30}`;
      y = a0.y + 30;
      const down = (toY: number, i: number) => {
        if (toY <= y) return;
        const dy = toY - y;
        d += ` C ${x + sway(i)} ${y + dy * 0.33}, ${x - sway(i)} ${y + dy * 0.66}, ${x} ${toY}`;
        y = toY;
      };
      for (let i = 1; i < anchors.length; i++) {
        const prev = anchors[i - 1], b = anchors[i];
        if (b.side !== prev.side) {
          // cross only through empty space: the padding between two chapters
          const yStart = Math.max(y + 10, prev.secBottom - prev.padBottom * 0.7);
          const yEnd = Math.max(yStart + 80, b.side === 'C' ? b.y - vh * 0.2 : b.secTop + Math.max(b.padTop * 0.7, 60));
          down(yStart, i);
          const nx = lane(b.side);
          d += ` C ${x} ${yStart + (yEnd - yStart) * 0.55}, ${nx} ${yEnd - (yEnd - yStart) * 0.55}, ${nx} ${yEnd}`;
          x = nx; y = yEnd;
        }
        down(b.side === 'C' ? b.y : b.y, i);
      }
      path.setAttribute('d', d);
      glow.setAttribute('d', d);
      total = path.getTotalLength();
      lookup = [];
      for (let l = 0; l <= total; l += 16) lookup.push({ y: path.getPointAtLength(l).y, len: l });
      lookup.push({ y: path.getPointAtLength(total).y, len: total });

      // a leaf beside each chapter, turned toward its content
      leavesG.replaceChildren();
      leaves = anchors.map((a, i) => {
        const lx = lane(a.side);
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('transform', `translate(${lx} ${a.y})`);
        const inner = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        inner.setAttribute('class', s.leaf);
        const flip = a.side === 'R' ? -1 : 1;
        inner.innerHTML = a.side === 'C'
          ? `<circle r="5" class="${s.node}"/>`
          : `<circle r="3.2" class="${s.node}"/><path class="${s.leafShape}" d="M0 0 C ${9 * flip} -11, ${22 * flip} -12, ${28 * flip} -4 C ${19 * flip} 3, ${8 * flip} 4, 0 0 Z"/>`;
        g.appendChild(inner);
        leavesG.appendChild(g);
        let best = 0, bestD = Infinity;
        for (const k of lookup) { const dd = Math.abs(k.y - a.y); if (dd < bestD) { bestD = dd; best = k.len; } }
        if (i === 0) best = 0;
        return { len: best, el: inner };
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
      tip.style.opacity = shown > 4 && shown < total - 4 ? '1' : '0';
      for (const l of leaves) l.el.toggleAttribute('data-on', shown >= l.len - 2);
    };

    const tick = () => {
      if (still) return;
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
        <filter id="vineBlur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5" /></filter>
      </defs>
      <path data-v="glow" className={s.glow} filter="url(#vineBlur)" />
      <path data-v="stem" className={s.stem} stroke="url(#vineGrad)" />
      <g data-v="leaves" />
      <circle data-v="tip" r="4" className={s.tip} />
    </svg>
  );
}
