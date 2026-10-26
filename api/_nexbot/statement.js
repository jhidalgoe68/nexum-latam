/**
 * NexBot — query tool over the sample card statement (#movimientos, fictional data).
 * Gives exact sums so the model never adds up transactions itself:
 * "¿cuánto gasté en supermercados?", "¿cuál fue mi compra más grande?", "gastos de la adicional".
 */
import { STATEMENT, STATEMENT_SUMMARY as SUM } from './knowledge.js';

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

// ── Full analysis: spending profile, credit health, cost of paying only the minimum, and signals ──
const DAYS = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'];
const dayOf = d => { const [dd, mm, yy] = d.split('/').map(Number); return new Date(Date.UTC(yy, mm - 1, dd)).getUTCDay(); };
const pick = re => { const k = Object.keys(SUM).find(x => re.test(x)); return k ? { label: k, ...SUM[k] } : null; };
const pct = (a, b) => (b ? round2(a / b * 100) : 0);
const n2 = n => Number(n).toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fc = n => `₡${n2(n)}`, fu = n => `US$${n2(n)}`, pc = n => `${String(n).replace('.', ',')}%`;

/** Months and interest to clear the balance paying only the minimum each month (no new purchases). */
export function minimumPaymentPlan(balance, monthlyRatePct, minRatio, floor = 5000) {
  const r = monthlyRatePct / 100;
  let b = balance, months = 0, interest = 0;
  while (b > 0.5 && months < 600) {
    const i = b * r; interest += i; b += i;
    const pay = Math.min(b, Math.max(b * minRatio, floor));
    b -= pay; months++;
  }
  return { months, years: round2(months / 12), total_interest: round2(interest), total_paid: round2(balance + interest) };
}

export function analyzeStatement() {
  if (!STATEMENT.length) return { ok: false, error: 'La página no publica un estado de cuenta de ejemplo.' };
  const purchases = STATEMENT.filter(r => r.category !== 'Pagos a la tarjeta');
  const payments = STATEMENT.filter(r => r.category === 'Pagos a la tarjeta');
  const crcBuys = purchases.filter(r => r.crc > 0);
  const totC = round2(purchases.reduce((s, r) => s + r.crc, 0)), totU = round2(purchases.reduce((s, r) => s + r.usd, 0));
  const groupBy = (list, key) => { const m = new Map(); for (const r of list) m.set(key(r), [...(m.get(key(r)) || []), r]); return [...m]; };
  const agg = ([k, list]) => ({ key: k, count: list.length, total_crc: round2(list.reduce((s, r) => s + r.crc, 0)), total_usd: round2(list.reduce((s, r) => s + r.usd, 0)) });

  const byCategory = groupBy(purchases, r => r.category).map(agg).map(g => ({ category: g.key, ...g, key: undefined, pct_of_crc_spend: pct(g.total_crc, totC) }))
    .sort((a, b) => b.total_crc - a.total_crc || b.total_usd - a.total_usd);
  const byCard = groupBy(purchases, r => r.card).map(agg).map(g => ({ card: `··${g.key}${g.key === '3391' ? ' (adicional)' : ' (titular)'}`, count: g.count, total_crc: g.total_crc, total_usd: g.total_usd, pct_of_crc_spend: pct(g.total_crc, totC) }));
  const merchants = groupBy(purchases, r => r.merchant).map(agg);
  const byDay = groupBy(crcBuys, r => DAYS[dayOf(r.date)]).map(agg).map(g => ({ day: g.key, count: g.count, total_crc: g.total_crc })).sort((a, b) => b.total_crc - a.total_crc);
  const weekend = crcBuys.filter(r => [0, 6].includes(dayOf(r.date)));
  const small = crcBuys.filter(r => r.crc < 5000);
  const dates = STATEMENT.map(r => r.date).sort((a, b) => ymd(a).localeCompare(ymd(b)));

  const due = pick(/^Pago contado/), min = pick(/^Pago m[ií]nimo/), cut = pick(/^Saldo al corte/), intr = pick(/^Intereses/), rate = pick(/^Tasa mensual/);
  const prevBal = pick(/^Saldo anterior/), util = pick(/^Utilizado/), limit = pick(/^Límite global/), avail = pick(/^Disponible/), points = pick(/NexMillas/);
  const dueDate = (due?.label.match(/vence (\d{2}\/\d{2}\/\d{4})/) || [])[1] || null;
  const paidC = -round2(payments.reduce((s, r) => s + r.crc, 0)), paidU = -round2(payments.reduce((s, r) => s + r.usd, 0));
  const monthly = rate?.value ?? null;
  const minRatio = due?.value && min?.value ? min.value / due.value : null;
  const plan = due?.value && monthly && minRatio ? minimumPaymentPlan(due.value, monthly, minRatio) : null;
  const utilPct = util?.value ?? null;
  const utilLevel = utilPct == null ? null : utilPct < 30 ? 'saludable (<30%)' : utilPct <= 50 ? 'moderada (30–50%)' : 'alta (>50%)';

  const top = byCategory[0];
  const dining = byCategory.find(c => c.category === 'Restaurantes y cafés');
  const dominantCard = byCard.find(c => c.pct_of_crc_spend >= 60);
  const signals = [
    plan && { code: 'minimum_payment_cost', detail: `Pagando solo el mínimo (≈${pc(round2(minRatio * 100))} del saldo) se tardarían ${plan.months} meses y se pagarían ≈${fc(plan.total_interest)} en intereses; pagando el contado (${fc(due.value)}) antes del ${dueDate} no se generan intereses corrientes.` },
    intr?.value > 0 && { code: 'interest_charged', detail: `Intereses corrientes del mes: ${fc(intr.value)}${intr.usd ? ` + ${fu(intr.usd)}` : ''}.` },
    paidC && prevBal?.value && Math.abs(paidC - prevBal.value) < 1 && { code: 'paid_previous_in_full', detail: 'El saldo anterior se pagó completo (buen hábito: evita intereses).' },
    utilPct != null && { code: 'credit_utilization', detail: `Utilización del límite global ${pc(utilPct)} → ${utilLevel}.` },
    top && top.pct_of_crc_spend >= 35 && { code: 'concentrated_category', detail: `${top.category} concentra el ${pc(top.pct_of_crc_spend)} del gasto en colones.` },
    dining && dining.count >= 8 && { code: 'frequent_dining', detail: `${dining.count} compras en restaurantes y cafés (${fc(dining.total_crc)}).` },
    small.length >= 8 && { code: 'small_tickets', detail: `${small.length} compras menores a ₡5.000 suman ${fc(round2(small.reduce((s, r) => s + r.crc, 0)))} ("gastos hormiga").` },
    dominantCard && { code: 'card_concentration', detail: `La tarjeta ${dominantCard.card} hace el ${pc(dominantCard.pct_of_crc_spend)} del gasto.` },
    totU > 0 && { code: 'usd_charges', detail: `Hay consumos en dólares (${fu(totU)}); el pago en US$ se cancela por separado.` },
  ].filter(Boolean);

  return {
    ok: true, note: 'Análisis del estado de cuenta de ejemplo (datos ficticios). Cifras calculadas sobre las transacciones publicadas.',
    period: { from: dates[0], to: dates.at(-1), cut_off: pick(/^Fecha de corte/)?.text || null, due_date: dueDate },
    balances: { previous: prevBal?.text, cut_off_balance: cut?.text, pay_in_full: due?.text, minimum_payment: min?.text, interest_this_month: intr?.text, monthly_rate: rate?.text,
      annual_effective_rate_pct: monthly ? round2((Math.pow(1 + monthly / 100, 12) - 1) * 100) : null, payments_received: { crc: paidC, usd: paidU } },
    credit: { limit_usd: limit?.value ?? null, available_usd: avail?.value ?? null, utilization_pct: utilPct, utilization_level: utilLevel },
    spending: {
      purchases: purchases.length, total_crc: totC, total_usd: totU, average_ticket_crc: crcBuys.length ? round2(totC / crcBuys.length) : 0,
      by_category: byCategory, by_card: byCard,
      top_merchants_by_amount: [...merchants].sort((a, b) => b.total_crc - a.total_crc).slice(0, 5).map(m => ({ merchant: m.key, count: m.count, total_crc: m.total_crc })),
      recurring_merchants: merchants.filter(m => m.count >= 3).sort((a, b) => b.count - a.count).map(m => ({ merchant: m.key, visits: m.count, total_crc: m.total_crc, average_crc: round2(m.total_crc / m.count) })),
      by_weekday: byDay, weekend_share_pct: pct(weekend.reduce((s, r) => s + r.crc, 0), totC),
      small_purchases_under_5000: { count: small.length, total_crc: round2(small.reduce((s, r) => s + r.crc, 0)) },
      largest: [...purchases].sort((a, b) => b.crc - a.crc).slice(0, 3).map(({ date, merchant, card, crc }) => ({ date, merchant, card, crc })),
    },
    rewards: { nexmillas_period: points?.value ?? null },
    minimum_payment_plan: plan, signals,
  };
}
