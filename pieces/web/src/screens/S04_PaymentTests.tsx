import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { WarningIcon, XCircleIcon, QuestionIcon, ArrowsLeftRightIcon } from '@phosphor-icons/react';
import { useCmel, useScenarios } from '../api/queries';
import type { MoneyEvent, ScenarioRow } from '../api/types';
import { useGraftCtx } from '../shell/GraftLayout';
import { GRADE, GRADE_ORDER, MONEY_EVENT, SCENARIO_FAMILY, SOURCE, STATUS_NORM, ruleText } from '../copy/words';
import { Details, Empty, Explain, NotInApiYet, PageHead, ProblemBanner, SampleChip, Tag } from '../components/ui';
import { Skeleton } from '../components/Loaders';
import { alignLanes, isNoise, type Row } from '../lib/align';
import { formatMoney, formatMs } from '../lib/format';
import { isMock } from '../config';
import s from './s04.module.css';

type Hit = { rule: string; side: string; evidence?: string[] };

function GradeTag({ grade }: { grade?: string }) {
  if (!grade) return <Tag>No verdict yet</Tag>;
  const g = GRADE[grade];
  return <Tag tone={g?.tone} title={g?.meaning}>{g?.label ?? grade}</Tag>;
}

function eventLine(e: MoneyEvent | null) {
  if (!e) return null;
  const m = (e as { money?: { minor: number; currency: string } }).money;
  const st = (e as { status_norm?: string }).status_norm;
  return (
    <>
      <span className={s.evKind}>{MONEY_EVENT[e.kind] ?? e.kind}</span>
      <span className={s.evMeta}>{m ? formatMoney(m as never) : ''}{st ? `${m ? ' · ' : ''}${STATUS_NORM[st] ?? st}` : ''}</span>
    </>
  );
}

function EventDetail({ e, masked }: { e: MoneyEvent; masked: string[] }) {
  const pp = ((e as { pp?: Record<string, string> }).pp ?? {}) as Record<string, string>;
  return (
    <span className={s.evDetail}>
      {SOURCE[e.source] ?? e.source} · {formatMs(e.t_ms)}
      {Object.entries(pp).map(([k, v]) => (
        <code key={k} data-noise={isNoise(e, `pp.${k}`, masked) || undefined}>{k}={v}{isNoise(e, `pp.${k}`, masked) ? ' · noise' : ''}</code>
      ))}
    </span>
  );
}

function Lanes({ rows, twin, masked, detail }: { rows: Row[]; twin: boolean; masked: string[]; detail: boolean }) {
  return (
    <div className={s.lanes} data-twin={twin || undefined} role="table" aria-label="Old shop, new shop and PayPal's own record, step by step">
      <div className={s.laneHeadRow} role="row">
        <span role="columnheader">Old shop</span>
        <span role="columnheader">New shop</span>
        <span role="columnheader">PayPal's own record</span>
        {twin && <span role="columnheader">Old shop, second run <Explain text="We run the old shop twice. What differs between runs is noise." /></span>}
      </div>
      {rows.map((r, i) => (
        <div key={i} className={s.laneRow} role="row" data-marker={r.marker ?? undefined} style={{ ['--i' as string]: i }}>
          <span role="cell" className={s.cell} data-empty={!r.old || undefined}>{eventLine(r.old)}{detail && r.old && <EventDetail e={r.old} masked={masked} />}</span>
          <span role="cell" className={s.cell} data-empty={!r.new || undefined}>{eventLine(r.new)}{detail && r.new && <EventDetail e={r.new} masked={masked} />}</span>
          <span role="cell" className={`${s.cell} ${s.ppCell}`} data-empty={!r.pp || undefined}>
            {r.pp && <><span className={s.ppTag}>{r.pp.tag}</span>{eventLine(r.pp)}</>}
          </span>
          {twin && <span role="cell" className={s.cell} data-empty={!r.twin || undefined}>{eventLine(r.twin)}</span>}
          {r.marker && <span className={s.marker}>{r.marker}</span>}
        </div>
      ))}
    </div>
  );
}

export default function S04_PaymentTests() {
  const { graftId } = useGraftCtx();
  const q = useScenarios(graftId);
  const [params, setParams] = useSearchParams();
  const [twin, setTwin] = useState(false);
  const list = useMemo(() => (q.data?.scenarios ?? []) as ScenarioRow[], [q.data]);
  const simulatedPayPal = list.some((r) => String(r.scenario.expect.evidence_class ?? '').includes('simulated-paypal'));

  const fallbackId = useMemo(() => {
    const by = (g: string) => list.find((r) => r.verdict?.grade === g)?.scenario.id;
    return by('PROBLEM') ?? by('PASS_FIXED') ?? list[0]?.scenario.id ?? null;
  }, [list]);
  const wanted = params.get('scenario');
  const selected = wanted && list.some((r) => r.scenario.id === wanted) ? wanted : fallbackId;
  const unknown = !!wanted && list.length > 0 && !list.some((r) => r.scenario.id === wanted);
  const cm = useCmel(graftId, selected);
  const row = list.find((r) => r.scenario.id === selected);

  useEffect(() => { document.title = 'GoldGraft · Payment tests'; }, []);

  const choose = (id: string) => setParams({ scenario: id }, { replace: true, preventScrollReset: true });

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const r of list) if (r.verdict?.grade) c[r.verdict.grade] = (c[r.verdict.grade] ?? 0) + 1;
    return GRADE_ORDER.filter((k) => c[k]).map((k) => ({ k, n: c[k], word: GRADE[k].count[c[k] === 1 ? 0 : 1] }));
  }, [list]);

  const v = row?.verdict;
  const hits = ((v?.rule_hits ?? []) as Hit[]);
  const oldHits = hits.filter((h) => h.side === 'OLD');
  const newHits = hits.filter((h) => h.side !== 'OLD');
  const masked = (v?.noise_masked ?? []) as string[];
  const rows = useMemo(() => (cm.data ? alignLanes(cm.data.old ?? [], cm.data.new ?? [], cm.data.old_twin ?? []) : []), [cm.data]);
  const hasLedger = rows.some((r) => r.pp);

  const callout = !v ? { tone: 'neutral', icon: <QuestionIcon size={18} />, text: 'No verdict yet.', note: '' }
    : oldHits.length ? { tone: 'warn', icon: <WarningIcon size={18} weight="fill" />, text: 'Bug found in your current shop. New checkout fixes it.', note: oldHits.map((h) => `Breaks ${h.rule}: ${ruleText(h.rule)}`).join(' · ') }
    : v.grade === 'PROBLEM' ? { tone: 'bad', icon: <XCircleIcon size={18} weight="fill" />, text: 'The new checkout is wrong here.', note: newHits.length ? newHits.map((h) => `Breaks ${h.rule}: ${ruleText(h.rule)}`).join(' · ') : 'The API sent no detail for this problem.' }
    : v.grade === 'UNVERIFIED' ? { tone: 'warn', icon: <QuestionIcon size={18} />, text: 'Not proven yet: some evidence is missing.', note: GRADE.UNVERIFIED.meaning }
    : null;

  if (q.isPending) return <div className={s.screen}><PageHead title="Payment tests" /><Skeleton what="payment tests" lines={5} /></div>;
  if (q.isError) return <div className={s.screen}><PageHead title="Payment tests" /><ProblemBanner error={q.error} onRetry={() => q.refetch()} /></div>;
  if (!list.length) return <div className={s.screen}><PageHead title="Payment tests" /><Empty title="No payment tests yet" text="They appear after the old shop is recorded." /></div>;

  const sc = row?.scenario as (ScenarioRow['scenario'] & { cart?: Record<string, unknown>; assured?: { passes_on_old?: boolean; flake_free_runs?: number }; expect?: Record<string, unknown>; rules?: string[] }) | undefined;

  return (
    <div className={s.screen}>
      <PageHead title="Payment tests" sub={<span className={s.chips}>{counts.map((c, i) => <span key={c.k} data-tone={GRADE[c.k].tone}>{i > 0 && <i aria-hidden>·</i>}{c.n} {c.word}</span>)}</span>} aside={isMock ? <SampleChip /> : undefined} />
      {simulatedPayPal && <p className={s.lanesNote}>Executed PHP recordings · simulated PayPal. The Proof page lists separately verified real sandbox checkout evidence.</p>}
      {unknown && <ProblemBanner error={{ message: `No payment test called ${wanted}. Showing the first one instead.` }} />}

      <div className={s.layout}>
        <div className={s.list} role="listbox" aria-label="Payment situations" aria-activedescendant={selected ? `sc-${selected}` : undefined}>
          {list.map((r) => {
            const on = r.scenario.id === selected;
            return (
              <button key={r.scenario.id} id={`sc-${r.scenario.id}`} role="option" aria-selected={on} className={s.option} data-on={on || undefined} onClick={() => choose(r.scenario.id)}>
                <span className={s.optName}>{SCENARIO_FAMILY[r.scenario.family] ?? r.scenario.family}</span>
                <span className={s.optTags}>
                  <GradeTag grade={r.verdict?.grade} />
                  {r.verdict?.grade === 'PASS_FIXED' && <span className={s.oldBug}>old bug found</span>}
                </span>
              </button>
            );
          })}
        </div>

        <div className={s.stage}>
          <h2 className={s.selHead}>
            {SCENARIO_FAMILY[row?.scenario.family ?? ''] ?? row?.scenario.family} <span>·</span> {GRADE[v?.grade ?? '']?.label ?? 'No verdict yet'}
          </h2>
          {callout && (
            <p key={selected} className={s.callout} data-tone={callout.tone} role={callout.tone === 'bad' ? 'alert' : undefined}>
              {callout.icon}<span>{callout.text}</span>{callout.note && <Explain text={callout.note} />}
            </p>
          )}
          <div className={s.lanesHead}>
            <span className={s.lanesNote}><ArrowsLeftRightIcon size={14} /> Old and new speak different PayPal; we translate both into one list.</span>
          </div>
          {cm.isPending ? <Skeleton what="money events" block height={220} /> : cm.isError ? <ProblemBanner error={cm.error} onRetry={() => cm.refetch()} /> : (
            <>
              <Lanes key={selected} rows={rows} twin={twin} masked={masked} detail={false} />
              {!hasLedger && <p className={s.noPP}>No PayPal record in this run.</p>}
            </>
          )}
        </div>
      </div>

      <Details>
        <div className={s.detailGrid}>
          <div>
            <h3 className={s.h3}>This situation</h3>
            <dl className={s.kv}>
              <dt>Scenario id</dt><dd><code className="gg-mono">{sc?.id}</code></dd>
              <dt>Rules checked</dt><dd>{(sc?.rules ?? []).map((r) => <div key={r}>{r} {ruleText(r)}</div>)}</dd>
              <dt>Cart</dt><dd>{Object.entries(sc?.cart ?? {}).map(([k, val]) => <div key={k}>{k}: {k === 'total' ? formatMoney(val as never) : String(val)}</div>)}</dd>
              <dt>Ran on the old shop first</dt><dd>{sc?.assured?.passes_on_old ? 'yes' : 'no'} · {sc?.assured?.flake_free_runs ?? 0} runs, same result</dd>
            </dl>
            {hits.length > 0 && <><h3 className={s.h3}>Evidence</h3><ul className={s.evList}>{hits.flatMap((h) => (h.evidence ?? []).map((e) => <li key={e}><code>{e}</code></li>))}</ul></>}
          </div>
          <div>
            <label className={s.twinToggle}><input type="checkbox" checked={twin} onChange={(e) => setTwin(e.target.checked)} /> Noise twin</label>
            {cm.data && <Lanes rows={rows} twin={twin} masked={masked} detail />}
            <dl className={s.kv}>
              <dt>Noise ignored</dt><dd className="gg-mono">{masked.join(', ') || '—'}</dd>
              <dt>Expected differences <Explain text="Old and new PayPal name things differently; declared up front." /></dt><dd>{((v?.deltas_applied ?? []) as string[]).join(' · ') || '—'}</dd>
              <dt>Differences found</dt>
              <dd>{((v?.parity_diff ?? []) as Array<Record<string, string>>).length === 0 ? 'No differences beyond the expected ones.' :
                ((v?.parity_diff ?? []) as Array<Record<string, string>>).map((d, i) => <div key={i}>{d.field ? `${d.field}: ${d.old} → ${d.new}${d.waived_by ? ` (waived: ${d.waived_by})` : ''}` : JSON.stringify(d)}</div>)}</dd>
              <dt>How it ran</dt>
              <dd>{((sc?.steps ?? []) as Array<Record<string, string>>).map((st, i) => <div key={i}>{st.driver_step ? `Robot buyer: ${st.driver_step}` : st.api_step ? `API: ${st.api_step}` : st.paypal_mock_response_code ? `PayPal test answer forced: ${st.paypal_mock_response_code}` : JSON.stringify(st)}</div>)}</dd>
              <dt>What we expected</dt><dd>{Object.entries(sc?.expect ?? {}).map(([k, val]) => <div key={k}>{k}: {String(val)}</div>)}</dd>
            </dl>
            <NotInApiYet what="Live buyer browser" gap="G3" />
          </div>
        </div>
      </Details>
    </div>
  );
}
