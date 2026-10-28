#!/usr/bin/env node
/**
 * NexBot Seguro — knowledge base compiler
 * ──────────────────────────────────────────────────────────────────────────
 * Reads nexumseguro/index.html and compiles everything the page publishes into
 * api/_nexseguro/knowledge.js, the grounding context of /api/nexseguro:
 *
 *   · The copy of every block (utility bar, header, hero, quote form, strip,
 *     each <section>, footer) in Spanish, as published.
 *   · The same copy in English, rebuilt from the page's own EN dictionary
 *     (the strings its ES/EN toggle shows), so nothing is retranslated.
 *   · Placeholders still marked on the page (<span class="ph">[…]</span>:
 *     phone numbers, email, address, figures, rating, testimonial) are listed
 *     as NOT PUBLISHED, so the assistant never quotes them as real data.
 *
 * Run it every time nexumseguro/index.html changes:
 *     npm run nexseguro:kb            (writes the file)
 *     npm run nexseguro:kb -- --check (exit 1 if the committed file is stale)
 * ─────────────────────────────────────────────────────────────────────────
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import vm from 'node:vm';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const PAGE = path.join(ROOT, 'nexumseguro', 'index.html');
const OUT  = path.join(ROOT, 'api', '_nexseguro', 'knowledge.js');

const html = readFileSync(PAGE, 'utf8');

// ── 1. English dictionary, evaluated from the page script ────────────────
const enSrc = html.match(/var EN=(\{[\s\S]*?\n\s*\});/);
if (!enSrc) throw new Error('No se encontró el diccionario EN (var EN={…}) en nexumseguro/index.html');
const EN = vm.runInNewContext(`(${enSrc[1]})`, {}, { timeout: 1000 });

// ── 2. HTML → plain text ─────────────────────────────────────────────────
const ENT = { amp: '&', lt: '<', gt: '>', quot: '"', '#39': "'", nbsp: ' ', middot: '·', rarr: '→' };
const decode = s => s.replace(/&(#?\w+);/g, (m, e) => ENT[e] ?? (e[0] === '#' ? String.fromCodePoint(+e.slice(1)) : m));
const placeholders = new Set();

/** Replaces each data-t element's inner HTML with the English string (the page's own ES/EN toggle). */
function toEnglish(src) {
  return src.replace(/<(\w+)((?:\s[^>]*?)?\sdata-t="([^"]+)"[^>]*)>([\s\S]*?)<\/\1>/g,
    (m, tag, attrs, key, inner) => (EN[key] != null ? `<${tag}${attrs}>${EN[key]}</${tag}>` : m));
}

function toText(src) {
  return decode(src
    .replace(/<(script|style|svg)[\s\S]*?<\/\1>/g, '')
    .replace(/<span class="ph"[^>]*>\[([^\]]+)\]<\/span>/g, (m, v) => { placeholders.add(v); return `[NO PUBLICADO: ${v}]`; })
    .replace(/<option[^>]*>([\s\S]*?)<\/option>/g, '$1 / ')
    .replace(/<li[^>]*>/g, '\n- ')
    .replace(/<(h[1-4])[^>]*>/g, '\n**').replace(/<\/h[1-4]>/g, '**\n')
    .replace(/<\/(p|div|article|dt|dd|label|ul|ol|nav|blockquote|form|select)>/g, '\n')
    .replace(/<br\s*\/?>/g, '\n')
    .replace(/<[^>]+>/g, ' '))
    .replace(/[ \t]+/g, ' ')
    .replace(/ ?\/ ?\n/g, '\n')
    .replace(/\s+\*\*\n/g, '**\n')
    .split('\n').map(l => l.trim()).filter(Boolean).join('\n')
    .replace(/^-\n\*\*/gm, '- **');
}

// ── 3. Blocks of the page, in reading order ──────────────────────────────
const body = html.slice(html.indexOf('<body>'), html.lastIndexOf('<script>'));
const BLOCKS = [
  ['barra-superior', 'Barra de utilidades (país, emergencias, portales)', /<div class="util">[\s\S]*?<\/nav>\s*<\/div>\s*<\/div>/],
  ['menu', 'Menú principal', /<nav class="nav"[\s\S]*?<\/nav>/],
  ['inicio', 'Portada (hero) y formulario “Cotice en un minuto”', /<section class="hero"[\s\S]*?<\/section>/],
  ['coberturas', 'Franja “Le acompañamos en”', /<div class="strip"[\s\S]*?<\/ul>/],
];
const main = body.slice(body.indexOf('<main'), body.indexOf('</main>')); // the chat window is a <section> too, outside <main>
for (const m of main.matchAll(/<section class="[^"]*" id="([^"]+)"[\s\S]*?<\/section>/g)) {
  const head = m[0].match(/<h2[^>]*>([\s\S]*?)<\/h2>/);
  BLOCKS.push([m[1], head ? toText(head[1]).replace(/\*/g, '') : m[1], m[0]]);
}
BLOCKS.push(['pie', 'Pie de página', /<footer class="foot">[\s\S]*?<\/footer>/]);

const sections = BLOCKS.map(([id, title, re]) => {
  const src = typeof re === 'string' ? re : (body.match(re) || [''])[0];
  if (!src) throw new Error(`No se encontró el bloque ${id} en nexumseguro/index.html`);
  return { id, title, es: toText(src), en: toText(toEnglish(src)) };
});

// ── 4. Compile ───────────────────────────────────────────────────────────
const L = [];
L.push('# NexumSeguro — contenido publicado en nexum-latam.com/nexumseguro/');
L.push('Fuente única: la página pública de NexumSeguro (seguros de salud, vida y asistencia en viajes). Es un sitio en preparación: los datos marcados [NO PUBLICADO: …] todavía no se han publicado y no deben citarse como reales.');
L.push(`\n## Datos aún no publicados en el sitio (marcadores de posición)`);
L.push(`El sitio muestra estos espacios resaltados para completar antes del lanzamiento. No existen todavía: ${[...placeholders].map(p => `“${p}”`).join(', ')}. Esto incluye el teléfono de emergencias / atención al cliente, el correo, la dirección de la casa matriz, los años de experiencia, el número de países, los beneficios pagados, la calificación de fortaleza financiera y los testimonios.`);
L.push(`\n## Anclas de la página (para botones go:)`);
L.push(sections.filter(s => !['barra-superior', 'menu', 'coberturas', 'pie'].includes(s.id)).map(s => `- #${s.id}: ${s.title}`).join('\n'));
L.push(`\n## Texto publicado en cada sección (español, versión oficial)`);
for (const s of sections) L.push(`\n### ${s.id} — ${s.title}\n${s.es}`);
L.push(`\n## Published copy of each section (English version shown by the site's EN toggle)`);
for (const s of sections) L.push(`\n### ${s.id}\n${s.en}`);

const KNOWLEDGE = L.join('\n') + '\n';
const SECTION_IDS = sections.map(s => s.id);
const version = createHash('sha256').update(KNOWLEDGE).digest('hex').slice(0, 12);

const out = `// AUTO-GENERATED by nexumseguro/tools/build-knowledge.mjs from nexumseguro/index.html — do not edit by hand.
// Regenerate with: npm run nexseguro:kb
export const KB_VERSION = ${JSON.stringify(version)};
export const SECTION_IDS = ${JSON.stringify(SECTION_IDS)};
export const PLACEHOLDERS = ${JSON.stringify([...placeholders])};
export const KNOWLEDGE = ${JSON.stringify(KNOWLEDGE)};
`;

if (process.argv.includes('--check')) {
  const current = existsSync(OUT) ? readFileSync(OUT, 'utf8') : '';
  if (current !== out) { console.error('api/_nexseguro/knowledge.js está desactualizado. Ejecuta: npm run nexseguro:kb'); process.exit(1); }
  console.log(`knowledge.js al día (${version}).`);
} else {
  writeFileSync(OUT, out);
  console.log(`knowledge.js escrito · versión ${version} · ${sections.length} bloques · ${placeholders.size} marcadores · ${KNOWLEDGE.length} caracteres`);
}
