import { useEffect, useRef, useState, type ReactNode } from 'react';
import s from './Bars.module.css';

export type Bar = { label: string; value: number; display: string; tag?: string; hot?: boolean };

/** C19: a plain bar chart whose title states what it shows. Bars grow once, when they come into view. */
export function Bars({ title, bars, note, unit }: { title: ReactNode; bars: Bar[]; note?: ReactNode; unit?: string }) {
  const ref = useRef<HTMLElement>(null);
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setSeen(true); io.disconnect(); } }, { threshold: 0.3 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  const max = Math.max(1e-9, ...bars.map((b) => b.value));
  return (
    <figure ref={ref} className={s.chart} data-seen={seen || undefined}>
      <figcaption className={s.title}>{title}{note}</figcaption>
      <ul className={s.list} aria-label={typeof title === 'string' ? title : undefined}>
        {bars.map((b, i) => (
          <li key={b.label} className={s.row} data-hot={b.hot || undefined} style={{ ['--i' as string]: i }}>
            <span className={s.label}>{b.label}{b.tag && <em className={s.tag}>{b.tag}</em>}</span>
            <span className={s.track}><span className={s.fill} style={{ width: `${Math.max(1.5, (b.value / max) * 100)}%` }} /></span>
            <span className={`gg-num ${s.value}`}>{b.display}{unit}</span>
          </li>
        ))}
      </ul>
    </figure>
  );
}
