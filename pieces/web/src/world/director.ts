// Reads every element with data-world="state" (or "a,b,c" for a pinned sequence)
// and turns the scroll position into one number: how far along the chain of pictures
// we are (2.4 = 40% of the way from picture 2 to picture 3). The world eases toward that
// number every frame, so the glitter glides between pictures instead of jumping.

type Key = { start: number; end: number; state: string };

export class Director {
  private keys: Key[] = [];

  measure(root: ParentNode = document) {
    const vh = window.innerHeight;
    const y0 = window.scrollY;
    const keys: Key[] = [];
    root.querySelectorAll<HTMLElement>('[data-world]').forEach((el) => {
      if (el === document.documentElement) return;
      const ids = (el.dataset.world || '').split(',').map((s) => s.trim()).filter(Boolean);
      if (!ids.length) return;
      const r = el.getBoundingClientRect();
      const top = r.top + y0;
      const height = r.height;
      const lead = Number(el.dataset.worldLead ?? 0.45);
      let start = top - vh * lead;
      let end = top + height - vh * 0.75;
      if (end < start) { const mid = (start + end) / 2; start = mid; end = mid; }
      if (ids.length === 1) { keys.push({ start, end, state: ids[0] }); return; }
      const seg = (end - start) / ids.length;
      ids.forEach((id, i) => {
        const s = start + seg * i;
        keys.push({ start: i === 0 ? s : s + seg * 0.14, end: s + seg * 0.84, state: id });
      });
    });
    keys.sort((a, b) => a.start - b.start);
    this.keys = keys;
  }

  /** The chain of pictures, in scroll order. */
  timeline(): string[] { return this.keys.map((k) => k.state); }

  /** Float position along the timeline for a scroll position. */
  positionAt(y: number): number {
    const k = this.keys;
    if (!k.length) return 0;
    if (y <= k[0].end) return 0;
    for (let i = 0; i < k.length; i++) {
      const cur = k[i];
      if (y >= cur.start && y <= cur.end) return i;
      const next = k[i + 1];
      if (next && y > cur.end && y < next.start) return i + (y - cur.end) / Math.max(1, next.start - cur.end);
    }
    return k.length - 1;
  }

  states(): string[] { return [...new Set(this.keys.map((k) => k.state))]; }
}
