import { createContext, useContext, useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useParams } from 'react-router-dom';
import { ArrowUpRightIcon, SealCheckIcon } from '@phosphor-icons/react';
import { useConnected, useGraft } from '../api/queries';
import type { Graft } from '../api/types';
import { GRAFT_TABS, PHASES, STAGE } from '../copy/words';
import { config } from '../config';
import { shopNameFor } from '../lib/store';
import { Explain, ProblemBanner } from '../components/ui';
import { Skeleton } from '../components/Loaders';
import s from './GraftLayout.module.css';

type Ctx = { graft: Graft; graftId: string; certId: string | null; reviewOpen: boolean; setReviewOpen: (v: boolean) => void };
const GraftCtx = createContext<Ctx | null>(null);
export const useGraftCtx = () => {
  const c = useContext(GraftCtx);
  if (!c) throw new Error('GraftLayout missing');
  return c;
};

/** G7: the API has no link from a graft to its certificate; only the stand-in demo graft has one. */
export const certFor = (graftId: string) => (graftId === config.standInIds.graftId ? config.standInIds.certId : null); // STAND-IN

export function statusLine(g: Graft) {
  const shop = shopNameFor(g.graft_id) ?? g.shop_id;
  const st = String(g.stage);
  const phase = STAGE[st]?.phase ?? 0;
  const ofN = String(g.lane) === 'NO-CODE' ? 4 : 10;
  switch (st) {
    case 'PR_OPEN': return { text: `Waiting for your approval · ${shop}`, tone: 'gold' as const };
    case 'FAILED': return { text: `Stopped: needs a person · ${shop}`, tone: 'bad' as const };
    case 'CUTBACK': return { text: 'Switched back to the old checkout · fixing the new code', tone: 'bad' as const };
    case 'DONE': return { text: `Done · ${shop} uses PayPal's new checkout`, tone: 'good' as const };
    case 'DELIVERED': return { text: `Done · new payment links delivered to ${shop}`, tone: 'good' as const };
    default: return { text: `Upgrading ${shop} · ${PHASES[phase - 1]?.name ?? ''} · ${phase} of ${ofN}`, tone: 'neutral' as const };
  }
}

export function GraftLayout() {
  const { graftId = '' } = useParams();
  const q = useGraft(graftId);
  const [reviewOpen, setReviewOpen] = useState(false);
  const certId = certFor(graftId);
  const connected = useConnected(graftId);

  useEffect(() => { document.title = 'GoldGraft · Progress'; }, []);

  if (q.isPending) return <div className={s.wrap}><Skeleton what="upgrade" lines={2} /></div>;
  if (q.isError) return <div className={s.wrap}><ProblemBanner error={q.error} onRetry={() => q.refetch()} /></div>;

  const g = q.data;
  const line = connected.data && !connected.data.certificate.issued
    ? { text: `Recorded run · ${g.shop_id} · qualification held`, tone: 'gold' as const }
    : statusLine(g);
  const st = String(g.stage);

  return (
    <GraftCtx.Provider value={{ graft: g, graftId, certId, reviewOpen, setReviewOpen }}>
      <div className={s.wrap}>
        <div className={`gg-lg ${s.status}`} data-tone={line.tone} role="status">
          <span className={s.statusDot} aria-hidden />
          <p className={s.statusText}>{line.text}</p>
          <div className={s.statusExtra}>
            {st === 'PR_OPEN' && <button className="gg-btn gg-btn--gold gg-btn--sm" onClick={() => setReviewOpen(true)}>Review</button>}
            {st === 'CUTBACK' && <Link className="gg-link" to={`/g/${graftId}/heal`}>Go-live</Link>}
            {st === 'DONE' && (connected.data
              ? <Link className="gg-btn gg-btn--ghost gg-btn--sm" to={`/g/${graftId}/certificate`}><SealCheckIcon size={15} weight="duotone" /> Certificate status</Link>
              : certId && <Link className="gg-btn gg-btn--ghost gg-btn--sm" to={`/c/${certId}`}><SealCheckIcon size={15} weight="duotone" /> Certificate <ArrowUpRightIcon size={12} /></Link>)}
          </div>
        </div>
        <nav className={s.tabs} aria-label="This upgrade">
          {GRAFT_TABS.map((t) => (
            <NavLink key={t.label} end to={`/g/${graftId}${t.path}`} className={({ isActive }) => `${s.tab} ${isActive ? s.tabOn : ''}`}>
              {t.label}
            </NavLink>
          ))}
          {connected.data
            ? <NavLink end to={`/g/${graftId}/certificate`} className={({ isActive }) => `${s.tab} ${isActive ? s.tabOn : ''}`}>Certificate</NavLink>
            : certId
              ? <Link className={s.tab} to={`/c/${certId}`}>Certificate ↗</Link>
              : <span className={s.tab} aria-disabled="true" data-off>Certificate ↗ <Explain text="Certificate link: not in the API yet (G7)" /></span>}
        </nav>
        <Outlet />
      </div>
    </GraftCtx.Provider>
  );
}
