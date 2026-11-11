import { gsap, ScrollTrigger, SplitText, reducedMotion } from './scroll';

/**
 * Text arrives as you reach it and leaves as you pass it, so the eye stays on what is coming.
 *   data-split          headings: each word rises out of its line (once, on enter)
 *   data-split="load"   same, on page load (hero)
 *   data-scramble       a label types itself in ("load" = on load)
 *   data-roll           a number rolls through digits into place
 *   data-flow           a paragraph lights up word by word, once, and is fully readable at rest
 *   data-rise           rises 28px and fades in (data-delay="0.1" to offset; "load" = on load)
 *   data-stagger        its children rise one after another ("load" = on load)
 *   data-draw           a hairline draws itself from the left
 *   data-exit           fades and lifts away as it passes the top fifth of the screen (scrubbed)
 *
 * Rise and exit drive two registered properties, --rise and --exit, which base.css turns into
 * opacity and `translate`. They never fight each other, and never touch `transform`
 * (buttons and tilting cards keep theirs). Reduced motion: nothing hidden, nothing moves.
 */
export function setupReveals(root: HTMLElement): () => void {
  if (reducedMotion()) return () => {};
  const ctx = gsap.context(() => {
    root.querySelectorAll<HTMLElement>('[data-split]').forEach((el) => {
      SplitText.create(el, {
        type: 'lines,words', mask: 'lines', linesClass: 'gg-line', autoSplit: true,
        onSplit(self) {
          const onLoad = el.dataset.split === 'load';
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
    });

    root.querySelectorAll<HTMLElement>('[data-scramble]').forEach((el) => {
      const node = [...el.childNodes].reverse().find((n) => n.nodeType === 3 && n.textContent?.trim());
      if (!node) return;
      const text = node.textContent ?? '';
      const span = document.createElement('span');
      span.textContent = text;
      node.replaceWith(span);
      const onLoad = el.dataset.scramble === 'load';
      gsap.from(span, {
        duration: 0.9,
        scrambleText: { text: '', chars: 'abcdefghijklmnopqrstuvwxyz', revealDelay: 0.1, speed: 0.6 },
        delay: onLoad ? 0.05 : 0,
        ease: 'none',
        scrollTrigger: onLoad ? undefined : { trigger: el, start: 'top 90%', once: true },
      });
    });

    root.querySelectorAll<HTMLElement>('[data-roll]').forEach((el) => {
      const final = el.textContent ?? '';
      gsap.to(el, {
        duration: 1.2,
        scrambleText: { text: final, chars: '0123456789', revealDelay: 0.3, speed: 0.8 },
        ease: 'none',
        scrollTrigger: { trigger: el, start: 'top 88%', once: true },
      });
    });

    root.querySelectorAll<HTMLElement>('[data-flow]').forEach((el) => {
      const split = SplitText.create(el, { type: 'words' });
      gsap.from(split.words, {
        opacity: 0.18,
        duration: 0.5,
        ease: 'power2.out',
        stagger: 0.018,
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

    // exits: a short element fades while its top crosses 22% → 2% of the screen; a tall one while
    // its bottom crosses 45% → 12%, so nothing fades while you still read it. Something that already
    // sits in that zone at the top of the page (the hero) leaves over the first quarter screen of scroll.
    const zone = (el: HTMLElement): [number, number] => {
      const h = window.innerHeight;
      const r = el.getBoundingClientRect();
      const top = r.top + window.scrollY, bottom = r.bottom + window.scrollY;
      const tall = r.height > h * 0.3;
      let s0 = tall ? bottom - h * 0.45 : top - h * 0.22;
      let s1 = tall ? bottom - h * 0.12 : top - h * 0.02;
      if (s0 < 0) { s1 = Math.max(s1, h * 0.25); s0 = 0; }
      return [s0, s1];
    };
    root.querySelectorAll<HTMLElement>('[data-exit]').forEach((el) => {
      gsap.fromTo(el, { '--exit': 0 }, {
        '--exit': 1,
        ease: 'none',
        immediateRender: false,
        scrollTrigger: { start: () => zone(el)[0], end: () => zone(el)[1], scrub: true, invalidateOnRefresh: true },
      });
    });
  }, root);
  requestAnimationFrame(() => ScrollTrigger.refresh());
  return () => ctx.revert();
}
