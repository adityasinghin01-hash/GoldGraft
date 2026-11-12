import type { Money } from '../api/types';

const ZERO_DIGITS = new Set(['HUF', 'JPY', 'TWD']);
const TWO_DIGITS = new Set(['AUD', 'BRL', 'CAD', 'CNY', 'CZK', 'DKK', 'EUR', 'GBP', 'HKD', 'ILS', 'MXN', 'MYR', 'NOK', 'NZD', 'PHP', 'PLN', 'RUB', 'SEK', 'SGD', 'CHF', 'THB', 'USD']);

/** {minor: 1999, currency: "USD"} → "19.99 USD", built from the integer (never floats). */
export function formatMoney(m: Money | null | undefined): string {
  if (!m) return '';
  const minor = Number(m.minor);
  const cur = String(m.currency);
  const d = ZERO_DIGITS.has(cur) ? 0 : TWO_DIGITS.has(cur) ? 2 : -1;
  if (d < 0 || !Number.isInteger(minor)) return `${m.minor} ${cur} (minor units)`;
  const abs = Math.abs(minor);
  const unit = 10 ** d;
  const whole = Math.trunc(abs / unit).toLocaleString('en-US');
  const frac = d ? '.' + String(abs % unit).padStart(d, '0') : '';
  return `${minor < 0 ? '-' : ''}${whole}${frac} ${cur}`;
}

export const formatUsd = (n: number | null | undefined) => (n == null ? '' : n > 0 && n < 0.005 ? '<$0.01' : `$${n.toFixed(2)}`);
export const formatPct = (p: number | null | undefined) => (p == null ? '' : `${Math.round(p * 100)}%`);

export function formatMinutes(n: number | null | undefined): string {
  if (n == null) return '';
  if (n < 1) return '<1 min';
  const r = Math.round(n);
  if (r < 60) return `${r} min`;
  return `${Math.floor(r / 60)} h ${String(r % 60).padStart(2, '0')} min`;
}

export const formatTime = (iso: string) => new Date(iso).toLocaleTimeString('en-GB', { hour12: false });
export function formatDate(iso: string) {
  const d = new Date(iso);
  const t = d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false });
  return `${d.getDate()} ${d.toLocaleString('en-GB', { month: 'short' })} ${d.getFullYear()}, ${t}`;
}
export const formatMs = (t: number) => `+${(t / 1000).toFixed(1)} s`;
export const shortHash = (h: string | null | undefined) => (h ? `${h.slice(0, 8)}…` : '');
export const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`;
