import { Link } from 'react-router-dom';
import { PlayIcon } from '@phosphor-icons/react';
import { GlassEntry } from '../components/GlassEntry';
import { HERO } from '../copy/landing';
import { FamilyBand, LiveCard } from './LiveCard';
import s from './landing.module.css';

export function Hero() {
  return (
    <section id="top" className={s.hero} data-world="graft" data-world-lead="1">
      <div className={`gg-wrap ${s.heroInner}`}>
        <div className={s.heroCopy}>
          <p className={`gg-label ${s.eyebrow}`} data-scramble="load">
            <span className={s.dot} aria-hidden /> {HERO.eyebrow}
          </p>
          <h1 className={s.heroTitle}>
            <span className={s.heroA} data-split="load" data-delay="0.1">{HERO.titleA}</span>
            <em className={s.heroB} data-split="load" data-delay="0.32">{HERO.titleB}</em>
          </h1>
          <p className={`gg-lead ${s.heroLead}`} data-rise="load" data-delay="0.6">{HERO.lead}</p>
          <div className={s.heroEntry} data-rise="load" data-delay="0.75" data-vine="hero">
            <GlassEntry inputId="shop-url" label={HERO.inputLabel} placeholder={HERO.placeholder} action={HERO.check} note={HERO.note} invalid={HERO.invalid} />
            <Link to="/g/demo-1" className={`gg-btn gg-btn--ghost gg-btn--sm ${s.sampleLink}`}>
              <PlayIcon size={13} weight="fill" aria-hidden /> {HERO.sample}
            </Link>
          </div>
        </div>
        <div className={s.heroSide} data-rise="load" data-delay="1.1">
          <LiveCard />
        </div>
      </div>
      <div className={s.heroFoot}>
        <FamilyBand />
      </div>
      <img className={s.fallbackArt} src="/world/01-graft-union.jpg" alt="" aria-hidden data-fallback-art />
    </section>
  );
}
