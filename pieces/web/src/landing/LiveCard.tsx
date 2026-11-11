import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowCounterClockwiseIcon, CheckIcon } from '@phosphor-icons/react';
import { reducedMotion } from '../motion/scroll';
import s from './landing.module.css';

// A sample upgrade playing in the hero, step by step, each line typed in as it happens.
// It plays once and holds; hover (or the replay button) plays it again.
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
  const [run, setRun] = useState(0);
  const playing = useRef(false);

  useEffect(() => {
    if (still) return;
    let row = 0, c = 0, t = 0;
    playing.current = true;
    setN(0); setChars(0);
    const tick = () => {
      if (row >= ROWS.length) { playing.current = false; return; }
      if (c === 0) setN(row + 1);
      c += 2;
      setChars(c);
      if (c >= ROWS[row].text.length) { row += 1; c = 0; t = window.setTimeout(tick, 650); return; }
      t = window.setTimeout(tick, 22);
    };
    t = window.setTimeout(tick, run === 0 ? 1700 : 250);
    return () => window.clearTimeout(t);
  }, [still, run]);

  const replay = useCallback(() => { if (!playing.current && !still) setRun((r) => r + 1); }, [still]);
  const done = n === ROWS.length && chars >= ROWS[ROWS.length - 1].text.length;

  return (
    <aside className={`gg-glass ${s.liveCard}`} data-tilt aria-label="A sample upgrade, step by step" onMouseEnter={replay}>
      <header className={s.liveHead}>
        <span className={s.liveDot} data-done={done || undefined} aria-hidden />
        <span>Upgrading <b>legacy-php-shop</b></span>
        <span className={s.chip} title="Stand-in sample data, not a recording of a real run">Sample</span>
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
      <footer className={s.liveFoot}>
        <div className={s.liveBar} aria-hidden><span style={{ width: `${(n / ROWS.length) * 100}%` }} /></div>
        {!still && (
          <button type="button" className={s.liveReplay} onClick={replay} disabled={!done} aria-label="Play the sample again">
            <ArrowCounterClockwiseIcon size={13} aria-hidden /> Replay
          </button>
        )}
      </footer>
    </aside>
  );
}
