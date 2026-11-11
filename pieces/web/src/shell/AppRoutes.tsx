import { lazy, Suspense, useEffect, useState } from 'react';
import { NavLink, Outlet, Route, Routes, useLocation, Link } from 'react-router-dom';
import { WorldCanvas } from '../world/WorldCanvas';
import { LANDING_STATES } from '../world/landingStates';
import { Mark } from '../components/Mark';
import { MockBanner, SandboxChip, DetailsProvider } from '../components/ui';
import { Skeleton, WakingLine } from '../components/Loaders';
import { NAV_APP } from '../copy/words';
import { onWaking } from '../api/client';
import { SiteFooter } from './SiteFooter';
import { GraftLayout } from './GraftLayout';
import s from './AppShell.module.css';

const S00 = lazy(() => import('../screens/S00_Check'));
const S01 = lazy(() => import('../screens/S01_Connect'));
const S02 = lazy(() => import('../screens/S02_Progress'));
const S03 = lazy(() => import('../screens/S03_OldPieces'));
const S04 = lazy(() => import('../screens/S04_PaymentTests'));
const S05 = lazy(() => import('../screens/S05_Proof'));
const S06 = lazy(() => import('../screens/S06_Certificate'));
const S07 = lazy(() => import('../screens/S07_GoLive'));
const S08 = lazy(() => import('../screens/S08_Recipes'));
const S09 = lazy(() => import('../screens/S09_PayPalTeam'));
const S10 = lazy(() => import('../screens/S10_Security'));
const S11 = lazy(() => import('../screens/S11_Compare'));
const S12 = lazy(() => import('../screens/S12_MyUpgrades'));
const NotFound = lazy(() => import('../screens/NotFound'));

const CALM = ['canopy'];

function AppHeader() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const f = () => setScrolled(window.scrollY > 8);
    f();
    window.addEventListener('scroll', f, { passive: true });
    return () => window.removeEventListener('scroll', f);
  }, []);
  return (
    <header className={s.header} data-scrolled={scrolled || undefined}>
      <div className={s.bar}>
        <Link to="/" className={s.brand} aria-label="GoldGraft home"><span className={s.mark}><Mark size={26} /></span><span className={s.word}>GoldGraft</span></Link>
        <nav className={s.nav} aria-label="App">
          {NAV_APP.map((n) => (
            <NavLink key={n.to} to={n.to} className={({ isActive }) => `${s.link} ${isActive ? s.active : ''}`}>{n.label}</NavLink>
          ))}
        </nav>
        <SandboxChip />
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
