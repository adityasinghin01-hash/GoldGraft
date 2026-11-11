// Reads {"path": "php source", ...} on stdin; prints {"path": {"ok": bool, "error": str|null}}.
import Engine from 'php-parser';
const parser = new Engine({ parser: { php8: true, suppressErrors: false }, ast: { withPositions: false } });
let input = '';
process.stdin.on('data', (d) => (input += d));
process.stdin.on('end', () => {
  const files = JSON.parse(input);
  const out = {};
  for (const [path, code] of Object.entries(files)) {
    try { parser.parseCode(code, path); out[path] = { ok: true, error: null }; }
    catch (e) { out[path] = { ok: false, error: String(e.message).slice(0, 300) }; }
  }
  process.stdout.write(JSON.stringify(out));
});
