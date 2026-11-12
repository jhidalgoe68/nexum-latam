/**
 * NexBot — phone channel (SmartIVR ChatBot API connector)
 * ──────────────────────────────────────────────────────────────────────────
 * Runtime  : Vercel Serverless Function (Node.js)
 * Route    : POST /api/nexbot-voice   ← called by the SmartIVR on every user turn
 *            GET  /api/nexbot-voice   → status { ok, configured, store, transfer, ip_filter } (no bot access)
 * Contract : https://chatbotapi.smartivr.ivrpowers.com/
 *   Request  headers: Authorization: Bearer <TOKEN>, Content-Type: application/json,
 *                     X-Phone, X-Destination
 *            body:    { "id": "PHONE-CALLTIMESTAMP", "text": "user speech" }
 *   Response { "type": "ask" | "info" | "transfer" | "hangup", text?, lang?, dest?, metadata? }
 *
 * ── SETUP (Vercel → Settings → Environment Variables → Production) ───────
 *   NEXBOT_VOICE_TOKEN          (required) the security token given to the SmartIVR
 *   NEXBOT_VOICE_ALLOWED_IPS    (optional) comma-separated public IPs allowed to call
 *                               the service; default 34.246.166.103 (SmartIVR demo).
 *                               "*" disables the filter.
 *   ANTHROPIC_API_KEY           (required, already used by the web chat)
 *   NEXBOT_VOICE_TRANSFER_DEST  (optional) DDI or extension for "talk to an agent";
 *                               without it the bot gives Línea Nexum instead
 *   UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN (or KV_REST_API_URL /
 *   KV_REST_API_TOKEN)          (recommended) call memory shared by all instances
 *   NEXBOT_VOICE_LANG_ES / _EN  (optional) BCP 47 voices, default es-ES / en-US
 *   NEXBOT_VOICE_EFFORT         (optional) default low (fast spoken answers)
 * Redeploy after changing variables.
 * ─────────────────────────────────────────────────────────────────────────
 */
import { timingSafeEqual } from 'node:crypto';
import { voiceTurn, storeKind } from './_nexbot/voice.js';

export const config = { maxDuration: 60 };

// Only the SmartIVR may consume the service (demo): other source IPs get 403 before anything runs.
const DEFAULT_ALLOWED_IPS = '34.246.166.103';
const allowedIps = () => (process.env.NEXBOT_VOICE_ALLOWED_IPS ?? DEFAULT_ALLOWED_IPS).split(',').map(s => s.trim()).filter(Boolean);
/** Caller's public IP. On Vercel, x-real-ip / x-forwarded-for are set by the platform (client values are overwritten). */
export function clientIp(req) {
  const h = req.headers;
  return String(h['x-real-ip'] || h['x-vercel-forwarded-for'] || h['x-forwarded-for'] || req.socket?.remoteAddress || '')
    .split(',')[0].trim().replace(/^::ffff:/, '');
}
const ipAllowed = ip => { const list = allowedIps(); return list.includes('*') || list.includes(ip); };

function tokenOk(header) {
  const expected = (process.env.NEXBOT_VOICE_TOKEN || '').trim();
  const m = /^Bearer\s+(.+)$/i.exec(String(header || '').trim());
  if (!expected || !m) return false;
  const a = Buffer.from(m[1].trim()), b = Buffer.from(expected);
  return a.length === b.length && timingSafeEqual(a, b);
}

export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method === 'GET') {
    res.status(200).json({ ok: true, configured: !!(process.env.NEXBOT_VOICE_TOKEN || '').trim(), store: storeKind(), transfer: !!(process.env.NEXBOT_VOICE_TRANSFER_DEST || '').trim(), ip_filter: !allowedIps().includes('*') });
    return;
  }
  if (req.method !== 'POST') { res.status(405).json({ error: 'method_not_allowed' }); return; }
  const ip = clientIp(req);
  if (!ipAllowed(ip)) { console.warn('[nexbot-voice] blocked request from', ip || 'unknown IP'); res.status(403).json({ error: 'forbidden' }); return; }
  if (!(process.env.NEXBOT_VOICE_TOKEN || '').trim()) { res.status(503).json({ error: 'voice_channel_not_configured' }); return; }
  if (!tokenOk(req.headers.authorization)) { res.status(401).json({ error: 'unauthorized' }); return; }

  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch { body = null; } }
  const id = typeof body?.id === 'string' ? body.id.trim().slice(0, 128) : '';
  const text = typeof body?.text === 'string' ? body.text.slice(0, 2000) : body?.text == null ? '' : null;
  if (!id || text === null) { res.status(400).json({ error: 'bad_request', detail: 'Se esperan los campos "id" (string) y "text" (string).' }); return; }

  const abort = new AbortController();
  res.on('close', () => { if (!res.writableFinished) abort.abort(); });
  try {
    const action = await voiceTurn({ id, text, phone: req.headers['x-phone'], destination: req.headers['x-destination'], signal: abort.signal });
    res.status(200).json(action);
  } catch (e) {
    console.error('[nexbot-voice] unexpected', e?.message);
    res.status(200).json({ type: 'ask', text: 'Disculpa, tuve un problema técnico. ¿Me lo puedes repetir?', lang: (process.env.NEXBOT_VOICE_LANG_ES || 'es-ES').trim() });
  }
}
