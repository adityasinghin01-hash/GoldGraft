import type { LedgerEntry } from '../api/types';

export const newIdempotencyKey = () =>
  typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

/** Each step carries a fingerprint of the one before. Returns the first broken seq, or null. */
export function chainBreak(entries: LedgerEntry[]): number | null {
  const sorted = [...entries].sort((a, b) => a.seq - b.seq);
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i].seq !== sorted[i - 1].seq + 1) continue;
    if (sorted[i].prev_hash !== sorted[i - 1].entry_hash) return sorted[i].seq;
  }
  return null;
}

// S12: upgrades started in this browser. Four fields only; keys are never saved.
export type MyUpgrade = { graft_id: string; shop_id: string; name?: string; started_at: string };
const KEY = 'goldgraft.myUpgrades.v1';

export function readUpgrades(): { list: MyUpgrade[]; ok: boolean } {
  try {
    const raw = localStorage.getItem(KEY);
    const list = raw ? (JSON.parse(raw) as MyUpgrade[]) : [];
    return { list: Array.isArray(list) ? list : [], ok: true };
  } catch {
    return { list: [], ok: false };
  }
}

function write(list: MyUpgrade[]): boolean {
  try {
    const slim = list.map(({ graft_id, shop_id, name, started_at }) => ({ graft_id, shop_id, name, started_at }));
    localStorage.setItem(KEY, JSON.stringify(slim));
    return true;
  } catch {
    return false;
  }
}

export function addUpgrade(u: MyUpgrade): boolean {
  const { list } = readUpgrades();
  return write([u, ...list.filter((x) => x.graft_id !== u.graft_id)]);
}

export function dropUpgrade(graftId: string): boolean {
  const { list } = readUpgrades();
  return write(list.filter((x) => x.graft_id !== graftId));
}

export const shopNameFor = (graftId: string) => readUpgrades().list.find((u) => u.graft_id === graftId)?.name;
