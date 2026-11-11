import { Link, useLocation } from 'react-router-dom';
import { Mark } from '../components/Mark';

// Temporary: the 13 app screens are built in phase 5. This keeps every landing link resolving meanwhile.
export default function AppRoutes() {
  const { pathname } = useLocation();
  return (
    <main style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', textAlign: 'center', padding: 24 }}>
      <div style={{ display: 'grid', gap: 16, justifyItems: 'center', color: 'var(--gg-gold)' }}>
        <Mark size={56} />
        <h1 className="gg-h3">This screen is on its way</h1>
        <p className="gg-mute"><code className="gg-mono">{pathname}</code> is being built next.</p>
        <Link to="/" className="gg-btn gg-btn--ghost">Back to the start</Link>
      </div>
    </main>
  );
}
