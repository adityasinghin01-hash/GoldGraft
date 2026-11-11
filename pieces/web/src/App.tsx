import { lazy, Suspense, useEffect } from 'react';
import { Route, Routes, useLocation } from 'react-router-dom';
import { LandingPage } from './landing/LandingPage';

const loadApp = () => import('./shell/AppRoutes');
const AppRoutes = lazy(loadApp);

/** While the visitor reads the landing, quietly load the app and all its screens. */
function usePreloadApp() {
  useEffect(() => {
    const ric = (window as Window & { requestIdleCallback?: (cb: () => void, o?: { timeout: number }) => number }).requestIdleCallback;
    const idle = (cb: () => void) => (ric ? ric(cb, { timeout: 5000 }) : window.setTimeout(cb, 2500));
    const t = window.setTimeout(() => idle(() => { loadApp().then((m) => m.prefetchScreens()).catch(() => {}); }), 2500);
    return () => window.clearTimeout(t);
  }, []);
}

function TitleAndFocus() {
  const { pathname } = useLocation();
  useEffect(() => {
    if (pathname !== '/') window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export function App() {
  usePreloadApp();
  return (
    <>
      <TitleAndFocus />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="*" element={<Suspense fallback={null}><AppRoutes /></Suspense>} />
      </Routes>
    </>
  );
}
