// Small tactile details, installed once for the whole app (event delegation, no per-component wiring):
//  · buttons: a soft light follows the pointer; pressing sends a ripple of light from the press point
//  · [data-tilt] cards: a gentle 3D lean toward the pointer with a moving specular highlight
import { reducedMotion } from './scroll';

let installed = false;

export function installPress() {
  if (installed || typeof window === 'undefined') return;
  installed = true;
  const still = reducedMotion();

  document.addEventListener('pointermove', (e) => {
    const t = e.target as HTMLElement | null;
    const btn = t?.closest?.('.gg-btn') as HTMLElement | null;
    if (btn) {
      const r = btn.getBoundingClientRect();
      btn.style.setProperty('--mx', `${e.clientX - r.left}px`);
      btn.style.setProperty('--my', `${e.clientY - r.top}px`);
    }
    if (still) return;
    const card = t?.closest?.('[data-tilt]') as HTMLElement | null;
    if (card) {
      const r = card.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top) / r.height - 0.5;
      card.style.setProperty('--rx', `${(-y * 4).toFixed(2)}deg`);
      card.style.setProperty('--ry', `${(x * 5).toFixed(2)}deg`);
      card.style.setProperty('--sx', `${((x + 0.5) * 100).toFixed(1)}%`);
      card.style.setProperty('--sy', `${((y + 0.5) * 100).toFixed(1)}%`);
      card.dataset.tiltOn = '';
    }
  }, { passive: true });

  document.addEventListener('pointerout', (e) => {
    const card = (e.target as HTMLElement | null)?.closest?.('[data-tilt]') as HTMLElement | null;
    if (card && !card.contains(e.relatedTarget as Node)) {
      card.style.setProperty('--rx', '0deg');
      card.style.setProperty('--ry', '0deg');
      delete card.dataset.tiltOn;
    }
  });

  document.addEventListener('pointerdown', (e) => {
    const btn = (e.target as HTMLElement | null)?.closest?.('.gg-btn') as HTMLElement | null;
    if (!btn || (btn as HTMLButtonElement).disabled || still) return;
    const r = btn.getBoundingClientRect();
    const dot = document.createElement('span');
    dot.className = 'gg-ripple';
    dot.style.left = `${e.clientX - r.left}px`;
    dot.style.top = `${e.clientY - r.top}px`;
    btn.appendChild(dot);
    window.setTimeout(() => dot.remove(), 650);
  });
}
