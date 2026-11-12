// Every word on the landing page. Passed through the humanizer skill (11–12 Nov 2026):
// no em dashes, no AI vocabulary, plain words a shop owner would use.
// Facts carry their source; anything that is a sample says so.
//
// Heading rule (landing and app): a heading is one phrase in sentence case with no full stop.
// Brand names keep their own case (PayPal, GoldGraft). A display heading may break into a main
// line and a smaller continuation line, which carries on the same phrase in lower case.
// Body text is sentences, with full stops.

export const SOURCES = {
  wps: {
    label: 'PayPal developer docs',
    href: 'https://developer.paypal.com/limited-release/multiparty/wps-deprecation',
  },
  call: {
    label: 'Q4 2025 earnings call, Feb 2026',
    href: 'https://www.marketbeat.com/instant-alerts/paypal-q4-earnings-call-highlights-2026-02-03/',
  },
  code: {
    label: 'Our GitHub code search, Nov 2026. It counts files, not shops.',
    href: 'https://github.com/search?q=%22cgi-bin%2Fwebscr%22&type=code',
  },
  devpost: { label: 'PayPal AI Hackathon 2026', href: 'https://paypalaihackathon.devpost.com/' },
  repo: { label: 'GitHub repository', href: 'https://github.com/adityasinghin01-hash/GoldGraft' },
  licence: { label: 'MIT licence', href: 'https://github.com/adityasinghin01-hash/GoldGraft/blob/main/LICENSE' },
} as const;

export const NAV = [
  { label: 'Why now', href: '#proof' },
  { label: 'What it does', href: '#features' },
  { label: 'How it works', href: '#steps' },
  { label: 'Questions', href: '#faq' },
] as const;

export const HERO = {
  titleA: "PayPal's new checkout",
  titleB: 'without rebuilding your shop',
  lead: 'GoldGraft finds your old PayPal code, writes the new checkout and tests every kind of payment before a single buyer sees it.',
  inputLabel: "Your shop's website or code link",
  placeholder: 'https://github.com/you/your-shop',
  check: 'Check',
  note: 'A quick check. It needs no keys.',
  sample: 'See a sample upgrade',
  invalid: 'Enter a full address starting with https://',
  promises: ['Runs on a sandbox copy', 'Sandbox keys only', 'Nothing goes live until you approve'],
};

export const PROOF = {
  label: 'Why now',
  title: 'PayPal is switching off the old checkout',
  lead: 'The date is set, and plenty of shops still run on it.',
  facts: [
    {
      big: '1 Jan 2027',
      text: 'After this date PayPal may retire Website Payments Standard, the classic Buy Now button.',
      source: SOURCES.wps,
    },
    {
      big: '518,144',
      text: 'public code files on GitHub still send buyers to the old PayPal payment page.',
      source: SOURCES.code,
    },
  ],
  quote: 'Our merchants, especially the largest ones, … require much more hands-on integration support than we anticipated.',
  quoteBy: 'PayPal',
  quoteSource: SOURCES.call,
  resultsLabel: 'Tested before we ask for your trust',
  resultsCaption: 'agent test runs passed, across all 13 AI agents',
  resultsMore: 'Results for each agent',
  resultsNote: 'Results from our own test runs with real AI model calls, November 2026.',
};

export const PROBLEM = {
  label: 'The problem',
  title: 'What breaks if you wait',
  lead: 'Your checkout runs on code PayPal is retiring. Three things go wrong.',
  pains: [
    { title: 'It stops taking money', text: 'When PayPal turns the old buttons off, a buyer presses Pay and nothing happens.' },
    { title: 'A rewrite takes weeks', text: 'Someone has to find every old PayPal call, rewrite it, then test refunds, held payments and notifications by hand.' },
    { title: 'The worst bugs are quiet', text: 'A payment that is still pending gets marked as paid. Nobody notices until the money never arrives.' },
  ],
  calcTitle: 'What a day without checkout costs you',
  calcLabel: 'Your monthly PayPal sales',
  calcPlaceholder: '12,000',
  calcPrefix: 'If your checkout stops, about',
  calcSuffix: 'a day stops with it.',
  calcNote: 'Worked out in your browser from your own number. Nothing is sent anywhere.',
};

export const GRAFT = {
  label: 'The idea',
  title: "Don't cut the tree, graft onto it",
  lead: "A gardener who wants better fruit doesn't cut the old tree down. They join a new branch to the living one. GoldGraft does that with your checkout, so the shop keeps selling while the new checkout grows in.",
  tags: ['Your shop stays', 'The new checkout joins', 'Every payment is tested at the joint'],
};

export type Feature = { id: string; state: string; title: string; benefit: string; text: string };
export const FEATURES_INTRO = {
  label: 'What it does',
  title: 'Seven jobs, each one checked',
  lead: 'GoldGraft does them in this order. Each one leaves a record you can open and check.',
};
export const FEATURES: Feature[] = [
  { id: 'find', state: 'f-find', title: 'Finds every old PayPal piece', benefit: 'Nothing gets missed.', text: 'It reads your code, your live pages and your PayPal account, then lists each old piece and where it sits.' },
  { id: 'write', state: 'f-write', title: 'Writes the new checkout', benefit: 'You skip weeks of developer time.', text: 'One AI agent is allowed to write code. Twelve others plan it, attack it and check it.' },
  { id: 'prove', state: 'f-prove', title: 'Tests each payment three ways', benefit: 'Money bugs have nowhere to hide.', text: "The old shop, the new shop and PayPal's own record have to agree on every payment, step by step." },
  { id: 'bugs', state: 'f-bugs', title: 'Tests its own tests', benefit: 'You can trust the result.', text: 'It plants 12 kinds of money bugs on purpose. A certificate needs at least 95% of them caught.' },
  { id: 'oldbug', state: 'f-oldbug', title: 'Finds bugs you already have', benefit: 'You fix problems you never knew about.', text: 'If your current shop marks a pending payment as paid, GoldGraft tells you, and the new checkout fixes it.' },
  { id: 'golive', state: 'f-golive', title: 'Moves buyers over slowly', benefit: 'There is no risky big launch.', text: 'First 1% of buyers, then 10%, then 50%. If one payment looks wrong, everyone goes back to the old checkout within seconds, on its own.' },
  { id: 'cert', state: 'f-cert', title: 'Signs a certificate anyone can check', benefit: 'Proof you can hand to your accountant.', text: 'Share one link. Anyone can check it, and changing a single byte turns the check red.' },
];

export const STEPS = {
  label: 'How it works',
  title: 'Four steps from old checkout to new',
  items: [
    { n: '01', title: 'Paste your link', text: 'Your code or your website. The first check needs no keys.' },
    { n: '02', title: 'Add test keys', text: "Only PayPal sandbox keys are accepted, so nothing in your live shop changes." },
    { n: '03', title: 'Watch it get proven', text: 'You can leave it running. Every step shows up live as it happens.' },
    { n: '04', title: 'Approve once', text: 'One click on GitHub. If anything goes wrong later, it switches back by itself.' },
  ],
};

export const FAQ = {
  label: 'Questions',
  title: 'Things people ask first',
  lead: 'Short answers. The sample upgrade shows the rest.',
  items: [
    { q: 'Will my live shop change while this runs?', a: "No. Everything runs on a copy of your shop in PayPal's test sandbox. Nothing live changes until you approve the pull request." },
    { q: 'Can GoldGraft see my PayPal keys?', a: 'Your keys go straight into a vault and the AI agents never see them. GoldGraft also refuses live keys and accepts sandbox keys only.' },
    { q: 'What if a payment breaks after launch?', a: 'Buyers move over a few at a time. If one payment breaks a money rule, every buyer is switched back to the old checkout automatically, usually within seconds.' },
    { q: 'Which old PayPal does it handle?', a: 'Classic Buy Now and cart buttons (Website Payments Standard), old Express Checkout (NVP and SOAP) and old payment notifications (IPN).' },
    { q: 'Do I need a developer?', a: 'For now, yes. GoldGraft works from your code repository. A version for shops that only pasted PayPal buttons into their pages is planned.' },
    { q: 'Who approves the change?', a: 'You do, once. GoldGraft opens a pull request on GitHub, and nothing goes live until you merge it.' },
    { q: 'How do I know the proof is real?', a: 'Every finished upgrade gets a signed certificate with a public link. Anyone can check it, and changing a single byte makes the check fail.' },
    { q: 'Is GoldGraft live today?', a: 'It is a working build made for the PayPal AI Hackathon 2026. It runs on test shops in the PayPal sandbox, and every sample on this site is labelled as one.' },
  ],
};

export const FINAL = {
  title: 'Keep your shop',
  titleEm: 'get the new checkout',
  lead: 'Paste your link and see which old PayPal pieces your shop still uses.',
  primary: 'Check my shop',
  secondary: 'See a sample upgrade',
};

export const FOOTER = {
  about: "GoldGraft moves a shop's old PayPal checkout to PayPal's newest one, proves every payment still works, and switches buyers back if anything looks wrong.",
  groups: [
    { title: 'This page', links: [
      { label: 'Why now', href: '#proof' }, { label: 'What it does', href: '#features' },
      { label: 'How it works', href: '#steps' }, { label: 'Questions', href: '#faq' },
    ] },
    { title: 'The app', links: [
      { label: 'Check a shop', href: '/check' }, { label: 'Sample upgrade', href: '/g/demo-1' },
      { label: 'My upgrades', href: '/my' }, { label: 'Recipes', href: '/bank' },
      { label: 'PayPal team view', href: '/orchard' }, { label: 'Security', href: '/security/run-1' }, { label: 'Compare', href: '/compare' },
    ] },
    { title: 'Project', links: [
      { label: 'GitHub repository (team access)', href: SOURCES.repo.href, external: true },
      { label: 'MIT licence (team access)', href: SOURCES.licence.href, external: true },
      { label: 'PayPal AI Hackathon 2026', href: SOURCES.devpost.href, external: true },
    ] },
  ],
  legal: 'Built for the PayPal AI Hackathon 2026. Not made or endorsed by PayPal. Every sample on this site is labelled.',
  credits: 'Photographs are AI-generated for GoldGraft.',
};
