import type { MoneyEvent } from '../api/types';

// S4 lane alignment (pack S04 "Alignment"). Markers are a visual aid only; the verdict comes from the API.
export type Ledger = MoneyEvent & { tag: 'old' | 'new' };
export type Row = { old: MoneyEvent | null; new: MoneyEvent | null; pp: Ledger | null; twin: MoneyEvent | null; marker: 'different' | 'only in old' | 'only in new' | null };

const bySeq = (a: MoneyEvent, b: MoneyEvent) => a.seq - b.seq;

/** Longest common subsequence of kinds; returns index pairs (ties prefer earlier rows). */
function lcsPairs(a: MoneyEvent[], b: MoneyEvent[]): Array<[number | null, number | null]> {
  const n = a.length, m = b.length;
  const dp: number[][] = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--)
    dp[i][j] = a[i].kind === b[j].kind ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  const out: Array<[number | null, number | null]> = [];
  let i = 0, j = 0;
  while (i < n && j < m) {
    if (a[i].kind === b[j].kind) { out.push([i, j]); i++; j++; }
    else if (dp[i + 1][j] >= dp[i][j + 1]) { out.push([i, null]); i++; }
    else { out.push([null, j]); j++; }
  }
  while (i < n) out.push([i++, null]);
  while (j < m) out.push([null, j++]);
  return out;
}

const statusOf = (e: MoneyEvent) => (e as { status_norm?: string }).status_norm;
const moneyOf = (e: MoneyEvent) => (e as { money?: { minor: number; currency: string } }).money;

export function alignLanes(oldAll: MoneyEvent[], newAll: MoneyEvent[], twinAll: MoneyEvent[] = []): Row[] {
  const isPP = (e: MoneyEvent) => e.source === 'PAYPAL_LEDGER';
  const old = oldAll.filter((e) => !isPP(e)).sort(bySeq);
  const neu = newAll.filter((e) => !isPP(e)).sort(bySeq);
  const twin = twinAll.filter((e) => !isPP(e)).sort(bySeq);
  const ledger: Ledger[] = [
    ...oldAll.filter(isPP).map((e) => ({ ...e, tag: 'old' as const })),
    ...newAll.filter(isPP).map((e) => ({ ...e, tag: 'new' as const })),
  ].sort((a, b) => a.t_ms - b.t_ms);

  const raw: Row[] = lcsPairs(old, neu).map(([i, j]) => ({ old: i === null ? null : old[i], new: j === null ? null : neu[j], pp: null, twin: null, marker: null }));
  // two neighbouring one-sided rows (old only, then new only) describe the same moment differently: one row
  const rows: Row[] = [];
  for (let k = 0; k < raw.length; k++) {
    const a = raw[k], b = raw[k + 1];
    if (b && a.old && !a.new && b.new && !b.old) { rows.push({ ...a, new: b.new }); k++; }
    else if (b && a.new && !a.old && b.old && !b.new) { rows.push({ ...a, old: b.old }); k++; }
    else rows.push(a);
  }

  // twin aligns to the old lane; twin-only rows go at the end
  const twinPairs = lcsPairs(old, twin);
  for (const [i, k] of twinPairs) {
    if (k === null) continue;
    if (i === null) { rows.push({ old: null, new: null, pp: null, twin: twin[k], marker: null }); continue; }
    const r = rows.find((x) => x.old === old[i]);
    if (r) r.twin = twin[k];
  }

  // PayPal's own record sits next to the latest shop event of its side at or before it
  for (const le of ledger) {
    let at = -1;
    rows.forEach((r, idx) => {
      const e = le.tag === 'old' ? r.old : r.new;
      if (e && e.t_ms <= le.t_ms) at = idx;
    });
    let placed = false;
    for (let idx = Math.max(0, at); idx < rows.length; idx++) {
      if (!rows[idx].pp) { rows[idx].pp = le; placed = true; break; }
    }
    if (!placed) rows.push({ old: null, new: null, pp: le, twin: null, marker: null });
  }

  for (const r of rows) {
    if (r.old && r.new) {
      const a = moneyOf(r.old), b = moneyOf(r.new);
      const moneyDiff = (a?.minor ?? null) !== (b?.minor ?? null) || (a?.currency ?? null) !== (b?.currency ?? null);
      if (moneyDiff || statusOf(r.old) !== statusOf(r.new) || r.old.kind !== r.new.kind) r.marker = 'different';
    } else if (r.old) r.marker = 'only in old';
    else if (r.new) r.marker = 'only in new';
  }
  return rows;
}

/** A field is noise if the event lists it, or the verdict masked it. */
export const isNoise = (e: MoneyEvent, field: string, masked: string[] = []) =>
  ((e as { noise?: string[] }).noise ?? []).includes(field) || masked.includes(field);
