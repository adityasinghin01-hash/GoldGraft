import { useId, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRightIcon, PlusIcon } from '@phosphor-icons/react';
import { FAQ, FINAL, STEPS } from '../copy/landing';
import { scrollToTarget } from '../motion/scroll';
import s from './landing.module.css';

export function Steps() {
  return (
    <section id="steps" className={s.steps} data-world="sapling">
      <div className={`gg-wrap gg-grid ${s.stepsGrid}`}>
        <div className={s.stepsHead}>
          <p className="gg-label" data-rise>{STEPS.label}</p>
          <h2 className="gg-h2" data-split>{STEPS.title} <em>{STEPS.titleEm}</em></h2>
        </div>
        <ol className={s.stepList} data-vine="steps">
          {STEPS.items.map((st) => (
            <li key={st.n} className={s.step} data-rise>
              <span className={`gg-num ${s.stepN}`}>{st.n}</span>
              <div>
                <h3 className={s.stepTitle}>{st.title}</h3>
                <p className={s.stepText}>{st.text}</p>
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
    <li className={s.faqItem} data-open={open || undefined}>
      <h3>
        <button className={s.faqQ} aria-expanded={open} aria-controls={id} onClick={() => setOpen((v) => !v)}>
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

export function Faq() {
  return (
    <section id="faq" className={s.faq} data-world="canopy">
      <div className={`gg-wrap gg-grid ${s.faqGrid}`}>
        <div className={s.faqHead}>
          <p className="gg-label" data-rise>{FAQ.label}</p>
          <h2 className="gg-h2" data-split>{FAQ.title}</h2>
        </div>
        <ul className={s.faqList} data-vine="faq" data-stagger>
          {FAQ.items.map((it) => <FaqItem key={it.q} q={it.q} a={it.a} />)}
        </ul>
      </div>
    </section>
  );
}

export function Final() {
  const checkMyShop = (e: React.MouseEvent) => {
    e.preventDefault();
    scrollToTarget('#top');
    window.setTimeout(() => document.getElementById('shop-url')?.focus({ preventScroll: true }), 1400);
  };
  return (
    <section id="start" className={s.final} data-world="bloom">
      <div className={`gg-wrap ${s.finalInner}`}>
        <h2 className={s.finalTitle} data-split>{FINAL.title} <em>{FINAL.titleEm}</em></h2>
        <p className={`gg-lead ${s.finalLead}`} data-rise>{FINAL.lead}</p>
        <div className={s.finalActions} data-rise data-vine="final">
          <a href="#top" onClick={checkMyShop} className="gg-btn gg-btn--gold">{FINAL.primary} <ArrowRightIcon size={16} weight="bold" aria-hidden /></a>
          <Link to="/g/demo-1" className="gg-btn gg-btn--ghost">{FINAL.secondary}</Link>
        </div>
      </div>
    </section>
  );
}
