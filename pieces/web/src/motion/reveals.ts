import { gsap, ScrollTrigger, SplitText, reducedMotion } from './scroll';

/**
 * Text and element entrances for one page, all on scroll, once, in reading order.
 *   data-split          heading lines rise out of a mask when they enter
 *   data-split="load"   same, on page load (hero)
 *   data-rise           element rises 28px and fades in; data-delay="0.1" to offset
 *   data-stagger        children rise one after another (60 ms apart)
 * Reduced motion: nothing is hidden, nothing moves.
 */
export function setupReveals(root: HTMLElement): () => void {
  if (reducedMotion()) return () => {};
  const ctx = gsap.context(() => {
    root.querySelectorAll<HTMLElement>('[data-split]').forEach((el) => {
      const split = SplitText.create(el, { type: 'lines', mask: 'lines', linesClass: 'gg-line', autoSplit: true,
        onSplit(self) {
          const onLoad = el.dataset.split === 'load';
          return gsap.from(self.lines, {
            yPercent: 112,
            rotate: 1.2,
            duration: onLoad ? 1.25 : 1.05,
            ease: 'expo.out',
            stagger: 0.085,
            delay: onLoad ? Number(el.dataset.delay ?? 0.15) : 0,
            scrollTrigger: onLoad ? undefined : { trigger: el, start: 'top 86%', once: true },
          });
        } });
      void split;
    });

    root.querySelectorAll<HTMLElement>('[data-rise]').forEach((el) => {
      gsap.from(el, {
        y: 28,
        autoAlpha: 0,
        duration: 1.0,
        ease: 'expo.out',
        delay: Number(el.dataset.delay ?? 0),
        scrollTrigger: el.dataset.rise === 'load' ? undefined : { trigger: el, start: 'top 88%', once: true },
      });
    });

    root.querySelectorAll<HTMLElement>('[data-stagger]').forEach((el) => {
      gsap.from(el.children, {
        y: 24,
        autoAlpha: 0,
        duration: 0.9,
        ease: 'expo.out',
        stagger: 0.06,
        scrollTrigger: { trigger: el, start: 'top 85%', once: true },
      });
    });
  }, root);
  requestAnimationFrame(() => ScrollTrigger.refresh());
  return () => ctx.revert();
}
