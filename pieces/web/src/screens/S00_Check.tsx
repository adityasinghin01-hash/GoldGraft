import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowRightIcon, CodeIcon, GlobeHemisphereWestIcon, UsersThreeIcon } from '@phosphor-icons/react';
import { api } from '../api/client';
import type { ProbeResult } from '../api/types';
import { FAMILY } from '../copy/words';
import { Details, NotInApiYet, PageHead, ProblemBanner, SampleChip, Tag } from '../components/ui';
import { ActionButton, SecondsWait } from '../components/Loaders';
import { isMock } from '../config';
import s from './s00.module.css';

const VALID = /^https?:\/\/\S+$/;
const TABS = [
  { id: 'code', label: 'My code', box: 'Repository link', ph: 'https://github.com/you/your-shop', Icon: CodeIcon },
  { id: 'site', label: 'My website', box: 'Website address', ph: 'https://your-shop.com', Icon: GlobeHemisphereWestIcon },
] as const;

/** S0: one paste tells anyone which old PayPal their shop has. */
export default function S00_Check() {
  const [params] = useSearchParams();
  const [tab, setTab] = useState<0 | 1>(0);
  const [url, setUrl] = useState(params.get('url') ?? '');
  const [invalid, setInvalid] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<unknown>(null);
  const [res, setRes] = useState<ProbeResult | null>(null);
  const [checked, setChecked] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const resultRef = useRef<HTMLParagraphElement>(null);
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const navigate = useNavigate();
  const auto = useRef(false);

  useEffect(() => { document.title = 'GoldGraft'; }, []);

  const run = async (value = url) => {
    const u = value.trim();
    if (!VALID.test(u)) { setInvalid(true); return; }
    setInvalid(false); setErr(null); setBusy(true); setRes(null);
    try {
      const r = await api.probe(u);
      setRes(r); setChecked(u);
      setTimeout(() => resultRef.current?.focus(), 50);
    } catch (e) { setErr(e); } finally { setBusy(false); }
  };

  // arriving from the landing page with ?url=… runs the check once
  useEffect(() => {
    const u = params.get('url');
    if (u && !auto.current) { auto.current = true; run(u); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onTabKey = (e: React.KeyboardEvent) => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    const next = (tab === 0 ? 1 : 0) as 0 | 1;
    setTab(next); tabRefs.current[next]?.focus();
  };

  const start = () => {
    const host = (() => { try { return new URL(checked).host; } catch { return ''; } })();
    const repo = ['github.com', 'gitlab.com', 'bitbucket.org'].some((h) => host === h || host.endsWith(`.${h}`));
    navigate(`/connect?${repo ? 'repo' : 'site'}=${encodeURIComponent(checked)}`);
  };

  const fams = (res?.families_found ?? []) as string[];
  const official = (res as { official_modern_module_available?: boolean | null } | null)?.official_modern_module_available;
  const notes = ((res?.deadline_notes ?? []) as string[]);
  const t = TABS[tab];

  return (
    <div className={s.screen}>
      <PageHead title={<>Don't cut the tree. <em className={s.em}>Graft.</em></>} sub="Upgrades old PayPal checkout, proves every payment, switches back if wrong." />

      <section className={`gg-glass ${s.card}`}>
        <div className={s.tabsRow}>
          <div role="tablist" aria-label="What you have" className={s.tabs} onKeyDown={onTabKey}>
            {TABS.map((x, i) => (
              <button key={x.id} ref={(el) => { tabRefs.current[i] = el; }} role="tab" aria-selected={tab === i} tabIndex={tab === i ? 0 : -1}
                className={s.tab} onClick={() => { setTab(i as 0 | 1); inputRef.current?.focus(); }}>
                <x.Icon size={16} weight={tab === i ? 'fill' : 'regular'} /> {x.label}
              </button>
            ))}
          </div>
          <Link to="/orchard" className={s.team}><UsersThreeIcon size={16} /> PayPal team</Link>
        </div>

        <form className={s.form} role="tabpanel" onSubmit={(e) => { e.preventDefault(); run(); }} noValidate>
          <label htmlFor="probe-url" className={s.label}>{t.box}</label>
          <div className={s.field} data-error={invalid || undefined}>
            <input ref={inputRef} id="probe-url" type="url" inputMode="url" spellCheck={false} autoComplete="url" placeholder={t.ph} value={url}
              onChange={(e) => { setUrl(e.target.value); setInvalid(false); }} aria-invalid={invalid || undefined} aria-describedby="probe-note" />
            <ActionButton type="submit" busy={busy} busyText="Checking…">Check <ArrowRightIcon size={15} weight="bold" /></ActionButton>
          </div>
          <p id="probe-note" className={s.note} role={invalid ? 'alert' : undefined} data-error={invalid || undefined}>
            {invalid ? 'Enter a full address starting with https://' : 'Quick check, no keys needed.'}
          </p>
        </form>

        {busy && <SecondsWait text="Checking your shop…" />}
        {err ? <ProblemBanner error={err} onRetry={() => run()} /> : null}
      </section>

      {res && (
        <section className={s.result} aria-live="polite">
          <div className={s.resultHead}>
            <p ref={resultRef} tabIndex={-1} className={s.top}>{fams.length === 0 ? 'No old PayPal found' : fams.length === 1 ? '1 kind of old PayPal found' : `${fams.length} kinds of old PayPal found`}</p>
            {isMock && <SampleChip />}
          </div>
          <ul className={s.fams}>
            {fams.map((f, i) => <li key={f} style={{ ['--i' as string]: i }}><Tag tone="gold" title={FAMILY[f]?.full}>{FAMILY[f]?.short ?? f}</Tag></li>)}
          </ul>
          <p className={s.path}>
            {official === true ? 'An official module exists. GoldGraft installs and proves it.' : official === false ? 'No official module. GoldGraft rewrites the PayPal code.' : 'Upgrade path not known yet.'}
          </p>
          <ul className={s.deadlines}>
            {notes.length ? notes.map((n) => <li key={n}>{n}</li>) : <li>No published deadline for these pieces.</li>}
          </ul>
          <div className={s.next}>
            {tab === 0 ? <button className="gg-btn gg-btn--gold" onClick={start}>Start upgrade <ArrowRightIcon size={16} weight="bold" /></button> : <NotInApiYet what="No-code upgrade" gap="G1" />}
          </div>
          <Details>
            <dl className={s.kv}>
              <dt>Found in</dt><dd>{((res.files_or_pages ?? []) as string[]).map((f) => <code key={f} className="gg-mono">{f}</code>)}</dd>
              <dt>Next step</dt><dd>{(res as { next_step?: string }).next_step}</dd>
            </dl>
          </Details>
        </section>
      )}
    </div>
  );
}
