import { useEffect, useRef } from 'react';
import { WorldCanvas } from '../world/WorldCanvas';
import { LANDING_STATES } from '../world/landingStates';
import { SiteHeader } from '../shell/SiteHeader';
import { SiteFooter } from '../shell/SiteFooter';
import { setupReveals } from '../motion/reveals';
import { startSmoothScroll, stopSmoothScroll } from '../motion/scroll';
import { Hero } from './Hero';
import { Proof } from './Proof';
import { Problem } from './Problem';
import { Graft } from './Graft';
import { Features } from './Features';
import { Faq, Final, Steps } from './Closing';
import { Vine } from './Vine';
import s from './landing.module.css';

const FIRST = ['graft'];

export function LandingPage() {
  const mainRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.title = "GoldGraft · PayPal's new checkout, without rebuilding your shop";
    startSmoothScroll();
    const root = mainRef.current;
    let undo = () => {};
    let cancelled = false;
    // wait for the display font so split lines are measured with the real type
    document.fonts.ready.then(() => { if (root && !cancelled) undo = setupReveals(root); });
    return () => { cancelled = true; undo(); stopSmoothScroll(); };
  }, []);

  return (
    <>
      <a href="#main" className="gg-skip">Skip to content</a>
      <WorldCanvas states={LANDING_STATES} first={FIRST} />
      <SiteHeader />
      <div ref={mainRef} className={s.page}>
        <Vine rootRef={mainRef} />
        <main id="main" className={s.main}>
        <Hero />
        <Proof />
        <Problem />
        <Graft />
        <Features />
        <Steps />
        <Faq />
        <Final />
        </main>
        <SiteFooter />
      </div>
    </>
  );
}
