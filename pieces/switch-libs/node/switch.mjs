import { createHash, createPublicKey, verify } from 'node:crypto';

const follows = new Set(['REFUND', 'VOID', 'RENEWAL', 'CAPTURE']);
const fields = ['expires_at', 'graft_id', 'origin_rules', 'signature', 'stage_pct', 'version'];

export function signedBytes(config) {
  const body = Object.fromEntries(Object.keys(config).filter(k => k !== 'signature').sort().map(k => [k, config[k]]));
  return Buffer.from(JSON.stringify(body), 'utf8');
}

function decoded(value, size) {
  if (typeof value !== 'string') throw new Error('invalid_base64');
  const bytes = Buffer.from(value, 'base64');
  if (bytes.length !== size || bytes.toString('base64') !== value) throw new Error('invalid_base64');
  return bytes;
}

export function timestamp(value) {
  if (value instanceof Date) {
    if (!Number.isFinite(value.valueOf())) throw new Error('invalid_timestamp');
    return BigInt(value.valueOf()) * 1000n;
  }
  const m = typeof value === 'string' && /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(Z|([+-])(\d{2}):(\d{2}))$/.exec(value);
  if (!m) throw new Error('invalid_timestamp');
  const [year, month, day, hour, minute, second] = m.slice(1, 7).map(Number);
  if (year < 1 || month < 1 || month > 12 || day < 1 || hour > 23 || minute > 59 || second > 59 || Number(m[10] ?? 0) > 23 || Number(m[11] ?? 0) > 59) throw new Error('invalid_timestamp');
  const date = new Date(0);
  date.setUTCFullYear(year, month - 1, day);
  date.setUTCHours(hour, minute, second, 0);
  if (date.getUTCMonth() !== month - 1 || date.getUTCDate() !== day) throw new Error('invalid_timestamp');
  const offset = (Number(m[10] ?? 0) * 60 + Number(m[11] ?? 0)) * 60 * (m[9] === '-' ? -1 : 1);
  return BigInt(date.valueOf() / 1000 - offset) * 1000000n + BigInt((m[7] ?? '').padEnd(6, '0'));
}

export function configValid(config, key, graftId, now) {
  try {
    if (!config || Array.isArray(config) || Object.keys(config).sort().join('|') !== fields.join('|') ||
        typeof config.graft_id !== 'string' || !config.graft_id || config.graft_id !== graftId ||
        !Number.isInteger(config.stage_pct) || ![0, 1, 10, 50, 100].includes(config.stage_pct) ||
        !Number.isSafeInteger(config.version) || config.version <= 0 ||
        !Array.isArray(config.origin_rules) || !config.origin_rules.every(s => typeof s === 'string' && s.length)) return false;
    const publicKey = createPublicKey({ format: 'jwk', key: { kty: 'OKP', crv: 'Ed25519', x: decoded(key, 32).toString('base64url') } });
    return verify(null, signedBytes(config), publicKey, decoded(config.signature, 64)) && timestamp(now) < timestamp(config.expires_at);
  } catch { return false; }
}

export function bucket(graftId, orderRef) {
  return Number.parseInt(createHash('sha256').update(`${graftId}:${orderRef}`, 'utf8').digest('hex').slice(0, 8), 16) % 100;
}

export function decide(config, key, { graft_id, order_ref, now, action = 'PAY', origin = null }) {
  if (follows.has(action)) return origin === 'NEW' ? 'NEW' : 'OLD';
  if (!configValid(config, key, graft_id, now)) return 'OLD';
  return bucket(graft_id, order_ref) < config.stage_pct ? 'NEW' : 'OLD';
}

export function routeExisting(action, origin) {
  if (!follows.has(action) || !['OLD', 'NEW'].includes(origin)) throw new Error('stored_origin_required');
  return origin;
}

export class VerifiedConfigCache {
  #config = null;
  constructor(graftId, key) { this.graftId = graftId; this.key = key; }
  accept(config, now) {
    if (!configValid(config, this.key, this.graftId, now)) return false;
    if (this.#config && (config.version < this.#config.version ||
        (config.version === this.#config.version && !signedBytes(config).equals(signedBytes(this.#config))))) return false;
    this.#config = structuredClone(config);
    return true;
  }
  current(now) { return configValid(this.#config, this.key, this.graftId, now) ? structuredClone(this.#config) : null; }
}

// Preserve the team's existing public Node API while adding the strict/cache API.
export const canonicalSignedBytes = signedBytes;
export const isConfigValid = configValid;
export const deterministicBucket = bucket;
export function decideRoute(config, key, { graftId, orderRef, now, action = 'PAY', origin = null }) {
  return decide(config, key, { graft_id: graftId, order_ref: orderRef, now, action, origin });
}
