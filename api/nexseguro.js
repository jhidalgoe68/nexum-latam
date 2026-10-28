/**
 * NexBot Seguro — AI assistant for the NexumSeguro page (/nexumseguro/)
 * ──────────────────────────────────────────────────────────────────────────
 * Runtime  : Vercel Serverless Function (Node.js)
 * Route    : POST /api/nexseguro   → text/event-stream (SSE)
 *            GET  /api/nexseguro   → health check { ok, configured, model, kb }
 *            GET  /api/nexseguro?check=1 → real round-trip diagnostic
 * Purpose  : Answers visitors in Spanish or English using Claude, grounded
 *            on the knowledge base compiled from nexumseguro/index.html
 *            (api/_nexseguro/knowledge.js).
 *
 * Uses the SAME configuration as /api/nexbot — no new keys needed:
 *   ANTHROPIC_API_KEY (required), NEXBOT_MODEL, NEXBOT_EFFORT,
 *   NEXBOT_FALLBACK_MODELS, NEXBOT_ALLOWED_ORIGINS.
 *   Advisor callbacks go to NEXSEGURO_HANDOFF_WEBHOOK, or NEXBOT_HANDOFF_WEBHOOK if unset.
 * ─────────────────────────────────────────────────────────────────────────
 */
import { respond } from './_nexseguro/engine.js';
import { KB_VERSION } from './_nexseguro/knowledge.js';
import { createChatHandler } from './_nexbot/http.js';

export const config = { maxDuration: 60 };

export default createChatHandler({
  tag: 'nexseguro',
  kb: KB_VERSION,
  respond: (body, emit, signal) =>
    respond({ messages: body.messages, lang: body.lang, product: body.product, country: body.country, voice: body.voice === true, emit, signal }),
});
