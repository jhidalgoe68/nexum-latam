# Nexumtestbank + NexBot (Claude)

`nexumtest/index.html` is the Nexumtestbank demo bank page. Its assistant, **NexBot**, is powered by Claude through `/api/nexbot`. It was previously a static keyword matcher.

## How it works

```
Browser (index.html)                Vercel function (api/nexbot.js)               Claude API
─────────────────────               ─────────────────────────────────             ──────────
chat widget / FAB / hero  ──POST──▶ 1. validate + redact card numbers, PINs
  · streams the reply (SSE)         2. emergencies → instant answer (no model)
  · renders Markdown safely         3. agent loop ─────────────────────────────▶  claude-opus-5-5
  · whitelisted action buttons         system prompt + knowledge base (cached)     adaptive thinking
  · simulation cards that pre-fill     tools: simulate_loan / term_deposit /       server-side
    the page simulators                savings_goal / request_advisor_callback     refusal fallback
  · ES / EN, session memory         4. events: meta · delta · tool · sim · done
  · offline fallback: the page's
    original answer engine
```

- **Grounded on the page.** `api/_nexbot/knowledge.js` is generated from `index.html` by `tools/build-knowledge.mjs`. It covers all 75 products, the cards and reward programs, the 23 FAQs, channels, campaigns, simulator ranges and the copy of every section. NexBot answers only from it. When something isn't published, it says so and points to Línea Nexum.
- **Exact numbers.** Loan, term-deposit and Ahorro Meta figures come from server-side tools that use the same formulas and slider ranges as the page simulators, so the model never does arithmetic. A test checks them against the page's own `amortTable()`.
- **Sample statement.** NexBot can read and explain the fictional card statement in the "Movimientos" section: concepts such as fecha de corte, pago contado vs. mínimo, intereses and límite disponible, plus any of its figures. For sums and rankings ("¿cuánto gasté en supermercados?") it calls `query_statement` (`api/_nexbot/statement.js`) for exact totals by merchant, category, card or dates. A `[[mov:…]]` button filters the table on the page.
- **Voice.** The 🎙 button lets the customer speak. The browser transcribes (`SpeechRecognition`, Spanish es-MX or English en-US), and the message is sent as a voice turn: Claude answers in short, speakable sentences. The reply is read aloud sentence by sentence as it streams (`speechSynthesis`, preferring a Latin-American voice), then the mic reopens for a hands-free conversation until the customer pauses, taps the mic or types. The 🔊 toggle in the chat header reads every reply aloud, and each message has an "Escuchar" button. No extra API key or service is needed. Speech recognition works in Chrome, Edge and Safari (in Chrome the audio is processed by the browser's speech service). Where it isn't available, such as Firefox, the mic button is hidden and reading aloud still works.
- **Bilingual.** NexBot replies in the language of each message (Spanish or English), and the chat's buttons and labels switch with it.
- **Guardrails.** Card numbers, PINs and codes are removed before anything reaches the model. Theft and fraud reports skip the model and go straight to the hotline. Off-topic requests are declined, and visitor text is never treated as instructions. Action buttons are limited to a fixed list of page destinations.
- **Advisor handoff.** If `NEXBOT_HANDOFF_WEBHOOK` is set (for example an **n8n** Webhook node), callback requests that the visitor consented to are POSTed there as JSON with fields `ticket, first_name, contact, segment, topic, preferred_time, language`.

## Setup (Vercel)

1. Project → Settings → Environment Variables:
   - `ANTHROPIC_API_KEY`: required.
   - `NEXBOT_MODEL`: optional, default `claude-opus-5-5`.
   - `NEXBOT_EFFORT`: optional, default `low` (fastest replies). Use `medium` for deeper answers.
   - `NEXBOT_HANDOFF_WEBHOOK`: optional, your n8n/Make/Zapier webhook URL.
   - `NEXBOT_ALLOWED_ORIGINS`: optional, extra comma-separated domains allowed to call the API.
2. Redeploy, then open `https://<your-domain>/nexumtest/`.

Until the key is set, the page still works: the chat header shows **Modo básico** and answers come from the page's original engine.

## Local development

```bash
npm install
ANTHROPIC_API_KEY=sk-ant-... npm run nexbot:dev   # http://localhost:3000/nexumtest/
npm test                                         # no key needed; Claude is mocked
```

## When you change the page

Regenerate the knowledge base so NexBot learns the new content:

```bash
npm run nexbot:kb
```

`npm test` fails if `knowledge.js` is out of date with `index.html`.
