import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowUpRightIcon as ArrowUpRight, ListIcon as List, XIcon as X } from '@phosphor-icons/react';
import { Mark } from '../components/Mark';
import { NAV } from '../copy/landing';
import { scrollToTarget } from '../motion/scroll';
import styles from './SiteHeader.module.css';

/** Landing header: clear over the hero, glass once you scroll; marks the chapter you're in. */
export function SiteHeader() {
  const [scrolled, setScrolled] = useState(false);
  const [active, setActive] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    const ids = NAV.map((n) => n.href.slice(1));
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) if (e.isIntersecting) setActive(e.target.id);
      },
      { rootMargin: '-45% 0px -50% 0px' },
    );
    ids.forEach((id) => { const el = document.getElementById(id); if (el) io.observe(el); });
    const hero = document.getElementById('top');
    if (hero) io.observe(hero);
    return () => { window.removeEventListener('scroll', onScroll); io.disconnect(); };
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  const go = (href: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    setOpen(false);
    scrollToTarget(href);
  };

  const checkMyShop = (e: React.MouseEvent) => {
    e.preventDefault();
    setOpen(false);
    scrollToTarget('#top');
    window.setTimeout(() => document.getElementById('shop-url')?.focus({ preventScroll: true }), 700);
  };

  return (
    <header className={styles.header} data-scrolled={scrolled || undefined} data-open={open || undefined}>
      <div className={`gg-wrap ${styles.bar}`}>
        <Link to="/" className={styles.brand} aria-label="GoldGraft home">
          <span className={styles.mark}><Mark size={30} /></span>
          <span className={styles.word}>GoldGraft</span>
        </Link>

        <nav className={styles.nav} aria-label="Page sections">
          {NAV.map((n) => (
            <a key={n.href} href={n.href} onClick={go(n.href)} className={styles.navLink}
               aria-current={active === n.href.slice(1) ? 'true' : undefined}>
              {n.label}
            </a>
          ))}
        </nav>

        <div className={styles.actions}>
          <Link to="/my" className={`gg-btn gg-btn--ghost gg-btn--sm ${styles.open}`}>
            Open app <ArrowUpRight size={14} weight="bold" aria-hidden />
          </Link>
          <a href="#top" onClick={checkMyShop} className="gg-btn gg-btn--gold gg-btn--sm">Check my shop</a>
          <button className={styles.menuBtn} aria-expanded={open} aria-controls="site-menu" aria-label={open ? 'Close menu' : 'Open menu'} onClick={() => setOpen((v) => !v)}>
            {open ? <X size={20} /> : <List size={20} />}
          </button>
        </div>
      </div>

      <div id="site-menu" className={styles.sheet} hidden={!open}>
        {NAV.map((n) => <a key={n.href} href={n.href} onClick={go(n.href)}>{n.label}</a>)}
        <Link to="/my" onClick={() => setOpen(false)}>Open app</Link>
      </div>
    </header>
  );
}
