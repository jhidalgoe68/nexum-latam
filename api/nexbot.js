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
 *        NEXBOT_EFFORT            = low | medium | high        (optional, default medium)
 *        NEXBOT_FALLBACK_MODELS   = claude-sonnet-5-5          (optional: used if the key
 *                                   has no access to NEXBOT_MODEL)
 *        NEXBOT_HANDOFF_WEBHOOK   = <n8n/Make webhook URL>     (optional:
 *                                   receives advisor-callback requests)
 *        NEXBOT_ALLOWED_ORIGINS   = extra comma-separated origins (optional)
 *   2. Redeploy. Until the key is set the page keeps working with its
 *      offline answer engine and shows "modo básico".
 *   3. Verify: open /api/nexbot?check=1 — "check.ok": true means Claude
 *      answers; otherwise "check.code" and "check.hint" say what to fix.
 * ─────────────────────────────────────────────────────────────────────────
 */
import { respond } from './_nexbot/engine.js';
import { KB_VERSION } from './_nexbot/knowledge.js';
import { createChatHandler } from './_nexbot/http.js';

export const config = { maxDuration: 60 };

export default createChatHandler({
  tag: 'nexbot',
  kb: KB_VERSION,
  respond: (body, emit, signal) =>
    respond({ messages: body.messages, lang: body.lang, segment: body.segment, voice: body.voice === true, emit, signal }),
});
