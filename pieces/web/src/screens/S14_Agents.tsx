import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRightIcon, CheckIcon, PauseIcon } from '@phosphor-icons/react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import type { AgentStep } from '../api/types';
import { useGraftCtx } from '../shell/GraftLayout';
import { Explain, PageHead, ProblemBanner, SampleChip, Tag } from '../components/ui';
import { Skeleton } from '../components/Loaders';
import { isMock } from '../config';
import { formatUsd } from '../lib/format';
import type { Tone } from '../copy/words';
import s from './s14.module.css';

const INPUT: Record<AgentStep['input'], { word: string; tone: Tone; meaning: string }> = {
  real: { word: 'Real shop data', tone: 'good', meaning: "This agent worked on this shop's own data." },
  mixed: { word: 'Real + recorded', tone: 'warn', meaning: 'Real data from this run plus a recorded or controlled part.' },
  sample: { word: 'Sample input', tone: 'neutral', meaning: 'This agent ran on a qualified sample, not on this shop yet.' },
};

const ISSUE: Record<string, string> = {
  INVALID_MODEL_OUTPUT: 'its answer was refused by the checks',
  MISSING_EVIDENCE: 'its input or reading was incomplete',
  DENIED: 'a safety gate refused it (correct)',
  TURN_LIMIT: 'it ran out of turns',
};

const modelName = (m: string | null) => (m?.includes('sonnet') ? 'Sonnet' : m?.includes('haiku') ? 'Haiku' : '—');

/** Where in the app each agent's output can be seen in full. */
function seeIt(role: string, graftId: string): { to: string; label: string } | null {
  switch (role) {
    case 'Surveyor': return { to: `/g/${graftId}/map`, label: 'Old pieces' };
    case 'Grafter': return { to: `/g/${graftId}/changes`, label: 'Code changes' };
    case 'Adversary': return { to: `/g/${graftId}/union`, label: 'Payment tests' };
    case 'Librarian': return { to: '/bank', label: 'Recipes' };
    case 'Orchard Analyst': return { to: '/orchard', label: 'PayPal team' };
    case 'Sentinel': return { to: `/security/${isMock ? 'run-1' : graftId}`, label: 'Security' };
    default: return null;
  }
}

function Step({ a, graftId }: { a: AgentStep; graftId: string }) {
  const input = INPUT[a.input];
  const link = seeIt(a.role, graftId);
  return (
    <li className={`gg-glass ${s.step}`} data-held={!a.passed || undefined}>
      <div className={s.head}>
        <span className={s.mark} aria-hidden>{a.passed ? <CheckIcon size={14} weight="bold" /> : <PauseIcon size={14} weight="fill" />}</span>
        <h2 className={s.role}>{a.role}</h2>
        {a.attempt > 1 && <Tag tone="warn" title="The first attempt was held; this is the one bounded retry">Retry</Tag>}
        <Tag tone={a.passed ? 'good' : 'bad'}>{a.passed ? 'Passed' : 'Held'}</Tag>
        <Tag title={a.escalated ? 'Moved to Sonnet after two Haiku misses on this kind of task' : undefined}>
          {modelName(a.model)}{a.escalated ? ' · auto-switched' : ''}
        </Tag>
        <span className={s.cost}>{formatUsd(a.cost_usd)}{a.seconds != null && <> · {Math.round(a.seconds)} s</>}</span>
      </div>
      {a.outputs.map((o) => <p key={o.schema} className={s.made}>{o.summary}</p>)}
      {!a.passed && a.issue && <p className={s.issue}>Held: {ISSUE[a.issue] ?? a.issue}.</p>}
      <div className={s.foot}>
        <Tag tone={input.tone} title={input.meaning}>{input.word}</Tag>
        <span className={s.note}>{a.input_note}</span>
        {link && <Link className={s.see} to={link.to}>{link.label} <ArrowRightIcon size={13} aria-hidden /></Link>}
      </div>
    </li>
  );
}

export default function S14_Agents() {
  const { graftId } = useGraftCtx();
  const q = useQuery({ queryKey: ['agents', graftId], queryFn: () => api.agents(graftId), retry: 0 });
  useEffect(() => { document.title = 'GoldGraft · Agents'; }, []);

  if (q.isPending) return <div className={s.screen}><PageHead title="Agents" /><Skeleton what="agent steps" lines={5} /></div>;
  if (q.isError) return (
    <div className={s.screen}>
      <PageHead title="Agents" sub="No agent steps recorded for this upgrade." />
      <ProblemBanner error={q.error} onRetry={() => q.refetch()} />
    </div>
  );

  const steps = q.data.agents;
  const roles = new Set(steps.map((a) => a.role));
  const passed = new Set(steps.filter((a) => a.passed).map((a) => a.role));
  const cost = steps.reduce((n, a) => n + a.cost_usd, 0);
  const real = steps.filter((a) => a.input === 'real').length;

  return (
    <div className={s.screen}>
      <PageHead
        title="Agents"
        sub={<>{passed.size} of {roles.size} agents passed · {steps.length} steps · {formatUsd(cost)} AI cost <Explain text="Every step went through GoldGraft's budget gateway: Haiku for simple tasks, Sonnet for hard ones." /></>}
        aside={q.data.recorded_from
          ? <Tag tone="gold" title="Recorded from a real integrated agent run">Real AI output · run {q.data.recorded_from}</Tag>
          : isMock ? <SampleChip /> : <Tag tone="gold">Real AI output</Tag>}
      />
      <p className={s.legend}>
        {real} of {steps.length} steps worked on this shop's own data. Steps marked <b>Real + recorded</b> or <b>Sample input</b> used
        a recorded runner or a qualified sample for part of their input; the label says which.
      </p>
      <ol className={s.list}>
        {steps.map((a) => <Step key={`${a.task}-${a.attempt}`} a={a} graftId={graftId} />)}
      </ol>
    </div>
  );
}
