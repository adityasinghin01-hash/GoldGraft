import { useEffect, useRef } from 'react';
import { GRAFT } from '../copy/landing';
import { gsap, reducedMotion } from '../motion/scroll';
import { ChapterMark } from './ChapterMark';
import s from './landing.module.css';

/**
 * The graft moment (pinned while you scroll): the cut is bound, three labels appear
 * at the joint one by one, and a ring of light seals it. Scrubbed by the scroll.
 */
export function Graft() {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || reducedMotion()) return;
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        scrollTrigger: { trigger: el, start: 'top top', end: 'bottom bottom', scrub: 0.6 },
      });
      tl.from('[data-g="title"]', { yPercent: 18, autoAlpha: 0, duration: 0.18, ease: 'none' }, 0.02)
        .from('[data-g="tag"]', { autoAlpha: 0, y: 14, duration: 0.12, stagger: 0.16, ease: 'none' }, 0.2)
        .from('[data-g="leader"]', { scaleX: 0, duration: 0.12, stagger: 0.16, ease: 'none' }, 0.2)
        .fromTo('[data-g="seal"]', { scale: 0.4, autoAlpha: 0 }, { scale: 1, autoAlpha: 1, duration: 0.2, ease: 'none' }, 0.72)
        .from('[data-g="lead"]', { autoAlpha: 0, y: 20, duration: 0.15, ease: 'none' }, 0.78);
    }, el);
    return () => ctx.revert();
  }, []);

  return (
    <section ref={ref} id="graft" className={s.graft} data-world="binding" data-world-lead="0.35">
      <div className={s.graftSticky}>
        <div className={`gg-wrap ${s.graftInner}`}>
          <div className={s.graftMark}><ChapterMark n="03" label="The idea" /></div>
          <h2 className={s.graftTitle} data-g="title" data-vine="graft">
            {GRAFT.title} <em>{GRAFT.titleEm}</em>
          </h2>
          <div className={s.joint} aria-hidden>
            <span className={s.seal} data-g="seal" />
          </div>
          <ul className={s.graftTags}>
            {GRAFT.tags.map((t, i) => (
              <li key={t} className={s.graftTag} data-pos={i} data-g="tag">
                <span className={s.leader} data-g="leader" aria-hidden />
                {t}
              </li>
            ))}
          </ul>
          <p className={`gg-lead ${s.graftLead}`} data-g="lead">{GRAFT.lead}</p>
        </div>
      </div>
    </section>
  );
}
