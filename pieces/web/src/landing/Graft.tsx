import { useEffect, useRef } from 'react';
import { GRAFT } from '../copy/landing';
import { gsap, reducedMotion } from '../motion/scroll';
import { ChapterMark } from './ChapterMark';
import s from './landing.module.css';

/**
 * The idea, pinned for one screen: the heading on the left, the bound cut on the right.
 * Three labels point at the real parts of the photo (rootstock, new branch, joint),
 * a ring of light seals the joint, then the explanation arrives and everything leaves together.
 */
export function Graft() {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || reducedMotion()) return;
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        scrollTrigger: { trigger: el, start: 'top top', end: 'bottom bottom', scrub: 0.5 },
        defaults: { ease: 'none' },
      });
      tl.from('[data-g="tag"]', { autoAlpha: 0, y: 12, duration: 0.1, stagger: 0.12 }, 0.08)
        .from('[data-g="leader"]', { scaleX: 0, duration: 0.1, stagger: 0.12 }, 0.08)
        .fromTo('[data-g="seal"]', { scale: 0.5, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: 0.18 }, 0.42)
        .from('[data-g="lead"]', { autoAlpha: 0, y: 20, duration: 0.14 }, 0.5)
        .to('[data-g="all"]', { autoAlpha: 0, y: -28, duration: 0.14 }, 0.86);
    }, el);
    return () => ctx.revert();
  }, []);

  return (
    <section ref={ref} id="graft" className={s.graft} data-world="binding" data-world-lead="0.35">
      <div className={s.graftSticky}>
        <div data-g="all" style={{ height: '100%' }}>
          <div className={`gg-wrap gg-grid ${s.graftGrid}`}>
            <div className={`${s.head} ${s.graftHead}`} data-vine="graft">
              <ChapterMark label={GRAFT.label} />
              <h2 className="gg-h2" data-split>{GRAFT.title}</h2>
            </div>
            <p className={s.graftLead} data-g="lead">{GRAFT.lead}</p>
          </div>
          <span className={s.seal} data-g="seal" aria-hidden />
          <ul aria-label="The graft, part by part">
            {GRAFT.tags.map((t, i) => (
              <li key={t} className={s.graftTag} data-pos={i} data-g="tag">
                <span className={s.leader} data-g="leader" aria-hidden />
                {t}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
