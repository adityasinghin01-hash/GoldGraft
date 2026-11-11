import type { Blend } from './World';

// Reads every element with data-world="state" (or "a,b,c" for a pinned sequence)
// and turns the scroll position into "which picture, morphing into which, how far".
// Each state holds while its section owns the middle of the screen and morphs
// across the boundary to the next one.

type Key = { start: number; end: number; state: string };

export class Director {
  private keys: Key[] = [];

  measure(root: ParentNode = document) {
    const vh = window.innerHeight;
    const y0 = window.scrollY;
    const keys: Key[] = [];
    root.querySelectorAll<HTMLElement>('[data-world]').forEach((el) => {
      const ids = (el.dataset.world || '').split(',').map((s) => s.trim()).filter(Boolean);
      if (!ids.length) return;
      const r = el.getBoundingClientRect();
      const top = r.top + y0;
      const height = r.height;
      const lead = Number(el.dataset.worldLead ?? 0.45); // how early (in vh) the state arrives
      let start = top - vh * lead;
      let end = top + height - vh * (1 - 0.25);
      if (end < start) { const mid = (start + end) / 2; start = mid; end = mid; }
      if (ids.length === 1) {
        keys.push({ start, end, state: ids[0] });
        return;
      }
      const seg = (end - start) / ids.length;
      ids.forEach((id, i) => {
        const s = start + seg * i;
        keys.push({ start: i === 0 ? s : s + seg * 0.14, end: s + seg * 0.84, state: id });
      });
    });
    keys.sort((a, b) => a.start - b.start);
    this.keys = keys;
  }

  blendAt(y: number): Blend {
    const k = this.keys;
    if (!k.length) return { from: 'cloud', to: 'cloud', mix: 0 };
    if (y <= k[0].end) return { from: k[0].state, to: k[0].state, mix: 0 };
    for (let i = 0; i < k.length; i++) {
      const cur = k[i];
      if (y >= cur.start && y <= cur.end) return { from: cur.state, to: cur.state, mix: 0 };
      const next = k[i + 1];
      if (next && y > cur.end && y < next.start) {
        const mix = (y - cur.end) / Math.max(1, next.start - cur.end);
        return { from: cur.state, to: next.state, mix };
      }
    }
    const last = k[k.length - 1];
    return { from: last.state, to: last.state, mix: 0 };
  }

  states(): string[] { return [...new Set(this.keys.map((k) => k.state))]; }
}
