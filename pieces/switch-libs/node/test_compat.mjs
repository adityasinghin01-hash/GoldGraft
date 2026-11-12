// Existing camelCase API and new strict API must satisfy the same frozen cases.
import { readFileSync } from 'node:fs';
import {
  decideRoute, isConfigValid, canonicalSignedBytes, deterministicBucket,
  decide, configValid, signedBytes, bucket,
} from './switch.mjs';

const data = JSON.parse(readFileSync(new URL('../../../plugtests/switch_cases.json', import.meta.url), 'utf8'));
for (const item of data.cases) {
  const options = {graftId:data.graft_id, orderRef:item.order_ref, now:new Date(data.now), action:item.action, origin:item.origin};
  if (decideRoute(item.config, data.public_key_b64, options) !== item.expect) throw Error(item.name);
  if (decide(item.config, data.public_key_b64, {...item, graft_id:data.graft_id, now:data.now}) !== item.expect) throw Error(item.name);
  if (isConfigValid(item.config, data.public_key_b64, data.graft_id, options.now) !== configValid(item.config, data.public_key_b64, data.graft_id, options.now)) throw Error('validation API drift');
  if (deterministicBucket(data.graft_id,item.order_ref) !== bucket(data.graft_id,item.order_ref)) throw Error('bucket API drift');
  if (item.config && !canonicalSignedBytes(item.config).equals(signedBytes(item.config))) throw Error('signing API drift');
}
console.log(JSON.stringify({compatibility_cases:data.cases.length, status:'PASS'}));
