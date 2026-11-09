/**
 * Graft Switch Library for Node.js / JavaScript (pieces/switch-libs/node).
 *
 * Implements deterministic stage cutover and origin routing for payment operations.
 * Uses native crypto.verify for Ed25519 signatures, enforces fail-safe expiration and origin rules,
 * and passes all shared cases in plugtests/switch_cases.json.
 */

import crypto from 'node:crypto';

const FOLLOW_UPS = new Set(['REFUND', 'VOID', 'RENEWAL', 'CAPTURE']);

/**
 * Serializes config into canonical JSON bytes without signature.
 */
export function canonicalSignedBytes(config) {
  const body = {};
  const sortedKeys = Object.keys(config).filter(k => k !== 'signature').sort();
  for (const k of sortedKeys) {
    body[k] = config[k];
  }
  return Buffer.from(JSON.stringify(body), 'utf8');
}

/**
 * Verifies Ed25519 signature, matching graft_id, and expiration.
 */
export function isConfigValid(config, publicKeyB64, graftId, now) {
  try {
    if (!config || typeof config !== 'object') return false;
    if (config.graft_id !== graftId) return false;

    // Expiration check
    const expiresAt = new Date(config.expires_at);
    if (now >= expiresAt) return false;

    // Ed25519 public key in SPKI DER format
    const rawPub = Buffer.from(publicKeyB64, 'base64');
    // Ed25519 SPKI header: 302a300506032b6570032100 + 32 bytes raw public key
    const spkiPrefix = Buffer.from('302a300506032b6570032100', 'hex');
    const spkiDer = Buffer.concat([spkiPrefix, rawPub]);

    const publicKey = crypto.createPublicKey({
      key: spkiDer,
      format: 'der',
      type: 'spki'
    });

    const sig = Buffer.from(config.signature, 'base64');
    const data = canonicalSignedBytes(config);

    return crypto.verify(null, data, publicKey, sig);
  } catch (err) {
    return false;
  }
}

/**
 * Computes deterministic percentage bucket (0-99).
 */
export function deterministicBucket(graftId, orderRef) {
  const hash = crypto.createHash('sha256').update(`${graftId}:${orderRef}`).digest('hex');
  const slice = hash.substring(0, 8);
  return parseInt(slice, 16) % 100;
}

/**
 * Evaluates payment routing: 'NEW' (Orders v2) vs 'OLD' (NVP/SOAP).
 */
export function decideRoute(config, publicKeyB64, { graftId, orderRef, now, action = 'PAY', origin = null }) {
  if (FOLLOW_UPS.has(action)) {
    return origin === 'NEW' ? 'NEW' : 'OLD';
  }

  if (!config || !isConfigValid(config, publicKeyB64, graftId, now)) {
    return 'OLD';
  }

  const stagePct = config.stage_pct || 0;
  const bucket = deterministicBucket(graftId, orderRef);
  return bucket < stagePct ? 'NEW' : 'OLD';
}

