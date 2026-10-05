#!/usr/bin/env node
/* Render-check the hero benchmark of the NEXUM landing page.
   Usage: node check_benchmark.cjs <path/to/index.html> <screenshot-dir>
   Loads the page from disk (?noloader skips the intro loader), waits for the bar
   entrance animation, then reports per viewport: kicker, rows, legend, tooltip text,
   clipped labels, horizontal overflow and page errors. Saves a PNG of the chart per
   viewport. Exit code 1 if a check fails. Needs Playwright (global install is fine). */
const path = require('path'), fs = require('fs');
let pw; try { pw = require('playwright'); } catch (e) {
  pw = require(path.join(require('child_process').execSync('npm root -g').toString().trim(), 'playwright')); }
const [file, outDir] = process.argv.slice(2);
if (!file || !outDir) { console.error('usage: node check_benchmark.cjs <index.html> <screenshot-dir>'); process.exit(2); }
fs.mkdirSync(outDir, { recursive: true });
const url = 'file://' + path.resolve(file) + '?noloader';
(async () => {
  const b = await pw.chromium.launch();
  let ok = true;
  for (const [tag, w, h] of [['desktop', 1440, 900], ['tablet', 834, 1194], ['mobile', 390, 844]]) {
    const p = await b.newPage({ viewport: { width: w, height: h } }); const errs = [];
    p.on('pageerror', e => { if (!/Chart/.test(e.message)) errs.push(e.message); });
    await p.goto(url, { waitUntil: 'domcontentloaded' });
    await p.evaluate(() => document.getElementById('benchmark').scrollIntoView({ block: 'center' }));
    await p.waitForTimeout(2600);                              // entrance animation finishes
    const r = await p.evaluate(() => {
      const f = document.getElementById('benchmark');
      const rows = [...f.querySelectorAll('.bench-row')];
      const clipped = [...f.querySelectorAll('.bench-lbl')].filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.textContent);
      return { kicker: f.querySelector('.bench-k').textContent.trim(), title: f.querySelector('.bench-t').textContent.trim(),
        rows: rows.length, legend: [...f.querySelectorAll('.bench-legend li')].map(l => l.textContent.trim()),
        animated: f.classList.contains('in'), clipped, hScroll: document.documentElement.scrollWidth > innerWidth,
        tableRows: f.querySelectorAll('table tbody tr').length };
    });
    await p.locator('#benchmark .bench-row').first().hover().catch(() => {});
    await p.waitForTimeout(300);
    r.tooltip = await p.evaluate(() => document.querySelector('#benchmark .bench-tip').textContent);
    const cdp = await p.context().newCDPSession(p);
    const box = await p.evaluate(() => { const e = document.getElementById('benchmark').getBoundingClientRect();
      return { x: e.left, y: e.top + scrollY, width: e.width, height: e.height }; });
    const { data } = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true, clip: { ...box, scale: 1 } });
    const shot = path.join(outDir, `benchmark-${tag}.png`); fs.writeFileSync(shot, Buffer.from(data, 'base64'));
    const fails = [];
    if (!/^Benchmark · ./.test(r.kicker)) fails.push('kicker must read "Benchmark · <topic>"');
    if (r.rows < 3) fails.push('fewer than 3 rows rendered');
    if (r.tableRows !== r.rows) fails.push('screen-reader table out of sync with rows');
    if (!r.animated) fails.push('entrance animation did not trigger');
    if (r.hScroll) fails.push('page scrolls horizontally');
    if (r.clipped.length) fails.push('labels cut off (shorten them in the spec): ' + r.clipped.join(', '));
    if (!r.tooltip) fails.push('tooltip empty on hover');
    if (errs.length) fails.push('page errors: ' + errs.join(' | '));
    if (fails.length) ok = false;
    console.log(JSON.stringify({ viewport: `${tag} ${w}x${h}`, ...r, screenshot: shot, status: fails.length ? 'FAIL' : 'PASS', fails }, null, 1));
    await p.close();
  }
  await b.close();
  process.exit(ok ? 0 : 1);
})();
