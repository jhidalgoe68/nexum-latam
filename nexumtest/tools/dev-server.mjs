#!/usr/bin/env node
/**
 * Local preview of /nexumtest/ and /nexumseguro/ with the real /api/nexbot and /api/nexseguro functions.
 *   ANTHROPIC_API_KEY=sk-ant-... npm run nexbot:dev   →  http://localhost:3000/nexumtest/ · /nexumseguro/
 * Without a key the page runs in "modo básico" (offline answer engine).
 */
import http from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import nexbot from '../../api/nexbot.js';
import nexseguro from '../../api/nexseguro.js';

const API = { '/api/nexbot': nexbot, '/api/nexseguro': nexseguro };

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const PORT = +process.env.PORT || 3000;
const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.mp4': 'video/mp4' };

// Minimal shim of the Vercel Node helpers used by the api/ functions.
function vercelify(req, res, body) {
  req.body = body;
  res.status = code => { res.statusCode = code; return res; };
  res.json = obj => { if (!res.headersSent) res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify(obj)); return res; };
}

http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const handler = API[url.pathname];
  if (handler) {
    let raw = '';
    for await (const c of req) raw += c;
    let body = raw;
    if ((req.headers['content-type'] || '').includes('application/json')) { try { body = JSON.parse(raw); } catch { body = raw; } }
    vercelify(req, res, body);
    return handler(req, res);
  }
  let file = path.normalize(path.join(ROOT, decodeURIComponent(url.pathname)));
  if (!file.startsWith(ROOT) || file.includes(`${path.sep}node_modules${path.sep}`) || file.includes(`${path.sep}.git`)) { res.writeHead(403).end(); return; }
  try {
    if ((await stat(file)).isDirectory()) file = path.join(file, 'index.html');
    const data = await readFile(file);
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' }).end(data);
  } catch {
    res.writeHead(404).end('Not found');
  }
}).listen(PORT, () => console.log(`NexBot dev → http://localhost:${PORT}/nexumtest/ · http://localhost:${PORT}/nexumseguro/  (IA: ${process.env.ANTHROPIC_API_KEY ? 'activada' : 'sin ANTHROPIC_API_KEY → modo básico'})`));
