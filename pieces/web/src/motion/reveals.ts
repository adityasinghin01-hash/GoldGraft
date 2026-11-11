import { gsap, ScrollTrigger, SplitText, reducedMotion } from './scroll';

/**
 * Text that builds and flows, all tied to load or scroll, once, in reading order.
 *   data-split          headings: each word rises out of its line with a soft blur, one after another
 *   data-split="load"   same, on page load (hero)
 *   data-scramble       labels type themselves in through scrambled letters ("load" = on load)
 *   data-roll           numbers roll through digits into place when they enter
 *   data-flow           paragraphs light up word by word as you scroll through them (scrubbed)
 *   data-rise           element rises 28px and fades in; data-delay="0.1" to offset
 *   data-stagger        children rise one after another
 *   data-draw           a hairline that draws itself from the left
 * Reduced motion: nothing is hidden, nothing moves.
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
            yPercent: 115,
            opacity: 0,
            filter: 'blur(6px)',
            duration: onLoad ? 1.2 : 1.05,
            ease: 'expo.out',
            stagger: { each: 0.045 },
            delay: onLoad ? Number(el.dataset.delay ?? 0.15) : 0,
            clearProps: 'filter',
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
        duration: 1.1,
        scrambleText: { text: '', chars: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', revealDelay: 0.1, speed: 0.6 },
        delay: onLoad ? 0.05 : 0,
        ease: 'none',
        scrollTrigger: onLoad ? undefined : { trigger: el, start: 'top 90%', once: true },
      });
    });

    root.querySelectorAll<HTMLElement>('[data-roll]').forEach((el) => {
      const final = el.textContent ?? '';
      gsap.to(el, {
        duration: 1.3,
        scrambleText: { text: final, chars: '0123456789', revealDelay: 0.35, speed: 0.8 },
        ease: 'none',
        scrollTrigger: { trigger: el, start: 'top 88%', once: true },
      });
    });

    root.querySelectorAll<HTMLElement>('[data-flow]').forEach((el) => {
      const split = SplitText.create(el, { type: 'words' });
      gsap.fromTo(split.words, { opacity: 0.16 }, {
        opacity: 1,
        ease: 'none',
        stagger: 0.08,
        scrollTrigger: { trigger: el, start: 'top 82%', end: 'bottom 52%', scrub: 0.6 },
      });
    });

    root.querySelectorAll<HTMLElement>('[data-rise]').forEach((el) => {
      gsap.from(el, {
        y: 28,
        autoAlpha: 0,
        duration: 1.0,
        ease: 'expo.out',
        delay: Number(el.dataset.delay ?? 0),
        clearProps: 'transform',
        scrollTrigger: el.dataset.rise === 'load' ? undefined : { trigger: el, start: 'top 90%', once: true },
      });
    });

    root.querySelectorAll<HTMLElement>('[data-stagger]').forEach((el) => {
      gsap.from(el.children, {
        y: 24,
        autoAlpha: 0,
        duration: 0.9,
        ease: 'expo.out',
        stagger: 0.07,
        scrollTrigger: { trigger: el, start: 'top 86%', once: true },
      });
    });

    root.querySelectorAll<HTMLElement>('[data-draw]').forEach((el) => {
      gsap.from(el, { scaleX: 0, transformOrigin: 'left center', duration: 1.4, ease: 'expo.out', scrollTrigger: { trigger: el, start: 'top 92%', once: true } });
    });

    // the band of old PayPal names leans with scroll speed
    const band = root.querySelector<HTMLElement>('[data-band]');
    if (band) {
      const skew = gsap.quickTo(band, 'skewX', { duration: 0.5, ease: 'power3.out' });
      ScrollTrigger.create({ onUpdate: (self) => skew(gsap.utils.clamp(-8, 8, self.getVelocity() / -260)) });
    }
  }, root);
  requestAnimationFrame(() => ScrollTrigger.refresh());
  return () => ctx.revert();
}
