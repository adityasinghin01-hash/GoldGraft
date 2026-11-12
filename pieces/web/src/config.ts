// Read once from the Vite environment. Empty VITE_API_BASE = sample (mock) mode.
const env = import.meta.env;
const base = ((env.VITE_API_BASE as string | undefined) ?? '').replace(/\/$/, '');

export const config = {
  apiBase: base,
  sseSpeed: (env.VITE_SSE_SPEED as string | undefined) || '',
  demoTools: env.VITE_DEMO_TOOLS === 'true' || !base, // sample mode shows the demo tools too
  // STAND-IN: ids the stand-in API serves; used only where the pack (10) says so
  standInIds: { graftId: 'demo-1', certId: 'cert-demo', tamperedCertId: 'cert-demo-tampered', gauntletRunId: 'run-1' },
  timeouts: { get: 15_000, probe: 45_000, ask: 30_000, connect: 20_000, verify: 20_000, post: 15_000, firstWake: 90_000 },
  CERT_MIN_PROOF_STRENGTH: 0.95,
};

export const isMock = !base;
