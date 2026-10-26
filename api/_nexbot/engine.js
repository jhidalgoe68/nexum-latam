/**
 * NexBot — conversation engine (transport-agnostic).
 * ──────────────────────────────────────────────────────────────────────────
 * Pipeline per visitor message:
 *   1. sanitize   → validate history, redact card numbers / PINs / codes
 *   2. fast paths → emergencies answered instantly, no model call
 *   3. agent loop → Claude (streaming) with the knowledge base as cached
 *                   context and server-side tools (simulators, handoff)
 *   4. emit       → typed events to the caller (delta, tool, sim, reset,
 *                   done, error), which the HTTP layer turns into SSE.
 */
import Anthropic from '@anthropic-ai/sdk';
import { KNOWLEDGE, KB_VERSION } from './knowledge.js';
import { SYSTEM_PROMPT, TOOLS } from './prompt.js';
import { simulateLoan, simulateDeposit, simulateSavings } from './simulators.js';
import { queryStatement, analyzeStatement } from './statement.js';

export const MODEL = process.env.NEXBOT_MODEL || 'claude-opus-5-5';
// Tried in order only when the key has no access to the model above (404 / permission error).
export const MODEL_CHAIN = [MODEL, ...(process.env.NEXBOT_FALLBACK_MODELS ?? 'claude-sonnet-5-5').split(',').map(s => s.trim()).filter(m => m && m !== MODEL)];
const EFFORT = process.env.NEXBOT_EFFORT || 'medium'; // medium: room for full statement analysis and recommendations
const MAX_TOOL_ROUNDS = 4;

export const LIMITS = { turns: 24, userChars: 1200, assistantChars: 4000, totalChars: 24000 };

// ── 1. Sanitizing ────────────────────────────────────────────────────────

/** Luhn check so we only redact digit runs that really look like card numbers. */
function luhn(d) {
  let s = 0, alt = false;
  for (let i = d.length - 1; i >= 0; i--) { let n = +d[i]; if (alt) { n *= 2; if (n > 9) n -= 9; } s += n; alt = !alt; }
  return s % 10 === 0;
}

export function redact(text) {
  let flagged = false;
  let out = String(text).replace(/\b(?:\d[ -]?){13,19}\b/g, m => {
    const d = m.replace(/\D/g, '');
    if (d.length >= 13 && d.length <= 19 && luhn(d)) { flagged = true; return '[número de tarjeta eliminado]'; }
    return m;
  });
  out = out.replace(/\b(pin|cvv|cvc|clave|contraseña|password|otp|c[oó]digo(?: de seguridad| de verificaci[oó]n)?)\b(\s*(?:es|is|:|=)?\s*)([A-Za-z0-9]{3,12})\b/gi,
    (m, k, sep, v) => (/\d/.test(v) ? (flagged = true, `${k}${sep}[dato eliminado]`) : m));
  return { text: out, flagged };
}

/** Validates the client-supplied transcript and returns Messages API params. */
export function sanitizeConversation(raw) {
  if (!Array.isArray(raw) || !raw.length) throw new BadRequest('messages vacío');
  const turns = raw.slice(-LIMITS.turns);
  const messages = [];
  let total = 0, flagged = false;
  for (const t of turns) {
    if (!t || (t.role !== 'user' && t.role !== 'assistant') || typeof t.content !== 'string') throw new BadRequest('mensaje inválido');
    const cap = t.role === 'user' ? LIMITS.userChars : LIMITS.assistantChars;
    let content = t.content.slice(0, cap).trim();
    if (!content) continue;
    if (t.role === 'user') { const r = redact(content); content = r.text; flagged = r.flagged; }
    total += content.length;
    const prev = messages[messages.length - 1];
    if (prev && prev.role === t.role) prev.content += '\n\n' + content; // keep strict alternation
    else messages.push({ role: t.role, content });
  }
  while (messages.length && messages[0].role !== 'user') messages.shift();
  if (!messages.length || messages[messages.length - 1].role !== 'user') throw new BadRequest('el último mensaje debe ser del usuario');
  if (total > LIMITS.totalChars) throw new BadRequest('conversación demasiado larga');
  return { messages, flaggedSensitive: flagged };
}

export class BadRequest extends Error {}

// ── 2. Deterministic fast paths ──────────────────────────────────────────

const EMERGENCY = /(me robaron|robo|robada|robaron|perd[ií] mi tarjeta|fraude|clonad|no reconozco|hacke|stolen|lost my card|fraud|cloned|unauthori[sz]ed|hacked|block my card)/i;

export function detectLanguage(text, hint) {
  const t = ` ${String(text).toLowerCase()} `;
  const en = (t.match(/\b(the|my|i|you|what|how|is|are|can|do|does|want|need|card|loan|account|rate|please|hello|hi|which|open)\b/g) || []).length;
  const es = (t.match(/\b(el|la|los|las|mi|yo|que|qué|cómo|como|es|son|puedo|quiero|necesito|tarjeta|crédito|cuenta|tasa|hola|cuál|abrir|para|una|un)\b/g) || []).length + (/[ñ¿¡áéíóú]/.test(t) ? 2 : 0);
  if (en > es) return 'en';
  if (es > en) return 'es';
  return hint === 'en' ? 'en' : 'es';
}

export function fastPath(lastUser, lang) {
  if (!EMERGENCY.test(lastUser)) return null;
  return lang === 'en'
    ? `**Block your card right now.** Message us on WhatsApp or call Línea Nexum at **(01) 555 0100** — immediate attention, no prior steps.\n\nNexumtestbank will never ask for your password, PIN or codes.\n[[copy:(01) 555 0100|Copy number]]\n[[go:canales|See channels]]\n[[src:Protocolo de emergencias · prioridad alta]]`
    : `**Bloquea tu tarjeta ahora.** Escríbenos por WhatsApp o llama a la Línea Nexum: **(01) 555 0100**. Atención inmediata, sin pasos previos.\n\nNexumtestbank nunca te pedirá claves, PIN ni códigos.\n[[copy:(01) 555 0100|Copiar número]]\n[[go:canales|Ver canales]]\n[[src:Protocolo de emergencias · prioridad alta]]`;
}

// ── 3. Tools ─────────────────────────────────────────────────────────────

async function requestCallback(input) {
  if (input.consent !== true) return { ok: false, error: 'Se requiere el consentimiento explícito del visitante.' };
  const ticket = 'NB-' + Date.now().toString(36).toUpperCase().slice(-6);
  const payload = {
    ticket, source: 'nexbot', kb_version: KB_VERSION, received_at: new Date().toISOString(),
    first_name: String(input.first_name || '').slice(0, 60), contact: String(input.contact || '').slice(0, 120),
    segment: input.segment || 'personas', topic: String(input.topic || '').slice(0, 500),
    preferred_time: String(input.preferred_time || '').slice(0, 80), language: input.language || 'es',
  };
  const hook = process.env.NEXBOT_HANDOFF_WEBHOOK; // e.g. an n8n / Make / Zapier webhook URL
  if (hook) {
    try {
      const r = await fetch(hook, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), signal: AbortSignal.timeout(5000) });
      if (!r.ok) throw new Error(`webhook ${r.status}`);
      return { ok: true, ticket, delivered: true, note: 'Un asesor contactará al visitante en horario de atención.' };
    } catch (e) {
      console.error('[nexbot] handoff webhook failed:', e.message);
      return { ok: false, ticket, error: 'No se pudo registrar la solicitud; indica al visitante la Línea Nexum (01) 555 0100.' };
    }
  }
  return { ok: true, ticket, delivered: false, note: 'Sitio de demostración: la solicitud queda registrada solo como ejemplo; no se almacenan datos personales. Ofrece también la Línea Nexum (01) 555 0100.' };
}

export async function runTool(name, input) {
  switch (name) {
    case 'simulate_loan': return simulateLoan(input);
    case 'simulate_term_deposit': return simulateDeposit({ ...input, interest_payment: input?.interest_payment === 'anticipado' ? 'anticipado' : 'vencimiento' });
    case 'simulate_savings_goal': return simulateSavings(input);
    case 'query_statement': return queryStatement(input);
    case 'analyze_statement': return analyzeStatement();
    case 'request_advisor_callback': return requestCallback(input || {});
    default: return { ok: false, error: `Herramienta desconocida: ${name}` };
  }
}

const isPlainObject = v => v !== null && typeof v === 'object' && !Array.isArray(v);

/** Eager input streaming means the server no longer validates tool input — check it against the schema shape here. */
function validateToolInput(name, input) {
  const tool = TOOLS.find(t => t.name === name);
  if (!tool) return `unknown tool ${name}`;
  if (!isPlainObject(input)) return 'input must be an object';
  const { properties, required = [] } = tool.input_schema;
  for (const k of required) if (!(k in input)) return `missing required field ${k}`;
  for (const [k, v] of Object.entries(input)) {
    const p = properties[k];
    if (!p) return `unexpected field ${k}`;
    if (p.type === 'number' && typeof v !== 'number') return `${k} must be a number`;
    if (p.type === 'string' && typeof v !== 'string') return `${k} must be a string`;
    if (p.type === 'boolean' && typeof v !== 'boolean') return `${k} must be a boolean`;
    if (p.enum && !p.enum.includes(v)) return `${k} must be one of ${p.enum.join(', ')}`;
  }
  return null;
}

// ── 4. Agent loop ────────────────────────────────────────────────────────

// ── Error classification (shared by the chat stream and the health check) ──
/** Maps an Anthropic/SDK error to a stable code the page understands, plus a hint for the site owner. */
export function classifyError(err) {
  const msg = String(err?.error?.error?.message || err?.message || '');
  if (err?.code === 'not_configured') return { code: 'not_configured', hint: 'Falta ANTHROPIC_API_KEY en las variables de entorno de este despliegue (Vercel → Settings → Environment Variables → Production) y volver a desplegar.' };
  if (err?.status === 401) return { code: 'invalid_key', hint: 'La clave ANTHROPIC_API_KEY no es válida o fue revocada. Crea una nueva en console.anthropic.com y actualízala en Vercel.' };
  if (/credit balance|billing|purchase credits|plans? & billing/i.test(msg)) return { code: 'billing', hint: 'La cuenta de Anthropic no tiene saldo. Agrega créditos en console.anthropic.com → Plans & Billing.' };
  if (err?.status === 404 || (/model/i.test(msg) && /not.?found|does not exist|not available|access/i.test(msg))) return { code: 'model_unavailable', hint: 'La clave no tiene acceso al modelo configurado. Revisa NEXBOT_MODEL / NEXBOT_FALLBACK_MODELS.' };
  if (err?.status === 403) return { code: 'forbidden', hint: 'La clave no tiene permiso para esta operación (revisa el workspace y los permisos de la clave).' };
  if (err?.status === 429) return { code: 'busy', hint: 'Límite de uso alcanzado; se reintenta más tarde.' };
  if (err?.status === 529 || err?.status >= 500) return { code: 'busy', hint: 'Servicio de Claude saturado o con error temporal.' };
  if (err?.status === 400) return { code: 'upstream_bad_request', hint: msg.slice(0, 200) };
  return { code: 'upstream', hint: msg.slice(0, 200) || 'Error de red hacia la API de Claude.' };
}
const isModelAccessError = err => ['model_unavailable', 'forbidden'].includes(classifyError(err).code);
const isFallbackParamError = err => err?.status === 400 && /fallback|anthropic-beta|beta/i.test(String(err?.error?.error?.message || err?.message || ''));

/** Real round-trip with a tiny request: tells the site owner exactly why the AI is (not) available. */
export async function diagnose() {
  let anthropic;
  try { anthropic = getClient(); } catch (e) { return { ok: false, ...classifyError(e) }; }
  const tried = [];
  for (const model of MODEL_CHAIN) {
    try {
      const r = await anthropic.messages.create({ model, max_tokens: 256, output_config: { effort: 'low' }, messages: [{ role: 'user', content: 'Responde solo: ok' }] });
      return { ok: true, model: r.model, tried };
    } catch (e) {
      const c = classifyError(e);
      tried.push({ model, status: e?.status ?? null, ...c });
      if (!isModelAccessError(e)) return { ok: false, ...c, status: e?.status ?? null, tried };
    }
  }
  return { ok: false, ...tried.at(-1), tried };
}

let client;
function getClient() {
  if (!process.env.ANTHROPIC_API_KEY && !process.env.ANTHROPIC_AUTH_TOKEN) {
    const e = new Error('ANTHROPIC_API_KEY no está configurada'); e.code = 'not_configured'; throw e;
  }
  return (client ??= new Anthropic({ maxRetries: 2, timeout: 55_000 }));
}

/** After a mid-output fallback, blocks before the last `fallback` marker other than text are not echoed back. */
function echoableContent(content) {
  const lastFallback = content.map(b => b.type).lastIndexOf('fallback');
  if (lastFallback < 0) return content;
  return content.filter((b, i) => i > lastFallback || b.type === 'text' || b.type === 'fallback');
}

/**
 * Runs one assistant turn.
 * @param {object} p
 * @param {Array<{role:string,content:string}>} p.messages  raw transcript from the browser
 * @param {'es'|'en'} [p.lang]     UI language hint
 * @param {string} [p.segment]     segment the visitor is browsing
 * @param {boolean} [p.voice]      the visitor spoke this message and will hear the reply
 * @param {(event:string, data:object)=>void} p.emit
 * @param {AbortSignal} [p.signal]
 */
export async function respond({ messages: raw, lang: uiLang, segment, voice, emit, signal }) {
  const { messages, flaggedSensitive } = sanitizeConversation(raw);
  const lastUser = messages[messages.length - 1].content;
  const lang = detectLanguage(lastUser, uiLang);
  emit('meta', { lang, kb: KB_VERSION });

  const quick = fastPath(lastUser, lang);
  if (quick) { emit('delta', { text: quick }); emit('done', { source: 'fast-path' }); return; }

  // Page context goes in its own block *after* the visitor's words, so the cached prefix stays intact.
  const seg = ['personas', 'pymes', 'empresas'].includes(segment) ? segment : 'personas';
  const context = `<page_context>ui_language=${uiLang === 'en' ? 'en' : 'es'}; detected_language=${lang}; segment=${seg}; input_mode=${voice === true ? 'voice' : 'text'}${flaggedSensitive ? '; note=the visitor tried to share a card number, PIN or code — it was removed; remind them never to share it' : ''}</page_context>`;
  const last = messages[messages.length - 1];
  const convo = [...messages.slice(0, -1), { role: 'user', content: [{ type: 'text', text: last.content }, { type: 'text', text: context }] }];

  const anthropic = getClient();
  let jsonRetries = 0, modelIdx = 0, useFallbacks = true;

  for (let round = 0; round <= MAX_TOOL_ROUNDS; round++) {
    let streamed = false;
    const stream = anthropic.beta.messages.stream({
      model: MODEL_CHAIN[modelIdx],
      max_tokens: 12000, // hard cap per answer for a public endpoint; covers thinking + reply
      ...(useFallbacks ? { betas: ['server-side-fallback-2026-07-01'], fallbacks: 'default' } : {}),
      thinking: { type: 'adaptive' },
      output_config: { effort: EFFORT },
      system: [
        { type: 'text', text: SYSTEM_PROMPT },
        { type: 'text', text: `<knowledge_base>\n${KNOWLEDGE}</knowledge_base>`, cache_control: { type: 'ephemeral' } },
      ],
      tools: TOOLS, // constant tool list keeps the prompt cache valid
      ...(round === MAX_TOOL_ROUNDS ? { tool_choice: { type: 'none' } } : {}),
      messages: convo,
    }, { signal });

    stream.on('text', text => { streamed = true; emit('delta', { text }); });

    let message;
    try {
      message = await stream.finalMessage();
    } catch (err) {
      // Configuration problems are recovered before anything was shown: next model in the chain,
      // or the same request without the optional server-side fallback beta.
      if (err instanceof Anthropic.APIError && !streamed && !signal?.aborted) {
        if (isModelAccessError(err) && modelIdx < MODEL_CHAIN.length - 1) { console.warn('[nexbot] model unavailable, trying', MODEL_CHAIN[modelIdx + 1]); modelIdx++; round--; continue; }
        if (useFallbacks && isFallbackParamError(err)) { console.warn('[nexbot] retrying without server-side fallbacks'); useFallbacks = false; round--; continue; }
      }
      // Only an unparseable streamed tool input is retried; other API errors propagate.
      if (err instanceof Anthropic.APIError || signal?.aborted || ++jsonRetries > 1) throw err;
      emit('reset', {});
      round--; continue;
    }

    if (message.stop_reason === 'refusal') {
      emit('reset', {});
      emit('delta', { text: lang === 'en'
        ? "I can't help with that here. For anything about your products, Línea Nexum and WhatsApp are available at (01) 555 0100.\n[[copy:(01) 555 0100|Copy number]]"
        : 'No puedo ayudarte con eso por aquí. Para cualquier gestión con tus productos, la Línea Nexum y WhatsApp están en el (01) 555 0100.\n[[copy:(01) 555 0100|Copiar número]]' });
      emit('done', { source: 'refusal' });
      return;
    }

    const toolUses = message.content.filter(b => b.type === 'tool_use');
    if (message.stop_reason !== 'tool_use' || !toolUses.length) {
      emit('done', { source: 'model', model: message.model, stop: message.stop_reason, usage: message.usage && {
        input: message.usage.input_tokens, cache_read: message.usage.cache_read_input_tokens, output: message.usage.output_tokens } });
      return;
    }

    convo.push({ role: 'assistant', content: echoableContent(message.content) });
    const results = await Promise.all(toolUses.map(async tu => {
      const problem = validateToolInput(tu.name, tu.input);
      if (problem) return { type: 'tool_result', tool_use_id: tu.id, is_error: true, content: `Invalid input: ${problem}` };
      emit('tool', { name: tu.name });
      try {
        const out = await runTool(tu.name, tu.input);
        if (tu.name.startsWith('simulate_')) emit('sim', out);
        return { type: 'tool_result', tool_use_id: tu.id, content: JSON.stringify(out) };
      } catch (e) {
        return { type: 'tool_result', tool_use_id: tu.id, is_error: true, content: `Tool failed: ${e.message}` };
      }
    }));
    convo.push({ role: 'user', content: results });
  }
  emit('done', { source: 'model', stop: 'tool_rounds_exhausted' });
}
