// Aliases only: every shape comes from the generated contract (never hand-written).
import type { components } from '../contracts/goldgraft-api';
type S = components['schemas'];
export type Graft = S['Graft'];
export type GraftCard = S['GraftCard'];
export type LedgerEntry = S['LedgerEntry'];
export type RootMap = S['RootMap'];
export type Touchpoint = S['Touchpoint'];
export type ScenarioList = S['ScenarioList'];
export type ScenarioRow = S['ScenarioRow'];
export type Verdict = S['Verdict'];
export type CmelView = S['CmelView'];
export type MoneyEvent = S['MoneyEvent'];
export type ProofView = S['ProofView'];
export type Certificate = S['Certificate'];
export type CertificateVerifyResult = S['CertificateVerifyResult'];
export type HealState = S['HealState'];
export type HealFrame = HealState & { seq: number };
export type GuardEvent = S['GuardEvent'];
export type RecipeList = S['RecipeList'];
export type LearningCurve = S['LearningCurve'];
export type OrchardView = S['OrchardView'];
export type OrchardAnswer = S['OrchardAnswer'];
export type GauntletRun = S['GauntletRun'];
export type Comparison = S['Comparison'];
export type ProbeResult = S['ProbeResult'];
export type Shop = S['Shop'];
export type Connection = S['Connection'];
export type InjectFaultResult = S['InjectFaultResult'];
export type Money = S['Money'];
export type Problem = { type?: string; title: string; status: number; detail?: string; instance?: string };

// Integrated agent runs (local agents service, 12 Nov). Not in the published v1 contract yet.
export type CodeChange = { path: string; before: string; after: string; author: 'model' | 'library' };
export type OpenItem = { touchpoint: string; family: string; location: { file: string; line: number } };
/** A money bug GoldGraft planted in the AI-written code, and whether its code review caught it. */
export type PlantedBug = {
  id: string; rule: string; what: string; file: string | null; applied: boolean;
  caught?: boolean; refusal?: string | null;
};
export type PlantedBugCheck = {
  run_id: string; original_passes_review: boolean; planted: number; caught: number;
  mutants: PlantedBug[]; note: string;
};
export type ChangeSet = {
  files: CodeChange[];
  mutations?: PlantedBugCheck;
  open_items: OpenItem[];
  lint: Record<string, { ok: boolean; error: string | null }> | null;
  /** Sample mode: the real run this recording comes from. */
  recorded_from?: string;
};
/** One agent step of an integrated run, with an honest label for what its input was. */
export type AgentStep = {
  task: string;
  attempt: number;
  role: string;
  operation: string | null;
  model: string | null;
  escalated: boolean;
  passed: boolean;
  issue: string | null;
  cost_usd: number;
  seconds: number | null;
  input: 'real' | 'mixed' | 'sample';
  input_note: string;
  outputs: { schema: string; summary: string }[];
};
export type AgentsView = {
  graft_id: string;
  status: string | null;
  agents: AgentStep[];
  /** Sample mode: the real run this recording comes from. */
  recorded_from?: string;
};
export type AgentRun = {
  run_id: string;
  shop: string;
  status: string;
  roles_passed: number;
  roles_participated: number;
  spent_usd: number;
  finished_at: string | null;
};
