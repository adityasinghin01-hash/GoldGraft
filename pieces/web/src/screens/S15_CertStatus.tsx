import { Fragment, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckIcon, SealWarningIcon, XIcon } from '@phosphor-icons/react';
import { api } from '../api/client';
import { useConnected } from '../api/queries';
import { useGraftCtx } from '../shell/GraftLayout';
import { foldRules } from '../components/ConnectedEvidence';
import { Explain, PageHead, ProblemBanner } from '../components/ui';
import { ActionButton, Skeleton } from '../components/Loaders';
import { config } from '../config';
import s from './s15.module.css';

type Step = { name: string; meaning: string; ok: boolean; detail: string };

const hex = (buf: ArrayBuffer) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');

/** Runs the four checks in this browser: our file, the public log, and the signer. */
async function checkInBrowser(graftId: string, logIndex: number, expectedSha: string, identity: string): Promise<Step[]> {
  const steps: Step[] = [];
  const bytes = await api.connectedProof(graftId);
  const sha = hex(await crypto.subtle.digest('SHA-256', bytes));
  steps.push({ name: 'This run\'s proof file', meaning: 'Downloaded the exact proof result and hashed it here, in your browser.', ok: sha === expectedSha, detail: `SHA-256 ${sha.slice(0, 16)}…` });
  const res = await fetch(`https://rekor.sigstore.dev/api/v1/log/entries?logIndex=${logIndex}`);
  if (!res.ok) throw new Error(`Public log answered HTTP ${res.status}`);
  const entry = Object.values((await res.json()) as Record<string, { body: string; integratedTime: number }>)[0];
  const body = JSON.parse(atob(entry.body)) as { spec: { data: { hash: { value: string } }; signature: { publicKey: { content: string } } } };
  const logged = body.spec.data.hash.value;
  steps.push({ name: 'Public log entry', meaning: 'Fetched the entry from Sigstore\'s public log (Rekor), which anyone can read.', ok: true, detail: `#${logIndex}, logged ${new Date(entry.integratedTime * 1000).toUTCString()}` });
  steps.push({ name: 'Same file', meaning: 'The hash the public log recorded equals the hash of the file you just downloaded.', ok: logged === sha, detail: logged === sha ? 'Hashes match' : `Log has ${logged.slice(0, 16)}…` });
  const certificate = atob(atob(body.spec.signature.publicKey.content).replace(/-----[^-]+-----|\s/g, ''));
  steps.push({ name: 'Signed by our workflow', meaning: 'The signing certificate in the log names GoldGraft\'s GitHub signing workflow.', ok: certificate.includes(identity), detail: identity.replace('https://github.com/', '') });
  return steps;
}

export default function S15_CertStatus() {
  const { graftId } = useGraftCtx();
  const q = useConnected(graftId);
  const [busy, setBusy] = useState(false);
  const [steps, setSteps] = useState<Step[] | null>(null);
  const [shown, setShown] = useState(0);
  const [err, setErr] = useState<unknown>(null);

  useEffect(() => { document.title = 'GoldGraft · Certificate'; }, []);

  if (q.isPending) return <div className={s.screen}><PageHead title="Certificate" /><Skeleton what="certificate" lines={4} /></div>;
  if (q.isError || !q.data) return <div className={s.screen}><PageHead title="Certificate" /><ProblemBanner error={q.error} onRetry={() => q.refetch()} /></div>;

  const run = q.data;
  const verified = run.checks.filter((c) => c.state === 'verified').length;
  const criticalOpen = run.checks.filter((c) => c.critical && c.state !== 'verified').length;
  const sig = run.signing;
  const sandbox = run.provider_checks.paypal_sandbox;
  const checkout = run.provider_checks.shop_checkout_paypal_sandbox;

  const check = async () => {
    if (!sig) return;
    setBusy(true); setErr(null); setSteps(null); setShown(0);
    try {
      const r = await checkInBrowser(graftId, sig.rekor_log_index, sig.payload_sha256, sig.signer_identity);
      setSteps(r);
      r.forEach((_, i) => window.setTimeout(() => setShown(i + 1), (i + 1) * 380));
    } catch (e) { setErr(e); } finally { setBusy(false); }
  };
  const allOk = steps?.every((x) => x.ok) && shown >= (steps?.length ?? 0);

  return (
    <div className={s.screen}>
      <PageHead title="Certificate" sub={run.certificate.issued ? 'Issued' : `Not issued yet · ${criticalOpen} critical checks still open`} />

      <section className={`gg-glass ${s.status}`}>
        <span className={s.statusIcon} aria-hidden><SealWarningIcon size={40} weight="duotone" /></span>
        <div>
          <p className={s.statusTitle}>Held: the evidence is not complete <Explain text="GoldGraft issues a certificate only when every critical check is verified. It never fills a gap with a guess." /></p>
          <p className={s.statusSub}>{verified} of {run.checks.length} checks verified on the AI-written code. These still need real evidence:</p>
          <ul className={s.needs}>{foldRules(run.holds).map((h) => <li key={h}>{h}</li>)}</ul>
        </div>
      </section>

      {sig && (
        <section className={`gg-glass ${s.signed}`}>
          <div className={s.signedHead}>
            <div>
              <p className={s.statusTitle}>The proof result is signed and public <Explain text={sig.scope} /></p>
              <p className={s.statusSub}>Signed by GoldGraft's GitHub workflow with Sigstore, and recorded in the public transparency log.</p>
            </div>
            <ActionButton busy={busy} busyText="Checking…" onClick={check}>Check it now</ActionButton>
          </div>
          {err ? <ProblemBanner error={err} onRetry={check} /> : null}
          {steps && (
            <ul className={s.ticks} aria-live="polite">
              {steps.map((x, i) => (
                <li key={x.name} data-ok={x.ok || undefined} data-on={i < shown || undefined}>
                  <span className={s.tickIcon} aria-hidden>{x.ok ? <CheckIcon size={13} weight="bold" /> : <XIcon size={13} weight="bold" />}</span>
                  <span className={s.tickName}>{x.name} <Explain text={x.meaning} /></span>
                  <span className={s.tickDetail}>{x.detail}</span>
                </li>
              ))}
            </ul>
          )}
          {allOk && <p className={s.verdict}>Real ✓ The public log holds exactly this run's proof result, signed by our workflow.</p>}
          <dl className={s.kv}>
            <dt>Public log</dt><dd><a className="gg-link" href={sig.rekor_search} target="_blank" rel="noreferrer">Rekor #{sig.rekor_log_index}</a></dd>
            <dt>File SHA-256</dt><dd className="gg-mono">{sig.payload_sha256}</dd>
            <dt>Signer</dt><dd className="gg-mono">{sig.signer_identity.replace('https://github.com/', '')}</dd>
          </dl>
        </section>
      )}

      {sandbox && (
        <section className={`gg-glass ${s.signed}`}>
          <p className={s.statusTitle}>Real PayPal sandbox payment <Explain text={sandbox.scope} /></p>
          <p className={s.statusSub}>Order, capture and refund made through GoldGraft's payment connection and each confirmed again by PayPal. Play money.</p>
          <dl className={s.kv}>
            {sandbox.ids.map((id) => <Fragment key={id}><dt>PayPal id</dt><dd className="gg-mono">{id}</dd></Fragment>)}
          </dl>
        </section>
      )}

      {checkout && checkout.state !== 'missing' && (
        <section className={`gg-glass ${s.signed}`}>
          <p className={s.statusTitle}>The shop's own PayPal sandbox checkout</p>
          <p className={s.statusSub}>{checkout.state === 'verified' ? 'Independently verified' : 'Verification held'} · {(checkout.scenarios ?? []).join(', ') || 'selected recordings'} · play money.</p>
          <p className={s.statusSub}>This covers the listed checkout scenarios only. Isolation, merchant delivery and the other open checks remain separate.</p>
        </section>
      )}

      {config.demoTools && graftId === config.standInIds.graftId && (
        <p className={s.muted}>The older sample certificate from recorded fixtures is still at <Link className="gg-link" to={`/c/${config.standInIds.certId}`}>/c/{config.standInIds.certId}</Link>.</p>
      )}
    </div>
  );
}
