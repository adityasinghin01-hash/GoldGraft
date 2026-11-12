import { useEffect, useMemo, useState } from 'react';
import { CheckIcon, CodeIcon, PackageIcon, WarningIcon } from '@phosphor-icons/react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { useConnected } from '../api/queries';
import { api } from '../api/client';
import type { CodeChange, PlantedBugCheck } from '../api/types';
import { useGraftCtx } from '../shell/GraftLayout';
import { Explain, PageHead, ProblemBanner, SampleChip, Tag } from '../components/ui';
import { Skeleton } from '../components/Loaders';
import { isMock } from '../config';
import s from './s13.module.css';

type Line = { kind: 'same' | 'add' | 'del'; text: string; a?: number; b?: number };

/** Line diff by longest common subsequence (files here are under ~200 lines). */
function diff(before: string, after: string): Line[] {
  const a = before ? before.split('\n') : [];
  const b = after.split('\n');
  const n = a.length, m = b.length;
  const dp: number[][] = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--)
    dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  const out: Line[] = [];
  let i = 0, j = 0;
  while (i < n && j < m) {
    if (a[i] === b[j]) { out.push({ kind: 'same', text: a[i], a: i + 1, b: j + 1 }); i++; j++; }
    else if (dp[i + 1][j] >= dp[i][j + 1]) { out.push({ kind: 'del', text: a[i], a: i + 1 }); i++; }
    else { out.push({ kind: 'add', text: b[j], b: j + 1 }); j++; }
  }
  while (i < n) { out.push({ kind: 'del', text: a[i], a: i + 1 }); i++; }
  while (j < m) { out.push({ kind: 'add', text: b[j], b: j + 1 }); j++; }
  return out;
}

/** Keep 3 lines of context around changes; fold longer unchanged runs. */
function hunks(lines: Line[]): Array<Line | { fold: number }> {
  const keep = lines.map((l, k) => l.kind !== 'same' || lines.slice(Math.max(0, k - 3), k + 4).some((x) => x.kind !== 'same'));
  const out: Array<Line | { fold: number }> = [];
  let folded = 0;
  lines.forEach((l, k) => {
    if (keep[k]) { if (folded) { out.push({ fold: folded }); folded = 0; } out.push(l); } else folded++;
  });
  if (folded) out.push({ fold: folded });
  return out;
}

function FileDiff({ change, lintOk }: { change: CodeChange; lintOk?: boolean }) {
  const [open, setOpen] = useState(change.author === 'model');
  const lines = useMemo(() => diff(change.before, change.after), [change]);
  const added = lines.filter((l) => l.kind === 'add').length;
  const removed = lines.filter((l) => l.kind === 'del').length;
  return (
    <section className={`gg-glass ${s.file}`}>
      <button className={s.fileHead} onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        {change.author === 'model' ? <CodeIcon size={18} aria-hidden /> : <PackageIcon size={18} aria-hidden />}
        <span className={s.path}>{change.path}</span>
        <Tag tone={change.author === 'model' ? 'gold' : undefined}>
          {change.author === 'model' ? 'Written by the Grafter agent' : 'GoldGraft library · not AI-written'}
        </Tag>
        {lintOk !== undefined && (
          <Tag tone={lintOk ? 'good' : 'bad'}>{lintOk ? 'PHP parses' : 'PHP error'}</Tag>
        )}
        <span className={s.counts}><b className={s.plus}>+{added}</b> <b className={s.minus}>−{removed}</b></span>
      </button>
      {open && (
        <pre className={s.code} aria-label={`Changes in ${change.path}`}>
          {hunks(lines).map((l, k) =>
            'fold' in l ? (
              <span key={k} className={s.fold}>⋯ {l.fold} unchanged lines</span>
            ) : (
              <span key={k} className={s[l.kind]}>
                <i className={s.no}>{l.kind === 'add' ? '' : l.a}</i>
                <i className={s.no}>{l.kind === 'del' ? '' : l.b}</i>
                <i className={s.sign}>{l.kind === 'add' ? '+' : l.kind === 'del' ? '−' : ' '}</i>
                {l.text || ' '}
              </span>
            ),
          )}
        </pre>
      )}
    </section>
  );
}

function PlantedBugs({ check }: { check: PlantedBugCheck }) {
  const applied = check.mutants.filter((m) => m.applied);
  return (
    <section className={s.open}>
      <h2 className={s.h2}>
        Code-review planted bugs: {check.caught} of {check.planted} caught{' '}
        <Explain text="GoldGraft copies the AI-written code, plants one known money bug in each copy, and runs its code review on every copy. A caught bug means the review refused that copy. This tests the review, not the independent proof or a real payment." />
      </h2>
      <ul className={s.bugs}>
        {applied.map((m) => (
          <li key={m.id}>
            <Tag tone={m.caught ? 'good' : 'bad'}>{m.caught ? 'Caught' : 'Missed'}</Tag>
            <span>{m.what}</span>
            {m.file && <code>{m.file}</code>}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function S13_Changes() {
  const { graftId } = useGraftCtx();
  const q = useQuery({ queryKey: ['changes', graftId], queryFn: () => api.changes(graftId), retry: 0 });
  const connected = useConnected(graftId);
  useEffect(() => { document.title = 'GoldGraft · Code changes'; }, []);

  if (q.isPending) return <div className={s.screen}><PageHead title="Code changes" /><Skeleton what="code changes" lines={4} /></div>;
  if (q.isError) return (
    <div className={s.screen}>
      <PageHead title="Code changes" sub="No code yet: the Grafter agent has not written this upgrade's checkout." />
      <ProblemBanner error={q.error} onRetry={() => q.refetch()} />
    </div>
  );

  const files = q.data.files ?? [];
  const model = files.filter((f) => f.author === 'model');
  const lint = q.data.lint ?? {};
  const lintKeys = Object.keys(lint);
  const parsed = lintKeys.filter((k) => lint[k].ok).length;

  return (
    <div className={s.screen}>
      <PageHead
        title="Code changes"
        sub={`${model.length} ${model.length === 1 ? 'file' : 'files'} rewritten by the Grafter agent, plus the GoldGraft library it calls`}
        aside={q.data.recorded_from
          ? <Tag tone="gold" title="Recorded from a real integrated agent run">Real AI output · run {q.data.recorded_from}</Tag>
          : isMock ? <SampleChip /> : <Tag tone="gold">Real AI output</Tag>}
      />
      {lintKeys.length > 0 && (
        <p className={s.check} data-ok={parsed === lintKeys.length || undefined}>
          {parsed === lintKeys.length ? <CheckIcon size={16} weight="bold" aria-hidden /> : <WarningIcon size={16} weight="fill" aria-hidden />}
          PHP syntax check: {parsed} of {lintKeys.length} files parse. {connected.data?.provider_checks.shop_checkout_paypal_sandbox?.state === 'verified'
            ? <>The shop's own PayPal sandbox checkout is independently verified for {(connected.data.provider_checks.shop_checkout_paypal_sandbox.scenarios ?? []).join(', ') || 'the selected recordings'}. <Link className="gg-link" to={`/g/${graftId}/proof`}>See scope and proof</Link>.</>
            : "Running the new checkout against PayPal's sandbox is not verified for this run yet."}
        </p>
      )}
      <div className={s.files}>
        {files.map((f) => <FileDiff key={f.path} change={f} lintOk={lint[f.path]?.ok} />)}
      </div>
      {q.data.mutations && q.data.mutations.planted > 0 && <PlantedBugs check={q.data.mutations} />}
      {(q.data.open_items ?? []).length > 0 && (
        <section className={s.open}>
          <h2 className={s.h2}>Not changed in this upgrade</h2>
          <ul>
            {q.data.open_items.map((o) => (
              <li key={o.touchpoint}>
                <code>{o.location.file}:{o.location.line}</code> · {o.family === 'CHECKOUT_JS_V4'
                  ? 'the checkout.js v4 browser button. This upgrade covers server code; the button moves to PayPal\'s JavaScript SDK in a separate step.'
                  : `${o.family}: outside this upgrade profile.`}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
