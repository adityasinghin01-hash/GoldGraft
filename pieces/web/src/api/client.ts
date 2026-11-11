import { config, isMock } from '../config';
import type {
  CertificateVerifyResult, Certificate, CmelView, Comparison, Connection, GauntletRun, Graft, HealFrame, HealState,
  InjectFaultResult, LearningCurve, LedgerEntry, OrchardAnswer, OrchardView, Problem, ProbeResult, ProofView,
  RecipeList, RootMap, ScenarioList, Shop,
} from './types';
import { mockApi } from './mock/mockApi';

/** Every failure the UI can show, already in the pack's words (05 §24). */
export class ApiError extends Error {
  constructor(
    public kind: 'problem' | 'timeout' | 'network' | 'unexpected',
    public status: number,
    public title: string,
    public detail?: string,
    public seconds?: number,
  ) {
    super(title);
  }
}

export type FeedStatus = 'connecting' | 'live' | 'reconnecting' | 'ended';
export type Feed = { close: () => void };

export interface GoldGraftApi {
  probe(url: string): Promise<ProbeResult>;
  createShop(body: { name?: string; repo?: string; site?: string }, key: string): Promise<Shop>;
  connect(shopId: string, body: Record<string, string>, key: string): Promise<Connection>;
  startGraft(shopId: string, key: string): Promise<Graft>;
  graft(id: string): Promise<Graft>;
  rootmap(id: string): Promise<RootMap>;
  scenarios(id: string): Promise<ScenarioList>;
  cmel(id: string, scenario: string): Promise<CmelView>;
  proof(id: string): Promise<ProofView>;
  certificate(id: string): Promise<Certificate>;
  verify(id: string): Promise<CertificateVerifyResult>;
  heal(id: string): Promise<HealState>;
  injectFault(id: string, op: string, key: string): Promise<InjectFaultResult>;
  recipes(): Promise<RecipeList>;
  learningCurve(): Promise<LearningCurve>;
  orchard(): Promise<OrchardView>;
  ask(question: string, key: string): Promise<OrchardAnswer>;
  gauntlet(runId: string): Promise<GauntletRun>;
  comparison(): Promise<Comparison>;
  ledgerFeed(id: string, onEvent: (e: LedgerEntry) => void, onStatus: (s: FeedStatus) => void): Feed;
  healFeed(id: string, onFrame: (f: HealFrame) => void, onStatus: (s: FeedStatus) => void): Feed;
}

// ── waking line (W7): the first live request may wake a sleeping server ──
type WakeListener = (waking: boolean) => void;
const wakeListeners = new Set<WakeListener>();
export const onWaking = (l: WakeListener) => { wakeListeners.add(l); return () => { wakeListeners.delete(l); }; };
let firstRequest = true;

async function request<T>(method: 'GET' | 'POST', path: string, opts: { body?: unknown; key?: string; limit?: number } = {}): Promise<T> {
  const isFirst = firstRequest;
  firstRequest = false;
  const limit = isFirst ? config.timeouts.firstWake : opts.limit ?? (method === 'GET' ? config.timeouts.get : config.timeouts.post);
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), limit);
  const wakeTimer = isFirst ? setTimeout(() => wakeListeners.forEach((l) => l(true)), 3000) : 0;
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (method === 'POST') headers['Content-Type'] = 'application/json';
  if (opts.key) headers['Idempotency-Key'] = opts.key;
  let res: Response;
  try {
    res = await fetch(`${config.apiBase}${path}`, { method, headers, body: opts.body === undefined ? undefined : JSON.stringify(opts.body), signal: ctrl.signal });
  } catch (e) {
    if ((e as Error).name === 'AbortError') throw new ApiError('timeout', 0, `No answer after ${Math.round(limit / 1000)} s.`, undefined, Math.round(limit / 1000));
    throw new ApiError('network', 0, `Can't reach GoldGraft at ${config.apiBase}.`);
  } finally {
    clearTimeout(timer);
    if (isFirst) { clearTimeout(wakeTimer); wakeListeners.forEach((l) => l(false)); }
  }
  if (res.ok) return (await res.json()) as T;
  let problem: Problem | null = null;
  try { problem = (await res.json()) as Problem; } catch { /* non-JSON body */ }
  if (!problem?.title) throw new ApiError('unexpected', res.status, `Error ${res.status}`, 'The API sent an unexpected answer.');
  if (res.status === 409) throw new ApiError('problem', 409, 'Already sent with different details. Start again.');
  if (res.status >= 500) throw new ApiError('problem', res.status, 'GoldGraft had a problem. Try again in a minute.', problem.detail);
  throw new ApiError('problem', res.status, problem.title, problem.detail);
}

const enc = encodeURIComponent;

function sseUrl(path: string) {
  const u = `${config.apiBase}${path}`;
  return config.sseSpeed ? `${u}${u.includes('?') ? '&' : '?'}speed=${enc(config.sseSpeed)}` : u;
}

/** Live feed rules (03 §E): named events, dedupe by seq, end after 3 empty reconnects. */
function openFeed<T extends { seq: number }>(path: string, event: string, onData: (d: T) => void, onStatus: (s: FeedStatus) => void, isEnd?: (d: T) => boolean): Feed {
  let maxSeq = 0;
  let emptyReconnects = 0;
  let gotSinceError = false;
  let closed = false;
  onStatus('connecting');
  const es = new EventSource(sseUrl(path));
  const end = () => { if (closed) return; closed = true; es.close(); onStatus('ended'); };
  es.addEventListener(event, (m) => {
    let d: T;
    try { d = JSON.parse((m as MessageEvent).data) as T; } catch { return; }
    if (typeof d.seq === 'number' && d.seq <= maxSeq) return;
    maxSeq = d.seq ?? maxSeq;
    gotSinceError = true;
    emptyReconnects = 0;
    onStatus('live');
    onData(d);
    if (isEnd?.(d)) end();
  });
  es.onerror = () => {
    if (closed) return;
    if (!gotSinceError) emptyReconnects++;
    gotSinceError = false;
    if (emptyReconnects >= 3) end(); else onStatus('reconnecting');
  };
  return { close: () => { closed = true; es.close(); } };
}

const liveApi: GoldGraftApi = {
  probe: (url) => request('POST', '/probe', { body: { url }, limit: config.timeouts.probe }),
  createShop: (body, key) => request('POST', '/shops', { body, key }),
  connect: (shopId, body, key) => request('POST', `/shops/${enc(shopId)}/connect`, { body, key, limit: config.timeouts.connect }),
  startGraft: (shopId, key) => request('POST', `/shops/${enc(shopId)}/graft`, { body: {}, key }),
  graft: (id) => request('GET', `/grafts/${enc(id)}`),
  rootmap: (id) => request('GET', `/grafts/${enc(id)}/rootmap`),
  scenarios: (id) => request('GET', `/grafts/${enc(id)}/scenarios`),
  cmel: (id, scenario) => request('GET', `/grafts/${enc(id)}/cmel?scenario=${enc(scenario)}`),
  proof: (id) => request('GET', `/grafts/${enc(id)}/proof`),
  certificate: (id) => request('GET', `/certificates/${enc(id)}`),
  verify: (id) => request('POST', `/certificates/${enc(id)}/verify`, { limit: config.timeouts.verify }),
  heal: (id) => request('GET', `/heal/${enc(id)}`),
  injectFault: (id, op, key) => request('POST', `/heal/${enc(id)}/inject-fault`, { body: { mutant_op: op }, key }),
  recipes: () => request('GET', '/recipes'),
  learningCurve: () => request('GET', '/learning-curve'),
  orchard: () => request('GET', '/orchard'),
  ask: (question, key) => request('POST', '/orchard/ask', { body: { question }, key, limit: config.timeouts.ask }),
  gauntlet: (runId) => request('GET', `/security/gauntlet/${enc(runId)}`),
  comparison: () => request('GET', '/comparison'),
  ledgerFeed: (id, onEvent, onStatus) =>
    openFeed<LedgerEntry>(`/grafts/${enc(id)}/events`, 'ledger', onEvent, onStatus,
      (e) => e.type === 'STAGE' && (e.payload as { to_stage?: string } | undefined)?.to_stage === 'DONE'),
  healFeed: (id, onFrame, onStatus) => openFeed<HealFrame>(`/heal/${enc(id)}`, 'heal', onFrame, onStatus),
};

export const api: GoldGraftApi = isMock ? mockApi : liveApi;
