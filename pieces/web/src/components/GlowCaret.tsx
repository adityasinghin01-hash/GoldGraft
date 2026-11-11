import { useEffect, useRef, useState, type RefObject } from 'react';

/**
 * A glowing gold typing cursor for single-line inputs (the Spotlight-style detail).
 * Hides the native caret on that input and draws its own at the cursor position.
 * Put it inside the input's positioned wrapper: <GlowCaret input={ref} />
 */
export function GlowCaret({ input }: { input: RefObject<HTMLInputElement | null> }) {
  const caret = useRef<HTMLSpanElement>(null);
  const [on, setOn] = useState(false);

  useEffect(() => {
    const el = input.current;
    const c = caret.current;
    if (!el || !c) return;
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d')!;
    el.style.caretColor = 'transparent';
    let typingTimer = 0;

    const place = () => {
      const cs = getComputedStyle(el);
      ctx.font = `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
      const pos = el.selectionStart ?? el.value.length;
      const text = el.type === 'password' ? '•'.repeat(pos) : el.value.slice(0, pos);
      const w = ctx.measureText(text).width;
      const left = el.offsetLeft + parseFloat(cs.paddingLeft) + w - el.scrollLeft;
      const max = el.offsetLeft + el.clientWidth - parseFloat(cs.paddingRight);
      c.style.left = `${Math.min(left, max)}px`;
      c.style.top = `${el.offsetTop + el.offsetHeight / 2}px`;
      c.style.fontSize = cs.fontSize;
      const sel = (el.selectionEnd ?? 0) !== (el.selectionStart ?? 0);
      c.style.opacity = sel ? '0' : '1';
    };
    const typing = () => {
      c.dataset.typing = '';
      window.clearTimeout(typingTimer);
      typingTimer = window.setTimeout(() => delete c.dataset.typing, 500);
      requestAnimationFrame(place);
    };
    const focus = () => { setOn(true); requestAnimationFrame(place); };
    const blur = () => setOn(false);
    const sel = () => requestAnimationFrame(place);

    el.addEventListener('input', typing);
    el.addEventListener('keydown', typing);
    el.addEventListener('focus', focus);
    el.addEventListener('blur', blur);
    el.addEventListener('click', sel);
    el.addEventListener('select', sel);
    el.addEventListener('scroll', sel);
    document.addEventListener('selectionchange', sel);
    if (document.activeElement === el) focus();
    return () => {
      el.removeEventListener('input', typing);
      el.removeEventListener('keydown', typing);
      el.removeEventListener('focus', focus);
      el.removeEventListener('blur', blur);
      el.removeEventListener('click', sel);
      el.removeEventListener('select', sel);
      el.removeEventListener('scroll', sel);
      document.removeEventListener('selectionchange', sel);
      window.clearTimeout(typingTimer);
    };
  }, [input]);

  return <span ref={caret} className="gg-caret" aria-hidden style={{ display: on ? 'block' : 'none', marginTop: 0, transform: 'translateY(-50%)' }} />;
}
