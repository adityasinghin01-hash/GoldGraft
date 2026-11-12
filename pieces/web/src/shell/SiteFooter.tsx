import { Link } from 'react-router-dom';
import { ArrowUpRightIcon } from '@phosphor-icons/react';
import { Mark } from '../components/Mark';
import { FOOTER } from '../copy/landing';
import { scrollToTarget } from '../motion/scroll';
import styles from './SiteFooter.module.css';

type L = { label: string; href: string; external?: boolean };

function FooterLink({ l }: { l: L }) {
  if (l.external) {
    return <a className="gg-link" href={l.href} target="_blank" rel="noreferrer">{l.label} <ArrowUpRightIcon size={11} aria-hidden /></a>;
  }
  if (l.href.startsWith('#')) {
    const go = (e: React.MouseEvent) => {
      const el = document.querySelector(l.href);
      if (!el) return;
      e.preventDefault();
      scrollToTarget(l.href);
    };
    return <a className="gg-link" href={`/${l.href}`} onClick={go}>{l.label}</a>;
  }
  return <Link className="gg-link" to={l.href}>{l.label}</Link>;
}

/** The final composition: identity, every checked link, then the roots and the wordmark. */
export function SiteFooter({ compact = false }: { compact?: boolean }) {
  const year = 2026;
  return (
    <footer className={styles.footer} data-compact={compact || undefined} data-world={compact ? undefined : 'roots'}>
      <div className={`gg-wrap ${styles.top}`}>
        <div className={styles.about}>
          <span className={styles.mark}><Mark size={40} /></span>
          <p>{FOOTER.about}</p>
        </div>
        {FOOTER.groups.map((g) => (
          <nav key={g.title} className={styles.group} aria-label={g.title}>
            <p className={`gg-label ${styles.groupTitle}`}>{compact && g.title === 'This page' ? 'Overview' : g.title}</p>
            <ul>{g.links.map((l) => <li key={l.label}><FooterLink l={l as L} /></li>)}</ul>
          </nav>
        ))}
      </div>
      <div className={styles.word} aria-hidden>
        <span>Gold</span><em>Graft</em>
      </div>
      <div className={`gg-wrap ${styles.legal}`}>
        <p>© {year} GoldGraft team · MIT</p>
        <p>{FOOTER.legal}</p>
        <p>{FOOTER.credits}</p>
      </div>
    </footer>
  );
}
