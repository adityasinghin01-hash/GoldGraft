import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { FileCodeIcon, PlayIcon, ShieldCheckIcon, ShieldWarningIcon, StopIcon } from '@phosphor-icons/react';
import { useGauntlet } from '../api/queries';
import { Details, PageHead, ProblemBanner, SampleChip, Tag } from '../components/ui';
import { Skeleton } from '../components/Loaders';
import { formatDate } from '../lib/format';
import { isMock } from '../config';
import { reducedMotion } from '../motion/scroll';
import s from './s10.module.css';

type Attempt = { attempt_id: string; source: string; summary: string; blocked: boolean; blocked_by?: string };
type Alert = { id: string; message: string; severity: string; created_at: string; producer?: { name?: string } };

export default function S10_Security() {
  const { runId = 'run-1' } = useParams();
  const q = useGauntlet(runId);
  const [shown, setShown] = useState<number | null>(null);
  const timer = useRef(0);
  useEffect(() => { document.title = 'GoldGraft · Security'; return () => window.clearInterval(timer.current); }, []);

  const attempts = ((q.data?.attempts ?? []) as Attempt[]);
  const blocked = attempts.filter((a) => a.blocked).length;
  const replaying = shown !== null;
  const replay = () => {
    window.clearInterval(timer.current);
    if (replaying) { setShown(null); return; }
    setShown(0);
    let n = 0;
    timer.current = window.setInterval(() => {
      n += 1; setShown(n);
      if (n >= attempts.length) { window.clearInterval(timer.current); window.setTimeout(() => setShown(null), 1800); }
    }, reducedMotion() ? 50 : 1100);
  };

  return (
    <div className={`gg-center ${s.screen}`}>
      <PageHead title="Security" explain="Test shops hide orders for the AI. GoldGraft treats them as data."
        sub={q.data ? <span className={s.top}>{blocked} of {attempts.length} tricks blocked{blocked < attempts.length && <b> · {attempts.length - blocked} NOT blocked</b>}</span> : undefined}
        aside={isMock ? <SampleChip /> : undefined} />
      {q.isPending ? <Skeleton what="security run" lines={3} /> : q.isError ? <ProblemBanner error={q.error} onRetry={() => q.refetch()} /> : (
        <>
          <div className={s.bar}>
            <button className="gg-btn gg-btn--ghost gg-btn--sm" onClick={replay} aria-pressed={replaying}>
              {replaying ? <><StopIcon size={14} weight="fill" /> Stop</> : <><PlayIcon size={14} weight="fill" /> Replay</>}
            </button>
            {replaying && <Tag tone="gold">Replaying the saved run</Tag>}
          </div>
          <ol className={s.cards}>
            {attempts.map((a, i) => {
              const hidden = replaying && i >= shown!;
              const stampNow = replaying && i === shown! - 1;
              return (
                <li key={a.attempt_id} className={`gg-glass ${s.card}`} data-hidden={hidden || undefined} data-blocked={a.blocked || undefined}>
                  <span className={s.icon} aria-hidden><FileCodeIcon size={22} weight="duotone" /></span>
                  <div className={s.body}>
                    <p className={s.line1}><b>{a.source}:</b> {a.summary}</p>
                    {!hidden && (
                      <p className={s.line2} role={a.blocked ? undefined : 'alert'} data-stamp={stampNow || undefined}>
                        {a.blocked ? <><ShieldCheckIcon size={16} weight="fill" /> Blocked · {a.blocked_by}</> : <><ShieldWarningIcon size={16} weight="fill" /> NOT blocked</>}
                      </p>
                    )}
                  </div>
                  {!hidden && a.blocked && <span className={s.stamp} data-now={stampNow || undefined} aria-hidden>Blocked</span>}
                </li>
              );
            })}
          </ol>
          <Details>
            <ul className={s.alerts}>
              {((q.data.alerts ?? []) as Alert[]).map((al) => (
                <li key={al.id}><Tag tone={al.severity === 'CRITICAL' ? 'bad' : 'warn'}>{al.severity}</Tag> {al.message} · {al.producer?.name} · <time title={al.created_at}>{formatDate(al.created_at)}</time></li>
              ))}
            </ul>
          </Details>
        </>
      )}
    </div>
  );
}
