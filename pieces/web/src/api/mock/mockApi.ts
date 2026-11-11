// Sample mode (03 §G): the stand-in's own saved answers, same signatures as the live client.
import type { FeedStatus, GoldGraftApi } from '../client';
import { ApiError } from '../errors';
import type { HealFrame, LedgerEntry } from '../types';
import graft from './data/GET_graft.json';
import rootmap from './data/GET_rootmap.json';
import scenarios from './data/GET_scenarios.json';
import cmelPending from './data/GET_cmel_pending.json';
import proof from './data/GET_proof.json';
import certificate from './data/GET_certificate.json';
import verifyOk from './data/POST_certificate_verify_ok.json';
import verifyTampered from './data/POST_certificate_verify_tampered.json';
import inject from './data/POST_heal_inject_fault.json';
import recipes from './data/GET_recipes.json';
import curve from './data/GET_learning_curve.json';
import orchard from './data/GET_orchard.json';
import ask from './data/POST_orchard_ask.json';
import gauntlet from './data/GET_gauntlet.json';
import comparison from './data/GET_comparison.json';
import probe from './data/POST_probe.json';
import shops from './data/POST_shops.json';
import connect from './data/POST_shops_connect.json';
import startGraft from './data/POST_shops_graft.json';
import notFound from './data/ERROR_404_graft.json';
import unionOldBug from './data/union_pending_old_bug.json';
import healSequence from './data/heal_cutback_sequence.json';
import ledgerTxt from './data/SSE_graft_events.txt?raw';

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));
const clone = <T,>(x: T): T => JSON.parse(JSON.stringify(x)) as T;
const GRAFT = 'demo-1';

async function get<T>(x: unknown, ms = 300): Promise<T> {
  await wait(ms);
  return clone(x) as T;
}

function parseSse<T>(txt: string): T[] {
  const out: T[] = [];
  for (const block of txt.split(/\n\n+/)) {
    const line = block.split('\n').find((l) => l.startsWith('data: '));
    if (!line) continue;
    try { out.push(JSON.parse(line.slice(6)) as T); } catch { /* skipped */ }
  }
  return out;
}

const LEDGER = parseSse<LedgerEntry>(ledgerTxt);
let injectedAt = 0;
const injectListeners = new Set<() => void>();

async function requireDemo(id: string) {
  if (id !== GRAFT) {
    await wait(300);
    const p = clone(notFound) as { title: string; detail?: string; status: number };
    throw new ApiError('problem', p.status, p.title, (p.detail ?? '').replace(/demo-1|\{graft_id\}/g, id) || `No graft ${id}`);
  }
}

export const mockApi: GoldGraftApi = {
  probe: async (url) => {
    await wait(2000);
    return { ...clone(probe), files_or_pages: [url] } as never;
  },
  createShop: async (body) => { await wait(500); return { ...clone(shops), ...body } as never; },
  connect: async (_shopId, body) => {
    await wait(1600);
    const c = clone(connect) as { checks?: Record<string, boolean> } & Record<string, unknown>;
    if (c.checks) { c.checks.nvp_ok = !!body.nvp_user; c.checks.webhook_ok = !!body.webhook_id; }
    else { (c as Record<string, unknown>).nvp_ok = !!body.nvp_user; (c as Record<string, unknown>).webhook_ok = !!body.webhook_id; }
    return c as never;
  },
  startGraft: async () => get(startGraft, 700),
  graft: async (id) => { await requireDemo(id); return get(graft); },
  rootmap: async (id) => { await requireDemo(id); return get(rootmap); },
  scenarios: async (id) => {
    await requireDemo(id);
    const s = clone(scenarios) as { scenarios: Array<{ scenario: { id: string }; verdict?: unknown }> };
    const row = s.scenarios.find((r) => r.scenario.id === 'pending');
    if (row) row.verdict = clone((unionOldBug as { verdict: unknown }).verdict);
    return get(s);
  },
  cmel: async (id, scenario) => {
    await requireDemo(id);
    if (scenario === 'pending') return get((unionOldBug as { cmel: unknown }).cmel, 450);
    return get({ ...clone(cmelPending), scenario_id: scenario }, 450);
  },
  proof: async (id) => { await requireDemo(id); return get(proof); },
  certificate: async (id) => {
    await wait(300);
    if (id !== 'cert-demo' && id !== 'cert-demo-tampered') {
        throw new ApiError('problem', 404, 'Certificate not found', `No certificate ${id}`);
    }
    return { ...clone(certificate), cert_id: id } as never;
  },
  verify: async (id) => get(id === 'cert-demo-tampered' ? verifyTampered : verifyOk, 1200),
  heal: async (id) => {
    await requireDemo(id);
    const first = (healSequence as { frames: unknown[] }).frames[0] as Record<string, unknown>;
    const { seq: _seq, ...rest } = first;
    void _seq;
    return get(rest);
  },
  injectFault: async () => {
    await wait(600);
    injectedAt = Date.now();
    injectListeners.forEach((l) => l());
    return clone(inject) as never;
  },
  recipes: async () => get(recipes),
  learningCurve: async () => get(curve),
  orchard: async () => get(orchard),
  ask: async (question) => { await wait(1500); return { ...clone(ask), question } as never; },
  gauntlet: async (runId) => get({ ...clone(gauntlet), run_id: runId }),
  comparison: async () => get(comparison),

  ledgerFeed: (_id, onEvent, onStatus: (s: FeedStatus) => void) => {
    let i = 0;
    let stopped = false;
    onStatus('connecting');
    const timer = setInterval(() => {
      if (stopped) return;
      if (i >= LEDGER.length) { clearInterval(timer); onStatus('ended'); return; }
      onStatus('live');
      onEvent(clone(LEDGER[i++]));
    }, 500);
    return { close: () => { stopped = true; clearInterval(timer); } };
  },

  healFeed: (_id, onFrame, onStatus) => {
    const frames = (healSequence as { frames: HealFrame[] }).frames;
    let i = 0;
    let stopped = false;
    const timers: number[] = [];
    onStatus('connecting');
    const push = (f: HealFrame) => { if (!stopped) { onStatus('live'); onFrame(clone(f)); } };
    const next = () => {
      if (stopped || i >= 3) return;
      push(frames[i++]);
      if (i < 3) timers.push(window.setTimeout(next, 2000));
    };
    timers.push(window.setTimeout(next, 400));
    const onInject = () => { timers.push(window.setTimeout(() => { if (frames[3]) push(frames[3]); }, 3000)); };
    injectListeners.add(onInject);
    if (injectedAt && Date.now() - injectedAt < 3000) onInject();
    return { close: () => { stopped = true; timers.forEach(clearTimeout); injectListeners.delete(onInject); } };
  },
};

