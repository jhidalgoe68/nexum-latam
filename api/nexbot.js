/**
 * NexBot — AI assistant for the Nexumtestbank demo page (/nexumtest/)
 * ──────────────────────────────────────────────────────────────────────────
 * Runtime  : Vercel Serverless Function (Node.js)
 * Route    : POST /api/nexbot   → text/event-stream (SSE)
 *            GET  /api/nexbot   → health check { ok, configured, model, kb }
 * Purpose  : Answers visitors in Spanish or English using Claude, grounded
 *            on the knowledge base compiled from nexumtest/index.html
 *            (api/_nexbot/knowledge.js), with server-side simulator tools.
 *            The API key is read ONLY from a server-side environment
 *            variable — it never reaches the browser.
 *
 * ── ONE-TIME SETUP ───────────────────────────────────────────────────────
 *   1. Vercel → this project → Settings → Environment Variables:
 *        ANTHROPIC_API_KEY        = <your Claude API key>      (required)
 *        NEXBOT_MODEL             = claude-opus-5-5            (optional)
 *        NEXBOT_EFFORT            = low | medium | high        (optional)
 *        NEXBOT_HANDOFF_WEBHOOK   = <n8n/Make webhook URL>     (optional:
 *                                   receives advisor-callback requests)
 *        NEXBOT_ALLOWED_ORIGINS   = extra comma-separated origins (optional)
 *   2. Redeploy. Until the key is set the page keeps working with its
 *      offline answer engine and shows "modo básico".
 * ─────────────────────────────────────────────────────────────────────────
 */
import { respond, BadRequest, MODEL } from './_nexbot/engine.js';
import { KB_VERSION } from './_nexbot/knowledge.js';

export const config = { maxDuration: 60 };

const ALLOWED_ORIGINS = [
  'https://nexum-latam.com',
  'https://www.nexum-latam.com',
  ...(process.env.NEXBOT_ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean),
];
const isAllowedOrigin = o =>
  !o || ALLOWED_ORIGINS.includes(o) || /^https:\/\/[a-z0-9-]+\.vercel\.app$/i.test(o) || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(o);

// Best-effort per-instance rate limit (serverless instances don't share memory).
const WINDOW_MS = 5 * 60_000, MAX_REQ = 30;
const hits = new Map();
function rateLimited(ip) {
  const now = Date.now();
  const list = (hits.get(ip) || []).filter(t => now - t < WINDOW_MS);
  list.push(now);
  hits.set(ip, list);
  if (hits.size > 5000) for (const [k, v] of hits) if (now - v[v.length - 1] > WINDOW_MS) hits.delete(k);
  return list.length > MAX_REQ;
}

function errorCode(err) {
  if (err?.code === 'not_configured') return ['not_configured', 503];
  switch (err?.status) {
    case 401: case 403: return ['not_configured', 503];
    case 429: return ['busy', 429];
    case 529: return ['busy', 503];
    case 400: return ['bad_request', 400];
    default: return ['upstream', 502];
  }
}

export default async function handler(req, res) {
  const origin = req.headers.origin;
  if (origin && isAllowedOrigin(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    res.setHeader('Vary', 'Origin');
  }
  if (req.method === 'OPTIONS') { res.status(204).end(); return; }
  if (req.method === 'GET') {
    res.status(200).json({ ok: true, configured: !!(process.env.ANTHROPIC_API_KEY || process.env.ANTHROPIC_AUTH_TOKEN), model: MODEL, kb: KB_VERSION });
    return;
  }
  if (req.method !== 'POST') { res.status(405).json({ ok: false, error: 'method_not_allowed' }); return; }
  if (!isAllowedOrigin(origin)) { res.status(403).json({ ok: false, error: 'origin_not_allowed' }); return; }

  const ip = String(req.headers['x-forwarded-for'] || req.socket?.remoteAddress || '').split(',')[0].trim();
  if (rateLimited(ip)) { res.status(429).json({ ok: false, error: 'rate_limited' }); return; }

  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch { body = null; } }
  if (!body || typeof body !== 'object') { res.status(400).json({ ok: false, error: 'bad_request' }); return; }

  res.writeHead(200, {
    'Content-Type': 'text/event-stream; charset=utf-8',
    'Cache-Control': 'no-cache, no-transform',
    'X-Accel-Buffering': 'no',
    Connection: 'keep-alive',
  });
  const emit = (event, data) => { if (!res.writableEnded) res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`); };

  const abort = new AbortController();
  res.on('close', () => { if (!res.writableFinished) abort.abort(); });

  try {
    await respond({ messages: body.messages, lang: body.lang, segment: body.segment, voice: body.voice === true, emit, signal: abort.signal });
  } catch (err) {
    if (!abort.signal.aborted) {
      const [code] = err instanceof BadRequest ? ['bad_request'] : errorCode(err);
      console.error('[nexbot]', code, err?.status || '', err?.message);
      emit('error', { code });
    }
  } finally {
    res.end();
  }
}
