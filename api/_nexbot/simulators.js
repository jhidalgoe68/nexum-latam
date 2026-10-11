/**
 * NexBot — server-side simulator tools
 * ──────────────────────────────────────────────────────────────────────────
 * Same formulas as the "Calcula antes de decidir" simulators in
 * nexumtest/index.html, so a figure quoted in the chat always matches what
 * the customer sees when they open the simulator. Ranges come from
 * SIM_LIMITS (generated from the page sliders) and inputs are clamped to
 * them, so the bot can never quote a product outside what the page offers.
 */
import { SIM_LIMITS } from './knowledge.js';

const round2 = n => Math.round(n * 100) / 100;
const clamp = (v, { min, max }) => Math.min(max, Math.max(min, v));
const num = (v, fallback) => (Number.isFinite(+v) && v !== null && v !== '' ? +v : fallback);

function pick(sim, field, value, adjustments) {
  const lim = SIM_LIMITS[sim][field];
  const raw = num(value, lim.default);
  const v = clamp(raw, lim);
  if (v !== raw) adjustments.push(`${field}: ${raw} → ${v} (rango del simulador ${lim.min}–${lim.max})`);
  return v;
}

/** French (fixed installment) or German (fixed principal) amortization — identical to amortTable() on the page. */
function amortize(principal, annualRate, n, table) {
  const r = annualRate / 12;
  const fixed = principal * r / (1 - Math.pow(1 + r, -n));
  let bal = principal, total = 0, first = 0, last = 0;
  for (let i = 1; i <= n; i++) {
    const interest = bal * r;
    const q = table === 'alemana' ? principal / n + interest : fixed;
    const cap = q - interest;
    bal = Math.max(0, bal - cap);
    total += q;
    if (i === 1) first = q;
    if (i === n) last = q;
  }
  return { first: round2(first), last: round2(last), totalPaid: round2(total), totalInterest: round2(total - principal) };
}

export function simulateLoan(input = {}) {
  const product = ['consumo', 'auto', 'hipo'].includes(input.product) ? input.product : 'consumo';
  const table = input.amortization === 'alemana' ? 'alemana' : 'francesa';
  const adj = [];
  let principal, months, rate, extra = {};

  if (product === 'consumo') {
    principal = pick('consumo', 's-m', input.amount, adj);
    months = pick('consumo', 's-n', input.term_months, adj);
    rate = pick('consumo', 's-r', input.annual_rate_pct, adj);
  } else if (product === 'auto') {
    const price = pick('auto', 's-v', input.price, adj);
    const down = pick('auto', 's-e', input.down_payment_pct, adj);
    months = pick('auto', 's-n', input.term_months, adj);
    rate = pick('auto', 's-r', input.annual_rate_pct, adj);
    const bonus = input.eco_bonus ? 100 : 0;
    principal = Math.max(0, price * (1 - down / 100) - bonus);
    extra = { vehicle_price: price, down_payment_pct: down, down_payment: round2(price * down / 100), eco_bonus_applied: bonus };
  } else {
    const value = pick('hipo', 's-v', input.price, adj);
    const pct = pick('hipo', 's-f', input.finance_pct, adj);
    const years = pick('hipo', 's-y', input.term_years ?? (input.term_months ? Math.round(input.term_months / 12) : undefined), adj);
    rate = pick('hipo', 's-r', input.annual_rate_pct, adj);
    months = years * 12;
    const bonus = input.eco_bonus ? 1000 : 0;
    principal = Math.max(0, value * pct / 100 - bonus);
    extra = { property_value: value, finance_pct: pct, term_years: years, eco_bonus_applied: bonus, contribution_0_5_pct: round2(principal * 0.005) };
  }

  const a = amortize(principal, rate / 100, months, table);
  return {
    simulator: product, amortization: table, principal: round2(principal), term_months: months, annual_rate_pct: rate,
    monthly_payment: table === 'francesa' ? a.first : undefined,
    first_payment: a.first, last_payment: a.last, total_interest: a.totalInterest, total_paid: a.totalPaid,
    ...extra, adjustments: adj,
    disclaimer: 'Resultado referencial con tasas de demostración; la cuota final depende de la evaluación de crédito.',
  };
}

export function simulateDeposit(input = {}) {
  const adj = [];
  const amount = pick('cdp', 's-m', input.amount, adj);
  const days = pick('cdp', 's-d', input.days, adj);
  const rate = pick('cdp', 's-r', input.annual_rate_pct, adj);
  const upfront = input.interest_payment === 'anticipado';
  const r = rate / 100;
  let interest = amount * r * days / 360;
  if (upfront) interest = interest / (1 + r * days / 360);
  return {
    simulator: 'cdp', amount, days, annual_rate_pct: rate, interest_payment: upfront ? 'anticipado' : 'al vencimiento',
    interest: round2(interest), receive_at_maturity: round2(upfront ? amount : amount + interest),
    yield_pct: round2(interest / amount * 100), adjustments: adj,
    minimums: 'Desde $500 en App y web, $1.000 en agencias. Base 360 días.',
    disclaimer: 'Tasa de demostración; en agencias puede ser distinta.',
  };
}

export function simulateSavings(input = {}) {
  const adj = [];
  const monthly = pick('ahorro', 's-m', input.monthly_contribution, adj);
  const months = pick('ahorro', 's-n', input.months, adj);
  const roundup = pick('ahorro', 's-rd', input.roundup_monthly, adj);
  const blindado = input.blindado !== false;
  const reto = !!input.challenge_52_weeks;
  const r = (blindado ? 5.25 : 4) / 100 / 12;
  const weeks = Math.min(52, Math.round(months * 52 / 12));
  const w52 = reto ? weeks * (weeks + 1) / 2 : 0;
  let bal = 0, dep = 0;
  for (let i = 0; i < months; i++) { const add = monthly + roundup + w52 / months; bal = (bal + add) * (1 + r); dep += add; }
  return {
    simulator: 'ahorro', goal_name: String(input.goal_name || '').slice(0, 40) || undefined,
    monthly_contribution: monthly, roundup_monthly: roundup, months, blindado, annual_rate_pct: blindado ? 5.25 : 4,
    challenge_52_weeks: reto, challenge_weeks_counted: reto ? weeks : 0, challenge_total: w52,
    final_balance: round2(bal), total_contributed: round2(dep), interest_earned: round2(bal - dep), adjustments: adj,
    disclaimer: 'Tasa base 4,00% y Blindado 5,25% (demostración, sujetas a condiciones). Interés diario capitalizado mensual.',
  };
}
