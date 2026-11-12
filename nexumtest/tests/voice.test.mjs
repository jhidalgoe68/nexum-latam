// SmartIVR ChatBot API connector (api/nexbot-voice.js) — Claude and Redis are local mocks.
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';

const TOKEN = 'test-voice-token-123';
const requests = [];
let script = [];
const sse = events => events.map(e => `event: ${e.type}\ndata: ${JSON.stringify(e)}\n\n`).join('');
const textTurn = text => sse([
  { type: 'message_start', message: { id: 'm', type: 'message', role: 'assistant', model: 'claude-opus-5-5', content: [], stop_reason: null, stop_sequence: null, usage: { input_tokens: 1, output_tokens: 1 } } },
  { type: 'content_block_start', index: 0, content_block: { type: 'text', text: '' } },
  { type: 'content_block_delta', index: 0, delta: { type: 'text_delta', text } },
  { type: 'content_block_stop', index: 0 },
  { type: 'message_delta', delta: { stop_reason: 'end_turn', stop_sequence: null }, usage: { output_tokens: 5 } },
  { type: 'message_stop' }]);

let claude, redisSrv, app, base;
const redisData = new Map(), redisCmds = [];
before(async () => {
  claude = http.createServer(async (req, res) => {
    let raw = ''; for await (const c of req) raw += c;
    requests.push(JSON.parse(raw));
    res.writeHead(200, { 'Content-Type': 'text/event-stream' }).end(script.shift() || textTurn('ok'));
  });
  redisSrv = http.createServer(async (req, res) => {
    let raw = ''; for await (const c of req) raw += c;
    const cmd = JSON.parse(raw); redisCmds.push({ auth: req.headers.authorization, cmd });
    const result = cmd[0] === 'GET' ? (redisData.get(cmd[1]) ?? null) : (redisData.set(cmd[1], cmd[2]), 'OK');
    res.writeHead(200, { 'Content-Type': 'application/json' }).end(JSON.stringify({ result }));
  });
  await new Promise(r => claude.listen(0, r)); await new Promise(r => redisSrv.listen(0, r));
  Object.assign(process.env, {
    ANTHROPIC_BASE_URL: `http://127.0.0.1:${claude.address().port}`, ANTHROPIC_API_KEY: 'test-key', NEXBOT_VOICE_TOKEN: TOKEN,
  });
  const { default: handler } = await import('../../api/nexbot-voice.js');
  app = http.createServer(async (req, res) => {
    let raw = ''; for await (const c of req) raw += c;
    req.body = raw ? JSON.parse(raw) : undefined;
    res.status = c => { res.statusCode = c; return res; };
    res.json = o => { res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(o)); return res; };
    handler(req, res);
  });
  await new Promise(r => app.listen(0, r));
  base = `http://127.0.0.1:${app.address().port}/api/nexbot-voice`;
});
after(() => { claude.close(); redisSrv.close(); app.close(); });

const SMARTIVR_IP = '34.246.166.103';
const call = async (body, { token = TOKEN, phone = '666555444', ip = SMARTIVR_IP } = {}) => {
  const r = await fetch(base, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}`, 'X-Phone': phone, 'X-Destination': '0015550100', 'X-Real-IP': ip }, body: JSON.stringify(body) });
  return { status: r.status, json: await r.json() };
};
const VALID = new Set(['ask', 'info', 'transfer', 'hangup']);

test('rejects requests without the right Bearer token', async () => {
  assert.equal((await call({ id: 'x-1', text: 'hola' }, { token: 'wrong' })).status, 401);
  const r = await fetch(base, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Real-IP': SMARTIVR_IP }, body: '{"id":"x","text":"hola"}' });
  assert.equal(r.status, 401);
  assert.equal((await call({ text: 'sin id' })).status, 400);
});

test('only the SmartIVR public IP can consume the service', async () => {
  requests.length = 0;
  const other = await call({ id: 'ip-1', text: 'hola' }, { ip: '203.0.113.7' });
  assert.equal(other.status, 403, 'valid token from another IP is refused');
  const noIp = await fetch(base, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${TOKEN}` }, body: '{"id":"ip-2","text":"hola"}' });
  assert.equal(noIp.status, 403, 'request without the SmartIVR IP is refused');
  assert.equal(requests.length, 0, 'refused requests never reach Claude');
  const fwd = await fetch(base, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${TOKEN}`, 'X-Forwarded-For': `${SMARTIVR_IP}, 10.0.0.1` }, body: '{"id":"ip-3","text":""}' });
  assert.equal(fwd.status, 200, 'first X-Forwarded-For address is the client');
  process.env.NEXBOT_VOICE_ALLOWED_IPS = '198.51.100.1, 203.0.113.7';
  try {
    assert.equal((await call({ id: 'ip-4', text: '' }, { ip: '203.0.113.7' })).status, 200, 'list is configurable');
    assert.equal((await call({ id: 'ip-5', text: '' })).status, 403, 'replaces the default IP');
    process.env.NEXBOT_VOICE_ALLOWED_IPS = '*';
    assert.equal((await call({ id: 'ip-6', text: '' }, { ip: '192.0.2.9' })).status, 200, '"*" disables the filter');
  } finally { delete process.env.NEXBOT_VOICE_ALLOWED_IPS; }
});

test('phone answers are short: at most two sentences, amounts intact', async () => {
  const { concise } = await import('../../api/_nexbot/voice.js');
  assert.equal(concise('Financias $12.000 a 36 meses. Cuota de $435,20. Tasa 15,60% reajustable. ¿Algo más?'), 'Financias $12.000 a 36 meses. Cuota de $435,20.');
  assert.ok(concise('palabra '.repeat(80)).length <= 281);
  script = [textTurn('Tu pago contado es ₡580.518,07 y vence el 12/10/2026. El mínimo es ₡24.962,00. Si pagas solo el mínimo pagarás intereses. Te recomiendo pagar el contado.')];
  const r = await call({ id: 'short-1', text: '¿cuánto debo pagar?' });
  assert.equal(r.json.text, 'Tu pago contado es ₡580.518,07 y vence el 12/10/2026. El mínimo es ₡24.962,00.');
  const { SYSTEM_PROMPT } = await import('../../api/_nexbot/prompt.js');
  assert.match(SYSTEM_PROMPT, /On channel=phone be concrete and brief/);
});

test('health check reports configuration without exposing the token', async () => {
  const j = await (await fetch(base)).json();
  assert.deepEqual(j, { ok: true, configured: true, store: 'memory', transfer: false, ip_filter: true });
});

test('call flow: greeting, NexBot answer in plain speech with memory, goodbye then hangup', async () => {
  const id = '666555444-1784037502';
  const g = await call({ id, text: '' });
  assert.equal(g.json.type, 'ask'); assert.equal(g.json.lang, 'es-ES'); assert.match(g.json.text, /NexBot/);
  requests.length = 0;
  script = [textTurn('Puedes abrir tu **Cuenta Digital** en menos de 7 minutos.\n- Solo con tu documento\n[[demo:Apertura de Cuenta Digital|Abrir cuenta]]\n[[src:Cuenta Digital · verificado 11/10/2026]]')];
  const a = await call({ id, text: 'quiero abrir una cuenta' });
  assert.equal(a.json.type, 'ask');
  assert.equal(a.json.text, 'Puedes abrir tu Cuenta Digital en menos de 7 minutos. Solo con tu documento.');
  assert.doesNotMatch(a.json.text, /\[\[|\*\*/);
  assert.match(requests[0].messages.at(-1).content[1].text, /channel=phone/);
  assert.match(requests[0].messages.at(-1).content[1].text, /input_mode=voice/);
  assert.equal(requests[0].output_config.effort, 'low');
  script = [textTurn('Necesitas tu documento de identidad vigente.')];
  await call({ id, text: '¿qué requisitos hay?' });
  assert.equal(requests[1].messages.length, 3, 'second turn carries the call history');
  const bye = await call({ id, text: 'eso es todo, gracias' });
  assert.equal(bye.json.type, 'info'); assert.match(bye.json.text, /Gracias por llamar/);
  assert.deepEqual((await call({ id, text: '' })).json, { type: 'hangup' });
});

test('English callers get English answers with an en-US voice', async () => {
  script = [textTurn('You can open a Cuenta Digital in under 7 minutes.')];
  const r = await call({ id: '111-1', text: 'How can I open an account?' });
  assert.equal(r.json.lang, 'en-US'); assert.equal(r.json.type, 'ask');
});

test('silence: asks again, then says goodbye and hangs up', async () => {
  const id = '222-1';
  await call({ id, text: '' });
  assert.equal((await call({ id, text: '' })).json.type, 'ask');
  assert.equal((await call({ id, text: '' })).json.type, 'info');
  assert.equal((await call({ id, text: '' })).json.type, 'hangup');
});

test('agent requests transfer to the configured destination with metadata', async () => {
  process.env.NEXBOT_VOICE_TRANSFER_DEST = '0012025550147';
  try {
    const id = '333-1';
    const i = await call({ id, text: 'quiero hablar con un agente' }, { phone: '88887777' });
    assert.equal(i.json.type, 'info'); assert.match(i.json.text, /transfiero/);
    const t = await call({ id, text: '' }, { phone: '88887777' });
    assert.equal(t.json.type, 'transfer'); assert.equal(t.json.dest, '0012025550147');
    assert.deepEqual(t.json.metadata.map(m => m.name), ['X-NexBot-Conversation', 'X-CustomerPhone', 'X-NexBot-Reason']);
    assert.equal(t.json.metadata[1].value, '88887777');
    const e = await call({ id: '333-2', text: 'me robaron la tarjeta' });
    assert.equal(e.json.type, 'info', 'emergencies go to an agent too');
  } finally { delete process.env.NEXBOT_VOICE_TRANSFER_DEST; }
});

test('without a transfer destination, agent requests are answered by NexBot (hotline)', async () => {
  script = [textTurn('Puedes llamar a la Línea Nexum al (01) 555 0100.')];
  const r = await call({ id: '444-1', text: 'quiero hablar con un agente' });
  assert.equal(r.json.type, 'ask'); assert.match(r.json.text, /555 0100/);
});

test('every response follows the contract schema', async () => {
  for (const text of ['', 'hola', '¿cuánto cuesta la cuenta?', 'adiós']) {
    script = [textTurn('Claro, te ayudo.')];
    const { json } = await call({ id: '555-1', text });
    assert.ok(VALID.has(json.type), json.type);
    if (json.text !== undefined) assert.match(json.lang, /^[a-z]{2}-[A-Z]{2}$/);
    if (json.type === 'ask' || json.type === 'info') assert.equal(typeof json.text, 'string');
  }
});

test('call memory is shared through Redis when configured', async () => {
  process.env.UPSTASH_REDIS_REST_URL = `http://127.0.0.1:${redisSrv.address().port}`;
  process.env.UPSTASH_REDIS_REST_TOKEN = 'redis-token';
  try {
    assert.equal((await (await fetch(base)).json()).store, 'redis');
    await call({ id: '777-1', text: '' });
    const set = redisCmds.find(c => c.cmd[0] === 'SET');
    assert.equal(set.cmd[1], 'nexbot:call:777-1'); assert.deepEqual(set.cmd.slice(3), ['EX', 3600]);
    assert.equal(set.auth, 'Bearer redis-token');
  } finally { delete process.env.UPSTASH_REDIS_REST_URL; delete process.env.UPSTASH_REDIS_REST_TOKEN; }
});
