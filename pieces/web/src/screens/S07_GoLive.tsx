import { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowUUpLeftIcon, ShieldCheckIcon, SirenIcon } from '@phosphor-icons/react';
import { api, type FeedStatus } from '../api/client';
import { useHealSnapshot } from '../api/queries';
import type { GuardEvent, HealFrame, HealState } from '../api/types';
import { useGraftCtx } from '../shell/GraftLayout';
import { GUARD_EVENT, H, HEAL_ACTION, MEANING, MUTANT, PATH, stageName } from '../copy/words';
import { DemoOnly, Details, Explain, HashText, LiveStatus, PageHead, Popup, ProblemBanner, SandboxChip } from '../components/ui';
import { ActionButton, Skeleton } from '../components/Loaders';
import { betaCurve, betaMean, betaSd } from '../lib/beta';
import { newIdempotencyKey } from '../lib/store';
import { formatDate, formatMoney, formatPct, formatTime } from '../lib/format';
import { config } from '../config';
import s from './s07.module.css';

const STEPS = [0, 1, 10, 50, 100];
const LIVE_STAGES = ['HEAL_1', 'HEAL_10', 'HEAL_50', 'LIVE_100'];
type Decision = NonNullable<HealState['last_decision']>;

function Curves({ st }: { st: NonNullable<Decision['stats']> }) {
  const a1 = st.success_old + 1, b1 = st.n_old - st.success_old + 1;
  const a2 = st.success_new + 1, b2 = st.n_new - st.success_new + 1;
  const lo = Math.max(0, Math.min(betaMean(a1, b1) - 4 * betaSd(a1, b1), betaMean(a2, b2) - 4 * betaSd(a2, b2)));
  const old = betaCurve(a1, b1, lo), neu = betaCurve(a2, b2, lo);
  const maxY = Math.max(...old.map((p) => p[1]), ...neu.map((p) => p[1]));
  const W = 560, Hh = 180;
  const path = (pts: Array<[number, number]>) => pts.map(([x, y], i) => `${i ? 'L' : 'M'}${(((x - lo) / (1 - lo)) * W).toFixed(1)} ${(Hh - (y / maxY) * (Hh - 10)).toFixed(1)}`).join(' ');
  return (
    <figure className={s.curves}>
      <figcaption>Each curve shows where a checkout's real success rate likely is <Explain text="New at or right of old means new does at least as well." /></figcaption>
      <svg viewBox={`0 0 ${W} ${Hh + 24}`} role="img" aria-label="Old and new success-rate curves">
        <path d={`${path(old)} L${W} ${Hh} L0 ${Hh} Z`} className={s.curveOldFill} />
        <path d={path(old)} className={s.curveOld} />
        <path d={path(neu)} className={s.curveNew} />
        <line x1="0" x2={W} y1={Hh} y2={Hh} className={s.axis} />
        <text x="0" y={Hh + 18} className={s.axisText}>{formatPct(lo)}</text>
        <text x={W} y={Hh + 18} textAnchor="end" className={s.axisText}>100%</text>
      </svg>
      <p className={s.legend}><span data-k="old" /> Old <span data-k="new" /> New · P(new not worse) {formatPct(st.prob_new_not_worse)} · needs {formatPct(st.threshold)}</p>
    </figure>
  );
}

export default function S07_GoLive() {
  const { graftId } = useGraftCtx();
  const snap = useHealSnapshot(graftId);
  const [state, setState] = useState<HealState | null>(null);
  const [payments, setPayments] = useState<GuardEvent[]>([]);
  const [status, setStatus] = useState<FeedStatus>('connecting');
  const [nonce, setNonce] = useState(0);
  const [p2, setP2] = useState(false);
  const [p3, setP3] = useState(false);
  const [op, setOp] = useState('M2');
  const [injecting, setInjecting] = useState(false);
  const [injectLabel, setInjectLabel] = useState<string | null>(null);
  const [timer, setTimer] = useState<{ t0: number; result: number | null; gaveUp: boolean } | null>(null);
  const [now, setNow] = useState(0);
  const [injectErr, setInjectErr] = useState<unknown>(null);
  const keyRef = useRef<string>('');

  useEffect(() => { document.title = 'GoldGraft · Go-live'; }, []);

  const addPayments = (list: GuardEvent[]) => {
    setPayments((prev) => {
      const key = (p: GuardEvent) => `${p.order_ref}|${p.event}|${p.ts}`;
      const have = new Set(prev.map(key));
      const fresh = list.filter((p) => !have.has(key(p)));
      return [...fresh.reverse(), ...prev].slice(0, 50);
    });
  };

  // first paint from the JSON snapshot
  useEffect(() => {
    if (snap.data && !state) { setState(snap.data); addPayments((snap.data.recent ?? []) as GuardEvent[]); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [snap.data]);

  // then the live feed; frames replace the state, payments accumulate
  useEffect(() => {
    let maxSeq = 0;
    const feed = api.healFeed(graftId, (f: HealFrame) => {
      if (f.seq <= maxSeq) return;
      maxSeq = f.seq;
      setState((prev) => {
        if (prev && prev.stage !== 'CUTBACK' && f.stage === 'CUTBACK') setP3(true);
        return f;
      });
      addPayments((f.recent ?? []) as GuardEvent[]);
      if (f.stage === 'CUTBACK' || f.last_decision?.action === 'CUTBACK') {
        setTimer((t) => (t && t.result === null ? { ...t, result: performance.now() - t.t0 } : t));
      }
    }, setStatus);
    return () => feed.close();
  }, [graftId, nonce]);

  // the switch-back timer counts only real waiting time; gives up after 60 s
  useEffect(() => {
    if (!timer || timer.result !== null || timer.gaveUp) return;
    const id = setInterval(() => {
      const el = performance.now() - timer.t0;
      setNow(el);
      if (el > 60_000) setTimer((t) => (t ? { ...t, gaveUp: true } : t));
    }, 100);
    return () => clearInterval(id);
  }, [timer]);

  const inject = async () => {
    if (!keyRef.current) keyRef.current = newIdempotencyKey();
    setInjecting(true); setInjectErr(null);
    try {
      const r = await api.injectFault(graftId, op, keyRef.current);
      setInjectLabel(r.accepted ? r.label : 'The system did not accept the fault.');
      if (r.accepted) setTimer({ t0: performance.now(), result: null, gaveUp: false });
      keyRef.current = '';
    } catch (e) { setInjectErr(e); } finally { setInjecting(false); }
  };

  const st = state;
  const d = st?.last_decision as Decision | undefined;
  const stats = d?.stats;
  const cut = st?.stage === 'CUTBACK' || d?.action === 'CUTBACK';
  const pctNow = st?.stage_pct ?? 0;
  const sure = stats ? stats.prob_new_not_worse >= stats.threshold : false;
  const t2 = d?.action === 'CUTBACK' ? 'New checkout broke a money rule' : stats && stats.prob_new_not_worse >= stats.threshold ? 'New checkout is no worse than the old' : 'Not sure yet: waiting for more payments';
  const topLine = st ? (st.stage === 'SHADOW' && st.stage_pct === 0 ? 'Testing on copies of real carts' : stageName(st.stage)) : '';
  const sw = st?.switch_config as { version?: number; stage_pct?: number; expires_at?: string; origin_rules?: string[]; signature?: string } | undefined;
  const lastTs = useMemo(() => payments[0]?.ts ?? null, [payments]);

  return (
    <div className={s.screen} data-cut={cut || undefined}>
      <div className={s.pinned}><SandboxChip text={st?.label ?? 'PayPal sandbox · simulated buyers'} /></div>
      <PageHead title="Go-live" aside={<LiveStatus status={status} last={lastTs} word="update" onReconnect={() => setNonce((n) => n + 1)} />} />

      {snap.isError && !st ? <ProblemBanner error={snap.error} onRetry={() => snap.refetch()} /> : !st ? <Skeleton what="go-live" lines={4} /> : (
        <>
          <section className={s.hero} aria-live="polite">
            <p className={s.top} key={st.stage}>{topLine}</p>
            <div className={s.track} role="img" aria-label={`Stepper: ${pctNow}% of buyers on the new checkout`}>
              <div className={s.flow} aria-hidden>
                <span className={s.flowOld} style={{ flexBasis: `${100 - pctNow}%` }}><i /><i /><i /></span>
                <span className={s.flowNew} style={{ flexBasis: `${pctNow}%` }}><i /><i /><i /></span>
              </div>
              <ol className={s.stepper}>
                {STEPS.map((p) => (
                  <li key={p} data-state={cut ? 'cut' : p < pctNow ? 'done' : p === pctNow ? 'now' : undefined}>{p}%</li>
                ))}
              </ol>
            </div>
            <div className={s.guard} data-bad={cut || undefined}>
              {cut ? <SirenIcon size={18} weight="fill" /> : <ShieldCheckIcon size={18} weight="duotone" />}
              <span>{st.guard}</span>
              <Explain text="Every new-checkout payment is checked; one broken rule switches back." />
            </div>
            <p className={s.move}>
              {d ? <>{HEAL_ACTION[d.action] ?? d.action} · {d.from_stage_pct}% → {d.to_stage_pct}%</> : 'No move yet.'}
              {d?.hard_stop && <span className={s.hardStop}>Hard stop: {d.hard_stop}</span>}
            </p>
          </section>

          {stats && (
            <section className={`gg-glass ${s.bars}`}>
              <h2 className={s.h2} data-bad={d?.action === 'CUTBACK' || undefined}>{t2}</h2>
              {[['Old', stats.success_old, stats.n_old], ['New', stats.success_new, stats.n_new]].map(([label, ok, n]) => (
                <div key={label as string} className={s.barRow}>
                  <span className={s.barLabel}>{label}: {ok} of {n} paid</span>
                  <span className={s.bar} data-k={label}><span style={{ width: `${(Number(ok) / Math.max(1, Number(n))) * 100}%` }} /></span>
                </div>
              ))}
              <p className={s.sure} data-bad={!sure || undefined}>
                {formatPct(stats.prob_new_not_worse)} sure new is no worse · needs {formatPct(stats.threshold)}
                <Explain text={MEANING.prob_new_not_worse} />
              </p>
            </section>
          )}

          <section className={s.payments} aria-label="Payments">
            <h2 className={s.h2}>Payments</h2>
            {payments.length === 0 ? <p className={s.muted}>No payments yet at this step.</p> : (
              <table className={s.table}>
                <thead><tr><th>Time</th><th>Amount</th><th>Payment</th><th>Checkout</th></tr></thead>
                <tbody>
                  {payments.slice(0, 12).map((p) => {
                    const ge = GUARD_EVENT[p.event];
                    return (
                      <tr key={`${p.order_ref}|${p.event}|${p.ts}`} data-path={p.path}>
                        <td className="gg-num">{formatTime(p.ts)}</td>
                        <td className="gg-num">{formatMoney(p.money)}</td>
                        <td data-tone={ge?.tone}>{ge?.text ?? p.event}</td>
                        <td>{PATH[p.path] ?? p.path}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </section>

          {LIVE_STAGES.includes(st.stage) && (
            <div className={s.switchRow}>
              <span title="Switch back: not in the API yet (G12)">
                <button className="gg-btn gg-btn--ghost" onClick={() => setP2(true)}><ArrowUUpLeftIcon size={16} /> Switch back</button>
              </span>
            </div>
          )}

          {config.demoTools && (
            <DemoOnly label={injectLabel?.replace(/^DEMO ONLY\s*[·:-]?\s*/i, '') || undefined}>
              <div className={s.inject}>
                <label htmlFor="mutant">Inject a fault</label>
                <select id="mutant" value={op} onChange={(e) => setOp(e.target.value)}>
                  {Object.entries(MUTANT).map(([k, v]) => <option key={k} value={k}>{k} · {v.text}</option>)}
                </select>
                <ActionButton busy={injecting} busyText="Injecting…" onClick={inject} variant="ghost">Inject</ActionButton>
              </div>
              {injectErr ? <ProblemBanner error={injectErr} onRetry={inject} /> : null}
              {timer && (
                <p className={s.timer} data-done={timer.result !== null || undefined}>
                  {timer.result !== null ? <>Switched back in <b className="gg-num">{(timer.result / 1000).toFixed(1)} s</b> {H.measured}</>
                    : timer.gaveUp ? 'No switch-back seen yet.' : <>Watching for the switch-back… <b className="gg-num">{(now / 1000).toFixed(1)} s</b></>}
                </p>
              )}
            </DemoOnly>
          )}

          <Details>
            <div className={s.detailGrid}>
              {d?.reason && <p><b>Why:</b> {d.reason}</p>}
              {stats && <Curves st={stats} />}
              <div>
                <h3 className={s.h3}>Payments, more detail</h3>
                <table className={s.table}>
                  <thead><tr><th>Time</th><th>Order</th><th>PayPal took <Explain text={MEANING.latency_ms} /></th><th>Payment</th></tr></thead>
                  <tbody>{payments.slice(0, 12).map((p) => (
                    <tr key={`d-${p.order_ref}|${p.event}|${p.ts}`}><td className="gg-num">{formatTime(p.ts)}</td><td><code className="gg-mono">{p.order_ref}</code></td><td className="gg-num">{p.latency_ms} ms</td><td>{GUARD_EVENT[p.event]?.text}</td></tr>
                  ))}</tbody>
                </table>
              </div>
              {sw && (
                <div>
                  <h3 className={s.h3}>Switch setting <Explain text="The shop's switch library reads this signed setting within about 15 s." /></h3>
                  <p>Setting version {sw.version} · {sw.stage_pct}% to new{sw.expires_at ? ` · valid until ${formatDate(sw.expires_at)}` : ''}</p>
                  {sw.origin_rules?.length ? <p>Kept on the old system: {sw.origin_rules.join(', ')}</p> : null}
                  {sw.signature && <HashText value={sw.signature} />}
                </div>
              )}
            </div>
          </Details>
        </>
      )}

      <Popup open={p2} lines={['All buyers will go back to the old checkout.']} onClose={() => setP2(false)} tone="bad" badge={<SandboxChip text={st?.label ?? 'PayPal sandbox · simulated buyers'} />}
        secondary={<button className="gg-btn gg-btn--ghost gg-btn--sm" onClick={() => setP2(false)}>Cancel</button>}
        primary={<span title="Switch back: not in the API yet (G12)"><button className="gg-btn gg-btn--gold gg-btn--sm" disabled>Switch back</button></span>} />
      <Popup open={p3} lines={['Switched back to the old checkout.', 'A payment looked wrong.']} onClose={() => setP3(false)} tone="bad" badge={<SandboxChip text={st?.label ?? 'PayPal sandbox · simulated buyers'} />}
        primary={<button className="gg-btn gg-btn--gold gg-btn--sm" onClick={() => setP3(false)} autoFocus>OK</button>} />
    </div>
  );
}
