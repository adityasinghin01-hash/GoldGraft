import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { BugBeetleIcon, CheckIcon, PlayIcon, StopIcon, XIcon } from '@phosphor-icons/react';
import { useProof } from '../api/queries';
import { useGraftCtx } from '../shell/GraftLayout';
import { MEANING, MUTANT, ruleText } from '../copy/words';
import { Details, Explain, PageHead, ProblemBanner, SampleChip, Tag } from '../components/ui';
import { Skeleton } from '../components/Loaders';
import { formatPct } from '../lib/format';
import { config, isMock } from '../config';
import { reducedMotion } from '../motion/scroll';
import s from './s05.module.css';

type Mutant = { id: string; op: string; killed_by: string[]; equivalent_suspect?: boolean; location?: { file: string; line: number }; patch?: string; rule?: string };
type Tri = { rule_id: string; scenario_ids: string[]; mutant_ids: string[]; killed: boolean };

export default function S05_Proof() {
  const { graftId } = useGraftCtx();
  const q = useProof(graftId);
  const [shown, setShown] = useState<number | null>(null); // null = all shown (no replay running)
  const timer = useRef(0);

  useEffect(() => { document.title = 'GoldGraft · Proof'; return () => window.clearInterval(timer.current); }, []);

  const mutants = ((q.data?.mutants ?? []) as Mutant[]);
  const ps = q.data?.proof_strength as { killed: number; total: number; equivalent_dropped: number; score: number } | undefined;
  const replaying = shown !== null;

  const replay = () => {
    window.clearInterval(timer.current);
    if (replaying) { setShown(null); return; }
    setShown(0);
    let n = 0;
    timer.current = window.setInterval(() => {
      n += 1;
      setShown(n);
      if (n >= mutants.length) { window.clearInterval(timer.current); window.setTimeout(() => setShown(null), 1400); }
    }, reducedMotion() ? 50 : 520);
  };

  if (q.isPending) return <div className={s.screen}><PageHead title="Proof" /><Skeleton what="proof" lines={4} /></div>;
  if (q.isError || !ps) return <div className={s.screen}><PageHead title="Proof" /><ProblemBanner error={q.error} onRetry={() => q.refetch()} /></div>;

  const denom = ps.total - ps.equivalent_dropped;
  const caughtSoFar = replaying ? mutants.slice(0, shown!).filter((m) => m.killed_by.length > 0).length : ps.killed;
  const pctShown = replaying ? caughtSoFar / Math.max(1, denom) : ps.score;
  const strong = ps.score >= config.CERT_MIN_PROOF_STRENGTH;
  const tri = (q.data?.triangle ?? []) as Tri[];

  return (
    <div className={s.screen}>
      <PageHead title="Proof" sub={<span className={s.top}>Caught {ps.killed} of {denom} planted bugs · needs 95%</span>} aside={isMock ? <SampleChip /> : undefined} />

      <section className={`gg-glass ${s.barPanel}`}>
        <p className={s.barTitle}>Our tests caught {formatPct(pctShown)} of planted bugs <Explain text="We plant money bugs in a test copy; strong tests catch them." /></p>
        <div className={s.bar} role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(pctShown * 100)} aria-label="Bugs caught">
          <span className={s.fill} style={{ width: `${pctShown * 100}%` }} data-strong={strong || undefined} />
          <i className={s.mark} style={{ left: '95%' }}><b>needs 95%</b></i>
        </div>
        <p className={s.verdict} data-strong={strong || undefined}>{strong ? 'Strong enough for a certificate' : 'Below the 95% a certificate needs'}</p>
      </section>

      <div className={s.tilesHead}>
        <button className="gg-btn gg-btn--ghost gg-btn--sm" onClick={replay} aria-pressed={replaying}>
          {replaying ? <><StopIcon size={14} weight="fill" /> Stop</> : <><PlayIcon size={14} weight="fill" /> Replay</>}
        </button>
        {replaying && <Tag tone="gold">Replaying the saved result</Tag>}
      </div>

      <ol className={s.tiles}>
        {mutants.map((m, i) => {
          const caught = m.killed_by.length > 0;
          const hidden = replaying && i >= shown!;
          return (
            <li key={m.id} className={s.tile} data-caught={caught || undefined} data-hidden={hidden || undefined} data-flip={replaying && i === shown! - 1 ? 'now' : undefined}>
              <span className={s.tileIcon} aria-hidden><BugBeetleIcon size={18} weight="duotone" /></span>
              <span className={s.tileText}>{MUTANT[m.op]?.text ?? m.op}</span>
              <span className={s.tileState}>{hidden ? '…' : caught ? <><CheckIcon size={13} weight="bold" /> Caught</> : <><XIcon size={13} weight="bold" /> Missed</>}</span>
            </li>
          );
        })}
      </ol>

      <Details>
        <div className={s.detailGrid}>
          <p className={s.muted}>{ps.equivalent_dropped} dropped: they change nothing visible <Explain text={MEANING.equivalent_dropped} /></p>
          <ul className={s.mList}>
            {mutants.map((m) => (
              <li key={m.id}>
                <b>{m.op}</b> · <code>{m.location ? `${m.location.file}:${m.location.line}` : ''}</code>
                {m.rule && <> · Checks {m.rule} {ruleText(m.rule)}</>}
                {' · '}Caught by: {m.killed_by.length ? m.killed_by.map((sc) => <Link key={sc} className="gg-link" to={`/g/${graftId}/union?scenario=${sc}`}>{sc}</Link>) : 'nothing'}
                {m.equivalent_suspect && <> <Tag tone="warn">may change nothing</Tag></>}
                {m.patch && <pre className={s.patch}>What was changed: {m.patch}</pre>}
                <span className={s.muted}> {m.id}</span>
              </li>
            ))}
          </ul>
          <table className={s.table}>
            <caption>Each rule needs a test and a planted bug that test catches.</caption>
            <thead><tr><th>Rule</th><th>Tests that check it</th><th>Planted bugs</th><th>Guarded?</th></tr></thead>
            <tbody>{tri.map((t) => (
              <tr key={t.rule_id}>
                <td>{t.rule_id} {ruleText(t.rule_id)}</td>
                <td>{t.scenario_ids.map((sc) => <Link key={sc} className="gg-link" to={`/g/${graftId}/union?scenario=${sc}`}>{sc} </Link>)}</td>
                <td className="gg-mono">{t.mutant_ids.join(', ')}</td>
                <td data-bad={!t.killed || undefined}>{t.killed ? 'Guarded' : 'Not guarded'}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Details>
    </div>
  );
}
