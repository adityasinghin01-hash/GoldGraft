import { useEffect } from 'react';
import { useComparison } from '../api/queries';
import { ARM, MEANING } from '../copy/words';
import { Explain, PageHead, ProblemBanner, SampleChip, Tag } from '../components/ui';
import { Bars } from '../components/Bars';
import { Skeleton } from '../components/Loaders';
import { formatMinutes, formatUsd } from '../lib/format';
import s from './s11.module.css';

type Arm = { arm: string; minutes: number; usd: number; pieces_missed: number; money_bugs_left: number };

export default function S11_Compare() {
  const q = useComparison();
  useEffect(() => { document.title = 'GoldGraft · Compare'; }, []);
  if (q.isPending) return <div className={s.screen}><PageHead title="Compare" /><Skeleton what="comparison" lines={4} /></div>;
  if (q.isError) return <div className={s.screen}><PageHead title="Compare" /><ProblemBanner error={q.error} onRetry={() => q.refetch()} /></div>;

  const arms = (q.data.arms ?? []) as Arm[];
  const label = String(q.data.label ?? '');
  const bars = (pick: (a: Arm) => number, show: (a: Arm) => string) => arms.map((a) => ({ label: ARM[a.arm] ?? a.arm, value: pick(a), display: show(a), hot: a.arm === 'GOLDGRAFT' }));

  return (
    <div className={s.screen}>
      <PageHead title="Compare" sub={<span className={s.top}>Same shop, upgraded 4 ways <Explain text="Each method upgraded the same frozen copy of the shop." /></span>} />
      <p className={s.label}>{label.includes('SYNTHETIC') && <SampleChip />} {label}</p>
      <p className={s.shop}>Shop: <code className="gg-mono">{q.data.shop_id}</code></p>
      <div className={s.tableWrap}>
        <table className={s.table}>
          <thead><tr>
            <th>Method</th>
            <th>Time <Explain text={MEANING.cmp_minutes} /></th>
            <th>AI cost <Explain text={MEANING.cmp_usd} /></th>
            <th>Pieces missed <Explain text={MEANING.cmp_pieces_missed} /></th>
            <th>Bugs left <Explain text={MEANING.cmp_money_bugs_left} /></th>
          </tr></thead>
          <tbody>{arms.map((a) => (
            <tr key={a.arm} data-hot={a.arm === 'GOLDGRAFT' || undefined}>
              <td>{a.arm === 'GOLDGRAFT' ? <Tag tone="gold">GoldGraft</Tag> : ARM[a.arm] ?? a.arm}</td>
              <td className="gg-num">{formatMinutes(a.minutes)}</td>
              <td className="gg-num">{formatUsd(a.usd)}</td>
              <td className="gg-num">{a.pieces_missed}</td>
              <td className="gg-num">{a.money_bugs_left}</td>
            </tr>
          ))}</tbody>
        </table>
      </div>
      <div className={s.charts}>
        <Bars title="Each method left this many money bugs" bars={bars((a) => a.money_bugs_left, (a) => String(a.money_bugs_left))} />
        <Bars title="Each method missed this many old pieces" bars={bars((a) => a.pieces_missed, (a) => String(a.pieces_missed))} />
        <Bars title="Each method took this long" bars={bars((a) => a.minutes, (a) => formatMinutes(a.minutes))} />
      </div>
      <p className={s.hint}>Lower is better in every chart.</p>
    </div>
  );
}
