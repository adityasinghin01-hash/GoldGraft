import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useLearningCurve, useRecipes } from '../api/queries';
import { FAMILY, MEANING, RECIPE_STATUS } from '../copy/words';
import { Details, Empty, Explain, HashText, PageHead, ProblemBanner, SampleChip, Tag } from '../components/ui';
import { Bars } from '../components/Bars';
import { Skeleton } from '../components/Loaders';
import { formatMinutes, formatPct, formatUsd } from '../lib/format';
import s from './s08.module.css';

type Pt = { shop_id: string; minutes: number; usd: number; recipe_used: boolean };
type Recipe = { id: string; status: string; confidence: number; scenarios: string[]; provenance: string[]; transform: string; signature?: string; env?: unknown; fingerprint: { lang: string; framework: string; family: string; ast_shape_hash: string } };

export default function S08_Recipes() {
  const lc = useLearningCurve();
  const rc = useRecipes();
  useEffect(() => { document.title = 'GoldGraft · Recipes'; }, []);
  const pts = ((lc.data?.points ?? []) as Pt[]);
  const label = String(lc.data?.label ?? '');
  const first = pts[0], last = pts[pts.length - 1];
  const top = pts.length >= 2 ? `First shop ${formatMinutes(first.minutes)}, ${formatUsd(first.usd)} · latest ${formatMinutes(last.minutes)}, ${formatUsd(last.usd)}`
    : pts.length === 1 ? `${first.shop_id}: ${formatMinutes(first.minutes)}, ${formatUsd(first.usd)}` : '';
  const t4 = pts.length >= 2 ? (last.minutes < first.minutes ? 'The latest shop took less time than the first' : 'The latest shop did not take less time') : 'Time to upgrade the first shop';
  const t5 = pts.length >= 2 ? (last.usd < first.usd ? 'The latest shop cost less AI than the first' : 'The latest shop did not cost less AI') : 'AI cost of the first shop';

  return (
    <div className={s.screen}>
      <PageHead title="Recipes" sub="Every proven upgrade is saved as a recipe for similar shops." />
      {lc.isPending ? <Skeleton what="learning curve" lines={3} /> : lc.isError ? <ProblemBanner error={lc.error} onRetry={() => lc.refetch()} /> : pts.length === 0 ? <Empty title="No upgrades finished yet" /> : (
        <>
          <p className={s.top}>{top}</p>
          {label.includes('SYNTHETIC') && <p className={s.label}><SampleChip /> {label}</p>}
          <Bars title={<>{t4}<Explain text={MEANING.lc_minutes} /></>} bars={pts.map((p) => ({ label: p.shop_id, value: p.minutes, display: formatMinutes(p.minutes), tag: p.recipe_used ? 'recipe used' : undefined, hot: p.recipe_used }))} />
        </>
      )}
      <Details>
        <div className={s.detailGrid}>
          {pts.length > 0 && <Bars title={<>{t5}<Explain text={MEANING.lc_usd} /></>} bars={pts.map((p) => ({ label: p.shop_id, value: p.usd, display: formatUsd(p.usd), tag: p.recipe_used ? 'recipe used' : undefined, hot: p.recipe_used }))} />}
          {rc.isError ? <ProblemBanner error={rc.error} onRetry={() => rc.refetch()} /> : (
            <div className={s.tableWrap}>
              <table className={s.table}>
                <thead><tr><th>Recipe</th><th>For</th><th>Code shape</th><th>Status</th><th>How often it worked <Explain text={MEANING.recipe_confidence} /></th><th>Tests</th><th>Proven by</th><th>Changes</th><th>Setup included</th></tr></thead>
                <tbody>{((rc.data?.recipes ?? []) as Recipe[]).map((r) => (
                  <tr key={r.id}>
                    <td className="gg-mono">{r.id}</td>
                    <td>{r.fingerprint.lang} · {r.fingerprint.framework} · <Tag tone="gold" title={FAMILY[r.fingerprint.family]?.full}>{FAMILY[r.fingerprint.family]?.short ?? r.fingerprint.family}</Tag></td>
                    <td><HashText value={r.fingerprint.ast_shape_hash} /></td>
                    <td><Tag title={RECIPE_STATUS[r.status]?.meaning}>{RECIPE_STATUS[r.status]?.name ?? r.status}</Tag></td>
                    <td className="gg-num">{formatPct(r.confidence)}</td>
                    <td title={r.scenarios.join(', ')}>{r.scenarios.length}</td>
                    <td>{r.provenance.map((p) => p.startsWith('cert-') ? <Link key={p} className="gg-link" to={`/c/${p}`}>{p}</Link> : <span key={p}>{p}</span>)}</td>
                    <td><code className="gg-mono">{r.transform}</code></td>
                    <td>{r.env ? 'yes' : 'no'}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
        </div>
      </Details>
    </div>
  );
}
