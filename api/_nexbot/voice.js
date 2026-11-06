/**
 * NexBot — phone channel for the SmartIVR "ChatBot API connector" contract
 * (https://chatbotapi.smartivr.ivrpowers.com/).
 * ──────────────────────────────────────────────────────────────────────────
 * The SmartIVR POSTs { id: "PHONE-CALLTIMESTAMP", text: "<user speech>" } on
 * every user turn and expects one action back:
 *   ask      → play text, then listen          { type, text, lang }
 *   info     → play text, then call us again with text ""   { type, text, lang }
 *   transfer → transfer the call to `dest`     { type, dest, metadata[] }
 *   hangup   → end the call                    { type }
 *
 * The same NexBot brain as the web chat answers (knowledge base, simulators,
 * statement analysis), with channel=phone so replies are short and speakable.
 * Conversation state lives in Redis (Upstash / Vercel KV REST) when configured,
 * otherwise in this instance's memory (fine for testing, not for production).
 */
import { respond, fastPath, detectLanguage } from './engine.js';

const env = (k, d = '') => (process.env[k] ?? d).trim();
const TTL_S = 60 * 60; // a call's memory lives one hour
const MAX_TURNS = 24;

// ── Conversation store ───────────────────────────────────────────────────
const mem = new Map();
function redisConfig() {
  const url = env('UPSTASH_REDIS_REST_URL') || env('KV_REST_API_URL');
  const token = env('UPSTASH_REDIS_REST_TOKEN') || env('KV_REST_API_TOKEN');
  return url && token ? { url: url.replace(/\/$/, ''), token } : null;
}
export const storeKind = () => (redisConfig() ? 'redis' : 'memory');

async function redis(cmd) {
  const { url, token } = redisConfig();
  const r = await fetch(url, { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify(cmd), signal: AbortSignal.timeout(3000) });
  if (!r.ok) throw new Error(`redis ${r.status}`);
  return (await r.json()).result;
}
export async function loadState(id) {
  const key = `nexbot:call:${id}`;
  try {
    if (redisConfig()) { const v = await redis(['GET', key]); return v ? JSON.parse(v) : null; }
  } catch (e) { console.error('[nexbot-voice] store read failed:', e.message); }
  const m = mem.get(key);
  return m && m.exp > Date.now() ? m.state : null;
}
export async function saveState(id, state) {
  const key = `nexbot:call:${id}`;
  try {
    if (redisConfig()) { await redis(['SET', key, JSON.stringify(state), 'EX', TTL_S]); return; }
  } catch (e) { console.error('[nexbot-voice] store write failed:', e.message); }
  mem.set(key, { state, exp: Date.now() + TTL_S * 1000 });
  if (mem.size > 2000) for (const [k, v] of mem) if (v.exp < Date.now()) mem.delete(k);
}

// ── Phrases and intents ──────────────────────────────────────────────────
const LANG = { es: () => env('NEXBOT_VOICE_LANG_ES', 'es-ES'), en: () => env('NEXBOT_VOICE_LANG_EN', 'en-US') };
const SAY = {
  greet: { es: 'Hola, te atiende NexBot, el asistente virtual de Nexumtestbank. ¿En qué te puedo ayudar? También puedes hablarme en inglés.', en: "Hi, this is NexBot, Nexumtestbank's virtual assistant. How can I help you? You can also speak to me in Spanish." },
  still: { es: '¿Sigues ahí? Dime en qué te puedo ayudar.', en: 'Are you still there? Tell me how I can help you.' },
  bye: { es: 'Gracias por llamar a Nexumtestbank. ¡Que tengas un excelente día!', en: 'Thank you for calling Nexumtestbank. Have a great day!' },
  transfer: { es: 'Con gusto. Te transfiero con un agente, un momento por favor.', en: "Sure. I'm transferring you to an agent, one moment please." },
  error: { es: 'Disculpa, tuve un problema técnico. ¿Me lo puedes repetir?', en: 'Sorry, I had a technical problem. Could you say that again?' },
  down: { es: 'En este momento el asistente no está disponible. Puedes llamar a la Línea Nexum al cero uno, cinco cinco cinco, cero uno cero cero. Gracias.', en: 'The assistant is not available right now. Please call Línea Nexum at zero one, five five five, zero one zero zero. Thank you.' },
};
const HUMAN_RE = /\b(agente|asesor(a)?|ejecutiv[oa]|operador(a)?|una persona|persona real|un humano|humano|representante|hablar con alguien|asistencia|agent|human|representative|operator|real person|someone)\b/i;
const BYE_RE = /^(\W*(adi[oó]s|chao|chau|bye|good ?bye|hasta (luego|pronto)|eso es todo|eso ser[ií]a todo|nada m[aá]s|no,? gracias|that'?s all|nothing else|no,? thanks?)\W*)+(gracias|thank you|thanks)?\W*$/i;

export const plainSpeech = text => String(text)
  .replace(/\[\[[^\]]*\]\]/g, ' ')                 // action / source tags
  .replace(/\*\*|__|`|^#+\s*/gm, '')               // markdown emphasis and headings
  .replace(/^\s*(?:[-*•]|\d+[.)])\s+/gm, '')       // list markers
  .replace(/\p{Extended_Pictographic}️?/gu, '')
  .replace(/[→×|]/g, ' ')
  .replace(/\s*\n+\s*/g, '. ').replace(/\.\s*\./g, '.').replace(/\s{2,}/g, ' ')
  .trim().slice(0, 900);

const transferDest = () => env('NEXBOT_VOICE_TRANSFER_DEST');
function transferAction(id, phone, reason) {
  return {
    type: 'transfer', dest: transferDest(),
    metadata: [
      { name: 'X-NexBot-Conversation', value: String(id).slice(0, 120) },
      ...(phone ? [{ name: 'X-CustomerPhone', value: String(phone).slice(0, 40) }] : []),
      { name: 'X-NexBot-Reason', value: String(reason || 'Solicitud de agente').replace(/[\r\n]+/g, ' ').slice(0, 200) },
    ],
  };
}

// ── One turn of the call ─────────────────────────────────────────────────
/**
 * @param {object} p
 * @param {string} p.id          conversation id "PHONE-CALLTIMESTAMP"
 * @param {string} p.text        transcription of the user speech ('' after an `info`, or on silence)
 * @param {string} [p.phone]     X-Phone header
 * @param {string} [p.destination] X-Destination header
 * @param {AbortSignal} [p.signal]
 * @returns {Promise<{type:string,text?:string,lang?:string,dest?:string,metadata?:Array}>}
 */
export async function voiceTurn({ id, text, phone, destination, signal }) {
  const st = (await loadState(id)) || { hist: [], lang: 'es', empties: 0, errors: 0, ending: false, pendingTransfer: null, phone, destination };
  const say = (type, key, lang = st.lang) => ({ type, text: SAY[key][lang], lang: LANG[lang]() });
  const done = async action => { await saveState(id, st); return action; };
  const input = String(text || '').trim();

  // Follow-ups to our own `info` actions (the IVR calls back with an empty text).
  if (st.ending) { st.hist = []; await saveState(id, { ...st, ended: true }); return { type: 'hangup' }; }
  if (st.pendingTransfer && !input) { const t = transferAction(id, phone || st.phone, st.pendingTransfer); st.pendingTransfer = null; st.transferred = true; return done(t); }
  st.pendingTransfer = null;

  if (!input) {
    if (!st.hist.length && !st.greeted) { st.greeted = true; return done(say('ask', 'greet')); }
    st.empties += 1;
    if (st.empties >= 2) { st.ending = true; return done(say('info', 'bye')); }
    return done(say('ask', 'still'));
  }
  st.empties = 0;
  st.lang = detectLanguage(input, st.lang);

  if (BYE_RE.test(input)) { st.ending = true; st.hist.push({ role: 'user', content: input }); return done(say('info', 'bye')); }

  // Person / agent requested, or an emergency (stolen card, fraud…): hand over to a human if a destination is configured.
  const wantsHuman = HUMAN_RE.test(input) || !!fastPath(input, st.lang);
  if (wantsHuman && transferDest()) {
    st.hist.push({ role: 'user', content: input }, { role: 'assistant', content: SAY.transfer[st.lang] });
    st.pendingTransfer = input;
    return done(say('info', 'transfer'));
  }

  // Everything else: NexBot answers (same brain as the web chat, phone-friendly).
  st.hist.push({ role: 'user', content: input });
  let reply = '', lang = st.lang;
  const ctrl = new AbortController();
  const onAbort = () => ctrl.abort();
  signal?.addEventListener('abort', onAbort);
  const timer = setTimeout(() => ctrl.abort(), +env('NEXBOT_VOICE_TIMEOUT_MS', '25000'));
  try {
    await respond({
      messages: st.hist.slice(-MAX_TURNS), lang: st.lang, segment: 'personas', voice: true, channel: 'phone',
      effort: env('NEXBOT_VOICE_EFFORT', 'low'), signal: ctrl.signal,
      emit: (ev, data) => {
        if (ev === 'meta' && data.lang) lang = data.lang;
        else if (ev === 'delta') reply += data.text;
        else if (ev === 'reset') reply = '';
        else if (ev === 'error') throw Object.assign(new Error(data.code), { code: data.code });
      },
    });
  } catch (e) {
    console.error('[nexbot-voice]', id, e?.code || e?.status || '', e?.message);
    st.hist.pop();
    st.errors += 1;
    if (e?.code === 'not_configured' || e?.status === 401 || st.errors >= 3) {
      if (transferDest()) { st.pendingTransfer = 'El asistente no está disponible'; return done(say('info', 'transfer')); }
      st.ending = true; return done(say('info', 'down'));
    }
    return done(say('ask', 'error'));
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', onAbort);
  }

  st.lang = lang === 'en' ? 'en' : 'es';
  const wantsAssist = /\[\[assist:/.test(reply);
  const spoken = plainSpeech(reply) || SAY.error[st.lang];
  st.hist.push({ role: 'assistant', content: spoken });
  st.hist = st.hist.slice(-MAX_TURNS);
  if (wantsAssist && transferDest()) { st.pendingTransfer = input; return done({ type: 'info', text: `${spoken} ${SAY.transfer[st.lang]}`, lang: LANG[st.lang]() }); }
  return done({ type: 'ask', text: spoken, lang: LANG[st.lang]() });
}
