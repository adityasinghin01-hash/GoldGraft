import { CheckIcon, HourglassMediumIcon, LinkSimpleIcon } from '@phosphor-icons/react';
import { useConnected } from '../api/queries';
import type { ConnectedCheck, ConnectedRun } from '../api/types';
import { Explain, Tag } from './ui';
import s from './ConnectedEvidence.module.css';

/** What each check kind proves, in plain words. */
const KIND: Record<string, { name: string; meaning: string }> = {
  baseline: { name: 'Old shop recordings', meaning: 'The original shop was run and every message recorded.' },
  candidate: { name: 'New code recordings', meaning: 'The AI-written code was run the same way and recorded.' },
  scenario: { name: 'Payment situations judged', meaning: 'Our judge compared old and new for each payment situation.' },
  mutation: { name: 'Planted bugs caught', meaning: 'Bugs planted in the new code were run; each must be caught.' },
  domain_rule: { name: 'Money rules guarded', meaning: 'Each critical money rule needs a planted bug that a test catches.' },
  payment: { name: "Shop's real PayPal checkout", meaning: "The shop's own checkout must run against real PayPal sandbox." },
  isolation: { name: 'Isolated run', meaning: 'The shop must run inside an isolated sandbox, not on a normal computer.' },
  security: { name: 'Security checks', meaning: 'Secret and injection checks.' },
  exit: { name: 'Clean exit', meaning: 'The shop keeps working after GoldGraft is disconnected.' },
};
const ORDER = ['baseline', 'candidate', 'scenario', 'mutation', 'domain_rule', 'payment', 'isolation', 'security', 'exit'];

/** Plain words for each hold the run reports. */
function holdText(hold: string): string {
  if (hold.startsWith('domain_rule:')) return `Money rule ${hold.split(':')[1].split(':')[0]} has no planted bug that a test catches yet`;
  if (hold.startsWith('payment:shop-checkout-paypal')) return "The shop's own checkout still uses simulated PayPal";
  if (hold.startsWith('isolation:')) return 'The shop ran on a normal computer, not an isolated sandbox';
  if (hold.startsWith('image:')) return 'No container image was built, so the exact-image review waits';
  if (hold.startsWith('promotion:')) return 'No real buyers yet, so going live stays at 0%';
  if (hold.startsWith('signer:')) return 'No signer is attached, so no certificate was signed';
  return hold;
}

/** One line for all unguarded money rules, then each other hold in plain words. */
function foldRules(holds: string[]): string[] {
  const rules = holds.filter((h) => h.startsWith('domain_rule:')).map((h) => h.split(':')[1]);
  const rest = holds.filter((h) => !h.startsWith('domain_rule:')).map(holdText);
  if (rules.length === 0) return rest;
  const head = rules.length === 1
    ? `Money rule ${rules[0]} has no planted bug that a test catches yet`
    : `${rules.length} money rules (${rules.join(', ')}) have no planted bug that a test catches yet`;
  return [head, ...rest];
}

function groups(checks: ConnectedCheck[]) {
  const by = new Map<string, ConnectedCheck[]>();
  for (const c of checks) by.set(c.kind, [...(by.get(c.kind) ?? []), c]);
  return ORDER.filter((k) => by.has(k)).map((k) => ({ kind: k, items: by.get(k)! }));
}

export function ConnectedEvidence({ graftId }: { graftId: string }) {
  const q = useConnected(graftId);
  if (q.isPending || q.isError || !q.data) return null;
  return <Panel run={q.data} />;
}

function Panel({ run }: { run: ConnectedRun }) {
  const verified = run.checks.filter((c) => c.state === 'verified').length;
  const held = run.checks.length - verified;
  const sandbox = run.provider_checks.paypal_sandbox;
  const steps = [
    { who: 'Start', what: run.gupta_control.status === 'operation_started' ? 'Work accepted and started' : run.gupta_control.status, ok: run.gupta_control.status === 'operation_started', explain: 'The control service accepted the work once, gave it a work id, and the worker re-read the shop source.' },
    { who: 'Run', what: `${run.checks.filter((c) => c.kind === 'baseline' || c.kind === 'candidate').length} recordings made`, ok: true, explain: 'The old shop and the AI-written code were both run on this computer under that work id.' },
    { who: 'Proof', what: `${verified} of ${run.checks.length} checks verified`, ok: run.proof_result.outcome === 'ready', explain: 'Every recording was checked against its sealed bytes and judged again.' },
    { who: 'Certificate', what: run.certificate.issued ? 'Signed' : 'Held, not signed', ok: run.certificate.issued, explain: 'A certificate is only signed when every critical check is verified.' },
  ];
  return (
    <section className={`gg-glass ${s.panel}`} aria-label="One connected run">
      <header className={s.head}>
        <p className={s.title}>One connected run <Explain text="One real run passed through every part: the control service, the shop run, the proof and the certificate. Each part checks the one before it." /></p>
        <Tag tone={run.proof_result.outcome === 'ready' ? 'good' : 'warn'}>{run.proof_result.outcome === 'ready' ? 'Ready' : `${held} on hold`}</Tag>
      </header>
      <p className={s.note}>A real recorded run on GoldGraft's own test computer · work {run.gupta_control.work_id.slice(0, 13)}</p>

      <ol className={s.chain}>
        {steps.map((st) => (
          <li key={st.who} className={s.step} data-ok={st.ok || undefined}>
            <span className={s.stepIcon} aria-hidden>{st.ok ? <CheckIcon size={14} weight="bold" /> : <HourglassMediumIcon size={14} />}</span>
            <span className={s.stepWho}>{st.who}</span>
            <span className={s.stepWhat}>{st.what} <Explain text={st.explain} /></span>
          </li>
        ))}
      </ol>

      <ul className={s.kinds}>
        {groups(run.checks).map(({ kind, items }) => {
          const ok = items.filter((c) => c.state === 'verified').length;
          return (
            <li key={kind} className={s.kind} data-done={ok === items.length || undefined}>
              <span className={s.kindCount}>{ok}/{items.length}</span>
              <span className={s.kindName}>{KIND[kind]?.name ?? kind} <Explain text={KIND[kind]?.meaning ?? kind} /></span>
            </li>
          );
        })}
      </ul>

      {sandbox && (
        <p className={s.sandbox} data-ok={sandbox.reverified_from_recording || undefined}>
          <LinkSimpleIcon size={15} aria-hidden /> Real PayPal sandbox: order, capture and refund {sandbox.reverified_from_recording ? 'confirmed from PayPal\'s own replies' : 'not confirmed'}
          <Explain text={`A separate real run against PayPal's sandbox (play money): ${sandbox.exchanges} messages, PayPal ids ${sandbox.ids.join(', ')}. It tested GoldGraft's payment connection, not this shop's checkout.`} />
        </p>
      )}

      <div className={s.holds}>
        <p className={s.holdsTitle}>On hold, and why <Explain text="On hold means GoldGraft will not claim this part is done until the real thing exists." /></p>
        <ul>{foldRules(run.holds).map((h) => <li key={h}>{h}</li>)}</ul>
      </div>
    </section>
  );
}
