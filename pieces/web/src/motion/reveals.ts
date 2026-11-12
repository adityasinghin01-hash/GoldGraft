import { gsap, ScrollTrigger, SplitText, reducedMotion } from './scroll';

/**
 * One motion language for text, borrowed from the gold dust:
 *   arrive  headings rise out of their lines word by word · paragraphs light up word by word ·
 *           blocks rise 28px into place
 *   leave   headings roll back up into their lines · paragraphs drift apart word by word like dust ·
 *           cards tip back and dissolve
 * Everything that leaves is scrubbed by the scroll, so scrolling back up rebuilds it exactly.
 *
 *   data-split          heading (or label): arrives word by word, leaves by rolling up line by line
 *   data-split="load"   arrives on page load (hero)
 *   data-roll           a number rolls through digits into place
 *   data-flow           a paragraph lights up word by word, once; fully readable at rest
 *   data-rise           rises into place (data-delay="0.1"; "load" = on load)
 *   data-stagger        its children rise one after another ("load" = on load)
 *   data-draw           a hairline draws itself from the left
 *   data-exit           a block tips back and dissolves as it passes the top fifth of the screen
 *   data-exit="dust"    its words drift apart and fade as it passes
 *   data-pin            a pinned scene: everything in it leaves together as the pin releases
 *
 * --rise / --exit are registered properties (base.css) that become opacity and `translate`.
 * Reduced motion: nothing hidden, nothing moves.
 */
export function setupReveals(root: HTMLElement): () => void {
  if (reducedMotion()) return () => {};
  const late: Array<() => void> = []; // tweens made later (on re-split) that the context can't see

  // Where an element leaves: short ones while their top crosses 22% → 2% of the screen, tall ones
  // while their bottom crosses 45% → 12%. Anything already in that zone at the top of the page
  // (the hero) leaves over the first quarter screen of scroll.
  const zone = (el: HTMLElement): [number, number] => {
    const h = window.innerHeight;
    const pin = el.closest<HTMLElement>('[data-pin]');
    if (pin) {
      // inside a pinned scene: leave as the pin releases, over the next 45% of a screen
      const sec = pin.parentElement ?? pin;
      const release = sec.getBoundingClientRect().bottom + window.scrollY - h;
      return [release, release + h * 0.45];
    }
    const r = el.getBoundingClientRect();
    const top = r.top + window.scrollY, bottom = r.bottom + window.scrollY;
    const tall = r.height > h * 0.3;
    let s0 = tall ? bottom - h * 0.45 : top - h * 0.22;
    let s1 = tall ? bottom - h * 0.12 : top - h * 0.02;
    if (s0 < 0) { s1 = Math.max(s1, h * 0.25); s0 = 0; }
    return [s0, s1];
  };
  const leaving = (el: HTMLElement): ScrollTrigger.Vars => ({ start: () => zone(el)[0], end: () => zone(el)[1], scrub: 0.3, invalidateOnRefresh: true });

  const ctx = gsap.context(() => {
    // headings and labels
    root.querySelectorAll<HTMLElement>('[data-split]').forEach((el) => {
      let exit: gsap.core.Timeline | null = null;
      const drop = () => { exit?.scrollTrigger?.kill(); exit?.kill(); exit = null; };
      SplitText.create(el, {
        type: 'lines,words', mask: 'lines', linesClass: 'gg-line', autoSplit: true,
        onSplit(self) {
          const onLoad = el.dataset.split === 'load';
          drop();
          exit = gsap.timeline({ scrollTrigger: leaving(el) })
            .to(self.lines, { yPercent: -112, ease: 'power2.in', stagger: 0.18, duration: 1 }, 0);
          return gsap.from(self.words, {
            yPercent: 110,
            opacity: 0,
            duration: onLoad ? 1.15 : 1.0,
            ease: 'expo.out',
            stagger: { each: 0.04 },
            delay: onLoad ? Number(el.dataset.delay ?? 0.15) : 0,
            scrollTrigger: onLoad ? undefined : { trigger: el, start: 'top 88%', once: true },
          });
        },
      });
      late.push(drop);
    });

    // numbers count up to their real value (never random digits); anything that isn't a plain
    // number (a date) rises out of a mask instead
    root.querySelectorAll<HTMLElement>('[data-roll]').forEach((el) => {
      const final = el.textContent ?? '';
      const n = Number(final.replace(/,/g, ''));
      if (!/^[\d,]+$/.test(final.trim()) || !Number.isFinite(n)) {
        gsap.from(el, { yPercent: 60, opacity: 0, duration: 1, ease: 'expo.out', scrollTrigger: { trigger: el, start: 'top 88%', once: true } });
        return;
      }
      const v = { n: 0 };
      const fmt = (x: number) => Math.round(x).toLocaleString('en-US');
      el.style.minWidth = `${final.length}ch`;
      gsap.to(v, {
        n,
        duration: 1.4,
        ease: 'expo.out',
        onStart: () => { el.textContent = fmt(0); },
        onUpdate: () => { el.textContent = fmt(v.n); },
        onComplete: () => { el.textContent = final; },
        scrollTrigger: { trigger: el, start: 'top 88%', once: true },
      });
    });

    root.querySelectorAll<HTMLElement>('[data-flow]').forEach((el) => {
      const split = SplitText.create(el, { type: 'words', wordsClass: 'gg-w' });
      gsap.from(split.words, {
        opacity: 0.18,
        duration: 0.5,
        ease: 'power2.out',
        stagger: 0.016,
        scrollTrigger: { trigger: el, start: 'top 86%', once: true },
      });
    });

    const rise = (targets: Element | Element[], vars: gsap.TweenVars, trigger: Element | null) =>
      gsap.fromTo(targets, { '--rise': 0 }, {
        '--rise': 1,
        duration: 1.0,
        ease: 'expo.out',
        ...vars,
        scrollTrigger: trigger ? { trigger, start: 'top 90%', once: true } : undefined,
      });

    root.querySelectorAll<HTMLElement>('[data-rise]').forEach((el) => {
      rise(el, { delay: Number(el.dataset.delay ?? 0) }, el.dataset.rise === 'load' ? null : el);
    });

    root.querySelectorAll<HTMLElement>('[data-stagger]').forEach((el) => {
      const onLoad = el.dataset.stagger === 'load';
      rise([...el.children], { duration: 0.9, stagger: 0.07, delay: onLoad ? Number(el.dataset.delay ?? 0) : 0 }, onLoad ? null : el);
    });

    root.querySelectorAll<HTMLElement>('[data-draw]').forEach((el) => {
      gsap.from(el, { scaleX: 0, transformOrigin: 'left center', duration: 1.2, ease: 'expo.out', scrollTrigger: { trigger: el, start: 'top 92%', once: true } });
    });

    // leaving
    root.querySelectorAll<HTMLElement>('[data-exit]').forEach((el) => {
      if (el.dataset.exit === 'dust') {
        // words drift apart (their own x/y/rotation) while the block fades (its --exit)
        const found = [...el.querySelectorAll<HTMLElement>('.gg-w')];
        const words = found.length ? found : (SplitText.create(el, { type: 'words', wordsClass: 'gg-w' }).words as HTMLElement[]);
        const rnd = gsap.utils.random;
        gsap.timeline({
          scrollTrigger: leaving(el),
          onUpdate() {
            const p = this.progress();
            el.style.filter = p > 0.001 ? `blur(${(p * 3).toFixed(2)}px)` : '';
          },
        })
          .to(words, {
            y: () => -rnd(10, 30),
            x: () => rnd(-9, 9),
            rotation: () => rnd(-5, 5),
            ease: 'power1.in',
            stagger: { amount: 0.45, from: 'start' },
            duration: 0.55,
          }, 0)
          .fromTo(el, { '--exit': 0 }, { '--exit': 1, ease: 'none', duration: 1, immediateRender: false }, 0);
        return;
      }
      // cards and blocks tip back from their lower edge, blur and fade
      el.style.transformOrigin = '50% 100%';
      gsap.fromTo(el, { '--exit': 0 }, {
        '--exit': 1,
        ease: 'power1.in',
        immediateRender: false,
        scrollTrigger: leaving(el),
        onUpdate() {
          const p = this.progress();
          el.style.transform = p > 0.001 ? `perspective(1000px) rotateX(${(p * 16).toFixed(2)}deg)` : '';
          el.style.filter = p > 0.001 ? `blur(${(p * 5).toFixed(2)}px)` : '';
        },
      });
    });
  }, root);
  requestAnimationFrame(() => ScrollTrigger.refresh());
  return () => { late.forEach((f) => f()); ctx.revert(); };
}
