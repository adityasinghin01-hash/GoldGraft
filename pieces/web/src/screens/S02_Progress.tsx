import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowUpRightIcon, CheckIcon, LightningIcon } from '@phosphor-icons/react';
import { useQueryClient } from '@tanstack/react-query';
import { api, type FeedStatus } from '../api/client';
import { useScenarios } from '../api/queries';
import type { Graft, LedgerEntry } from '../api/types';
import { useGraftCtx } from '../shell/GraftLayout';
import { AGENT_JOB, ENTRY_TYPE, GRADE, GRADE_ORDER, HEAL_ACTION, LANE, MEANING, PHASES, STAGE, stageName } from '../copy/words';
import { Details, Empty, Explain, HashText, LiveStatus, Popup, PageHead, ProblemBanner, SampleChip, Stat, Tag } from '../components/ui';
import { Skeleton } from '../components/Loaders';
import { chainBreak } from '../lib/store';
import { formatDate, formatMinutes, formatPct, formatTime, formatUsd, plural } from '../lib/format';
import { config } from '../config';
import s from './screens.module.css';

type P = Record<string, unknown>;
const payload = (e: LedgerEntry) => (e.payload ?? {}) as P;
const isFake = (e: LedgerEntry) => String(payload(e).reason ?? '').includes('FAKE');

/** The live line: the newest step, in words (S2 table). */
function liveText(e: LedgerEntry | undefined): string {
  if (!e) return 'Waiting for the first step…';
  const p = payload(e);
  if ((e.type === 'STAGE' || e.type === 'MESSAGE') && e.schema === 'StageChange/1') {
    const actor = (p.actor as { name?: string } | undefined)?.name;
    if (actor === 'merchant-consent') return 'Approved by the merchant';
    return stageName(String(p.to_stage));
  }
  if (e.type === 'ARTIFACT' && e.schema === 'HealDecision/1') return `${HEAL_ACTION[String(p.action)] ?? p.action} · ${p.from_stage_pct}% → ${p.to_stage_pct}%`;
  if (e.type === 'ALERT' && e.schema === 'Alert/1') return `Alert: ${p.message}`;
  if (e.type === 'COST' && e.schema === 'BudgetRecord/1') return `AI cost: ${p.agent} ${formatUsd(Number(p.usd))}`;
  return `${ENTRY_TYPE[e.type] ?? e.type} · ${e.schema}`;
}

/** C11: one feed item, plain words first. */
function feedWords(e: LedgerEntry): string {
  const p = payload(e);
  if (e.schema === 'StageChange/1') {
    const actor = (p.actor as { name?: string } | undefined)?.name;
    if (actor === 'merchant-consent') return 'Merchant approved the change';
    const from = p.from_stage ? `${stageName(String(p.from_stage))} → ` : '';
    return `${from}${stageName(String(p.to_stage))}`;
  }
  if (e.schema === 'HealDecision/1') return `Go-live: ${HEAL_ACTION[String(p.action)] ?? p.action} ${p.from_stage_pct}% → ${p.to_stage_pct}%`;
  return liveText(e);
}

/** C5: ten phases, ticked off; repeats and switch-backs called out. */
function Rail({ g, showCost }: { g: Graft; showCost: boolean }) {
  const cur = STAGE[String(g.stage)]?.phase ?? 0;
  const done = String(g.stage) === 'DONE';
  const stages = g.stages ?? [];
  const visits = (name: string) => stages.filter((x) => x.stage === name).length;
  const perPhase = PHASES.map((ph) => {
    const rows = stages.filter((x) => STAGE[x.stage]?.phase === ph.n);
    return { minutes: rows.reduce((a, r) => a + (r.minutes ?? 0), 0), usd: rows.reduce((a, r) => a + (r.usd ?? 0), 0) };
  });
  return (
    <ol className={s.rail} aria-label="Upgrade phases">
      {PHASES.map((ph, i) => {
        const state = ph.n < cur || (done && ph.n === 10) ? 'done' : ph.n === cur ? 'now' : 'todo';
        const extra = ph.n === 7 && visits('PROVING') > 1 ? `×${visits('PROVING')}` : ph.n === 9 && visits('CUTBACK') > 0 ? `Switched back ×${visits('CUTBACK')}` : '';
        return (
          <li key={ph.n} className={s.railStep} data-state={state} style={{ ['--i' as string]: i }}>
            <span className={s.railDot} aria-hidden>{state === 'done' ? <CheckIcon size={11} weight="bold" /> : ph.n}</span>
            <span className={s.railName}>{ph.name}<Explain text={ph.meaning} /></span>
            <span className={s.railState}>{state === 'done' ? 'done' : state === 'now' ? (done ? 'done' : 'now') : 'not yet'}{extra && <b> · {extra}</b>}</span>
            {showCost && <span className={s.railCost}>{formatMinutes(perPhase[i].minutes)} · {formatUsd(perPhase[i].usd)}</span>}
          </li>
        );
      })}
    </ol>
  );
}

export default function S02_Progress() {
  const { graft: g, graftId, certId, reviewOpen, setReviewOpen } = useGraftCtx();
  const scen = useScenarios(graftId);
  const qc = useQueryClient();
  const [events, setEvents] = useState<LedgerEntry[]>([]);
  const [status, setStatus] = useState<FeedStatus>('connecting');
  const [nonce, setNonce] = useState(0);
  const refetchTimer = useRef(0);
  const [p1Closed, setP1Closed] = useState(false);
  const stageRef = useRef(String(g.stage));

  useEffect(() => { document.title = 'GoldGraft · Progress'; }, []);

  useEffect(() => {
    const seen = new Set<number>();
    setEvents([]);
    const feed = api.ledgerFeed(graftId, (e) => {
      if (seen.has(e.seq)) return;
      seen.add(e.seq);
      setEvents((prev) => [...prev, e]);
      const p = payload(e);
      if (e.schema === 'StageChange/1') {
        if (String(p.to_stage) === 'PR_OPEN') { setP1Closed(false); setReviewOpen(true); }
        window.clearTimeout(refetchTimer.current);
        refetchTimer.current = window.setTimeout(() => qc.invalidateQueries({ queryKey: ['graft', graftId] }), 1000);
      }
    }, setStatus);
    return () => { feed.close(); window.clearTimeout(refetchTimer.current); };
  }, [graftId, nonce, qc, setReviewOpen]);

  // P1 opens when the graft first loads in PR_OPEN
  useEffect(() => {
    if (String(g.stage) === 'PR_OPEN' && stageRef.current !== 'seen') { setReviewOpen(true); stageRef.current = 'seen'; }
  }, [g.stage, setReviewOpen]);

  const newest = events[events.length - 1];
  const card = g.card;
  const notes = (card?.notes ?? {}) as Record<string, string>;
  const synthetic = String(notes._label ?? '').includes('SYNTHETIC');
  const brk = useMemo(() => chainBreak(events), [events]);
  const ended = status === 'ended';
  const rootMatch = ended && newest ? newest.entry_hash === g.ledger_root : null;

  const grades = useMemo(() => {
    const c: Record<string, number> = {};
    let none = 0;
    for (const r of scen.data?.scenarios ?? []) {
      const gr = r.verdict?.grade;
      if (gr) c[gr] = (c[gr] ?? 0) + 1; else none++;
    }
    return { c, none };
  }, [scen.data]);
  const fixedCount = grades.c.PASS_FIXED ?? 0;
  const lastProve = useMemo(() => {
    const st = (g.stages ?? []).map((x) => x.stage);
    const pr = st.lastIndexOf('PR_OPEN');
    for (let i = pr - 1; i >= 0; i--) if (st[i] === 'CERTIFIED' || st[i] === 'PARTIAL') return st[i];
    return null;
  }, [g.stages]);

  const p1Lines = [
    lastProve === 'PARTIAL' ? 'Upgrade partly proven. Check Details before approving.' : 'Upgrade proven. Approve it to go live.',
    ...(fixedCount > 0 && scen.isSuccess ? [`Also fixes ${plural(fixedCount, 'bug', 'bugs')} in your current shop.`] : []),
  ];

  return (
    <div className={s.screen}>
      <PageHead title="Progress" aside={<LiveStatus status={status} last={newest?.ts} word="step" onReconnect={() => setNonce((n) => n + 1)} />} />

      <section className={s.block} aria-label="Phases">
        <Rail g={g} showCost={false} />
      </section>

      <section className={`gg-glass ${s.liveLine}`} aria-label="Newest step">
        <span className={s.liveIcon} aria-hidden><LightningIcon size={18} weight="duotone" /></span>
        <p key={newest?.seq ?? 0} className={s.liveText} aria-live="polite">{liveText(newest)}</p>
        {newest && <span className={s.liveSeq}>step {newest.seq}</span>}
      </section>

      <section className={s.block} aria-label="Numbers">
        <div className={s.statsHead}>{synthetic && <SampleChip />}</div>
        {card ? (
          <div className={s.stats}>
            <Stat label="Old pieces" value={card.old_pieces_found} note={notes.old_pieces_found ?? MEANING.old_pieces_found} />
            <Stat label="Upgraded" value={`${card.pieces_upgraded} of ${card.old_pieces_found}`} note={MEANING.pieces_upgraded} />
            <Stat label="Tests passed" value={`${card.scenarios_pass} of ${card.scenarios_total}`} note={notes.scenarios_pass ?? MEANING.scenarios_pass} to={`/g/${graftId}/union`} />
            <Stat label="Problems" value={card.problems} tone={(card.problems ?? 0) > 0 ? 'bad' : undefined} note={notes.problems ?? MEANING.problems} />
            <Stat label="Bugs caught" value={card.proof_strength_score == null ? 'not measured yet' : formatPct(card.proof_strength_score)} note={notes.proof_strength_score ?? MEANING.proof_strength_score} to={`/g/${graftId}/proof`} />
            <Stat label="AI cost" value={formatUsd(card.cost_usd)} note={notes.cost_usd ?? MEANING.cost_usd} />
            <Stat label="Time" value={formatMinutes(card.minutes)} note={MEANING.minutes} />
          </div>
        ) : <Skeleton what="numbers" lines={2} />}
      </section>

      {String(g.stage) === 'DONE' && certId && (
        <Link to={`/c/${certId}`} className={`gg-glass ${s.certCta}`}>
          <span>Upgrade finished. See its signed certificate.</span>
          <span className="gg-btn gg-btn--gold gg-btn--sm">Certificate <ArrowUpRightIcon size={13} /></span>
        </Link>
      )}

      <Details>
        <div className={s.detailGrid}>
          <div>
            <h2 className={s.h2}>Time and AI cost per phase</h2>
            <Rail g={g} showCost />
          </div>
          <div>
            <h2 className={s.h2}>Every step, newest first</h2>
            <p className={s.chain}>
              {brk === null ? `Step log intact: ${plural(events.length, 'step', 'steps')} linked.` : `Step log broken before step #${brk}`}
              <Explain text="Each step carries a fingerprint of the one before." />
            </p>
            {rootMatch !== null && <p className={s.muted}>{rootMatch ? 'Latest step matches the ledger root.' : "Latest step doesn't match the ledger root yet."}</p>}
            {events.length === 0 ? <Empty title="No steps yet" /> : (
              <ol className={s.feed}>
                {[...events].reverse().map((e) => {
                  const bad = e.type === 'ALERT' || (e.schema === 'StageChange/1' && String(payload(e).to_stage) === 'CUTBACK');
                  const who = e.producer?.name ?? '';
                  return (
                    <li key={e.seq} className={s.feedItem} data-bad={bad || undefined}>
                      <span className={`gg-num ${s.feedSeq}`}>#{e.seq}</span>
                      <span className={s.feedText}>{feedWords(e)}</span>
                      <span className={s.feedMeta}>
                        <Tag>{ENTRY_TYPE[e.type] ?? e.type}</Tag>
                        <span title={AGENT_JOB[who] ?? who}>{who}</span>
                        <time dateTime={e.ts} title={e.ts}>{formatTime(e.ts)}</time>
                        {isFake(e) && <SampleChip />}
                      </span>
                      {e.schema === 'HealDecision/1' && (() => {
                        const st = payload(e).stats as P | undefined;
                        return st ? <span className={s.feedSub}>P(new not worse) {formatPct(Number(st.prob_new_not_worse))} · needs {formatPct(Number(st.threshold))}</span> : null;
                      })()}
                    </li>
                  );
                })}
              </ol>
            )}
          </div>
          <div>
            <h2 className={s.h2}>Verdicts</h2>
            {scen.isError ? <ProblemBanner error={scen.error} onRetry={() => scen.refetch()} /> : scen.isPending ? <Skeleton what="verdicts" lines={1} /> : (
              <p>
                {GRADE_ORDER.filter((k) => (grades.c[k] ?? 0) > 0).map((k) => `${grades.c[k]} ${GRADE[k].count[grades.c[k] === 1 ? 0 : 1]}`).join(' · ')}
                {grades.none > 0 && ` · ${grades.none} no verdict yet`}
                {' '}<Link className="gg-link" to={`/g/${graftId}/union`}>Payment tests</Link>
              </p>
            )}
            <dl className={s.kv}>
              <dt>Upgrade id</dt><dd><code className="gg-mono">{g.graft_id}</code></dd>
              <dt>Path</dt><dd><Tag title={LANE[String(g.lane)]?.meaning}>{LANE[String(g.lane)]?.name ?? String(g.lane)}</Tag></dd>
              {g.started_at && <><dt>Started</dt><dd title={g.started_at}>{formatDate(g.started_at)}</dd></>}
              <dt>Ledger root <Explain text={MEANING.ledger_root} /></dt><dd><HashText value={g.ledger_root} /></dd>
            </dl>
          </div>
        </div>
      </Details>

      <Popup
        open={reviewOpen && String(g.stage) === 'PR_OPEN' && !p1Closed}
        lines={p1Lines}
        onClose={() => { setP1Closed(true); setReviewOpen(false); }}
        secondary={<button className="gg-btn gg-btn--ghost gg-btn--sm" onClick={() => { setP1Closed(true); setReviewOpen(false); }}>Later</button>}
        primary={<span title="Link to the pull request: not in the API yet (G2)"><button className="gg-btn gg-btn--gold gg-btn--sm" disabled>Approve ↗</button></span>}
      />
      {config.demoTools && null}
    </div>
  );
}
