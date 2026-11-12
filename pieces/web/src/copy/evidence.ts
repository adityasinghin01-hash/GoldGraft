// Measured results from GoldGraft's own agent tests (real AI model calls, 11 Nov 2026).
// Source: ~/reports/goldgraft-all-agents-20261111/STATUS.json and
// docs/engineering/plan5/FINAL_AGENTS_REPORT_2026-11-11.md. Never edit by hand without a new run.

export type AgentResult = { name: string; job: string; passed: number; total: number };

export const AGENT_RESULTS: AgentResult[] = [
  { name: 'Surveyor', job: 'finds every old PayPal piece', passed: 49, total: 49 },
  { name: 'Gardener', job: 'moves the shop through the stages', passed: 54, total: 56 },
  { name: 'Builder', job: 'starts the old shop in a locked box', passed: 35, total: 36 },
  { name: 'Explorer', job: 'records how the old shop handles money', passed: 35, total: 36 },
  { name: 'Scribe', job: "writes the shop's money rules", passed: 28, total: 28 },
  { name: 'Architect', job: 'plans what each old piece becomes', passed: 27, total: 28 },
  { name: 'Grafter', job: 'writes the new code', passed: 24, total: 29 },
  { name: 'Adversary', job: 'attacks the new code with planted bugs', passed: 28, total: 28 },
  { name: 'Healer', job: 'watches go-live and can pause it', passed: 24, total: 24 },
  { name: 'Librarian', job: 'turns a success into a recipe', passed: 23, total: 24 },
  { name: 'Herald', job: 'writes plain summaries', passed: 32, total: 32 },
  { name: 'Orchard Analyst', job: "answers PayPal's questions", passed: 20, total: 20 },
  { name: 'Sentinel', job: 'halts anything unsafe', passed: 32, total: 32 },
];

export const AGENT_TOTALS = {
  passed: AGENT_RESULTS.reduce((a, r) => a + r.passed, 0),
  total: AGENT_RESULTS.reduce((a, r) => a + r.total, 0),
  tricksHeld: 37,
  tricksTotal: 37,
  spendUsd: '3.35',
};
