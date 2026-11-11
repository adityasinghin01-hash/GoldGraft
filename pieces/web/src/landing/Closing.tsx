import { useId, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRightIcon, PlusIcon } from '@phosphor-icons/react';
import { FAQ, FINAL, STEPS } from '../copy/landing';
import { scrollToTarget } from '../motion/scroll';
import { ChapterMark } from './ChapterMark';
import s from './landing.module.css';

/** How it works: the sapling on the left, four numbered steps on cols 7–12 (order matters here). */
export function Steps() {
  return (
    <section id="steps" className={s.steps} data-world="sapling">
      <div className={`gg-wrap gg-grid ${s.stepsGrid}`}>
        <div className={s.head} data-exit>
          <ChapterMark label={STEPS.label} />
          <h2 className="gg-h2" data-split>{STEPS.title}</h2>
        </div>
        <ol className={s.stepList} data-vine="steps">
          {STEPS.items.map((st, i) => (
            <li key={st.n} className={s.step} data-rise data-delay={i * 0.06} data-exit>
              <span className={s.stepN} aria-hidden>{i + 1}</span>
              <div>
                <h3 className={s.h3}>{st.title}</h3>
                <p className={s.body} data-flow>{st.text}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  return (
    <li className={s.faqItem} data-open={open || undefined} data-exit>
      <h3>
        <button className={`${s.h3} ${s.faqQ}`} aria-expanded={open} aria-controls={id} onClick={() => setOpen((v) => !v)}>
          <span>{q}</span>
          <PlusIcon size={18} className={s.faqIcon} aria-hidden />
        </button>
      </h3>
      <div id={id} role="region" className={s.faqA} aria-hidden={!open}>
        <div><p>{a}</p></div>
      </div>
    </li>
  );
}

/** Questions: heading on cols 1–6, then the answers in two columns across the grid. */
export function Faq() {
  const half = Math.ceil(FAQ.items.length / 2);
  const cols = [FAQ.items.slice(0, half), FAQ.items.slice(half)];
  return (
    <section id="faq" className={s.faq} data-world="canopy">
      <div className={`gg-wrap gg-grid ${s.faqGrid}`}>
        <div className={`${s.head} ${s.faqHead}`} data-exit data-vine="faq">
          <ChapterMark label={FAQ.label} />
          <h2 className="gg-h2" data-split>{FAQ.title}</h2>
          <p className={s.headLead} data-rise>{FAQ.lead}</p>
        </div>
        {cols.map((items, c) => (
          <ul key={c} className={s.faqCol} data-stagger>
            {items.map((it) => <FaqItem key={it.q} q={it.q} a={it.a} />)}
          </ul>
        ))}
      </div>
    </section>
  );
}

/** The last word: the same promise as the hero, the bloom on the right, the Check action. */
export function Final() {
  const checkMyShop = (e: React.MouseEvent) => {
    e.preventDefault();
    scrollToTarget('#top');
    window.setTimeout(() => document.getElementById('shop-url')?.focus({ preventScroll: true }), 1400);
  };
  return (
    <section id="start" className={s.final} data-world="bloom" data-world-lead="0.4">
      <div className={`gg-wrap gg-grid ${s.finalGrid}`}>
        <div data-exit>
          <h2 className={s.finalTitle}>
            <span className={s.heroA} data-split>{FINAL.title}</span>
            <span className={s.heroB} data-split>{FINAL.titleEm}</span>
          </h2>
          <p className={`gg-lead ${s.finalLead}`} data-rise>{FINAL.lead}</p>
          <div className={s.finalActions} data-rise data-vine="final">
            <a href="#top" onClick={checkMyShop} className="gg-btn gg-btn--gold">{FINAL.primary} <ArrowRightIcon size={16} weight="bold" aria-hidden /></a>
            <Link to="/g/demo-1" className="gg-btn gg-btn--ghost">{FINAL.secondary}</Link>
          </div>
        </div>
      </div>
    </section>
  );
}
