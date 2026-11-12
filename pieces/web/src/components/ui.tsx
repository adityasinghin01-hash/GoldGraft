import { createContext, useContext, useEffect, useId, useRef, useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { ArrowClockwiseIcon, CaretRightIcon, CheckIcon, CopyIcon, FlaskIcon, InfoIcon, ShieldCheckIcon, XIcon } from '@phosphor-icons/react';
import { H } from '../copy/words';
import type { Tone } from '../copy/words';
import { ApiError, type FeedStatus } from '../api/client';
import { formatTime, shortHash } from '../lib/format';
import { isMock } from '../config';
import s from './ui.module.css';

/* C1 ExplainNote — ⓘ with one line behind it (hover, focus or tap). */
export function Explain({ text, label = 'What this means' }: { text: ReactNode; label?: string }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  return (
    <span className={s.explain} onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <button type="button" className={s.explainBtn} aria-label={label} aria-describedby={open ? id : undefined}
        onClick={() => setOpen((v) => !v)} onFocus={() => setOpen(true)} onBlur={() => setOpen(false)}>
        <InfoIcon size={14} weight="regular" />
      </button>
      {open && <span role="tooltip" id={id} className={s.tip}>{text}</span>}
    </span>
  );
}

/* Tag — grade, stage, lane, family: text + tone, never colour alone. */
export function Tag({ children, tone = 'neutral', title, icon }: { children: ReactNode; tone?: Tone; title?: string; icon?: ReactNode }) {
  return <span className={s.tag} data-tone={tone} title={title}>{icon}{children}</span>;
}

/* C2 Stat — a number with a 1–3 word label and its meaning behind ⓘ. */
export function Stat({ label, value, note, to, tone, sub }: { label: string; value: ReactNode; note?: string; to?: string; tone?: Tone; sub?: ReactNode }) {
  const body = (
    <>
      <span className={s.statLabel}>{label}{note && <Explain text={note} />}</span>
      <span className={`gg-num ${s.statValue}`} data-tone={tone} data-words={(typeof value === 'string' && /[a-z]{3,} [a-z]{3,}/.test(value)) || undefined}>{value}</span>
      {sub && <span className={s.statSub}>{sub}</span>}
    </>
  );
  return to ? <Link to={to} className={`${s.stat} ${s.statLink}`}>{body}</Link> : <div className={s.stat}>{body}</div>;
}

/* C15 SampleDataChip */
export function SampleChip() {
  return <span className={s.sample} title={H.sampleTitle}><FlaskIcon size={12} weight="duotone" /> {H.sample}</span>;
}

/* C16 MockModeBanner */
export function MockBanner() {
  if (!isMock) return null;
  return <div className={s.mockBanner} role="note"><FlaskIcon size={14} weight="duotone" /> {H.mock}</div>;
}

/* C17 SandboxChip */
export function SandboxChip({ text = H.sandboxTop }: { text?: string }) {
  return <span className={s.sandbox}><ShieldCheckIcon size={13} weight="duotone" /> {text}</span>;
}

/* C12 ProblemBanner — the pack's error words, with Retry where it helps. */
export function ProblemBanner({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const e = error instanceof ApiError ? error : new ApiError('unexpected', 0, 'Something went wrong.', String((error as Error)?.message ?? ''));
  // The agents service answers "Not available yet" for steps that have not run: a note, not an error.
  const notYet = e.kind === 'problem' && e.title === 'Not available yet';
  const canRetry = onRetry && !notYet && (e.kind !== 'problem' || e.status >= 500);
  return (
    <div className={s.problem} role={notYet ? 'status' : 'alert'} data-tone={notYet ? 'note' : undefined}>
      {notYet ? <InfoIcon size={16} weight="bold" className={s.problemIcon} /> : <XIcon size={16} weight="bold" className={s.problemIcon} />}
      <div>
        <p className={s.problemTitle}>{e.title}</p>
        {e.detail && <p className={s.problemDetail}>{e.detail}</p>}
        {e.status > 0 && !notYet && <p className={s.problemStatus}>Error {e.status}</p>}
      </div>
      <div className={s.problemActions}>
        {canRetry && <button className="gg-btn gg-btn--ghost gg-btn--sm" onClick={onRetry}><ArrowClockwiseIcon size={14} /> Retry</button>}
        {e.status === 404 && !notYet && <Link className="gg-btn gg-btn--ghost gg-btn--sm" to="/check">Start</Link>}
      </div>
    </div>
  );
}

/* C14 EmptyState */
export function Empty({ title, text, action }: { title: string; text?: string; action?: ReactNode }) {
  return (
    <div className={s.empty}>
      <svg width="54" height="54" viewBox="0 0 64 64" fill="none" aria-hidden className={s.emptyArt}>
        <circle cx="32" cy="32" r="29" stroke="currentColor" strokeOpacity=".35" />
        <path d="M22 50 C 24 43, 27 38, 31 34" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
        <path d="M31 34 L 37 29" stroke="currentColor" strokeDasharray="2 3" strokeLinecap="round" />
      </svg>
      <p className={s.emptyTitle}>{title}</p>
      {text && <p className={s.emptyText}>{text}</p>}
      {action}
    </div>
  );
}

/* C24 NotInApiYet — an honest "not wired yet" note. */
export function NotInApiYet({ what, gap }: { what: string; gap: string }) {
  return <span className={s.notYet}>{what}: not in the API yet ({gap})</span>;
}

/* C21 HashText — 8 characters, full value on hover + Copy. */
export function HashText({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try { await navigator.clipboard.writeText(value); setCopied(true); setTimeout(() => setCopied(false), 1600); } catch { /* clipboard blocked */ }
  };
  return (
    <span className={s.hash}>
      <code title={value}>{shortHash(value)}</code>
      <button type="button" onClick={copy} className={s.hashBtn} aria-label="Copy the full value">
        {copied ? <><CheckIcon size={12} /> Copied</> : <><CopyIcon size={12} /> Copy</>}
      </button>
    </span>
  );
}

/* C9 LiveStatus (W5) */
export function LiveStatus({ status, last, word = 'step', onReconnect }: { status: FeedStatus; last?: string | null; word?: 'step' | 'update'; onReconnect?: () => void }) {
  const text = status === 'connecting' ? 'Connecting…'
    : status === 'reconnecting' ? 'Reconnecting…'
    : status === 'live' ? `Live${last ? ` · last ${word} ${formatTime(last)}` : ''}`
    : `Feed ended${last ? ` · last ${word} ${formatTime(last)}` : ''}`;
  return (
    <span className={s.live} data-status={status} role="status" aria-live="polite">
      <span className={s.liveDot} aria-hidden />
      {text}
      {status === 'ended' && onReconnect && <button className={s.liveBtn} onClick={onReconnect}>Reconnect</button>}
    </span>
  );
}

/* C26 Details — open state shared across the graft tabs during one visit. */
const DetailsCtx = createContext<{ open: boolean; set: (v: boolean) => void } | null>(null);
export function DetailsProvider({ children }: { children: ReactNode }) {
  const [open, set] = useState(false);
  return <DetailsCtx.Provider value={{ open, set }}>{children}</DetailsCtx.Provider>;
}
export function Details({ children, label = 'Details' }: { children: ReactNode; label?: string }) {
  const shared = useContext(DetailsCtx);
  const [own, setOwn] = useState(false);
  const open = shared ? shared.open : own;
  const set = shared ? shared.set : setOwn;
  const id = useId();
  return (
    <section className={s.details} data-open={open || undefined}>
      <button className={s.detailsBtn} aria-expanded={open} aria-controls={id} onClick={() => set(!open)}>
        <CaretRightIcon size={14} weight="bold" className={s.detailsCaret} aria-hidden />
        {open ? 'Hide details' : `Show ${label.toLowerCase()}`}
      </button>
      <div id={id} className={s.detailsBody} hidden={!open}>{children}</div>
    </section>
  );
}

/* C27 Popup — max 2 lines, max 2 buttons, a real dialog. */
export function Popup({ open, lines, primary, secondary, onClose, tone, badge }: {
  open: boolean; lines: string[]; primary: ReactNode; secondary?: ReactNode; onClose: () => void; tone?: Tone; badge?: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);
  return (
    <dialog ref={ref} className={s.popup} data-tone={tone} onClose={onClose} onCancel={onClose} aria-label={lines[0]}>
      <div className={s.popupBody}>
        {lines.slice(0, 2).map((l, i) => <p key={i} className={i === 0 ? s.popupLead : s.popupLine}>{l}</p>)}
      </div>
      <div className={s.popupActions}>{badge && <span className={s.popupBadge}>{badge}</span>}{secondary}{primary}</div>
    </dialog>
  );
}

/* C23 DemoOnly frame */
export function DemoOnly({ children, label }: { children: ReactNode; label?: string }) {
  return (
    <div className={s.demo}>
      <span className={s.demoTag}>{H.demoOnly}{label ? ` · ${label}` : ''}</span>
      {children}
    </div>
  );
}

/* Simple page header used by the app screens */
export function PageHead({ title, sub, aside, explain }: { title: ReactNode; sub?: ReactNode; aside?: ReactNode; explain?: string }) {
  return (
    <header className={s.pageHead}>
      <div className={s.pageHeadText}>
        <h1 className={s.pageTitle} tabIndex={-1} data-page-title>{title}{explain && <Explain text={explain} />}</h1>
        {sub && <div className={s.pageSub}>{sub}</div>}
      </div>
      {aside && <div className={s.pageAside}>{aside}</div>}
    </header>
  );
}

export function Panel({ children, className = '', as: As = 'section' }: { children: ReactNode; className?: string; as?: 'section' | 'div' | 'article' }) {
  return <As className={`gg-glass ${s.panel} ${className}`}>{children}</As>;
}
