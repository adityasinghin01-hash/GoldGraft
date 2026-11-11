import { CheckIcon, ArrowRightIcon, SealCheckIcon, WarningIcon } from '@phosphor-icons/react';
import s from './panels.module.css';

// Small working versions of the real app screens, one per feature.
// Every number here is the stand-in sample from the frontend pack and is labelled "Sample".

function Sample() { return <span className={s.sample}>Sample</span>; }

function Find() {
  const rows = [
    ['Old Express Checkout (NVP)', 'includes/modules/payment/paypalwpp.php'],
    ['Old payment notifications', 'ipn_main_handler.php'],
    ['Old Buy Now button', 'templates/product_info.tpl'],
  ];
  return (
    <div className={s.panel}>
      <header className={s.head}><b>3 old PayPal pieces found</b><Sample /></header>
      <ul className={s.rows}>
        {rows.map(([a, b]) => (
          <li key={a} className={s.findRow}><span className={s.tag}>{a}</span><code>{b}</code></li>
        ))}
      </ul>
    </div>
  );
}

function Write() {
  return (
    <div className={s.panel}>
      <header className={s.head}><b>Old call → new call</b><Sample /></header>
      <pre className={s.code}>
        <span className={s.del}>- $nvp = hash_call('SetExpressCheckout', $req);</span>{'\n'}
        <span className={s.del}>- header('Location: ' . PAYPAL_URL . $token);</span>{'\n'}
        <span className={s.add}>+ const order = await paypal.orders.create({'{'}</span>{'\n'}
        <span className={s.add}>+   intent: 'CAPTURE',</span>{'\n'}
        <span className={s.add}>+   purchase_units: [{'{'} amount {'}'}],</span>{'\n'}
        <span className={s.add}>+ {'}'});</span>
      </pre>
      <p className={s.foot}>Written by Grafter, the only agent allowed to write code.</p>
    </div>
  );
}

function Prove() {
  const rows = ['Order created', 'Buyer approved', 'Money captured', 'Shop marked paid'];
  return (
    <div className={s.panel}>
      <header className={s.head}><b>Normal payment · Same as before</b><Sample /></header>
      <div className={s.lanes}>
        <span className={s.laneHead}>Old shop</span><span className={s.laneHead}>New shop</span><span className={s.laneHead}>PayPal's record</span>
        {rows.map((r) => (
          <div key={r} className={s.laneRow}>
            <span>{r}</span><span>{r}</span><span className={s.ok}><CheckIcon size={12} weight="bold" /> matches</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Bugs() {
  return (
    <div className={s.panel}>
      <header className={s.head}><b>Caught 12 of 12 planted bugs · needs 95%</b><Sample /></header>
      <div className={s.tiles}>
        {Array.from({ length: 12 }, (_, i) => (
          <span key={i} className={s.tile}><CheckIcon size={11} weight="bold" /> M{i + 1}</span>
        ))}
      </div>
      <div className={s.bar}><span style={{ width: '100%' }} /><i style={{ left: '95%' }} /></div>
    </div>
  );
}

function OldBug() {
  return (
    <div className={s.panel}>
      <header className={s.head}><b>Payment held as pending</b><Sample /></header>
      <p className={s.callout}><WarningIcon size={15} weight="fill" /> Bug found in your current shop. New checkout fixes it.</p>
      <div className={s.compare}>
        <div><span className={s.small}>Old shop</span><b className={s.badText}>Marked it paid</b></div>
        <ArrowRightIcon size={14} />
        <div><span className={s.small}>New shop</span><b className={s.goodText}>Marked it pending</b></div>
      </div>
      <p className={s.foot}>Breaks R07: a pending payment is not marked paid.</p>
    </div>
  );
}

function GoLive() {
  const steps = ['0%', '1%', '10%', '50%', '100%'];
  return (
    <div className={s.panel}>
      <header className={s.head}><b>10% of buyers on the new checkout</b><Sample /></header>
      <ol className={s.stepper}>
        {steps.map((t, i) => <li key={t} data-state={i < 2 ? 'done' : i === 2 ? 'now' : undefined}>{t}</li>)}
      </ol>
      <div className={s.paid}>
        <span>Old: 100 of 100 paid</span><span>New: 30 of 30 paid</span>
      </div>
      <p className={s.foot}>PayPal sandbox · simulated buyers</p>
    </div>
  );
}

function Cert() {
  const checks = ['Signature', 'Public log entry', 'Same build', 'Proof numbers'];
  return (
    <div className={s.panel}>
      <header className={s.head}><b>Certificate · legacy-php-shop</b><Sample /></header>
      <ul className={s.ticks}>
        {checks.map((c) => <li key={c}><CheckIcon size={12} weight="bold" /> {c}</li>)}
      </ul>
      <p className={s.real}><SealCheckIcon size={18} weight="fill" /> Real</p>
    </div>
  );
}

export const PANELS: Record<string, () => JSX.Element> = { find: Find, write: Write, prove: Prove, bugs: Bugs, oldbug: OldBug, golive: GoLive, cert: Cert };
