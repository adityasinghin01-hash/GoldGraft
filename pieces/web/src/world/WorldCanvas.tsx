import { useEffect, useRef, useState } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { World } from './World';
import { Director } from './director';
import type { StateDef } from './states';
import { onScroll, reducedMotion } from '../motion/scroll';
import styles from './WorldCanvas.module.css';

function webglOk(): boolean {
  try {
    const c = document.createElement('canvas');
    return !!(c.getContext('webgl2') || c.getContext('webgl'));
  } catch {
    return false;
  }
}

type Props = {
  states: StateDef[];
  /** state ids to load first (the opening picture) */
  first: string[];
  /** quieter world for app screens: no dust, dimmer light */
  calm?: boolean;
};

/**
 * The living background: one fixed canvas behind the whole page.
 * Silk light always; gold dust that becomes each chapter's picture as you scroll.
 * Falls back to a still CSS field (no WebGL) and to a still frame (reduced motion).
 */
export function WorldCanvas({ states, first, calm = false }: Props) {
  const ref = useRef<HTMLCanvasElement>(null);
  const [mode, setMode] = useState<'live' | 'still' | 'fallback'>('live');

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    if (!webglOk()) { setMode('fallback'); document.documentElement.dataset.worldMode = 'off'; return; }
    const still = reducedMotion();
    setMode(still ? 'still' : 'live');
    document.documentElement.dataset.worldMode = still ? 'still' : 'live';

    const world = new World(canvas);
    const director = new Director();
    if (import.meta.env.DEV) Object.assign(window, { __gg: { world, director } });
    let disposed = false;

    const sync = (y: number) => {
      const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
      world.setScroll(y / max);
      world.setBlend(director.blendAt(y));
      if (still) world.still();
    };
    const measure = () => { director.measure(); sync(window.scrollY); };

    const onResize = () => { world.resize(); measure(); };
    const onMove = (e: PointerEvent) => { if (e.pointerType === 'mouse') world.setPointer(e.clientX, e.clientY, true); };
    const onLeave = () => world.setPointer(window.innerWidth / 2, window.innerHeight / 2, false);
    const onVis = () => world.setVisible(document.visibilityState === 'visible');

    window.addEventListener('resize', onResize);
    if (!still && !calm) {
      window.addEventListener('pointermove', onMove, { passive: true });
      document.documentElement.addEventListener('pointerleave', onLeave);
    }
    document.addEventListener('visibilitychange', onVis);
    const offScroll = onScroll(sync);
    ScrollTrigger.addEventListener('refresh', measure);
    const ro = new ResizeObserver(() => measure());
    ro.observe(document.body);

    // opening: start with calm dust, gather into the first picture once it's ready
    const intro = { v: calm ? 1 : 0 };
    world.setIntro(intro.v);
    measure();

    if (calm) {
      world.load(states.filter((s) => s.id === 'cloud' || s.id === 'canopy'), ['canopy']).then(() => {
        if (disposed) return;
        world.setBlend({ from: 'canopy', to: 'canopy', mix: 0 });
        if (still) world.still(); else world.start();
      });
    } else {
      world.load(states, ['cloud', ...first]).then(() => { if (!disposed) measure(); });
      const waitFirst = async () => {
        await world.load(states.filter((s) => s.id === 'cloud' || first.includes(s.id)), ['cloud', ...first]);
        if (disposed) return;
        measure();
        if (still) { world.setIntro(1); world.still(); return; }
        world.start();
        gsap.to(intro, { v: 1, duration: 2.2, ease: 'power3.out', delay: 0.1, onUpdate: () => world.setIntro(intro.v) });
      };
      waitFirst();
    }

    return () => {
      disposed = true;
      window.removeEventListener('resize', onResize);
      window.removeEventListener('pointermove', onMove);
      document.documentElement.removeEventListener('pointerleave', onLeave);
      document.removeEventListener('visibilitychange', onVis);
      ScrollTrigger.removeEventListener('refresh', measure);
      offScroll();
      ro.disconnect();
      world.dispose();
    };
  }, [states, first, calm]);

  return (
    <div className={styles.root} data-mode={mode} aria-hidden="true">
      <canvas ref={ref} className={styles.canvas} />
      <div className={styles.fallback} />
    </div>
  );
}
