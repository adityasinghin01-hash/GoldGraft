import { useEffect, useState, type ReactNode } from 'react';
import { WAIT } from '../copy/words';
import s from './Loaders.module.css';

/** Waits only show after 300 ms, so fast answers never flash a loader (T09). */
export function useDelayed(active: boolean, ms = 300) {
  const [show, setShow] = useState(false);
  useEffect(() => {
    if (!active) { setShow(false); return; }
    const t = setTimeout(() => setShow(true), ms);
    return () => clearTimeout(t);
  }, [active, ms]);
  return show;
}

/** The graft-seam loader: two branches lean toward a diagonal cut and a light crosses the seam. */
export function SeamLoader({ size = 28, label }: { size?: number; label?: string }) {
  return (
    <span className={s.seam} role={label ? 'status' : undefined} aria-label={label}>
      <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden>
        <circle cx="16" cy="16" r="14.5" className={s.ring} />
        <path d="M9.5 26 C 10.6 22.4, 12.2 19.4, 14.4 17.2" className={s.root} />
        <path d="M17.6 14.8 C 19.6 12.6, 21 9.6, 21.7 5.6" className={s.scion} />
        <path d="M12.6 18.8 L 19.2 13.2" className={s.cut} />
        <circle r="1.6" className={s.spark}><animateMotion dur="1.6s" repeatCount="indefinite" path="M12.6 18.8 L 19.2 13.2" keyPoints="0;1;0" keyTimes="0;0.5;1" calcMode="spline" keySplines="0.65 0 0.35 1;0.65 0 0.35 1" /></circle>
      </svg>
    </span>
  );
}

/** W1 / W6: skeleton shapes with a slow sheen; screen readers hear "Loading <what>". */
export function Skeleton({ what, lines = 3, height, block }: { what: string; lines?: number; height?: number; block?: boolean }) {
  return (
    <div className={s.skel} role="status" aria-label={`Loading ${what}`}>
      {block ? <span className={s.skelBlock} style={{ height: height ?? 160 }} /> :
        Array.from({ length: lines }, (_, i) => <span key={i} className={s.skelLine} style={{ width: `${92 - i * 14}%` }} />)}
    </div>
  );
}

/** W3: a seconds counter that only counts real waiting time. */
export function SecondsWait({ text }: { text: string }) {
  const [sec, setSec] = useState(0);
  useEffect(() => {
    const t0 = performance.now();
    const id = setInterval(() => setSec(Math.floor((performance.now() - t0) / 1000)), 250);
    return () => clearInterval(id);
  }, []);
  return (
    <p className={s.seconds} role="status">
      <SeamLoader size={20} />
      <span>{text} <b className="gg-num">{sec} s</b></span>
    </p>
  );
}

/** W4: the AI is thinking: three specks circle the seam. */
export function Thinking() {
  return (
    <p className={s.thinking} role="status">
      <span className={s.orbit} aria-hidden><i /><i /><i /></span>
      {WAIT.thinking}
    </p>
  );
}

/** W7: the server is waking up: a sapling grows on a loop. */
export function WakingLine() {
  return (
    <div className={s.waking} role="status">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden className={s.sapling}>
        <path d="M12 22 V 11" className={s.stem} />
        <path d="M12 14 C 8 14, 6 11, 6 8 C 9 8, 12 10, 12 14 Z" className={s.leafL} />
        <path d="M12 11 C 16 11, 18 8, 18 5 C 15 5, 12 7, 12 11 Z" className={s.leafR} />
      </svg>
      {WAIT.waking}
    </div>
  );
}

/** A button that shows its own working words (W2) and a small seam while busy. */
export function ActionButton({ busy, busyText, children, variant = 'gold', ...rest }: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  busy?: boolean; busyText: string; children: ReactNode; variant?: 'gold' | 'ghost';
}) {
  return (
    <button {...rest} className={`gg-btn gg-btn--${variant} ${rest.className ?? ''}`} disabled={busy || rest.disabled} aria-busy={busy || undefined}>
      {busy ? <><SeamLoader size={16} /> {busyText}</> : children}
    </button>
  );
}
