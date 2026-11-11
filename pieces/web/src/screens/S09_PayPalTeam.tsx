import { useEffect, useRef, useState } from 'react';
import { ChatCircleDotsIcon, SparkleIcon } from '@phosphor-icons/react';
import { api } from '../api/client';
import { useOrchard } from '../api/queries';
import type { OrchardAnswer } from '../api/types';
import { FAMILY, H, MEANING, stageName } from '../copy/words';
import { Details, Explain, NotInApiYet, PageHead, ProblemBanner, SampleChip, Tag } from '../components/ui';
import { Bars } from '../components/Bars';
import { ActionButton, Skeleton, Thinking } from '../components/Loaders';
import { newIdempotencyKey } from '../lib/store';
import s from './s09.module.css';

type Shop = { shop_id: string; stage: string; old_families: string[]; deadline_risk?: string; paypal_only_items: number };
type Spec = { title?: string; question?: string; metrics?: string[]; group_by?: string[]; filters?: Record<string, string>; producer?: { name?: string }; evidence_refs?: string[] };

const CHIPS = [
  { label: 'Express Checkout', q: 'Which shops still use old Express Checkout?' },
  { label: 'PayPal-only steps', q: 'Which shops have steps only PayPal can do?' },
  { label: '2027 deadline', q: 'Which shops face the 2027 Buy Now deadline?' },
];

/** DashboardView: counts computed from the shops table, only for the specs the pack supports. */
function Dashboard({ spec, shops }: { spec: Spec; shops: Shop[] }) {
  const metrics = spec.metrics ?? [];
  const groups = spec.group_by ?? [];
  const ok = metrics.every((m) => m === 'shop_count') && groups.every((g) => ['family', 'stage', 'deadline_risk'].includes(g));
  if (!ok) return <NotInApiYet what={`Dashboard data for ${metrics.join(', ')}`} gap="G6" />;
  const rows = shops.filter((sh) => Object.entries(spec.filters ?? {}).every(([k, v]) => k === 'family' ? sh.old_families.includes(v) : String((sh as Record<string, unknown>)[k]) === v));
  const counts = new Map<string, number>();
  for (const sh of rows) {
    const keys = groups[0] === 'family' ? sh.old_families : groups[0] === 'stage' ? [sh.stage] : [sh.deadline_risk ?? '—'];
    for (const k of keys) counts.set(k, (counts.get(k) ?? 0) + 1);
  }
  const n = rows.length;
  const title = n === 1 ? '1 shop matches this question' : `${n} shops match this question`;
  return (
    <div className={s.dash}>
      <Bars title={title} bars={[...counts.entries()].map(([k, v]) => ({ label: groups[0] === 'family' ? FAMILY[k]?.short ?? k : groups[0] === 'stage' ? stageName(k) : k, value: v, display: String(v), hot: true }))} />
      {spec.title && <p className={s.dashTitle}>{spec.title}</p>}
      {n === 0 && <p className={s.muted}>No shops match.</p>}
    </div>
  );
}

export default function S09_PayPalTeam() {
  const q = useOrchard();
  const [question, setQuestion] = useState('');
  const [asked, setAsked] = useState<string | null>(null);
  const [answer, setAnswer] = useState<OrchardAnswer | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<unknown>(null);
  const key = useRef({ q: '', k: '' });
  const inputRef = useRef<HTMLInputElement>(null);
  useEffect(() => { document.title = 'GoldGraft · PayPal team view'; }, []);

  const ask = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const text = question.trim();
    if (!text) return;
    if (key.current.q !== text) key.current = { q: text, k: newIdempotencyKey() };
    setAsked(text); setAnswer(null); setBusy(true); setErr(null);
    try { setAnswer(await api.ask(text, key.current.k)); } catch (x) { setErr(x); } finally { setBusy(false); }
  };

  const shops = ((q.data?.shops ?? []) as Shop[]);
  const needPP = shops.filter((x) => x.paypal_only_items > 0).length;
  const label = String(q.data?.label ?? '');

  return (
    <div className={s.screen}>
      <PageHead title="PayPal team view" sub={<span className={s.honest}>{H.testShopsOnly} {label.includes('SYNTHETIC') && <SampleChip />}</span>} />
      {q.isPending ? <Skeleton what="shops" lines={3} /> : q.isError ? <ProblemBanner error={q.error} onRetry={() => q.refetch()} /> : (
        <>
          <p className={s.top}>{shops.length === 1 ? '1 test shop' : `${shops.length} test shops`} · {needPP === 1 ? '1 needs' : `${needPP} need`} PayPal's own steps</p>

          <form className={`gg-glass ${s.ask}`} onSubmit={ask}>
            <label htmlFor="ask" className={s.askLabel}><ChatCircleDotsIcon size={16} weight="duotone" /> Ask about all shops <Explain text="The Analyst only reads the shop table. It changes nothing." /></label>
            <div className={s.askRow}>
              <input ref={inputRef} id="ask" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Which shops still take old Buy Now money?" />
              <ActionButton type="submit" busy={busy} busyText="Asking…" disabled={!question.trim()}><SparkleIcon size={15} weight="fill" /> Ask</ActionButton>
            </div>
            <div className={s.chips}>
              {CHIPS.map((c) => <button key={c.label} type="button" className={s.chip} onClick={() => { setQuestion(c.q); inputRef.current?.focus(); }}>{c.label}</button>)}
            </div>
          </form>

          {asked && (
            <section className={s.answer} aria-live="polite">
              <p className={s.asked}>{asked}</p>
              {busy && <Thinking />}
              {err ? <ProblemBanner error={err} onRetry={() => ask()} /> : null}
              {answer && (
                <>
                  <p className={s.answerText}><span className={s.answerLabel}>Answer to: {answer.question}</span>{answer.answer}</p>
                  {answer.dashboard && <Dashboard spec={answer.dashboard as Spec} shops={shops} />}
                  <Details>
                    {answer.dashboard && (() => {
                      const d = answer.dashboard as Spec;
                      return (
                        <div className={s.spec}>
                          <p>Shows {(d.metrics ?? []).join(', ')} grouped by {(d.group_by ?? []).join(', ')}</p>
                          {Object.entries(d.filters ?? {}).map(([k, v]) => <p key={k}>Filter: {k} = {v}</p>)}
                          {d.question && <p>Built for: {d.question}</p>}
                          {d.producer?.name && <p>made by {d.producer.name}</p>}
                        </div>
                      );
                    })()}
                  </Details>
                </>
              )}
            </section>
          )}

          <div className={s.tableWrap}>
            <table className={s.table}>
              <thead><tr><th>Shop</th><th>Stage</th><th>Old PayPal</th><th>Deadline risk</th><th>PayPal-only steps <Explain text={MEANING.paypal_only_items} /></th></tr></thead>
              <tbody>{shops.map((sh) => (
                <tr key={sh.shop_id}>
                  <td className="gg-mono">{sh.shop_id}</td>
                  <td><Tag tone={sh.stage === 'DONE' ? 'good' : 'gold'}>{stageName(sh.stage)}</Tag></td>
                  <td className={s.fams}>{sh.old_families.map((f) => <Tag key={f} title={FAMILY[f]?.full}>{FAMILY[f]?.short ?? f}</Tag>)}</td>
                  <td>{sh.deadline_risk}</td>
                  <td className="gg-num">{sh.paypal_only_items}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
          <NotInApiYet what="Open a shop's upgrade" gap="G5" />
        </>
      )}
    </div>
  );
}
