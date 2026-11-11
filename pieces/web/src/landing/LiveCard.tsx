import { useEffect, useState } from 'react';
import { CheckIcon } from '@phosphor-icons/react';
import { reducedMotion } from '../motion/scroll';
import s from './landing.module.css';

// A sample upgrade playing in the hero, step by step, each line typed in as it happens.
// Words and numbers are the stand-in sample (labelled), so nothing here claims a real run.
const ROWS = [
  { who: 'Surveyor', text: 'Found 5 old PayPal pieces' },
  { who: 'Grafter', text: 'Wrote the new checkout' },
  { who: 'Union Judge', text: 'Payment tests: 5 same, 1 old bug fixed' },
  { who: 'Adversary', text: 'Caught 11 of 12 planted bugs' },
  { who: 'Heal Controller', text: '10% of buyers on the new checkout' },
];

export function LiveCard() {
  const still = reducedMotion();
  const [n, setN] = useState(still ? ROWS.length : 0);
  const [chars, setChars] = useState(0);

  useEffect(() => {
    if (still) return;
    let row = 0, c = 0;
    let t = 0;
    const tick = () => {
      if (row >= ROWS.length) { t = window.setTimeout(() => { row = 0; c = 0; setN(0); setChars(0); t = window.setTimeout(tick, 600); }, 3800); return; }
      if (c === 0) setN(row + 1);
      c += 2;
      setChars(c);
      if (c >= ROWS[row].text.length) { row += 1; c = 0; t = window.setTimeout(tick, 700); return; }
      t = window.setTimeout(tick, 22);
    };
    t = window.setTimeout(tick, 1600);
    return () => window.clearTimeout(t);
  }, [still]);

  return (
    <aside className={`gg-glass ${s.liveCard}`} data-tilt aria-label="A sample upgrade, step by step">
      <header className={s.liveHead}>
        <span className={s.liveDot} aria-hidden />
        <span>Upgrading <b>legacy-php-shop</b></span>
        <span className={s.liveSample} title="Stand-in sample data, not a recording of a real run">Sample</span>
      </header>
      <ol className={s.liveRows}>
        {ROWS.slice(0, n).map((r, i) => {
          const typing = i === n - 1 && !still && chars < r.text.length;
          return (
            <li key={r.text} data-done={!typing || undefined}>
              <span className={s.liveTick} aria-hidden>{typing ? <i /> : <CheckIcon size={11} weight="bold" />}</span>
              <span className={s.liveWho}>{r.who}</span>
              <span className={s.liveText}>{typing ? r.text.slice(0, chars) : r.text}{typing && <i className={s.liveCaret} />}</span>
            </li>
          );
        })}
      </ol>
      <div className={s.liveBar} aria-hidden><span style={{ width: `${(n / ROWS.length) * 100}%` }} /></div>
    </aside>
  );
}

const FAMILIES = ['Website Payments Standard', 'Express Checkout (NVP)', 'Express Checkout (SOAP)', 'Instant Payment Notification', 'checkout.js v4', 'JavaScript SDK v5', 'REST v1 payments', 'Direct Payment', 'Recurring payments (NVP)', 'Payment Data Transfer', 'Billing agreements', 'Payflow'];

/** A band of every old PayPal product GoldGraft upgrades; it drifts and leans with scroll speed. */
export function FamilyBand() {
  const items = [...FAMILIES, ...FAMILIES];
  return (
    <div className={s.band} aria-label="Old PayPal products GoldGraft upgrades">
      <p className={s.bandLabel}>Old PayPal it upgrades</p>
      <div className={s.bandTrack} data-band>
        <ul className={s.bandRow}>
          {items.map((f, i) => <li key={i} aria-hidden={i >= FAMILIES.length || undefined}><span className={s.bandDot} />{f}</li>)}
        </ul>
      </div>
    </div>
  );
}
