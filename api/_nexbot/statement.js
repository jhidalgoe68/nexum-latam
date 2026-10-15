/**
 * NexBot — query tool over the sample card statement (#movimientos, fictional data).
 * Gives exact sums so the model never adds up transactions itself:
 * "¿cuánto gasté en supermercados?", "¿cuál fue mi compra más grande?", "gastos de la adicional".
 */
import { STATEMENT } from './knowledge.js';

export const STATEMENT_CATEGORIES = [...new Set(STATEMENT.map(r => r.category))];
const round2 = n => Math.round(n * 100) / 100;
const norm = s => String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
const ymd = d => { const [dd, mm, yy] = String(d).split('/'); return `${yy}${mm}${dd}`; };

export function queryStatement(input = {}) {
  if (!STATEMENT.length) return { ok: false, error: 'La página no publica un estado de cuenta de ejemplo.' };
  const card = ['1027', '3391'].includes(input.card) ? input.card : 'all';
  const merchant = norm(input.merchant);
  const from = /^\d{2}\/\d{2}\/\d{4}$/.test(input.date_from || '') ? ymd(input.date_from) : null;
  const to = /^\d{2}\/\d{2}\/\d{4}$/.test(input.date_to || '') ? ymd(input.date_to) : null;
  const includePayments = input.include_payments === true || input.category === 'Pagos a la tarjeta';
  const groupBy = ['merchant', 'category', 'card', 'date'].includes(input.group_by) ? input.group_by : 'none';
  const top = Math.min(40, Math.max(1, Math.round(+input.top || 10)));

  const rows = STATEMENT.filter(r =>
    (card === 'all' || r.card === card) &&
    (!merchant || norm(`${r.merchant} ${r.place}`).includes(merchant)) &&
    (!input.category || r.category === input.category) &&
    (includePayments || r.category !== 'Pagos a la tarjeta') &&
    (!from || ymd(r.date) >= from) && (!to || ymd(r.date) <= to));

  const sum = list => ({ count: list.length, total_crc: round2(list.reduce((s, r) => s + r.crc, 0)), total_usd: round2(list.reduce((s, r) => s + r.usd, 0)) });
  let groups;
  if (groupBy !== 'none') {
    const key = r => (groupBy === 'card' ? `··${r.card}${r.card === '3391' ? ' (adicional)' : ' (titular)'}` : r[groupBy]);
    const map = new Map();
    for (const r of rows) map.set(key(r), [...(map.get(key(r)) || []), r]);
    groups = [...map].map(([k, list]) => ({ [groupBy]: k, ...sum(list) }))
      .sort((a, b) => (b.total_crc - a.total_crc) || (b.total_usd - a.total_usd)).slice(0, top);
  }
  const sorted = [...rows].sort((a, b) => (b.crc - a.crc) || (b.usd - a.usd));
  return {
    ok: true, note: 'Estado de cuenta de ejemplo con datos ficticios (fecha de corte 27/09/2026).',
    filters: { card, merchant: input.merchant || null, category: input.category || null, date_from: input.date_from || null, date_to: input.date_to || null, include_payments: includePayments },
    ...sum(rows),
    largest: sorted.slice(0, 3).map(({ date, merchant, card: c, crc, usd }) => ({ date, merchant, card: c, crc, usd })),
    groups,
    rows: rows.length <= top ? rows.map(({ date, merchant, place, card: c, category, crc, usd }) => ({ date, merchant, place, card: c, category, crc, usd })) : undefined,
  };
}
