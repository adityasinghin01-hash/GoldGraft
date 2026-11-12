import { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { GitPullRequestIcon, KeyIcon, PlayIcon, ShieldCheckIcon } from '@phosphor-icons/react';
import { GlassEntry } from '../components/GlassEntry';
import { HERO } from '../copy/landing';
import { LANDING_STATES } from '../world/landingStates';
import { fitState } from '../world/fit';
import { LiveCard } from './LiveCard';
import s from './landing.module.css';

const PHOTO_ASPECT = 1.5; // public/world/01-graft-union.jpg is 1600 × 1066
const GAP = 32;           // clear space between the branch and anything around it
const TOP = 86;           // below the header islands
// The branch runs diagonally across its photo, from the lower-left end (u 0.03, v 0.88) to the
// upper-right bud (u 0.93, v 0.04). Its lower edge, with the dust around it, stays above
// v = 0.98 − 0.9·u (measured on the photo, with margin). u, v are 0..1 across the photo.
const END_U = 0.03;
const lowerEdge = (u: number) => 0.98 - 0.9 * u;

/** Largest branch (right-aligned, under the header) whose end clears the form and whose lower
    edge passes above the card. Returns null when the window is too small to judge. */
function fitBranch(vw: number, vh: number, formRight: number, cardLeft: number, cardTop: number) {
  const R = vw * 1.04; // the photo's dark right edge may run off the screen
  for (let h = Math.min(vh * 0.8, (vh - 24 - TOP) / 0.95); h > vh * 0.3; h -= 4) {
    const w = PHOTO_ASPECT * h, L = R - w;
    if (L + END_U * w < formRight + GAP) continue;          // the branch end must clear the form
    const uc = (cardLeft - GAP - L) / w;                     // where the card's left edge meets the photo
    const yAtCard = uc <= 0 ? TOP + 0.95 * h : TOP + lowerEdge(Math.min(1, uc)) * h;
    if (yAtCard > cardTop - GAP) continue;                   // the branch must pass above the card
    return { cx: (L + w / 2 - vw / 2) / (vw / 2), cy: (vh / 2 - (TOP + h / 2)) / (vh / 2), h: h / vh };
  }
  return null;
}

/**
 * Hero on the 12-column grid: the promise and the Check box on columns 1–7,
 * the living graft upper right, a sample upgrade playing below it on columns 9–12.
 * The branch is fitted at every window size so its lower edge passes above the card and its end
 * clears the form: the card can never cover it.
 */
export function Hero() {
  const sideRef = useRef<HTMLDivElement>(null);
  const entryRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fit = () => {
      const side = sideRef.current, entry = entryRef.current;
      if (!side || !entry || window.innerWidth <= 960) return;
      // offsetTop/Left ignore the rise animation's translate, so this is where things will rest
      const layout = fitBranch(window.innerWidth, window.innerHeight, entry.offsetLeft + entry.offsetWidth, side.offsetLeft, side.offsetTop);
      if (layout) fitState(LANDING_STATES, 'graft', layout);
    };
    fit();
    document.fonts.ready.then(fit);
    const ro = new ResizeObserver(fit);
    if (sideRef.current) ro.observe(sideRef.current);
    window.addEventListener('resize', fit);
    return () => { ro.disconnect(); window.removeEventListener('resize', fit); };
  }, []);

  return (
    <section id="top" className={s.hero} data-world="graft" data-world-lead="1">
      <div className={`gg-wrap gg-grid ${s.heroGrid}`}>
        <div className={s.heroCopy}>
          <h1 className={s.heroTitle}>
            <span className={s.heroA} data-split="load" data-delay="0.1">{HERO.titleA}</span>
            <span className={s.heroB} data-split="load" data-delay="0.34">{HERO.titleB}</span>
          </h1>
          <p className={`gg-lead ${s.heroLead}`} data-rise="load" data-delay="0.55" data-exit="dust">{HERO.lead}</p>
          <div ref={entryRef} className={s.heroEntry} data-rise="load" data-delay="0.7" data-vine="hero" data-exit>
            <GlassEntry inputId="shop-url" label={HERO.inputLabel} placeholder={HERO.placeholder} action={HERO.check} note={HERO.note} invalid={HERO.invalid}
              extra={<Link to="/g/demo-1" className={s.sampleLink}><PlayIcon size={12} weight="fill" aria-hidden /> {HERO.sample}</Link>} />
          </div>
        </div>
        <ul className={s.promises} data-stagger="load" data-delay="0.9" data-exit>
          {HERO.promises.map((t, i) => {
            const Icon = [ShieldCheckIcon, KeyIcon, GitPullRequestIcon][i];
            return <li key={t}><Icon size={18} weight="light" aria-hidden /> {t}</li>;
          })}
        </ul>
        <div ref={sideRef} className={s.heroSide} data-rise="load" data-delay="1.0">
          <div data-exit><LiveCard /></div>
        </div>
      </div>
      <img className={s.fallbackArt} src="/world/01-graft-union.jpg" alt="" aria-hidden data-fallback-art />
    </section>
  );
}
