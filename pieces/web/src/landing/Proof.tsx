import { ArrowUpRightIcon, QuotesIcon } from '@phosphor-icons/react';
import { PROOF } from '../copy/landing';
import { AGENT_RESULTS, AGENT_TOTALS } from '../copy/evidence';
import s from './landing.module.css';

export function Proof() {
  return (
    <section id="proof" className={s.proof} data-world="rings">
      <div className={`gg-wrap gg-grid ${s.proofGrid}`}>
        <div className={s.proofHead}>
          <p className="gg-label" data-rise>{PROOF.label}</p>
          <h2 className="gg-h2" data-split>
            {PROOF.title} <em>{PROOF.titleEm}</em>
          </h2>
        </div>

        <div className={s.facts} data-vine="proof">
          {PROOF.facts.map((f) => (
            <article key={f.big} className={s.fact} data-rise>
              <p className={`gg-num ${s.factBig}`}>{f.big}</p>
              <p className={s.factText}>{f.text}</p>
              <a className={s.source} href={f.source.href} target="_blank" rel="noreferrer">
                {f.source.label} <ArrowUpRightIcon size={12} aria-hidden />
              </a>
            </article>
          ))}
        </div>

        <figure className={s.quote} data-rise>
          <QuotesIcon size={28} weight="fill" className={s.quoteMark} aria-hidden />
          <blockquote>{PROOF.quote}</blockquote>
          <figcaption>
            {PROOF.quoteBy} ·{' '}
            <a className={s.source} href={PROOF.quoteSource.href} target="_blank" rel="noreferrer">
              {PROOF.quoteSource.label} <ArrowUpRightIcon size={12} aria-hidden />
            </a>
          </figcaption>
        </figure>

        <div className={`gg-glass ${s.results}`} data-rise>
          <div className={s.resultsHead}>
            <p className="gg-label">{PROOF.resultsLabel}</p>
            <p className={s.resultsBig}>
              <span className="gg-num">{AGENT_TOTALS.passed}</span>
              <span className={s.resultsOf}> of {AGENT_TOTALS.total}</span>
            </p>
            <p className={s.resultsCap}>agent test runs passed, across all 13 AI agents</p>
          </div>
          <ul className={s.agentList} aria-label="Results per agent">
            {AGENT_RESULTS.map((r) => (
              <li key={r.name} title={`${r.name} ${r.job}`}>
                <span className={s.agentName}>{r.name}</span>
                <span className={s.agentBar} aria-hidden><span style={{ width: `${(r.passed / r.total) * 100}%` }} /></span>
                <span className={`gg-num ${s.agentNum}`}>{r.passed}/{r.total}</span>
              </li>
            ))}
          </ul>
          <p className={s.resultsFoot}>
            <span><b className="gg-num">{AGENT_TOTALS.tricksHeld} of {AGENT_TOTALS.tricksTotal}</b> hidden tricks stopped</span>
            <span><b className="gg-num">${AGENT_TOTALS.spendUsd}</b> spent on all of this testing</span>
          </p>
          <p className={s.resultsNote}>{PROOF.resultsNote}</p>
        </div>
      </div>
    </section>
  );
}
