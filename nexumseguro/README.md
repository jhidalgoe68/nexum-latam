# NexumSeguro + NexBot (Claude)

`nexumseguro/index.html` is the NexumSeguro insurance page (health, life and travel). Its assistant, **NexBot**, is powered by Claude through `/api/nexseguro`. It uses the same engine, API key and models as the NexBot of `/nexumtest/`.

## How it works

```
Browser (index.html)                 Vercel function (api/nexseguro.js)            Claude API
─────────────────────                ──────────────────────────────────            ──────────
floating button / "Asistente IA" ─▶  1. validate + redact card numbers, PINs
  · streams the reply (SSE)          2. medical emergencies → instant answer
  · safe Markdown, whitelisted       3. shared agent loop (api/_nexbot/engine.js) ─▶ same key, model
    buttons: go:<section>,              knowledge of the page (cached)              and fallbacks
    quote:salud|vida|viajes, ask:       tools: simulate_life_cover,                 as /api/nexbot
  · life-cover result card              request_advisor_callback
  · ES / EN (follows the page toggle), voice, session memory
  · offline fallback: searches the page's own text ("Modo básico")
```

- **Grounded on the page.** `api/_nexseguro/knowledge.js` is generated from `index.html` by `tools/build-knowledge.mjs`: the copy of every section in Spanish, and in English from the page's own EN dictionary. Placeholders still highlighted on the page (phone, email, address, figures, rating, testimonial) are marked **NO PUBLICADO**, so the bot says they are not published yet instead of quoting them.
- **Interprets intent.** A semantic layer in the prompt maps everyday wording ("si me pasa algo", "perdieron mi maleta", "mis empleados", "¿me devuelven lo que pagué?") to the right plan, section or claim step, and recommends plans as **Recomendación → Por qué → Qué confirmar con un asesor → Siguiente paso**. It addresses visitors as "usted", like the site.
- **Page context.** Each question carries the plan selected in "Cotice en un minuto" and the country selector value. A `quote:` button preselects the plan in that form and focuses the email field.
- **Life cover.** `simulate_life_cover` computes an educational needs-based estimate (income × years + debts + education + final expenses − savings − existing cover). It is not a quote.
- **Guardrails.** Medical emergencies skip the model and tell the visitor to call 911 or the local emergency number first. No prices, limits or exclusions are invented (the site doesn't publish them). Card numbers and PINs are removed before reaching the model; health details and policy numbers are never requested.
- **Advisor handoff.** If `NEXSEGURO_HANDOFF_WEBHOOK` (or, if unset, `NEXBOT_HANDOFF_WEBHOOK`) is set, consented callback requests are POSTed there as JSON with `source: "nexumseguro"` and fields `ticket, first_name, contact, plan, policyholder_age, people, country, topic, preferred_time, language`.

## Setup

Nothing new: it reads the same Vercel environment variables as `/api/nexbot` (`ANTHROPIC_API_KEY`, `NEXBOT_MODEL`, `NEXBOT_EFFORT`, `NEXBOT_FALLBACK_MODELS`, `NEXBOT_ALLOWED_ORIGINS`). Diagnose with `https://<your-domain>/api/nexseguro?check=1`.

## When you change the page

```bash
npm run nexseguro:kb   # regenerate the knowledge base
npm test               # fails if knowledge.js is out of date
npm run nexbot:dev     # http://localhost:3000/nexumseguro/
```
