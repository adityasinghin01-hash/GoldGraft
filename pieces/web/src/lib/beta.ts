// Beta density for the S7 curves (Details). Log-gamma via Lanczos; unit-checkable:
// betaPdf(0.5, 1, 1) = 1 and the curve integrates to ~1.
function logGamma(z: number): number {
  const g = 7;
  const c = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313, -176.61502916214059,
    12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
  if (z < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * z)) - logGamma(1 - z);
  z -= 1;
  let x = c[0];
  for (let i = 1; i < g + 2; i++) x += c[i] / (z + i);
  const t = z + g + 0.5;
  return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(x);
}

export function betaPdf(x: number, a: number, b: number): number {
  if (x <= 0 || x >= 1) return (x === 0 && a === 1) || (x === 1 && b === 1) ? Math.exp(-logBeta(a, b)) : 0;
  return Math.exp((a - 1) * Math.log(x) + (b - 1) * Math.log(1 - x) - logBeta(a, b));
}
const logBeta = (a: number, b: number) => logGamma(a) + logGamma(b) - logGamma(a + b);

export function betaCurve(a: number, b: number, from: number, to = 1, points = 200): Array<[number, number]> {
  const out: Array<[number, number]> = [];
  for (let i = 0; i < points; i++) {
    const x = from + ((to - from) * i) / (points - 1);
    out.push([x, betaPdf(Math.min(0.999999, Math.max(1e-6, x)), a, b)]);
  }
  return out;
}

export const betaMean = (a: number, b: number) => a / (a + b);
export const betaSd = (a: number, b: number) => Math.sqrt((a * b) / ((a + b) ** 2 * (a + b + 1)));
