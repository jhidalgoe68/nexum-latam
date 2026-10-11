#!/usr/bin/env node
/**
 * NexBot — knowledge base compiler
 * ──────────────────────────────────────────────────────────────────────────
 * Reads nexumtest/index.html (the Nexumtestbank page) and compiles EVERYTHING
 * the page publishes into api/_nexbot/knowledge.js, which the /api/nexbot
 * function loads as NexBot's grounding context:
 *
 *   · The page's data layer (products, cards, loyalty programs, FAQ,
 *     channels, operations matrix, campaigns, segment heroes) — evaluated
 *     from the page's own <script> in an isolated VM, so nothing is retyped.
 *   · Simulator ranges, defaults and disclaimers — parsed from renderSim().
 *   · All static copy in <header>, every <section> and the <footer>.
 *
 * Run it every time index.html changes:
 *     npm run nexbot:kb            (writes the file)
 *     npm run nexbot:kb -- --check (exit 1 if the committed file is stale)
 * ─────────────────────────────────────────────────────────────────────────
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import vm from 'node:vm';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const PAGE = path.join(ROOT, 'nexumtest', 'index.html');
const OUT  = path.join(ROOT, 'api', '_nexbot', 'knowledge.js');

const html = readFileSync(PAGE, 'utf8');

// ── 1. Data layer, evaluated from the page script ────────────────────────
const script = html.slice(html.lastIndexOf('<script>') + 8, html.lastIndexOf('</script>'));
const start = script.indexOf('const ASOF=');
const end = script.indexOf('let seg=');
if (start < 0 || end < 0) throw new Error('No se encontró la capa de datos (const ASOF … let seg=) en index.html');
const data = vm.runInNewContext(
  `(function(){${script.slice(start, end)}
   return {ASOF,P,LOY,FAQ,CHANNELS,OPS,OPS_COLS,CAMPS,SEGS,CATS};})()`,
  {}, { timeout: 2000 },
);

// ── 2. Simulators (ranges + notes) parsed from renderSim() ───────────────
const simSrc = script.slice(script.indexOf('function renderSim('), script.indexOf('/* ---------- Channels'));
const SIM_KEYS = { consumo: 'Crédito en línea', auto: 'Crédito Automotriz', hipo: 'Crédito Hipotecario', cdp: 'Depósito a Plazo', ahorro: 'Ahorro Meta' };
const UNITS = { m: 'USD', mo: 'meses', y: 'años', p: '%', d: 'días' };
const sims = {};
for (const block of simSrc.split(/if\(simCur==='/).slice(1)) {
  const key = block.slice(0, block.indexOf("'"));
  const fields = [...block.matchAll(/rangeField\('([^']+)','([^']+)',([\d.]+),([\d.]+),([\d.]+),([\d.]+),'(\w+)'\)/g)]
    .map(([, id, label, min, max, step, def, fmt]) => ({ id, label, min: +min, max: +max, step: +step, default: +def, unit: UNITS[fmt] || fmt }));
  const notes = [...block.matchAll(/note:'([^']+)'/g), ...block.matchAll(/<p class="note"[^>]*>([^<]+)</g)].map(m => m[1].trim());
  const extras = [...block.matchAll(/<input type="checkbox" id="[^"]+"(?: checked)?> ([^<]+)<\/label>/g)].map(m => m[1].trim());
  sims[key] = { name: SIM_KEYS[key] || key, fields, notes, options: extras };
}

// ── 3. Static copy, per section ──────────────────────────────────────────
const decode = s => s
  .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
  .replace(/&quot;/g, '"').replace(/&#39;/g, "'");
const textOf = frag => decode(frag
  .replace(/<(script|style|svg)[\s\S]*?<\/\1>/gi, ' ')
  .replace(/<(br|\/p|\/li|\/h\d|\/div|\/dd|\/span|\/b|\/strong|\/small|\/kbd|\/a|\/button)\s*>/gi, m => (/^<\/(b|strong|small|a|span|kbd)/i.test(m) ? ' ' : '\n'))
  .replace(/<[^>]+>/g, ' '))
  .split('\n').map(l => l.replace(/\s+/g, ' ').trim()).filter(Boolean)
  .filter((l, i, a) => a.indexOf(l) === i)
  .join('\n');

const sections = [];
const banner = html.match(/<div class="demo"[\s\S]*?<\/div><\/div>/);
if (banner) sections.push(['Aviso del sitio', textOf(banner[0])]);
const header = html.match(/<header class="top"[\s\S]*?<\/header>/);
if (header) sections.push(['Encabezado', textOf(header[0])]);
for (const m of html.matchAll(/<section([^>]*)>([\s\S]*?)<\/section>/g)) {
  const id = (m[1].match(/\bid="([^"]+)"/) || [, 'inicio'])[1];
  if (id === 'asistente') continue; // the bot's own widget copy is in the system prompt
  const t = textOf(m[2]);
  if (t) sections.push([`#${id}`, t]);
}
const footer = html.match(/<footer>[\s\S]*?<\/footer>/);
if (footer) sections.push(['Pie de página', textOf(footer[0])]);

// ── 4. Render the knowledge document (Markdown, Spanish = source) ────────
const { ASOF, P, LOY, FAQ, CHANNELS, OPS, OPS_COLS, CAMPS, SEGS, CATS } = data;
const catLabel = Object.fromEntries(Object.values(CATS).flat());
const segLabel = { personas: 'Personas', pymes: 'Pymes', empresas: 'Empresas' };
const L = [];
L.push(`# Base de conocimiento de Nexumtestbank`);
L.push(`Fuente única: sitio público de Nexumtestbank (banco ficticio de demostración). Tasas y datos verificados al ${ASOF}.`);

L.push(`\n## Productos y servicios (catálogo completo)`);
for (const seg of Object.keys(CATS)) {
  L.push(`\n### Segmento ${segLabel[seg]}`);
  for (const [cat, label] of CATS[seg]) {
    const items = P.filter(p => p.seg === seg && p.cat === cat);
    if (!items.length) continue;
    L.push(`\n#### ${label}`);
    for (const p of items) {
      const kv = p.kv.length ? ' · ' + p.kv.map(([k, v]) => `${k}: ${v}`).join(' · ') : '';
      const tags = [p.green && 'producto verde', p.sim && `simulador: ${SIM_KEYS[p.sim]}`, p.tier && `nivel ${p.tier}`].filter(Boolean).join(', ');
      L.push(`- **${p.n}** [id:${p.id}] — ${p.d}${kv}. Acción principal: “${p.cta}”${tags ? ` (${tags})` : ''}. Sinónimos de búsqueda: ${p.k || '—'}.`);
    }
  }
}

L.push(`\n## Programas de recompensa (tabla “Cinco formas de que tus compras te devuelvan algo”)`);
L.push(`Ninguno acumula por avances de efectivo, gasolineras ni servicios públicos. Los puntos no caducan mientras uses tu tarjeta.`);
for (const [n, acc, bono, canje, cards] of LOY) L.push(`- **${n}** — Acumulación: ${acc}. Bono de bienvenida: ${bono}. Canje: ${canje}. Tarjetas: ${cards}.`);

L.push(`\n## Simuladores (sección “Calcula antes de decidir”)`);
L.push(`Resultados referenciales con tasas de demostración. La cuota final depende de la evaluación de crédito. Créditos: tabla francesa (cuota fija) o alemana (capital fijo, cuota decreciente).`);
for (const [key, s] of Object.entries(sims)) {
  L.push(`- **${s.name}** [sim:${key}] — ` + s.fields.map(f => `${f.label}: ${f.min}–${f.max} ${f.unit} (predeterminado ${f.default})`).join('; ') +
    (s.options.length ? `. Opciones: ${s.options.join('; ')}` : '') + (s.notes.length ? `. Notas: ${s.notes.join(' ')}` : ''));
}

L.push(`\n## Preguntas frecuentes (sección “Respuestas rápidas”)`);
for (const [cat, q, a] of FAQ) L.push(`- [${catLabel[cat] || cat}] **${q}** ${a}`);

L.push(`\n## Canales (“Diez canales, una misma cuenta”)`);
for (const [n, m, d] of CHANNELS) L.push(`- **${n}** (${m}): ${d}`);
L.push(`\n### Qué operación se puede hacer en qué canal`);
for (const [op, v] of OPS) L.push(`- ${op}: ${OPS_COLS.filter((_, i) => v[i]).join(', ')}.`);

L.push(`\n## Campañas vigentes`);
for (const [t, v] of CAMPS) L.push(`- ${t} (${v})`);

L.push(`\n## Mensajes por segmento (portada)`);
for (const [k, s] of Object.entries(SEGS)) {
  L.push(`- **${s.eye}** — ${s.title.replace(/<[^>]+>/g, '')} ${s.lede} Atajos: ${s.chips.join(', ')}. Cifras: ${s.proof.map(([b, t]) => `${b} ${t}`).join(' · ')}.`);
}

L.push(`\n## Texto publicado en cada sección del sitio`);
for (const [id, t] of sections) L.push(`\n### ${id}\n${t}`);

const KNOWLEDGE = L.join('\n') + '\n';

// Structured limits the server-side calculators enforce (kept in sync with the page sliders).
const SIM_LIMITS = Object.fromEntries(Object.entries(sims).map(([k, s]) => [k, Object.fromEntries(s.fields.map(f => [f.id, { min: f.min, max: f.max, default: f.default }]))]));
const PRODUCT_IDS = P.map(p => p.id);
const version = createHash('sha256').update(KNOWLEDGE + JSON.stringify(SIM_LIMITS)).digest('hex').slice(0, 12);

const out = `// AUTO-GENERATED by nexumtest/tools/build-knowledge.mjs from nexumtest/index.html — do not edit by hand.
// Regenerate with: npm run nexbot:kb
export const KB_VERSION = ${JSON.stringify(version)};
export const ASOF = ${JSON.stringify(ASOF)};
export const SIM_LIMITS = ${JSON.stringify(SIM_LIMITS, null, 2)};
export const PRODUCT_IDS = ${JSON.stringify(PRODUCT_IDS)};
export const KNOWLEDGE = ${JSON.stringify(KNOWLEDGE)};
`;

if (process.argv.includes('--check')) {
  const current = existsSync(OUT) ? readFileSync(OUT, 'utf8') : '';
  if (current !== out) { console.error('api/_nexbot/knowledge.js está desactualizado. Ejecuta: npm run nexbot:kb'); process.exit(1); }
  console.log(`knowledge.js al día (${version}).`);
} else {
  writeFileSync(OUT, out);
  console.log(`knowledge.js escrito · versión ${version} · ${P.length} productos · ${FAQ.length} FAQ · ${sections.length} secciones · ${KNOWLEDGE.length} caracteres`);
}
