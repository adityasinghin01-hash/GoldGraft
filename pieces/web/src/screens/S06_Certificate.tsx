import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { CheckIcon, LinkSimpleIcon, SealCheckIcon, SealWarningIcon, XIcon } from '@phosphor-icons/react';
import { api } from '../api/client';
import { useCertificate } from '../api/queries';
import type { CertificateVerifyResult } from '../api/types';
import { CERT_CHECK, H, MEANING } from '../copy/words';
import { DemoOnly, Details, Explain, HashText, PageHead, ProblemBanner, SampleChip } from '../components/ui';
import { ActionButton, Skeleton } from '../components/Loaders';
import { formatDate, formatMinutes, formatPct, formatUsd, plural } from '../lib/format';
import { config, isMock } from '../config';
import s from './s06.module.css';

type Check = { name: string; ok: boolean; detail?: string };
const isHex = (v: string) => /^[0-9a-f]{40}$|^[0-9a-f]{64}$/i.test(v);
const Val = ({ v }: { v?: string | null }) => (!v ? <>—</> : isHex(v) ? <HashText value={v} /> : v.startsWith('http') ? <a className="gg-link" href={v} target="_blank" rel="noreferrer">{v}</a> : <code className="gg-mono">{v}</code>);

export default function S06_Certificate() {
  const { certId = '' } = useParams();
  const q = useCertificate(certId);
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<CertificateVerifyResult | null>(null);
  const [err, setErr] = useState<unknown>(null);
  const [revealed, setRevealed] = useState(0);
  const [copied, setCopied] = useState(false);

  useEffect(() => { document.title = 'GoldGraft · Certificate'; setRes(null); setRevealed(0); }, [certId]);

  const check = async () => {
    setBusy(true); setErr(null); setRes(null); setRevealed(0);
    try {
      const r = await api.verify(certId);
      setRes(r);
      const n = (r.checks ?? []).length;
      for (let i = 1; i <= n + 1; i++) window.setTimeout(() => setRevealed(i), i * 380);
    } catch (e) { setErr(e); } finally { setBusy(false); }
  };
  const copy = async () => {
    try { await navigator.clipboard.writeText(window.location.href); setCopied(true); setTimeout(() => setCopied(false), 1600); } catch { /* blocked */ }
  };

  if (q.isPending) return <div className={s.screen}><PageHead title="Certificate" /><Skeleton what="certificate" lines={4} /></div>;
  if (q.isError) return <div className={s.screen}><PageHead title="Certificate" /><ProblemBanner error={q.error} onRetry={() => q.refetch()} /></div>;

  const c = q.data as typeof q.data & Record<string, unknown>;
  const r = c.results as { scenarios: number; problem: number; pass: number; pass_fixed: number; unverified: number; n_a: number };
  const ps = c.proof_strength as { killed: number; mutants_total: number; equivalent_dropped: number; score: number };
  const sec = c.security as { secrets_found: number; injection_attempts_blocked: number; deps_blocked: number };
  const sv = c.survey as { recall: number; precision: number; misses_learned: number };
  const sample = String(c.signature ?? '').includes('fixture') || isMock;
  const tampered = certId === config.standInIds.tamperedCertId;
  const checks = ((res?.checks ?? []) as Check[]);
  const sigFailed = checks.some((k) => k.name === 'SIGNATURE' && !k.ok);
  const done = res && revealed > checks.length;
  const evidence = ((c.paypal_evidence ?? []) as Array<Record<string, string>>);

  return (
    <div className={s.screen}>
      <div className={s.layout}>
        <div className={s.main}>
          <PageHead title={<>Certificate <span className={s.shop}>· {c.shop_id}</span></>} sub="Proof that this shop's PayPal upgrade was tested and signed." />
          <p className={s.issued} title={c.issued_at}>Issued {formatDate(c.issued_at)}</p>
          {sample && <p className={s.honest}><SampleChip /> {H.sampleCert}</p>}
          {tampered && <p className={s.honest} data-bad>{H.tamperedCopy}</p>}

          <div className={s.actions}>
            <ActionButton busy={busy} busyText="Checking…" onClick={check}>Check</ActionButton>
            <button className="gg-btn gg-btn--ghost" onClick={copy}><LinkSimpleIcon size={16} /> {copied ? 'Copied' : 'Copy link'}</button>
          </div>
          {err ? <ProblemBanner error={err} onRetry={check} /> : null}

          {res && (
            <ul className={s.ticks} aria-live="polite">
              {checks.map((k, i) => (
                <li key={k.name} data-ok={k.ok || undefined} data-on={i < revealed || undefined}>
                  <span className={s.tickIcon} aria-hidden>{k.ok ? <CheckIcon size={13} weight="bold" /> : <XIcon size={13} weight="bold" />}</span>
                  <span>{CERT_CHECK[k.name]?.name ?? k.name}</span><span className="gg-sr-only">{k.ok ? 'passed' : 'failed'}</span>
                  <Explain text={CERT_CHECK[k.name]?.meaning ?? k.name} />
                </li>
              ))}
            </ul>
          )}

          <section className={s.proven} aria-label="What was proven">
            <p>{plural(r.scenarios, 'payment situation', 'payment situations')} tested · {plural(r.problem, 'problem', 'problems')} <Explain text={MEANING.problems} /></p>
            <p>Caught {ps.killed} of {ps.mutants_total - ps.equivalent_dropped} planted bugs <Explain text={MEANING.proof_strength_score} /></p>
            <p>{plural(sec.secrets_found, 'secret', 'secrets')} leaked · {plural(sec.injection_attempts_blocked, 'trick', 'tricks')} blocked <Explain text={MEANING.secrets_found} /></p>
          </section>

          {config.demoTools && !tampered && (
            <DemoOnly><Link className="gg-btn gg-btn--ghost gg-btn--sm" to={`/c/${config.standInIds.tamperedCertId}`}>Tampered copy</Link></DemoOnly>
          )}
        </div>

        <aside className={s.sealWrap} aria-live="polite">
          <div className={s.seal} data-state={!done ? 'idle' : res!.ok ? 'real' : 'bad'}>
            <svg viewBox="0 0 200 200" aria-hidden className={s.sealRing}>
              <defs><path id="sealText" d="M100 100 m -78 0 a 78 78 0 1 1 156 0 a 78 78 0 1 1 -156 0" /></defs>
              <circle cx="100" cy="100" r="92" />
              <circle cx="100" cy="100" r="64" />
              <text><textPath href="#sealText">GOLDGRAFT · TESTED AND SIGNED · PAYPAL UPGRADE · </textPath></text>
            </svg>
            <span className={s.sealCore}>
              {!done ? <SealCheckIcon size={44} weight="thin" /> : res!.ok ? <SealCheckIcon size={52} weight="fill" /> : <SealWarningIcon size={52} weight="fill" />}
            </span>
          </div>
          <p className={s.result} role={done && !res!.ok ? 'alert' : undefined} data-state={!done ? 'idle' : res!.ok ? 'real' : 'bad'}>
            {!done ? 'Press Check to verify it.' : res!.ok ? 'Real ✓' : sigFailed ? 'Changed ✗' : 'Not valid ✗'}
          </p>
        </aside>
      </div>

      <Details>
        <div className={s.detailGrid}>
          {res && <ul className={s.detailList}>{checks.map((k) => <li key={k.name}><b>{CERT_CHECK[k.name]?.name ?? k.name}:</b> {k.detail}</li>)}</ul>}
          <div>
            <p>{r.pass} same as before · {r.pass_fixed} fixed an old bug · {r.unverified} not proven yet · {r.n_a} doesn't apply <Explain text="A certificate is only issued with 0 problems." /></p>
            <p>Bugs caught {formatPct(ps.score)}</p>
            <p>Found {formatPct(sv.recall)} of the old pieces · {formatPct(sv.precision)} of flags were right · {sv.misses_learned} misses learned</p>
            <p>{sec.deps_blocked} unsafe packages blocked</p>
          </div>
          <div>
            <h3 className={s.h3}>Cost and time</h3>
            <p>{formatUsd((c.cost as { usd: number }).usd)} · {(c.cost as { tokens: number }).tokens} AI tokens</p>
            <p>{Object.entries((c.time ?? {}) as Record<string, number>).map(([k, v]) => `${k}: ${formatMinutes(v)}`).join(' · ')}</p>
          </div>
          <div>
            <h3 className={s.h3}>PayPal evidence</h3>
            {evidence.length === 0 ? <p className={s.muted}>No PayPal ids in this certificate.</p> : (
              <table className={s.table}><caption>PayPal's own ids for the test payments.</caption>
                <thead><tr><th>Scenario</th><th>Order</th><th>Capture</th><th>Debug</th></tr></thead>
                <tbody>{evidence.map((e, i) => <tr key={i}><td>{e.scenario}</td><td className="gg-mono">{e.order_id}</td><td className="gg-mono">{e.capture_id}</td><td className="gg-mono">{e.debug_id}</td></tr>)}</tbody>
              </table>
            )}
          </div>
          <div>
            <h3 className={s.h3}>Code</h3>
            <p>Old code <Val v={c.commit_old as string} /> → new code <Val v={c.commit_new as string} /> on branch <Val v={c.branch as string} /></p>
            <p><Val v={c.repo as string} /></p>
          </div>
          <div>
            <h3 className={s.h3}>Signing <Explain text="Signed in GoldGraft's GitHub workflow and logged publicly." /></h3>
            <dl className={s.kv}>
              <dt>Ledger root</dt><dd><Val v={c.ledger_root as string} /></dd>
              <dt>Workflow</dt><dd><Val v={(c.runner_identity as { workflow?: string })?.workflow} /></dd>
              <dt>Commit</dt><dd><Val v={(c.runner_identity as { sha?: string })?.sha} /></dd>
              <dt>Signature</dt><dd><Val v={c.signature as string} /></dd>
              <dt>Public log</dt><dd><Val v={c.rekor_entry as string} /></dd>
            </dl>
          </div>
        </div>
      </Details>
    </div>
  );
}
