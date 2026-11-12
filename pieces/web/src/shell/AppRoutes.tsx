import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import { NavLink, Outlet, Route, Routes, useLocation, Link } from 'react-router-dom';
import { WorldCanvas } from '../world/WorldCanvas';
import { LANDING_STATES } from '../world/landingStates';
import { Mark } from '../components/Mark';
import { MockBanner, SandboxChip, DetailsProvider } from '../components/ui';
import { Skeleton, WakingLine } from '../components/Loaders';
import { NAV_APP } from '../copy/words';
import { onWaking } from '../api/client';
import { SiteFooter } from './SiteFooter';
import { useLiquidGlass } from '../components/liquidGlass';
import h from './SiteHeader.module.css';
import { GraftLayout } from './GraftLayout';
import s from './AppShell.module.css';

// Every screen is its own chunk; prefetchScreens() loads them all in the background
// (called while the visitor reads), so a click never waits for code.
const load = {
  S00: () => import('../screens/S00_Check'),
  S01: () => import('../screens/S01_Connect'),
  S02: () => import('../screens/S02_Progress'),
  S03: () => import('../screens/S03_OldPieces'),
  S04: () => import('../screens/S04_PaymentTests'),
  S05: () => import('../screens/S05_Proof'),
  S06: () => import('../screens/S06_Certificate'),
  S07: () => import('../screens/S07_GoLive'),
  S08: () => import('../screens/S08_Recipes'),
  S09: () => import('../screens/S09_PayPalTeam'),
  S10: () => import('../screens/S10_Security'),
  S11: () => import('../screens/S11_Compare'),
  S12: () => import('../screens/S12_MyUpgrades'),
  S13: () => import('../screens/S13_Changes'),
  S14: () => import('../screens/S14_Agents'),
  S15: () => import('../screens/S15_CertStatus'),
  NotFound: () => import('../screens/NotFound'),
};
export function prefetchScreens() {
  for (const l of Object.values(load)) l().catch(() => {});
}
const S00 = lazy(load.S00);
const S01 = lazy(load.S01);
const S02 = lazy(load.S02);
const S03 = lazy(load.S03);
const S04 = lazy(load.S04);
const S05 = lazy(load.S05);
const S06 = lazy(load.S06);
const S07 = lazy(load.S07);
const S08 = lazy(load.S08);
const S09 = lazy(load.S09);
const S10 = lazy(load.S10);
const S11 = lazy(load.S11);
const S12 = lazy(load.S12);
const S13 = lazy(load.S13);
const S14 = lazy(load.S14);
const S15 = lazy(load.S15);
const NotFound = lazy(load.NotFound);

const CALM = ['canopy'];

/** App header: the same three liquid-glass islands as the landing (brand · screens · sandbox). */
function AppHeader() {
  const [scrolled, setScrolled] = useState(false);
  const brandRef = useRef<HTMLAnchorElement>(null);
  const navRef = useRef<HTMLElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  useLiquidGlass(brandRef);
  useLiquidGlass(navRef);
  useLiquidGlass(endRef);
  useEffect(() => {
    const f = () => setScrolled(window.scrollY > 8);
    f();
    window.addEventListener('scroll', f, { passive: true });
    return () => window.removeEventListener('scroll', f);
  }, []);
  return (
    <header className={s.header} data-scrolled={scrolled || undefined}>
      <div className={`${h.bar} ${s.bar}`}>
        <Link ref={brandRef} to="/" className={`gg-lg ${h.island} ${h.brand}`} aria-label="GoldGraft home">
          <span className={h.mark}><Mark size={24} /></span><span className={h.word}>GoldGraft</span>
        </Link>
        <nav ref={navRef} className={`gg-lg ${h.island} ${h.nav} ${s.nav}`} aria-label="App">
          {NAV_APP.map((n) => (
            <NavLink key={n.to} to={n.to} className={h.navLink}>{n.label}</NavLink>
          ))}
        </nav>
        <div ref={endRef} className={`gg-lg ${h.island} ${h.actions} ${s.end}`}>
          <SandboxChip />
        </div>
      </div>
    </header>
  );
}

/** Focus the page heading on every route change (02 §B). */
function FocusOnRoute() {
  const { pathname } = useLocation();
  useEffect(() => {
    const t = setTimeout(() => document.querySelector<HTMLElement>('[data-page-title]')?.focus({ preventScroll: true }), 60);
    return () => clearTimeout(t);
  }, [pathname]);
  return null;
}

function AppLayout() {
  const [waking, setWaking] = useState(false);
  useEffect(() => onWaking(setWaking), []);
  useEffect(() => { const t = window.setTimeout(prefetchScreens, 400); return () => window.clearTimeout(t); }, []);
  return (
    <DetailsProvider>
      <WorldCanvas states={LANDING_STATES} first={CALM} calm />
      <a href="#app-main" className="gg-skip">Skip to content</a>
      <MockBanner />
      {waking && <WakingLine />}
      <AppHeader />
      <FocusOnRoute />
      <main id="app-main" className={`gg-wrap ${s.main}`}>
        <Suspense fallback={<div className={s.fallback}><Skeleton what="page" lines={4} /></div>}>
          <Outlet />
        </Suspense>
      </main>
      <SiteFooter compact />
    </DetailsProvider>
  );
}

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/check" element={<S00 />} />
        <Route path="/connect" element={<S01 />} />
        <Route path="/my" element={<S12 />} />
        <Route path="/g/:graftId" element={<GraftLayout />}>
          <Route index element={<S02 />} />
          <Route path="map" element={<S03 />} />
          <Route path="union" element={<S04 />} />
          <Route path="proof" element={<S05 />} />
          <Route path="heal" element={<S07 />} />
          <Route path="changes" element={<S13 />} />
          <Route path="agents" element={<S14 />} />
          <Route path="certificate" element={<S15 />} />
        </Route>
        <Route path="/c/:certId" element={<S06 />} />
        <Route path="/bank" element={<S08 />} />
        <Route path="/orchard" element={<S09 />} />
        <Route path="/security/:runId" element={<S10 />} />
        <Route path="/compare" element={<S11 />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
