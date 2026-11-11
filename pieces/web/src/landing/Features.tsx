import { useEffect, useRef, useState } from 'react';
import { FEATURES, FEATURES_INTRO } from '../copy/landing';
import { gsap, onScroll, reducedMotion, scrollToTarget } from '../motion/scroll';
import { PANELS } from './FeaturePanels';
import { ChapterMark } from './ChapterMark';
import s from './landing.module.css';

const PER = 30;   // svh of scroll per feature while the stage is pinned
const TAIL = 0; // the stage leaves only once its pin releases, as the next chapter arrives

/**
 * Seven features. The heading scrolls in and away; then one stage pins: the list with its
 * progress on the left (cols 1–5), the working screen for the current feature on the right
 * (cols 7–12) with the dust gathered into a ring of light behind it. Scroll or click.
 */
export function Features() {
  const wrapRef = useRef<HTMLDivElement>(null);
  const stickyRef = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(0);

  const range = () => {
    const el = wrapRef.current!;
    const top = el.getBoundingClientRect().top + window.scrollY;
    const len = el.offsetHeight - window.innerHeight;
    return { top, len: len * (1 - TAIL) };
  };

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const update = (y: number) => {
      const { top, len } = range();
      const p = Math.min(0.9999, Math.max(0, (y - top) / Math.max(1, len)));
      setActive(Math.floor(p * FEATURES.length));
    };
    update(window.scrollY);
    const off = onScroll(update);
    let ctx: gsap.Context | undefined;
    if (!reducedMotion()) {
      ctx = gsap.context(() => {
        gsap.fromTo(stickyRef.current, { '--exit': 0 }, {
          '--exit': 1, ease: 'none', immediateRender: false,
          scrollTrigger: { trigger: el, start: 'bottom bottom', end: 'bottom 45%', scrub: 0.3 },
        });
      }, el);
    }
    return () => { off(); ctx?.revert(); };
  }, []);

  const jump = (i: number) => {
    const { top, len } = range();
    const y = top + ((i + 0.5) / FEATURES.length) * len;
    const marker = document.createElement('div');
    marker.style.cssText = `position:absolute;top:${y + 72}px;left:0;height:1px;width:1px`;
    document.body.appendChild(marker);
    scrollToTarget(marker);
    window.setTimeout(() => marker.remove(), 1600);
  };

  const Panel = PANELS[FEATURES[active].id];

  return (
    <section id="features" className={s.features}>
      <div className={`gg-wrap gg-grid ${s.featHeadGrid}`}>
        <div className={s.head}>
          <ChapterMark label={FEATURES_INTRO.label} />
          <h2 className="gg-h2" data-split>{FEATURES_INTRO.title}</h2>
          <p className={s.headLead} data-rise data-exit="dust">{FEATURES_INTRO.lead}</p>
        </div>
      </div>
      <div ref={wrapRef} className={s.featStageWrap} data-world="stage" data-world-lead="0.6"
        style={{ height: `calc(100svh + ${FEATURES.length * PER}svh)` }}>
        <div ref={stickyRef} className={s.featSticky} data-exit-manual data-pin>
          <div className={`gg-wrap gg-grid ${s.featGrid}`}>
            <ol className={s.featList} data-vine="features">
              {FEATURES.map((f, i) => (
                <li key={f.id} data-active={i === active || undefined} data-done={i < active || undefined}>
                  <button className={s.featBtn} onClick={() => jump(i)} aria-current={i === active ? 'step' : undefined}>
                    {f.title}
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
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
