import Lenis from 'lenis';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { SplitText } from 'gsap/SplitText';
import { DrawSVGPlugin } from 'gsap/DrawSVGPlugin';
import { ScrambleTextPlugin } from 'gsap/ScrambleTextPlugin';

gsap.registerPlugin(ScrollTrigger, SplitText, DrawSVGPlugin, ScrambleTextPlugin);

export const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

let lenis: Lenis | null = null;
const listeners = new Set<(y: number) => void>();

/** One clock for smooth scroll, ScrollTrigger and the world (Lenis drives, GSAP ticks). */
export function startSmoothScroll(): Lenis | null {
  if (lenis || reducedMotion()) return lenis;
  lenis = new Lenis({ lerp: 0.14, wheelMultiplier: 1.05, smoothWheel: true, syncTouch: false });
  lenis.on('scroll', () => {
    ScrollTrigger.update();
    for (const l of listeners) l(window.scrollY);
  });
  gsap.ticker.add((time) => lenis?.raf(time * 1000));
  gsap.ticker.lagSmoothing(0);
  return lenis;
}

export function stopSmoothScroll() {
  lenis?.destroy();
  lenis = null;
}

export function onScroll(cb: (y: number) => void): () => void {
  listeners.add(cb);
  const native = () => cb(window.scrollY);
  window.addEventListener('scroll', native, { passive: true });
  return () => { listeners.delete(cb); window.removeEventListener('scroll', native); };
}

export function scrollToTarget(target: string | HTMLElement) {
  const el = typeof target === 'string' ? document.querySelector<HTMLElement>(target) : target;
  if (!el) return;
  if (lenis) lenis.scrollTo(el, { offset: -72, duration: 1.3 });
  else el.scrollIntoView({ behavior: reducedMotion() ? 'auto' : 'smooth', block: 'start' });
}

export { gsap, ScrollTrigger, SplitText };
