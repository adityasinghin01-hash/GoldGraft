import { useId, useState } from 'react';
import { ArrowUpRightIcon, PlusIcon } from '@phosphor-icons/react';
import { PROOF } from '../copy/landing';
import { AGENT_RESULTS, AGENT_TOTALS } from '../copy/evidence';
import { ChapterMark } from './ChapterMark';
import s from './landing.module.css';

function Source({ href, label }: { href: string; label: string }) {
  return (
    <a className={s.source} href={href} target="_blank" rel="noreferrer">
      {label}<ArrowUpRightIcon size={12} aria-hidden />
    </a>
  );
}

/** Why now: the tree rings on the left, the dated facts and our own test results on cols 7–12. */
export function Proof() {
  const [open, setOpen] = useState(false);
  const drawer = useId();
  return (
    <section id="proof" className={s.proof} data-world="rings">
      <div className={`gg-wrap gg-grid ${s.proofGrid}`}>
        <div className={s.head} data-exit>
          <ChapterMark label={PROOF.label} />
          <h2 className="gg-h2" data-split>{PROOF.title}</h2>
          <p className={s.headLead} data-rise>{PROOF.lead}</p>
        </div>

        <div className={s.facts} data-vine="proof">
          {PROOF.facts.map((f) => (
            <article key={f.big} className={s.fact} data-rise data-exit>
              <p className={`gg-num ${s.factBig}`} data-roll>{f.big}</p>
              <p className={s.body} data-flow>{f.text}</p>
              <Source {...f.source} />
            </article>
          ))}
        </div>

        <figure className={s.quote} data-rise data-exit>
          <blockquote>{PROOF.quote}</blockquote>
          <figcaption className={s.meta}>
            {PROOF.quoteBy} · <Source {...PROOF.quoteSource} />
          </figcaption>
        </figure>

        <div className={`gg-glass ${s.results}`} data-rise data-exit>
          <div className={s.resultsHead}>
            <h3 className={s.h3}>{PROOF.resultsLabel}</h3>
            <p className={s.resultsBig}>
              <span className="gg-num" data-roll>{AGENT_TOTALS.passed}</span>
              <span className={s.resultsOf}> of {AGENT_TOTALS.total}</span>
            </p>
            <p className={s.body}>{PROOF.resultsCaption}</p>
          </div>
          <div className={s.resultsRow}>
            <p><b className="gg-num">{AGENT_TOTALS.tricksHeld} of {AGENT_TOTALS.tricksTotal}</b> hidden tricks stopped</p>
            <p><b className="gg-num">${AGENT_TOTALS.spendUsd}</b> spent on all of this testing</p>
          </div>
          <button type="button" className={s.more} aria-expanded={open} aria-controls={drawer} onClick={() => setOpen((v) => !v)}>
            {PROOF.resultsMore} <PlusIcon size={18} aria-hidden />
          </button>
          <div id={drawer} className={s.drawer} data-open={open || undefined}>
            <div>
              <ul className={s.agentList} aria-label="Results per agent">
                {AGENT_RESULTS.map((r) => (
                  <li key={r.name} title={`${r.name} ${r.job}`}>
                    <span className={s.agentName}>{r.name}</span>
                    <span className={s.agentBar} aria-hidden><span style={{ width: `${(r.passed / r.total) * 100}%` }} /></span>
                    <span className={`gg-num ${s.agentNum}`}>{r.passed}/{r.total}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <p className={s.meta}>{PROOF.resultsNote}</p>
        </div>
      </div>
    </section>
  );
}
