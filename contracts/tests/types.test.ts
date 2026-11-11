import type { MoneyV1, SwitchConfigV1, RawCaptureV1, LedgerEntryV1, RawExchange } from '../ts/goldgraft-contracts';

const money: MoneyV1 = {minor: 1999, currency: 'USD'};
const zeroDecimal: MoneyV1 = {minor: 1999, currency: 'JPY'};
// @ts-expect-error Currency is the confirmed PayPal code union.
const invalidCurrency: MoneyV1 = {minor: 1, currency: 'ZZZ'};
// @ts-expect-error Unknown fields must not appear on money.
const extraField: MoneyV1 = {minor: 1, currency: 'USD', extra: true};
const stage: SwitchConfigV1['stage_pct'] = 10;
// @ts-expect-error Rollout stages are a literal union.
const invalidStage: SwitchConfigV1['stage_pct'] = 5;
const capture: RawCaptureV1 = {
  graft_id: 'graft-1', run_id: 'run-1', variant: 'OLD', scenario_id: 'happy',
  exchanges: [{seq: 0, t_ms: 0, direction: 'BROWSER_TO_SHOP', method: 'GET',
    url: 'https://shop.example.test/', headers: {}, body_text: ''}],
};
void [money, zeroDecimal, invalidCurrency, extraField, stage, invalidStage, capture];

// @ts-expect-error Common ledger fields must survive conditional-schema generation.
const incompleteLedger: LedgerEntryV1 = {payload_ref: 'r2://artifacts/map'};
// @ts-expect-error Common exchange fields must survive conditional-schema generation.
const incompleteExchange: RawExchange = {body_text: ''};
void [incompleteLedger, incompleteExchange];

const ledger: LedgerEntryV1 = {
  seq: 0, graft_id: 'graft-1', ts: '2026-11-02T09:00:00Z', type: 'ARTIFACT',
  producer: {kind: 'service', name: 'fixture', version: '1'}, inputs: [],
  payload: {minor: 1999, currency: 'USD'}, payload_hash: '0'.repeat(64),
  schema: 'Money/1', prev_hash: '0'.repeat(64), entry_hash: '0'.repeat(64),
};
// @ts-expect-error A ledger envelope cannot carry both payload forms.
const bothPayloads: LedgerEntryV1 = {...ledger, payload_ref: 'r2://map'};
const rawArray: RawExchange = {
  seq: 0, t_ms: 0, direction: 'PAYPAL_TO_SHOP', method: 'POST',
  url: 'https://shop.example.test/', headers: {}, body_json: ['synthetic', null, true, 10],
};
const rawNull: RawExchange = {...rawArray, body_json: null};
// @ts-expect-error Both body encodings cannot coexist.
const bothBodies: RawExchange = {...rawArray, body_text: ''};
void [ledger, bothPayloads, rawArray, rawNull, bothBodies];

import type {
  AgentResultV1, ChangeListV2, ModelTurnResultV1, TaskContextV1,
  PublicProofViewV1, IssueV1,
} from '../ts/goldgraft-contracts';

declare const plan5Context: TaskContextV1;
// @ts-expect-error Generation is an integer-valued number, never a boolean.
const boolGeneration: TaskContextV1 = {...plan5Context, generation: true};
// @ts-expect-error Logical roles are a closed catalog.
const unknownRole: TaskContextV1 = {...plan5Context, role: 'Unregistered'};
declare const turn: ModelTurnResultV1;
// @ts-expect-error A final result cannot carry tool calls or omit the final artifact.
const mixedTurn: ModelTurnResultV1 = {...turn, kind: 'final', final_artifact_ref: null};
declare const change: ChangeListV2;
// @ts-expect-error Snapshot provenance cannot invent a Git branch.
const fakeGit: ChangeListV2 = {...change, provenance: 'snapshot', branch: 'invented'};
declare const result: AgentResultV1;
declare const heldIssue: IssueV1;
// @ts-expect-error A completed result cannot carry a blocking issue.
const falseCompletion: AgentResultV1 = {...result, outcome: 'completed', issue: heldIssue};
declare const publicProof: PublicProofViewV1;
// @ts-expect-error Public proof has no private source-reference field.
const privateProof: PublicProofViewV1 = {...publicProof, source_snapshot_ref: 'private:source'};
void [boolGeneration, unknownRole, mixedTurn, fakeGit, falseCompletion, privateProof];
