import { useEffect, useRef } from 'react';
import { GRAFT } from '../copy/landing';
import { gsap, reducedMotion } from '../motion/scroll';
import { ChapterMark } from './ChapterMark';
import s from './landing.module.css';

/**
 * The idea, pinned for one screen: the heading on the left, the bound cut on the right.
 * Three labels point at the real parts of the photo (rootstock, new branch, joint),
 * a ring of light seals the joint, then the explanation arrives. The finished scene holds until
 * the pin releases; then it leaves the same way as the rest of the page (reveals.ts, data-pin).
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
        .to({}, { duration: 0.3 }); // hold the finished scene until the pin releases
    }, el);
    return () => ctx.revert();
  }, []);

  return (
    <section ref={ref} id="graft" className={s.graft} data-world="binding" data-world-lead="0.35">
      <div className={s.graftSticky} data-pin>
        <div className={`gg-wrap gg-grid ${s.graftGrid}`}>
          <div className={`${s.head} ${s.graftHead}`} data-vine="graft">
            <ChapterMark label={GRAFT.label} />
            <h2 className="gg-h2" data-split>{GRAFT.title}</h2>
          </div>
          <div className={s.graftLead} data-exit="dust">
            <p data-g="lead">{GRAFT.lead}</p>
          </div>
        </div>
        {/* covers the whole stage so the labels keep their positions while it moves */}
        <div data-exit="dust" style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
          <span className={s.seal} data-g="seal" aria-hidden />
          <ul aria-label="The graft, part by part">
            {GRAFT.tags.map((t, i) => (
              <li key={t} className={s.graftTag} data-pos={i} data-g="tag">
                <span className={s.leader} data-g="leader" aria-hidden />
                <span>{t}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
