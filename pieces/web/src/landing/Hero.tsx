import { Link } from 'react-router-dom';
import { GitPullRequestIcon, KeyIcon, PlayIcon, ShieldCheckIcon } from '@phosphor-icons/react';
import { GlassEntry } from '../components/GlassEntry';
import { HERO } from '../copy/landing';
import { LiveCard } from './LiveCard';
import s from './landing.module.css';

/**
 * Hero on the 12-column grid: the promise and the Check box on columns 1–7,
 * the living graft (world picture) upper right, a sample upgrade playing below it on columns 9–12.
 */
export function Hero() {
  return (
    <section id="top" className={s.hero} data-world="graft" data-world-lead="1">
      <div className={`gg-wrap gg-grid ${s.heroGrid}`}>
        <div className={s.heroCopy}>
          <h1 className={s.heroTitle}>
            <span className={s.heroA} data-split="load" data-delay="0.1">{HERO.titleA}</span>
            <span className={s.heroB} data-split="load" data-delay="0.34">{HERO.titleB}</span>
          </h1>
          <p className={`gg-lead ${s.heroLead}`} data-rise="load" data-delay="0.55" data-exit="dust">{HERO.lead}</p>
          <div className={s.heroEntry} data-rise="load" data-delay="0.7" data-vine="hero" data-exit>
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
        <div className={s.heroSide} data-rise="load" data-delay="1.0">
          <div data-exit><LiveCard /></div>
        </div>
      </div>
      <img className={s.fallbackArt} src="/world/01-graft-union.jpg" alt="" aria-hidden data-fallback-art />
    </section>
  );
}
