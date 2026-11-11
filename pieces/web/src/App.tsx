import { lazy, Suspense, useEffect } from 'react';
import { Route, Routes, useLocation } from 'react-router-dom';
import { LandingPage } from './landing/LandingPage';

const AppRoutes = lazy(() => import('./shell/AppRoutes'));

function TitleAndFocus() {
  const { pathname } = useLocation();
  useEffect(() => {
    if (pathname !== '/') window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export function App() {
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
