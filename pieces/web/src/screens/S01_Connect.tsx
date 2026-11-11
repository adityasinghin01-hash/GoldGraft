import { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckIcon, LockKeyIcon, XIcon } from '@phosphor-icons/react';
import { api } from '../api/client';
import type { Connection, Shop } from '../api/types';
import { H } from '../copy/words';
import { Details, Explain, PageHead, ProblemBanner } from '../components/ui';
import { ActionButton, SecondsWait } from '../components/Loaders';
import { addUpgrade, newIdempotencyKey } from '../lib/store';
import s from './s01.module.css';

const VALID = /^https?:\/\/\S+$/;
type Checks = { rest_ok?: boolean; nvp_ok?: boolean; webhook_ok?: boolean; version_match?: boolean };
const TICKS: Array<{ k: keyof Checks; ok: string; bad: string; note?: string }> = [
  { k: 'rest_ok', ok: 'PayPal accepted your app keys.', bad: 'PayPal refused these keys. Use sandbox keys from one app.' },
  { k: 'nvp_ok', ok: 'Old NVP keys work.', bad: 'No working NVP keys. Fine unless your shop uses old Express Checkout.', note: "Without them, the old checkout's recording is marked not proven." },
  { k: 'webhook_ok', ok: 'Webhook is set up.', bad: 'No webhook yet. You can add it later.' },
  { k: 'version_match', ok: "Keys match your shop's PayPal version.", bad: "Keys don't match your shop's PayPal version. Add the matching keys." },
];

/** Step 2 keeps the keys inside this component only and clears them right after sending. */
function KeysStep({ shopId, onDone }: { shopId: string; onDone: (c: Connection) => void }) {
  const [f, setF] = useState({ paypal_client_id: '', paypal_client_secret: '', webhook_id: '', nvp_user: '', nvp_password: '', nvp_signature: '' });
  const [nvp, setNvp] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<unknown>(null);
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement>) => setF((p) => ({ ...p, [k]: e.target.value }));
  const empty = { paypal_client_id: '', paypal_client_secret: '', webhook_id: '', nvp_user: '', nvp_password: '', nvp_signature: '' };

  const check = async (e: React.FormEvent) => {
    e.preventDefault();
    const body = Object.fromEntries(Object.entries(f).filter(([, v]) => v.trim())) as Record<string, string>;
    setF(empty); // keys never stay on screen after sending
    setBusy(true); setErr(null);
    try { onDone(await api.connect(shopId, body, newIdempotencyKey())); } catch (x) { setErr(x); } finally { setBusy(false); }
  };

  return (
    <form className={s.keys} onSubmit={check} autoComplete="off">
      <div className={s.honestRow}>
        <p className={s.honest}><LockKeyIcon size={15} weight="duotone" /> {H.sandboxKeys}</p>
        <a className="gg-link" href="https://developer.paypal.com/dashboard/applications/sandbox" target="_blank" rel="noopener noreferrer">Get keys ↗</a>
        <Explain text="Keys go straight to a vault. Our AI never sees them." />
      </div>
      <div className={s.fields}>
        <label>Client ID<input required value={f.paypal_client_id} onChange={set('paypal_client_id')} spellCheck={false} /></label>
        <label>Client secret<input required type="password" value={f.paypal_client_secret} onChange={set('paypal_client_secret')} /></label>
        <label>Webhook ID (optional)<input value={f.webhook_id} onChange={set('webhook_id')} spellCheck={false} /></label>
      </div>
      <button type="button" className={s.nvpBtn} aria-expanded={nvp} onClick={() => setNvp((v) => !v)}>NVP keys</button>
      <Explain text="Only if your shop uses old Express Checkout." />
      {nvp && (
        <div className={s.fields}>
          <label>API username<input value={f.nvp_user} onChange={set('nvp_user')} spellCheck={false} /></label>
          <label>API password<input type="password" value={f.nvp_password} onChange={set('nvp_password')} /></label>
          <label>API signature<input type="password" value={f.nvp_signature} onChange={set('nvp_signature')} /></label>
        </div>
      )}
      <div className={s.actions}><ActionButton type="submit" busy={busy} busyText="Checking…" disabled={!f.paypal_client_id || !f.paypal_client_secret}>Check</ActionButton></div>
      {busy && <SecondsWait text="Checking your keys…" />}
      {err ? <ProblemBanner error={err} /> : null}
    </form>
  );
}

export default function S01_Connect() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [repo, setRepo] = useState(params.get('repo') ?? '');
  const [site, setSite] = useState(params.get('site') ?? '');
  const [shop, setShop] = useState<Shop | null>(null);
  const [conn, setConn] = useState<Connection | null>(null);
  const [busy, setBusy] = useState<'next' | 'start' | null>(null);
  const [err, setErr] = useState<unknown>(null);
  const [rule, setRule] = useState('');
  const startKey = useRef('');

  useEffect(() => { document.title = 'GoldGraft · Connect your shop'; }, []);

  const step = !shop ? 1 : !conn || !(conn.checks as Checks)?.rest_ok || !(conn.checks as Checks)?.version_match ? 2 : 3;
  const checks = (conn?.checks ?? {}) as Checks;
  const ready = !!checks.rest_ok && !!checks.version_match;

  const next = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repo.trim() && !site.trim()) { setRule('Add a repository link or a website address.'); return; }
    if ((repo && !VALID.test(repo.trim())) || (site && !VALID.test(site.trim()))) { setRule('Enter a full address starting with https://'); return; }
    setRule(''); setBusy('next'); setErr(null);
    try {
      const body = { ...(name.trim() ? { name: name.trim().slice(0, 80) } : {}), ...(repo.trim() ? { repo: repo.trim() } : {}), ...(site.trim() ? { site: site.trim() } : {}) };
      setShop(await api.createShop(body, newIdempotencyKey()));
    } catch (x) { setErr(x); } finally { setBusy(null); }
  };

  const start = async () => {
    if (!shop) return;
    if (!startKey.current) startKey.current = newIdempotencyKey();
    setBusy('start'); setErr(null);
    try {
      const g = await api.startGraft(shop.shop_id, startKey.current);
      addUpgrade({ graft_id: g.graft_id, shop_id: shop.shop_id, name: (shop as { name?: string | null }).name ?? undefined, started_at: new Date().toISOString() });
      navigate(`/g/${g.graft_id}`);
    } catch (x) { setErr(x); } finally { setBusy(null); }
  };

  const reset = () => { setShop(null); setConn(null); setName(''); setRepo(''); setSite(''); setErr(null); startKey.current = ''; };

  return (
    <div className={`gg-center ${s.screen}`}>
      <PageHead title={<>Connect your shop <span className={s.count}>· {step} of 3</span></>} />
      <ol className={s.steps}>
        <li className={`gg-glass ${s.step}`} data-state={step > 1 ? 'done' : 'now'}>
          <h2 className={s.stepTitle}><span className={s.n}>{step > 1 ? <CheckIcon size={13} weight="bold" /> : 1}</span> Your shop</h2>
          {shop ? (
            <p className={s.summary}>{(shop as { name?: string }).name || 'Unnamed shop'} · {shop.repo ?? shop.site}</p>
          ) : (
            <form className={s.fields} onSubmit={next}>
              <label>Shop name (optional)<input value={name} maxLength={80} onChange={(e) => setName(e.target.value)} /></label>
              <label><span className={s.lab}>Repository link <Explain text="Private repository? GitHub App access comes later." /></span><input value={repo} onChange={(e) => setRepo(e.target.value)} placeholder="https://github.com/you/your-shop" spellCheck={false} /></label>
              <label>Website address<input value={site} onChange={(e) => setSite(e.target.value)} placeholder="https://your-shop.com" spellCheck={false} /></label>
              {rule && <p className={s.rule} role="alert">{rule}</p>}
              <div className={s.actions}><ActionButton type="submit" busy={busy === 'next'} busyText="Saving…">Next</ActionButton></div>
            </form>
          )}
        </li>

        <li className={`gg-glass ${s.step}`} data-state={step > 2 ? 'done' : step === 2 ? 'now' : 'todo'}>
          <h2 className={s.stepTitle}><span className={s.n}>{step > 2 ? <CheckIcon size={13} weight="bold" /> : 2}</span> PayPal sandbox keys</h2>
          {shop && step >= 2 && <KeysStep key={conn ? 'again' : 'first'} shopId={shop.shop_id} onDone={setConn} />}
          {conn && (
            <ul className={s.ticks}>
              {TICKS.map((t, i) => {
                const ok = !!checks[t.k];
                return (
                  <li key={t.k} data-ok={ok || undefined} style={{ ['--i' as string]: i }}>
                    <span className={s.tickIcon}>{ok ? <CheckIcon size={12} weight="bold" /> : <XIcon size={12} weight="bold" />}</span>
                    {ok ? t.ok : t.bad}{!ok && t.note && <Explain text={t.note} />}
                  </li>
                );
              })}
            </ul>
          )}
        </li>

        <li className={`gg-glass ${s.step}`} data-state={step === 3 ? 'now' : 'todo'}>
          <h2 className={s.stepTitle}><span className={s.n}>3</span> Start</h2>
          {shop && <p className={s.summary}>Ready: {(shop as { name?: string }).name || shop.shop_id}</p>}
          <div className={s.startRow}>
            <ActionButton busy={busy === 'start'} busyText="Starting…" disabled={!ready} onClick={start}>Start</ActionButton>
            <p className={s.honest}>{H.noLiveChange}</p>
          </div>
          {!ready && shop && conn && <p className={s.rule}>Fix the red checks first.</p>}
        </li>
      </ol>
      {err ? <ProblemBanner error={err} /> : null}
      <button className={`gg-link ${s.over}`} onClick={reset}>Start over</button>
      <Details>
        <dl className={s.kv}>
          {shop && <><dt>Shop id</dt><dd><code className="gg-mono">{shop.shop_id}</code></dd></>}
          {conn && <><dt>Stored in the vault <Explain text="Only the address of your keys, not the keys." /></dt><dd><code className="gg-mono">{(conn as { secrets_ref?: string }).secrets_ref}</code></dd></>}
        </dl>
      </Details>
    </div>
  );
}
