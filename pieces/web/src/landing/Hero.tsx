import { Link } from 'react-router-dom';
import { ArrowDownIcon, PlayIcon } from '@phosphor-icons/react';
import { GlassEntry } from '../components/GlassEntry';
import { HERO } from '../copy/landing';
import s from './landing.module.css';

export function Hero() {
  return (
    <section id="top" className={s.hero} data-world="graft" data-world-lead="1">
      <div className={`gg-wrap ${s.heroInner}`}>
        <p className={`gg-label ${s.eyebrow}`} data-rise="load" data-delay="0.05">
          <span className={s.dot} aria-hidden /> {HERO.eyebrow}
        </p>
        <h1 className={s.heroTitle}>
          <span className={s.heroA} data-split="load" data-delay="0.12">{HERO.titleA}</span>
          <em className={s.heroB} data-split="load" data-delay="0.3">{HERO.titleB}</em>
        </h1>
        <div className={s.heroBody}>
          <p className={`gg-lead ${s.heroLead}`} data-rise="load" data-delay="0.55">{HERO.lead}</p>
          <div className={s.heroEntry} data-rise="load" data-delay="0.7" data-vine="hero">
            <GlassEntry inputId="shop-url" label={HERO.inputLabel} placeholder={HERO.placeholder} action={HERO.check} note={HERO.note} invalid={HERO.invalid} />
            <Link to="/g/demo-1" className={`gg-link ${s.sampleLink}`}>
              <PlayIcon size={14} weight="fill" aria-hidden /> {HERO.sample}
            </Link>
          </div>
        </div>
      </div>
      <a href="#proof" className={s.scrollCue} data-rise="load" data-delay="1.1">
        <span className={s.cueLine} aria-hidden><span /></span>
        {HERO.scroll}
        <ArrowDownIcon size={13} aria-hidden />
      </a>
      <img className={s.fallbackArt} src="/world/01-graft-union.webp" alt="" aria-hidden data-fallback-art />
    </section>
  );
}
