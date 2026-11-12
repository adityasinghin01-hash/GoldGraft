import { useMemo, useState } from 'react';
import { HourglassLowIcon, PlugsIcon, ProhibitIcon } from '@phosphor-icons/react';
import { PROBLEM } from '../copy/landing';
import { ChapterMark } from './ChapterMark';
import s from './landing.module.css';

const ICONS = [ProhibitIcon, HourglassLowIcon, PlugsIcon];

/** The visitor's own number, worked out in the browser. Starts empty: we don't presume their sales. */
function Calculator() {
  const [raw, setRaw] = useState('');
  const perDay = useMemo(() => {
    const n = Number(raw.replace(/[^0-9.]/g, ''));
    if (!raw.trim() || !Number.isFinite(n) || n <= 0) return null;
    return n / 30;
  }, [raw]);
  const fmt = (v: number) => v.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: v < 100 ? 2 : 0 });
  return (
    <div className={`gg-glass ${s.calc}`} data-rise data-exit>
      <h3 className={s.h3}>{PROBLEM.calcTitle}</h3>
      <label htmlFor="monthly" className={s.meta}>{PROBLEM.calcLabel}</label>
      <div className={s.calcField}>
        <span aria-hidden>$</span>
        <input id="monthly" inputMode="decimal" placeholder={PROBLEM.calcPlaceholder} value={raw} onChange={(e) => setRaw(e.target.value)} aria-describedby="calc-out calc-note" />
        <span className={s.calcUnit}>a month</span>
      </div>
      <p id="calc-out" className={s.calcOut} aria-live="polite">
        {perDay === null ? 'Type your monthly sales to see the daily figure.' : (
          <>{PROBLEM.calcPrefix} <b className="gg-num">{fmt(perDay)}</b> {PROBLEM.calcSuffix}</>
        )}
      </p>
      <p id="calc-note" className={s.meta}>{PROBLEM.calcNote}</p>
    </div>
  );
}

/** The problem: text and the calculator on cols 1–6, the dying branch on the right. */
export function Problem() {
  return (
    <section id="problem" className={s.problem} data-world="dying">
      <div className={`gg-wrap gg-grid ${s.problemGrid}`}>
        <div className={s.head}>
          <ChapterMark label={PROBLEM.label} />
          <h2 className="gg-h2" data-split>{PROBLEM.title}</h2>
          <p className={s.headLead} data-rise data-exit="dust">{PROBLEM.lead}</p>
        </div>
        <ol className={s.pains} data-vine="pains">
          {PROBLEM.pains.map((p, i) => {
            const Icon = ICONS[i];
            return (
              <li key={p.title} className={s.pain} data-rise data-delay={i * 0.08} data-exit="dust">
                <span className={s.painIcon} aria-hidden><Icon size={22} weight="light" /></span>
                <div>
                  <h3 className={s.h3}>{p.title}</h3>
                  <p className={s.body} data-flow>{p.text}</p>
                </div>
              </li>
            );
          })}
        </ol>
        <Calculator />
      </div>
    </section>
  );
}
