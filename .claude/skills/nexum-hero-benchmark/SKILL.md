---
name: nexum-hero-benchmark
description: Replaces the benchmark chart in the hero (first section, "Consultoría Estratégica · América Latina") of the NEXUM LATAM landing page with the data from an attached benchmark graphic, rebuilt natively in the NEXUM design system with the same staggered bar animation, tooltip and accessibility, and retitles it "Benchmark · (tema)" using the topic of the attachment. Use whenever the user attaches an image (or screenshot, PDF page or slide) of a benchmark, maturity chart, ranking, scorecard, gap analysis or comparison and wants it on the website, the landing page, the hero, "la primera sección" or in place of "Benchmark · Madurez empresarial", even if they just say "cambia el benchmark", "reemplaza la gráfica", "nuevo benchmark", "actualiza el gráfico del inicio" or "put this chart on the site".
---

# NEXUM hero benchmark replacement

The landing page hero of nexum-latam.com has a benchmark chart beside the headline (`<figure id="benchmark">` in `index.html`). This skill swaps its **data**, never its **design**: the user's attachment is a source of numbers and wording only. The site already contains the validated styling, the entrance animation (bars grow from the baseline one after another, then targets land), the hover/tap tooltip and the screen-reader table. The bundled script regenerates the figure's markup so all of that applies automatically to the new data.

Why it works this way: earlier attempts that recreated a chart from an image tended to import the source's look (gradients, rounded pills, foreign fonts), which made the hero feel like a pasted widget. Generating the markup from structured data keeps every future benchmark visually identical in kind to the original one.

## Workflow

### 1. Read the attachment and extract the data faithfully

Look at the image closely and pull out:
- **Topic**: what the benchmark measures, in 1–4 words (e.g. "Madurez empresarial", "Ciberseguridad", "Adopción de IA"). This becomes the label line **"Benchmark · {topic}"**. The site uses the middle dot "·" as its separator, so use it even if the user writes "Benchmark - topic".
- **Title / subtitle**: the graphic's own heading and description. Keep the meaning, in Spanish.
- **Series**: the bar series (e.g. "Nivel actual", "Organización", "2025") and, if present, a second per-row value shown as a marker (target, sector average, peer best, previous year), plus a word for the difference between them ("Brecha", "Diferencia", "Variación").
- **Scale**: min and max of the axis. Read them from the graphic (axis labels, "escala 1–5", percentages). If the graphic doesn't state it, infer the conventional scale (maturity models are usually 0–5 or 1–5; shares are 0–100%) and **tell the user what you assumed**.
- **Rows**: every label with its value(s), exactly as printed. If a number is unreadable, ask rather than guess. Wrong numbers on an executive site are worse than a short delay.

The website is in Spanish, so translate English labels into natural business Spanish and keep acronyms and proper nouns (IA, ESG, ERP). Keep labels to about 24 characters, because longer ones get cut on desktop and the check in step 5 fails. Shorten with meaning intact ("Security Awareness" → "Cultura de seguridad", not "Concienc. seg.").

### 2. Map the graphic onto what the hero chart can show

The hero chart shows **one bar per row (3–12 rows) on a shared scale, with an optional second value per row as a marker**. Most benchmark graphics fit:

| Source graphic | How to map it |
|---|---|
| Current vs target/objective | primary = current, secondary = target, gap = "Brecha" |
| Company vs sector/peer average | primary = company, secondary = "Promedio del sector", gap = "Diferencia", `"gap_mode": "vs_secondary"` (company − average, so "−9%" reads as "9 points behind") |
| This year vs last year | primary = current year, secondary = previous year, gap = "Variación", `"gap_mode": "vs_secondary"` |
| Single-value ranking / scores | primary only (omit `secondary`); no dots or gap |
| Percentages | `scale` 0–100, `format.suffix` "%", `decimals` 0 |

If it doesn't fit (a time series, a pie or donut, more than two series, more than 12 rows), choose the most faithful reduction, such as the latest period, the top 12 rows or the two most important series. Explain the choice to the user in one or two sentences. If the reduction would change the message, ask first.

### 3. Write the spec

Save the extracted data as JSON in the scratchpad (not in the repo). `assets/example-spec.json` is the current "Madurez empresarial" benchmark, a complete worked example:

```json
{
  "topic": "Madurez empresarial",
  "title": "Dónde estamos hoy",
  "subtitle": "Nivel actual frente al objetivo 2030, por dimensión empresarial (escala 0–5).",
  "caption": "optional — screen-reader table caption; generated from title + series if omitted",
  "source": "optional — e.g. 'Fuente: NEXUM Executive Insights 2026'; shown small under the chart",
  "scale": { "min": 0, "max": 5, "ticks": "optional list; integer ticks or 5 even steps are generated" },
  "format": { "decimals": 1, "suffix": "" },
  "series": { "primary": "Nivel actual", "secondary": "Objetivo 2030", "gap": "Brecha" },
  "gap_mode": "optional — 'to_target' (default: secondary − primary) or 'vs_secondary' (primary − secondary)",
  "rows": [ { "label": "Datos e IA", "value": 2.6, "target": 4.3 } ]
}
```

Include a `source` line only when the attachment names a source; never invent one.

### 4. Replace the chart

Run from the repository root (`index.html` is the landing page):

```bash
python3 <skill-dir>/scripts/replace_benchmark.py --spec <spec.json> --html index.html
```

The script validates the spec (row count, every value inside the scale, required fields), then rewrites only the `<figure id="benchmark">` block. It prints a summary line and warns about labels that are too long. Use `--dry-run` to preview the markup without writing. Fix any ERROR it reports by correcting the spec, not by editing the generated HTML by hand. Hand edits are lost on the next replacement and tend to break the animation hooks (`--cur`, `--tgt`, `--i`, the `data-*` attributes).

Don't modify the benchmark CSS, the entrance-animation or tooltip script, the KPI row or the hero layout. Those are shared, validated parts of the site. The bar teal (`#0A8FA8`) and target amber were checked for contrast and color-blind separation on the hero background.

### 5. Verify before showing anyone

```bash
node <skill-dir>/scripts/check_benchmark.cjs index.html <scratchpad>/benchmark-check
```

The script renders the page at desktop, tablet and mobile sizes. It checks the label line reads "Benchmark · …", the rows and screen-reader table match, the animation fired, the tooltip works, nothing overflows sideways, and there are no page errors. It saves a PNG of the chart for each viewport. **Open the screenshots and compare every number against the attachment.** The script checks structure; only you can confirm the data matches. If Playwright isn't available, say so and verify with whatever browser tooling exists.

### 6. Publish

- Commit `index.html` on the working branch with a message like `feat(hero): benchmark → <topic>` and push. Follow the repository's branch instructions for the session.
- If the site's live preview artifact exists (the user's artifact titled "index"; find it with the Artifact tool's `list` action), republish `index.html` to that same URL so the change is visible immediately. Files already in the artifact, such as the scroll animation frames, stay in place.

### 7. Report back

Keep it short:
- the new label line ("Benchmark · …") and title;
- a compact table of the extracted rows and values, so the user can spot-check them against the attachment;
- any assumption (scale, translation, rows dropped or merged, a missing source);
- the desktop screenshot of the new chart;
- the commit and preview link.

## Files

- `scripts/replace_benchmark.py`: validates a spec and regenerates the figure (no dependencies beyond Python 3).
- `scripts/check_benchmark.cjs`: Playwright render check with screenshots.
- `assets/example-spec.json`: the original "Madurez empresarial" benchmark; also a quick way to restore it.
