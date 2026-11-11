import { useEffect } from 'react';
import { ArrowRightIcon } from '@phosphor-icons/react';
import { useRootMap } from '../api/queries';
import { useGraftCtx } from '../shell/GraftLayout';
import { FAMILY, LENS, MEANING } from '../copy/words';
import { Details, Empty, Explain, PageHead, ProblemBanner, SampleChip, Tag } from '../components/ui';
import { Skeleton } from '../components/Loaders';
import { formatMoney, formatPct } from '../lib/format';
import { isMock } from '../config';
import s from './s03.module.css';

type TP = { id: string; family: string; location?: { file?: string; line?: number; url?: string; selector?: string; kind?: string }; operation?: string; target?: { rest_op?: string }; paypal_only?: boolean; lenses?: string[]; confidence?: number; live?: boolean; money_30d?: unknown };

const where = (l: TP['location']) => (!l ? '' : l.file ? `${l.file}${l.line ? `:${l.line}` : ''}` : l.url ?? l.selector ?? l.kind ?? '');

export default function S03_OldPieces() {
  const { graftId } = useGraftCtx();
  const q = useRootMap(graftId);
  useEffect(() => { document.title = 'GoldGraft · Old pieces'; }, []);

  if (q.isPending) return <div className={s.screen}><PageHead title="Old pieces" /><Skeleton what="old pieces" lines={4} /></div>;
  if (q.isError) return <div className={s.screen}><PageHead title="Old pieces" /><ProblemBanner error={q.error} onRetry={() => q.refetch()} /></div>;

  const tps = (q.data.touchpoints ?? []) as TP[];
  const rec = q.data.recall_evidence as { matched_by_static?: number; runtime_calls_total?: number; misses?: unknown[] } | undefined;
  const stack = q.data.stack as { lang?: string; framework?: string; db?: string; versions?: Record<string, string> } | undefined;

  return (
    <div className={s.screen}>
      <PageHead title="Old pieces" sub={tps.length === 0 ? undefined : tps.length === 1 ? '1 old PayPal piece found' : `${tps.length} old PayPal pieces found`} aside={isMock ? <SampleChip /> : undefined} />
      {tps.length === 0 ? <Empty title="No old PayPal pieces found" /> : (
        <table className={s.table}>
          <thead><tr><th>Piece</th><th>Where</th><th>Becomes</th></tr></thead>
          <tbody>
            {tps.map((t, i) => (
              <tr key={t.id} style={{ ['--i' as string]: i }}>
                <td><Tag tone="gold" title={FAMILY[t.family]?.full}>{FAMILY[t.family]?.short ?? t.family}</Tag>{t.paypal_only && <Tag tone="warn">Only PayPal can do this</Tag>}</td>
                <td><code className="gg-mono">{where(t.location)}</code></td>
                <td className={s.becomes}><span className={s.old}>{t.operation}</span> <ArrowRightIcon size={13} /> <b>{t.target?.rest_op ?? '—'}</b></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <Details>
        <div className={s.detailGrid}>
          <ul className={s.dlist}>
            {tps.map((t) => (
              <li key={t.id}>
                <b>{t.id}</b> · {(t.lenses ?? []).map((l) => LENS[l] ?? l).join(', ')} · sure {formatPct(t.confidence ?? 0)} <Explain text={MEANING.confidence} />
                {t.live !== undefined && <> · {t.live ? 'in use' : 'not seen in use'}</>}
                {t.money_30d ? <> · {formatMoney(t.money_30d as never)} in 30 days</> : null}
              </li>
            ))}
          </ul>
          {rec && <p>PayPal calls seen while running that the code scan also found: {rec.matched_by_static} of {rec.runtime_calls_total}</p>}
          {stack && <p>Shop: {[stack.lang, stack.framework, stack.db].filter(Boolean).join(' · ')}{stack.versions ? ` · ${Object.entries(stack.versions).map(([k, v]) => `${k} ${v}`).join(', ')}` : ''}</p>}
        </div>
      </Details>
    </div>
  );
}
