import { useEffect, useRef, useState } from 'react';
import { FEATURES, FEATURES_INTRO } from '../copy/landing';
import { onScroll, scrollToTarget } from '../motion/scroll';
import { PANELS } from './FeaturePanels';
import { ChapterMark } from './ChapterMark';
import s from './landing.module.css';

const LEAD = 0.1; // must match data-world-lead below: the world and the list change together

/**
 * Seven features on one pinned stage. The list on the left, a small working screen
 * on the right, and behind it the dust acting the feature out. Scroll or click.
 */
export function Features() {
  const ref = useRef<HTMLElement>(null);
  const [active, setActive] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const update = (y: number) => {
      const vh = window.innerHeight;
      const top = el.getBoundingClientRect().top + y;
      const start = top - vh * LEAD;
      const end = top + el.offsetHeight - vh * 0.75;
      const p = Math.min(0.9999, Math.max(0, (y - start) / Math.max(1, end - start)));
      setActive(Math.floor(p * FEATURES.length));
    };
    update(window.scrollY);
    return onScroll(update);
  }, []);

  const jump = (i: number) => {
    const el = ref.current;
    if (!el) return;
    const vh = window.innerHeight;
    const top = el.getBoundingClientRect().top + window.scrollY;
    const start = top - vh * LEAD;
    const end = top + el.offsetHeight - vh * 0.75;
    const y = start + ((i + 0.45) / FEATURES.length) * (end - start);
    const marker = document.createElement('div');
    marker.style.cssText = `position:absolute;top:${y + 72}px;left:0;height:1px;width:1px`;
    document.body.appendChild(marker);
    scrollToTarget(marker);
    window.setTimeout(() => marker.remove(), 1600);
  };

  const Panel = PANELS[FEATURES[active].id];

  return (
    <section ref={ref} id="features" className={s.features} data-world={FEATURES.map((f) => f.state).join(',')} data-world-lead={LEAD}
      style={{ height: `${FEATURES.length * 62 + 100}vh` }}>
      <div className={s.featSticky}>
        <div className={`gg-wrap gg-grid ${s.featGrid}`}>
          <div className={s.featHead}>
            <ChapterMark n="04" label={FEATURES_INTRO.label} />
            <h2 className={`gg-h3 ${s.featTitle}`}>{FEATURES_INTRO.title} <em>{FEATURES_INTRO.titleEm}</em></h2>
          </div>
          <ol className={s.featList} data-vine="features">
            {FEATURES.map((f, i) => (
              <li key={f.id} data-active={i === active || undefined} data-done={i < active || undefined}>
                <button className={s.featBtn} onClick={() => jump(i)} aria-current={i === active ? 'step' : undefined}>
                  <span className={`gg-num ${s.featNum}`}>{String(i + 1).padStart(2, '0')}</span>
                  <span className={s.featName}>{f.title}</span>
                </button>
                <div className={s.featBody} aria-hidden={i !== active}>
                  <div>
                    <p className={s.featBenefit}>{f.benefit}</p>
                    <p className={s.featText}>{f.text}</p>
                  </div>
                </div>
              </li>
            ))}
          </ol>
          <div className={s.featStage}>
            <div key={active} className={`gg-glass ${s.featPanel}`} data-tilt>
              <Panel />
            </div>
            <div className={s.featProgress} aria-hidden>
              {FEATURES.map((f, i) => <span key={f.id} data-on={i <= active || undefined} />)}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
