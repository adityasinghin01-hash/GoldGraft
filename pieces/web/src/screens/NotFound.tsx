import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { PageHead } from '../components/ui';

/** A lone cut branch: nothing grafted here. */
export default function NotFound() {
  useEffect(() => { document.title = 'GoldGraft · Page not found'; }, []);
  return (
    <div className="gg-center" style={{ display: 'grid', justifyItems: 'center', textAlign: 'center', gap: 24, maxWidth: 640, paddingTop: 64 }}>
      <svg width="120" height="120" viewBox="0 0 64 64" fill="none" aria-hidden style={{ color: 'var(--gg-gold)' }}>
        <circle cx="32" cy="32" r="29" stroke="currentColor" strokeOpacity=".25" strokeDasharray="3 4" />
        <path d="M20.5 53.5 C 22.6 46.4, 25.8 40.4, 30.3 35.7" stroke="currentColor" strokeWidth="5" strokeLinecap="round" />
        <path d="M27.4 37.9 L 36.9 30.1" stroke="currentColor" strokeOpacity=".5" strokeDasharray="2 3" strokeLinecap="round" />
      </svg>
      <PageHead title="Page not found" sub="No GoldGraft page at this address." />
      <Link to="/check" className="gg-btn gg-btn--gold">Start</Link>
    </div>
  );
}
