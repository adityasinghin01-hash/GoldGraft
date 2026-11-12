import { readFileSync } from 'node:fs';
import { decide } from './switch.mjs';
const data = JSON.parse(readFileSync(process.argv[2] ?? new URL('../../../plugtests/switch_cases.json', import.meta.url), 'utf8'));
const failures = data.cases.filter(c => decide(c.config, data.public_key_b64, {
  ...c, graft_id: data.graft_id, now: data.now }) !== c.expect).map(c => c.name);
console.log(JSON.stringify({ language: 'node', cases: data.cases.length, failures, evidence: 'SYNTHETIC_SWITCH_CONFORMANCE' }));
process.exitCode = failures.length ? 1 : 0;
