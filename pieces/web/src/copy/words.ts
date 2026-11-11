// Every shared word in the app, from the frontend pack (05_WORDS_AND_LABELS.md), typed.
// Honesty labels (H) are word for word and never shortened.

export const STAGE: Record<string, { name: string; phase: number }> = {
  CREATED: { name: 'Upgrade created', phase: 1 },
  GATED: { name: 'Connected and checked', phase: 1 },
  SURVEYED: { name: 'Old PayPal pieces found', phase: 2 },
  BUILT: { name: 'Old shop running in a locked box', phase: 3 },
  RECORDED: { name: "Old shop's payments recorded", phase: 3 },
  CONTRACTED: { name: 'Money rules written', phase: 4 },
  ATTACK_PLANNED: { name: 'Tricky tests and planted bugs ready', phase: 5 },
  GRAFTED: { name: 'New code written', phase: 6 },
  REPAIRING: { name: 'Fixing what the proof found', phase: 6 },
  PROVING: { name: 'Proving every payment', phase: 7 },
  CERTIFIED: { name: 'Certified', phase: 7 },
  PARTIAL: { name: 'Partly certified', phase: 7 },
  FAILED: { name: 'Stopped: needs a person', phase: 7 },
  PR_OPEN: { name: 'Waiting for approval', phase: 8 },
  MERGED: { name: 'Approved', phase: 8 },
  SHADOW: { name: 'Testing on copies of real carts', phase: 9 },
  HEAL_1: { name: '1% of buyers on the new checkout', phase: 9 },
  HEAL_10: { name: '10% of buyers on the new checkout', phase: 9 },
  HEAL_50: { name: '50% of buyers on the new checkout', phase: 9 },
  LIVE_100: { name: 'All buyers on the new checkout', phase: 9 },
  CUTBACK: { name: 'Switched everyone back to the old checkout', phase: 9 },
  CLEANUP_PR: { name: 'Removing the old code', phase: 10 },
  DONE: { name: 'Done', phase: 10 },
  LINKS_PROVEN: { name: 'New payment links proven', phase: 3 },
  DELIVERED: { name: 'Delivered', phase: 4 },
  LANE_NO_CODE: { name: 'Switched to the no-code path', phase: 0 },
  LANE_NO_RUNTIME: { name: 'Switched to the code-only path', phase: 0 },
  LANE_MAP_ONLY: { name: 'Switched to map only', phase: 0 },
};
export const stageName = (s?: string | null) => (s ? STAGE[s]?.name ?? s : '');

export const PHASES = [
  { n: 1, name: 'Connect', meaning: 'Connect the shop and check the test keys' },
  { n: 2, name: 'Find', meaning: 'Find every old PayPal piece' },
  { n: 3, name: 'Record', meaning: 'Run the old shop and record how it handles money' },
  { n: 4, name: 'Rules', meaning: "Write the shop's money rules" },
  { n: 5, name: 'Attack', meaning: 'Plan tricky payments and plant test bugs' },
  { n: 6, name: 'Rewrite', meaning: 'Write the new code' },
  { n: 7, name: 'Prove', meaning: 'Prove every payment behaves the same' },
  { n: 8, name: 'Approve', meaning: 'You approve the change' },
  { n: 9, name: 'Go-live', meaning: 'Move buyers to the new checkout step by step' },
  { n: 10, name: 'Finish', meaning: 'Remove old code and save what we learned' },
];

export const LANE: Record<string, { name: string; meaning: string }> = {
  FULL: { name: 'Full upgrade', meaning: 'Code found, shop runs, full proof' },
  'NO-CODE': { name: 'No-code path', meaning: 'Only pasted buttons; replaced with new payment links' },
  'NO-RUNTIME': { name: 'Code-only path', meaning: 'The shop could not run, so the proof is partial' },
};

export const FAMILY: Record<string, { short: string; full: string }> = {
  WPS: { short: 'Old Buy Now buttons', full: 'Website Payments Standard (Buy Now / Add to Cart)' },
  EC_NVP: { short: 'Old Express Checkout (NVP)', full: 'Express Checkout through the old NVP API' },
  EC_SOAP: { short: 'Old Express Checkout (SOAP)', full: 'Express Checkout through the old SOAP API' },
  DIRECT_PAYMENT: { short: 'Old card payments', full: "Direct Payment: the shop's server handles card details" },
  RECURRING_NVP: { short: 'Old recurring payments', full: 'Recurring payment profiles through the NVP API' },
  BILLING_AGREEMENT: { short: 'Old billing agreements', full: 'Saved PayPal agreements; converting them needs PayPal' },
  IPN: { short: 'Old payment notifications', full: 'Instant Payment Notification (IPN)' },
  PDT: { short: 'Old payment data transfer', full: 'Payment Data Transfer (PDT)' },
  CHECKOUT_JS_V4: { short: 'Old checkout.js buttons', full: 'checkout.js (JavaScript SDK v4)' },
  JS_V5: { short: 'JavaScript SDK v5', full: 'PayPal JavaScript SDK v5, replaced by v6' },
  REST_V1: { short: 'Old REST v1 payments', full: 'PayPal REST API v1 payments' },
  SERVER_SDK_OLD: { short: 'Old server SDK', full: 'An old PayPal server-side SDK' },
  PAYFLOW: { short: 'Payflow', full: 'Payflow gateway' },
  BUTTON_HOSTED: { short: 'Buttons saved in PayPal', full: 'Buttons saved in the PayPal account (hosted)' },
};

export type Tone = 'good' | 'bad' | 'warn' | 'neutral' | 'gold';
export const GRADE: Record<string, { label: string; meaning: string; count: [string, string]; tone: Tone }> = {
  PASS: { label: 'Same as before', meaning: 'Same result as the old checkout, by every money rule.', count: ['same', 'same'], tone: 'good' },
  PASS_FIXED: { label: 'Fixed an old bug', meaning: 'New checkout is right here; your current shop has a bug.', count: ['old bug fixed', 'old bugs fixed'], tone: 'gold' },
  PROBLEM: { label: 'Problem', meaning: 'New checkout breaks a money rule here. Not certified until fixed.', count: ['problem', 'problems'], tone: 'bad' },
  UNVERIFIED: { label: 'Not proven yet', meaning: "Evidence is missing, so we don't count it as a pass.", count: ['not proven', 'not proven'], tone: 'warn' },
  'N/A': { label: "Doesn't apply", meaning: "This situation doesn't exist in this shop.", count: ["doesn't apply", "don't apply"], tone: 'neutral' },
};
export const GRADE_ORDER = ['PASS', 'PASS_FIXED', 'PROBLEM', 'UNVERIFIED', 'N/A'];

export const SCENARIO_FAMILY: Record<string, string> = {
  HAPPY: 'Normal payment', CANCEL: 'Buyer cancels at PayPal', DECLINE: 'Payment declined', PAYER_ACTION: 'Buyer must take an extra step',
  DOUBLE: 'Double click or two tabs', LOST_RESPONSE: "PayPal's answer gets lost", TAMPER: 'Someone edits the amount', PENDING: 'Payment held as pending',
  REFUND: 'Refund', REFUND_TWICE: 'Refund pressed twice', NOTIFY_FORGED: 'Fake payment notification', NOTIFY_DUP: 'Same notification twice',
  RESTART: 'Server restarts mid-payment', RENEWAL: 'Subscription renewal', EDGE_CURRENCY: 'Unusual currency or amount', PROPERTY: 'Random-input check',
};

export const MONEY_EVENT: Record<string, string> = {
  INTENT: 'Order created at PayPal', APPROVE: 'Buyer approved', AUTHORIZE: 'Money held', CAPTURE: 'Money captured', VOID: 'Hold cancelled',
  SHOP_PAID: 'Shop marked it paid', SHOP_PENDING: 'Shop marked it pending', SHOP_UNPAID: 'Shop marked it unpaid', NOTIFY: 'Notification arrived',
  NOTIFY_VERIFIED: 'Notification checked as genuine', NOTIFY_REJECTED: 'Notification rejected', REFUND: 'Refund', RECUR_SETUP: 'Recurring payment set up',
  RECUR_CHARGE: 'Recurring charge', ERROR: 'Error',
};
export const STATUS_NORM: Record<string, string> = { COMPLETED: 'completed', PENDING: 'pending', DECLINED: 'declined', REFUNDED: 'refunded', FAILED: 'failed' };
export const SOURCE: Record<string, string> = { SHOP_HTTP: 'shop web page', SHOP_DB: 'shop database', PAYPAL_CALL: 'call to PayPal', PAYPAL_LEDGER: "PayPal's own record", NOTIFICATION: 'notification from PayPal' };

export const HEAL_ACTION: Record<string, string> = { HOLD: 'Waiting for more payments', STEP_UP: 'Moved more buyers to the new checkout', CUTBACK: 'Switched everyone back to the old checkout' };
export const GUARD_EVENT: Record<string, { text: string; tone: Tone }> = {
  ATTEMPT: { text: 'started', tone: 'neutral' }, APPROVED: { text: 'approved', tone: 'neutral' }, CAPTURED: { text: 'paid ✓', tone: 'good' },
  DECLINED: { text: 'declined ✗', tone: 'bad' }, ERROR: { text: 'error ✗', tone: 'bad' }, REFUNDED: { text: 'refunded', tone: 'neutral' },
};
export const PATH: Record<string, string> = { OLD: 'old checkout', NEW: 'new checkout' };

export const RULE: Record<string, { severity: string; text: string }> = {
  R01: { severity: 'CRITICAL', text: 'An order is paid only if PayPal shows one completed capture' },
  R02: { severity: 'CRITICAL', text: 'The amount captured equals the order total' },
  R03: { severity: 'CRITICAL', text: 'The currency captured equals the order currency' },
  R04: { severity: 'CRITICAL', text: 'An unpaid order has no completed capture' },
  R05: { severity: 'CRITICAL', text: 'Retries and double clicks never charge twice' },
  R06: { severity: 'CRITICAL', text: "An order the buyer didn't approve is never confirmed" },
  R07: { severity: 'MAJOR', text: 'A pending payment is not marked paid' },
  R08: { severity: 'CRITICAL', text: 'A notification is acted on only after it is verified' },
  R09: { severity: 'MAJOR', text: 'A duplicate notification changes nothing' },
  R10: { severity: 'MAJOR', text: 'A replayed confirmation gives the same result, no second charge' },
  R11: { severity: 'CRITICAL', text: 'Refunds never exceed the capture; a second full refund is refused' },
  R12: { severity: 'CRITICAL', text: "Amounts never come from the buyer's browser" },
  R13: { severity: 'MAJOR', text: "If PayPal's callback never arrives, the shop asks PayPal" },
  R14: { severity: 'MAJOR', text: 'A restart in the middle of a payment loses nothing' },
  R15: { severity: 'MAJOR', text: 'Old payments stay on the old system, like old refunds' },
  R16: { severity: 'MINOR', text: 'Money is stored as whole numbers, never decimals' },
};
export const ruleText = (id: string, title?: string | null) => RULE[id]?.text ?? title ?? id;

export const MUTANT: Record<string, { text: string; rules: string }> = {
  M1: { text: 'Ignores the currency when checking the amount', rules: 'R03' },
  M2: { text: 'Skips checking the capture status', rules: 'R01' },
  M3: { text: "Confirms without the buyer's approval", rules: 'R06' },
  M4: { text: 'Removes the lock that stops two tabs paying twice', rules: 'R05' },
  M5: { text: 'Uses a new request id on every retry', rules: 'R05, R10' },
  M6: { text: 'Stores money as a decimal number', rules: 'R02, R16' },
  M7: { text: "Takes the amount from the buyer's browser", rules: 'R12, R02' },
  M8: { text: "Skips checking the notification's signature", rules: 'R08' },
  M9: { text: 'Reads the order id from the wrong field', rules: 'R01' },
  M10: { text: 'Looks up the signature header case-sensitively', rules: 'R08' },
  M11: { text: 'Keeps "approved, not yet captured" only in memory', rules: 'R14' },
  M12: { text: "Doesn't check refund state before refunding", rules: 'R11' },
};

export const CERT_CHECK: Record<string, { name: string; meaning: string }> = {
  SIGNATURE: { name: 'Signature matches', meaning: 'The content is exactly what was signed' },
  REKOR: { name: 'Public log matches', meaning: 'The public log (Rekor) has this exact signature' },
  LEDGER_CHAIN: { name: 'Step log unbroken', meaning: 'The step log leads here with no edits' },
  PAYPAL_REFETCH: { name: 'PayPal still agrees', meaning: 'The named payments still look the same at PayPal' },
};

export const RECIPE_STATUS: Record<string, { name: string; meaning: string }> = {
  QUARANTINE: { name: 'On trial', meaning: 'Not used on other shops yet' },
  ACTIVE: { name: 'Active', meaning: 'Used on matching shops' },
  RETIRED: { name: 'Retired', meaning: 'Stopped working, no longer used' },
};

export const ARM: Record<string, string> = { HAND: 'A teammate by hand', PAYPAL_AI_TOOLKIT: 'PayPal AI Toolkit', PLAIN_CLAUDE_CODE: 'Plain Claude Code', GOLDGRAFT: 'GoldGraft' };
export const LENS: Record<string, string> = { code: 'found in the code', runtime: 'seen while the shop ran', site: 'seen on the website', account: 'seen in the PayPal account' };
export const ENTRY_TYPE: Record<string, string> = { STAGE: 'step', ARTIFACT: 'result', MESSAGE: 'message', VERDICT: 'verdict', SWITCH: 'switch', ALERT: 'alert', COST: 'cost' };

export const AGENT_JOB: Record<string, string> = {
  Gardener: 'moves the shop through the stages and assigns work', Surveyor: 'finds every old PayPal piece',
  Builder: 'starts the old shop in a locked box and writes the robot buyer', Explorer: 'records how the old shop handles money',
  Scribe: "writes the shop's money rules", Architect: 'plans what each old piece becomes', Grafter: 'writes the new code (the only agent that writes code)',
  Adversary: 'attacks the new code and plants money bugs', Healer: 'watches go-live and can pause it (never speed it up)',
  Librarian: 'turns a success into a reusable recipe', Herald: 'writes plain-language summaries', 'Orchard Analyst': 'answers PayPal-team questions with dashboards',
  Sentinel: 'watches every agent action and halts anything unsafe', 'step-tracker': 'the stage machine', 'merchant-consent': "the merchant's approval",
};

export const MEANING: Record<string, string> = {
  old_pieces_found: "Places in the shop's code that use old PayPal",
  pieces_upgraded: "Old pieces replaced with PayPal's current version",
  scenarios_total: 'Payment situations tested',
  scenarios_pass: 'Payment situations that work the same or better',
  problems: 'Payment situations where the new code is wrong',
  proof_strength_score: 'Share of planted money bugs our tests caught',
  cost_usd: 'AI cost for this shop so far',
  minutes: 'Machine time from start to now',
  confidence: 'How sure we are; finding it more ways raises it',
  money_30d: 'Money through this spot in the last 30 days',
  stage_pct: 'Share of buyers sent to the new checkout',
  success: 'Payments seen on each checkout at this step, and how many went through',
  prob_new_not_worse: 'How sure we are new is no worse than old (2-point margin)',
  threshold: 'How sure we must be before moving more buyers',
  latency_ms: 'How long PayPal took to answer',
  recipe_confidence: 'How often this recipe worked so far',
  lc_minutes: 'Time to upgrade each shop',
  lc_usd: 'AI cost to upgrade each shop',
  paypal_only_items: 'Steps only PayPal can do, like moving saved agreements',
  cmp_minutes: 'Time each method took',
  cmp_usd: 'AI cost of each method',
  cmp_pieces_missed: 'Old PayPal pieces the method missed',
  cmp_money_bugs_left: 'Money bugs still there after the method finished',
  injection_attempts_blocked: "Hidden tricks in the shop's files, all blocked",
  secrets_found: 'Secrets leaked into prompts, logs or code (must be 0)',
  ledger_root: 'Fingerprint of the whole step log; any edit changes it',
  equivalent_dropped: 'Planted bugs that change nothing visible; not counted',
  killed: 'Planted bugs caught by at least one test',
};

export const H = {
  sandboxTop: 'PayPal sandbox only',
  sample: 'Sample data',
  sampleTitle: 'This is stand-in or mock data, not a recording of a real run.',
  mock: 'Mock mode: showing saved sample data, not a live system.',
  testShopsOnly: "Shows GoldGraft's test shops only.",
  sandboxKeys: 'Sandbox keys only. Live keys are refused.',
  noLiveChange: 'Nothing in your live shop changes until you approve.',
  sampleCert: 'This is a sample certificate, not a real signed one.',
  tamperedCopy: 'This copy has one number changed on purpose, for the demo.',
  demoOnly: 'DEMO ONLY',
  measured: '(measured in this browser)',
};

export const WAIT = {
  waking: 'Starting up… this can take a minute',
  thinking: 'Thinking…',
  connecting: 'Connecting…',
  reconnecting: 'Reconnecting…',
};

export const NAV_APP = [
  { label: 'Start', to: '/check' },
  { label: 'My upgrades', to: '/my' },
  { label: 'Recipes', to: '/bank' },
  { label: 'PayPal team', to: '/orchard' },
  { label: 'Security', to: '/security/run-1' },
  { label: 'Compare', to: '/compare' },
];

export const GRAFT_TABS = [
  { label: 'Progress', path: '' },
  { label: 'Old pieces', path: '/map' },
  { label: 'Code changes', path: '/changes' },
  { label: 'Payment tests', path: '/union' },
  { label: 'Proof', path: '/proof' },
  { label: 'Go-live', path: '/heal' },
];
