/**
 * Shared Vercel handler for the site's Claude assistants (/api/nexbot, /api/nexseguro).
 * Same CORS whitelist, rate limit, health check (?check=1) and SSE transport for every bot.
 */
import { BadRequest, MODEL, MODEL_CHAIN, classifyError, diagnose } from './engine.js';

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

/**
 * @param {object} p
 * @param {string} p.tag        log prefix, e.g. 'nexbot'
 * @param {string} p.kb         knowledge base version reported by the health check
 * @param {(body:object, emit:Function, signal:AbortSignal)=>Promise<void>} p.respond
 */
export function createChatHandler({ tag, kb, respond }) {
  return async function handler(req, res) {
    const origin = req.headers.origin;
    if (origin && isAllowedOrigin(origin)) {
      res.setHeader('Access-Control-Allow-Origin', origin);
      res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
      res.setHeader('Vary', 'Origin');
    }
    if (req.method === 'OPTIONS') { res.status(204).end(); return; }
    if (req.method === 'GET') {
      const configured = !!(process.env.ANTHROPIC_API_KEY || process.env.ANTHROPIC_AUTH_TOKEN);
      const base = { ok: true, configured, model: MODEL, models: MODEL_CHAIN, kb, env: process.env.VERCEL_ENV || 'local' };
      // ?check=1 → real tiny call to Claude: shows the exact reason when the bot falls back to "modo básico".
      if (/[?&]check=1\b/.test(req.url || '')) {
        const ip = String(req.headers['x-forwarded-for'] || req.socket?.remoteAddress || '').split(',')[0].trim();
        if (rateLimited(ip)) { res.status(429).json({ ok: false, error: 'rate_limited' }); return; }
        res.setHeader('Cache-Control', 'no-store');
        res.status(200).json({ ...base, check: await diagnose() });
        return;
      }
      res.status(200).json(base);
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
      await respond(body, emit, abort.signal);
    } catch (err) {
      if (!abort.signal.aborted) {
        const { code, hint } = err instanceof BadRequest ? { code: 'bad_request', hint: err.message } : classifyError(err);
        console.error(`[${tag}]`, code, err?.status || '', err?.message);
        emit('error', { code, hint });
      }
    } finally {
      res.end();
    }
  };
}
