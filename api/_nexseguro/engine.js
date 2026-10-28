/**
 * NexBot Seguro — conversation engine for the NexumSeguro page (/nexumseguro/).
 * Reuses the NexBot pipeline (api/_nexbot/engine.js): same sanitizing and
 * redaction, the same Claude client, API key, models and fallbacks, and the
 * shared agent loop. Only the knowledge base, prompt, tools and emergency
 * fast path are specific to the insurer.
 */
import { sanitizeConversation, detectLanguage, runAgent } from '../_nexbot/engine.js';
import { KNOWLEDGE, KB_VERSION } from './knowledge.js';
import { SYSTEM_PROMPT, TOOLS } from './prompt.js';

export const PRODUCTS = ['salud', 'vida', 'viajes'];

// ── Medical emergencies: instant answer, no model call ──────────────────
const EMERGENCY = /(tengo una emergencia|es una emergencia|emergencia ahora|ambulancia|infarto|no respira|inconsciente|desmay|convulsi|sangrando|hemorragia|me accident|tuve un accidente|chocamos|i have an emergency|it'?s an emergency|ambulance|heart attack|not breathing|unconscious|fainted|seizure|bleeding|i had an accident|car crash)/i;

export function fastPath(lastUser, lang) {
  if (!EMERGENCY.test(lastUser)) return null;
  return lang === 'en'
    ? `**If someone's life is at risk, call your country's emergency number now (911 or the local equivalent) or go to the nearest emergency room.**\n\nThen contact the NexumSeguro 24/7 assistance center with the number on your policy or insurance card: they coordinate care and payment with the hospital. At a network hospital, in most cases you don't pay up front.\n[[go:reclamos|See claim steps]]\n[[src:Reclamos · nexumseguro]]`
    : `**Si hay riesgo para la vida, llame ya al número de emergencias de su país (911 o el equivalente local) o acuda a la sala de emergencias más cercana.**\n\nLuego comuníquese con la central de asistencia 24/7 de NexumSeguro con el número que figura en su póliza o tarjeta de asegurado: coordinamos la atención y el pago con el hospital. En un hospital de la red, en la mayoría de los casos no tiene que pagar por adelantado.\n[[go:reclamos|Ver pasos de reclamo]]\n[[src:Reclamos · nexumseguro]]`;
}

// ── Tools ────────────────────────────────────────────────────────────────
const clamp = (v, min, max, def) => (typeof v === 'number' && Number.isFinite(v) ? Math.min(max, Math.max(min, v)) : def);
const round = n => Math.round(n);

export function simulateLifeCover(input = {}) {
  const adjustments = [];
  const income = clamp(input.annual_income, 0, 5_000_000, 0);
  const years = clamp(input.years_of_support, 1, 40, 10);
  if (input.years_of_support != null && years !== input.years_of_support) adjustments.push(`Años de apoyo ajustados a ${years} (rango 1–40).`);
  const amt = k => clamp(input[k], 0, 50_000_000, 0);
  const parts = {
    income_replacement: round(income * years),
    debts: round(amt('debts')),
    education: round(amt('education')),
    final_expenses: round(amt('final_expenses')),
  };
  const needs = parts.income_replacement + parts.debts + parts.education + parts.final_expenses;
  const resources = round(amt('savings')) + round(amt('existing_cover'));
  return {
    ok: true,
    simulator: 'vida',
    method: 'Necesidades: ingreso anual × años de apoyo + deudas + educación + gastos finales − ahorros − seguros de vida existentes.',
    annual_income: round(income), years_of_support: years, ...parts,
    total_needs: needs, available_resources: resources,
    suggested_cover: Math.max(0, needs - resources),
    currency: 'USD', adjustments,
    note: 'Estimación educativa con un método general; no es una cotización de NexumSeguro. Un asesor confirma la suma asegurada final.',
  };
}

async function requestCallback(input) {
  if (input.consent !== true) return { ok: false, error: 'Se requiere el consentimiento explícito del visitante.' };
  const ticket = 'NS-' + Date.now().toString(36).toUpperCase().slice(-6);
  const payload = {
    ticket, source: 'nexumseguro', kb_version: KB_VERSION, received_at: new Date().toISOString(),
    first_name: String(input.first_name || '').slice(0, 60), contact: String(input.contact || '').slice(0, 120),
    plan: input.plan || 'salud', policyholder_age: typeof input.policyholder_age === 'number' ? input.policyholder_age : null,
    people: input.people || null, country: String(input.country || '').slice(0, 60),
    topic: String(input.topic || '').slice(0, 500), preferred_time: String(input.preferred_time || '').slice(0, 80), language: input.language || 'es',
  };
  const hook = process.env.NEXSEGURO_HANDOFF_WEBHOOK || process.env.NEXBOT_HANDOFF_WEBHOOK; // e.g. an n8n / Make / Zapier webhook URL
  if (hook) {
    try {
      const r = await fetch(hook, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), signal: AbortSignal.timeout(5000) });
      if (!r.ok) throw new Error(`webhook ${r.status}`);
      return { ok: true, ticket, delivered: true, note: 'Un asesor contactará al visitante en horario de oficina (lunes a viernes, 8:30 a 17:00).' };
    } catch (e) {
      console.error('[nexseguro] handoff webhook failed:', e.message);
      return { ok: false, ticket, error: 'No se pudo registrar la solicitud; indica al visitante el formulario “Cotice en un minuto”.' };
    }
  }
  return { ok: true, ticket, delivered: false, note: 'Sitio en preparación: la solicitud queda registrada solo como ejemplo y no se almacenan datos personales. Sugiere también el formulario “Cotice en un minuto”.' };
}

export async function runTool(name, input) {
  switch (name) {
    case 'simulate_life_cover': return simulateLifeCover(input);
    case 'request_advisor_callback': return requestCallback(input || {});
    default: return { ok: false, error: `Herramienta desconocida: ${name}` };
  }
}

/**
 * Runs one assistant turn.
 * @param {object} p
 * @param {Array<{role:string,content:string}>} p.messages  raw transcript from the browser
 * @param {'es'|'en'} [p.lang]     UI language hint
 * @param {string} [p.product]     plan selected in the page's quote form
 * @param {string} [p.country]     country selected in the page's country selector
 * @param {boolean} [p.voice]      the visitor spoke this message and will hear the reply
 * @param {(event:string, data:object)=>void} p.emit
 * @param {AbortSignal} [p.signal]
 */
export async function respond({ messages: raw, lang: uiLang, product, country, voice, emit, signal }) {
  const { messages, flaggedSensitive } = sanitizeConversation(raw);
  const lastUser = messages[messages.length - 1].content;
  const lang = detectLanguage(lastUser, uiLang);
  emit('meta', { lang, kb: KB_VERSION });

  const quick = fastPath(lastUser, lang);
  if (quick) { emit('delta', { text: quick }); emit('done', { source: 'fast-path' }); return; }

  // Page context goes in its own block *after* the visitor's words, so the cached prefix stays intact.
  const plan = PRODUCTS.includes(product) ? product : 'salud';
  const ctry = String(country || 'Internacional').replace(/[^\p{L} .-]/gu, '').slice(0, 40) || 'Internacional';
  const context = `<page_context>ui_language=${uiLang === 'en' ? 'en' : 'es'}; detected_language=${lang}; product=${plan}; country=${ctry}; input_mode=${voice === true ? 'voice' : 'text'}${flaggedSensitive ? '; note=the visitor tried to share a card number, PIN or code — it was removed; remind them never to share it' : ''}</page_context>`;
  const last = messages[messages.length - 1];
  const convo = [...messages.slice(0, -1), { role: 'user', content: [{ type: 'text', text: last.content }, { type: 'text', text: context }] }];

  await runAgent({
    convo, emit, signal,
    system: [
      { type: 'text', text: SYSTEM_PROMPT },
      { type: 'text', text: `<knowledge_base>\n${KNOWLEDGE}</knowledge_base>`, cache_control: { type: 'ephemeral' } },
    ],
    tools: TOOLS,
    runTool,
    refusalText: lang === 'en'
      ? "I can't help with that here. I can tell you about NexumSeguro's health, life and travel plans, or help you get a quote.\n[[quote:salud|Get a quote]]"
      : 'No puedo ayudarle con eso por aquí. Con gusto le cuento sobre los planes de salud, vida y viajes de NexumSeguro o le ayudo a cotizar.\n[[quote:salud|Cotizar]]',
  });
}
