// GoldGraft verification harness: screenshots at given widths and scroll positions,
// console errors, optional reduced motion. Zero dependencies (Chrome + Node 22 WebSocket).
//
//   node tools/shoot.mjs <url> [--widths 1280,1440,1920] [--height 900] [--at 0,1.2,2.4] [--wait 2500]
//                        [--out .shots] [--name hero] [--reduced] [--gpu] [--full] [--eval "js"] [--clip x,y,w,h]
// --at  scroll positions in viewport heights (each gets its own shot)
// Prints PNG paths and any console errors / page exceptions.

import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, rmSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';

const argv = process.argv.slice(2);
const url = argv.find((a) => !a.startsWith('--') && !argv[argv.indexOf(a) - 1]?.startsWith('--') ) ?? argv[0];
const opt = (k, d) => { const i = argv.indexOf(`--${k}`); return i < 0 ? d : argv[i + 1]; };
const flag = (k) => argv.includes(`--${k}`);
const widths = opt('widths', '1440').split(',').map(Number);
const height = Number(opt('height', 900));
const ats = opt('at', '0').split(',').map(Number);
const wait = Number(opt('wait', 2500));
const out = resolve(opt('out', '.shots'));
const name = opt('name', 'shot');
const extraEval = opt('eval', '');
mkdirSync(out, { recursive: true });

const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
if (!existsSync(CHROME)) { console.error('Chrome not found at ' + CHROME); process.exit(2); }
const profile = join(tmpdir(), `gg-shoot-${process.pid}`);
const port = 9300 + (process.pid % 500);
const args = [
  `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, '--headless=new', '--no-first-run',
  '--no-default-browser-check', '--hide-scrollbars', '--mute-audio', `--window-size=${widths[0]},${height}`,
  ...(flag('nogl') ? ['--disable-webgl', '--disable-3d-apis'] : flag('gpu') ? ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] : ['--use-angle=swiftshader', '--enable-unsafe-swiftshader']),
];
const chrome = spawn(CHROME, args, { stdio: 'ignore' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function version() {
  for (let i = 0; i < 60; i++) {
    try { const r = await fetch(`http://127.0.0.1:${port}/json/version`); if (r.ok) return r.json(); } catch {}
    await sleep(150);
  }
  throw new Error('Chrome did not start');
}

let ws, seq = 0;
const pending = new Map();
const events = [];
function send(method, params = {}, sessionId) {
  const id = ++seq;
  ws.send(JSON.stringify({ id, method, params, sessionId }));
  return new Promise((res, rej) => pending.set(id, { res, rej }));
}

try {
  const v = await version();
  ws = new WebSocket(v.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  ws.addEventListener('message', (m) => {
    const msg = JSON.parse(m.data);
    if (msg.id && pending.has(msg.id)) { const p = pending.get(msg.id); pending.delete(msg.id); msg.error ? p.rej(new Error(msg.error.message)) : p.res(msg.result); }
    else if (msg.method) events.push(msg);
  });
  const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
  const S = (m, p) => send(m, p, sessionId);
  await S('Page.enable'); await S('Runtime.enable'); await S('Log.enable');
  if (flag('reduced')) await S('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });

  const paths = [];
  for (const w of widths) {
    await S('Emulation.setDeviceMetricsOverride', { width: w, height, deviceScaleFactor: 1, mobile: false });
    await S('Page.navigate', { url });
    await sleep(wait);
    if (extraEval) { const r = await S('Runtime.evaluate', { expression: extraEval, awaitPromise: true, returnByValue: true }); console.log('EVAL', JSON.stringify(r.result?.value ?? r.exceptionDetails?.text)); }
    for (const at of ats) {
      if (at > 0 || ats.length > 1) {
        await S('Runtime.evaluate', { expression: `window.scrollTo(0, ${Math.round(at * height)}); window.dispatchEvent(new Event('scroll'));`, awaitPromise: true });
        await sleep(Math.max(1400, wait * 0.6));
      }
      let clip;
      if (opt('clip', '')) {
        // clip is given in viewport coordinates; CDP wants document coordinates
        const [x, y, cw, ch] = opt('clip').split(',').map(Number);
        const { result: sy } = await S('Runtime.evaluate', { expression: 'window.scrollY', returnByValue: true });
        clip = { x, y: y + (sy.value || 0), width: cw, height: ch, scale: 1 };
      }
      if (flag('full')) {
        const { result } = await S('Runtime.evaluate', { expression: 'document.documentElement.scrollHeight', returnByValue: true });
        clip = { x: 0, y: 0, width: w, height: Math.min(result.value, 16000), scale: 1 };
      }
      const shot = await S('Page.captureScreenshot', { format: 'png', ...(clip ? { clip, captureBeyondViewport: true } : {}) });
      const p = join(out, `${name}-${w}${ats.length > 1 || at ? `-at${String(at).replace('.', '_')}` : ''}.png`);
      writeFileSync(p, Buffer.from(shot.data, 'base64'));
      paths.push(p);
    }
  }
  console.log(paths.join('\n'));
  const errs = events.filter((e) => e.method === 'Runtime.exceptionThrown' || (e.method === 'Runtime.consoleAPICalled' && ['error', 'warning'].includes(e.params.type)) || (e.method === 'Log.entryAdded' && e.params.entry.level === 'error'));
  for (const e of errs.slice(0, 12)) {
    if (e.method === 'Runtime.exceptionThrown') console.log('EXCEPTION', e.params.exceptionDetails.exception?.description?.split('\n').slice(0, 3).join(' | ') ?? e.params.exceptionDetails.text);
    else if (e.method === 'Log.entryAdded') console.log('LOG', e.params.entry.text, e.params.entry.url ?? '');
    else console.log(e.params.type.toUpperCase(), e.params.args.map((a) => a.value ?? a.description).join(' ').slice(0, 300));
  }
  if (!errs.length) console.log('console: clean');
} catch (e) {
  console.error('harness error:', e.message);
  process.exitCode = 1;
} finally {
  try { ws?.close(); } catch {}
  chrome.kill('SIGKILL');
  await sleep(200);
  try { rmSync(profile, { recursive: true, force: true }); } catch {}
}
