#!/usr/bin/env python3
"""Replace the hero benchmark chart of the NEXUM LATAM landing page.

Reads a benchmark spec (JSON) and regenerates <figure class="hero-bench" id="benchmark">
in index.html using the site's existing benchmark components, so the new chart inherits
the NEXUM styling, the staggered bar entrance animation, the hover/tap tooltip and the
screen-reader table automatically. Only the figure's markup is replaced; the CSS and JS
that drive it live in the page and are left untouched.

Usage:
  python3 replace_benchmark.py --spec spec.json [--html index.html] [--dry-run]

Spec format: see the skill's SKILL.md ("Benchmark spec").
"""
import argparse
import html
import json
import math
import re
import sys

MIN_ROWS, MAX_ROWS = 3, 12        # what fits the hero column without crowding the CTA area
LABEL_SOFT_MAX = 24               # longer labels get ellipsised on desktop; warn so they can be shortened
NEAR = 0.14                       # marker this close past the bar end would sit on the value label


def fail(msg):
    sys.exit(f"ERROR: {msg}")


def esc(v):
    return html.escape(str(v), quote=True)


def nice_ticks(lo, hi):
    """Integer ticks for small integer scales (0–5, 1–7, 0–10); otherwise 5 even steps."""
    span = hi - lo
    if span <= 10 and float(lo).is_integer() and float(hi).is_integer():
        return [lo + i for i in range(int(span) + 1)]
    step = span / 5
    mag = 10 ** math.floor(math.log10(step))
    step = min((m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= step), default=step)
    ticks, t = [], lo
    while t <= hi + 1e-9:
        ticks.append(round(t, 6))
        t += step
    return ticks


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True, help="benchmark spec JSON")
    ap.add_argument("--html", default="index.html", help="landing page to update (default: index.html)")
    ap.add_argument("--dry-run", action="store_true", help="validate and print the figure without writing")
    a = ap.parse_args()

    spec = json.load(open(a.spec, encoding="utf-8"))

    # ── Validate ────────────────────────────────────────────────────────────
    for key in ("topic", "title", "series", "rows"):
        if key not in spec:
            fail(f"spec is missing '{key}'")
    rows = spec["rows"]
    if not (MIN_ROWS <= len(rows) <= MAX_ROWS):
        fail(f"{len(rows)} rows; the hero chart holds {MIN_ROWS}–{MAX_ROWS}. "
             "Keep the most decision-relevant rows (or merge the rest) and say so to the user.")
    series = spec["series"]
    if not series.get("primary"):
        fail("series.primary (name of the bar series) is required")
    has_tgt = bool(series.get("secondary"))
    scale = spec.get("scale", {})
    vals = [r["value"] for r in rows] + ([r["target"] for r in rows if r.get("target") is not None] if has_tgt else [])
    lo = scale.get("min", 0)
    hi = scale.get("max")
    if hi is None:
        fail("scale.max is required (read it from the source graphic; do not infer it from the data alone)")
    if not lo < hi:
        fail("scale.min must be below scale.max")
    bad = [v for v in vals if v < lo or v > hi]
    if bad:
        fail(f"values outside the scale {lo}–{hi}: {bad}")
    if has_tgt and all(r.get("target") is None for r in rows):
        fail("series.secondary is set but no row has a 'target'")
    fmt = spec.get("format", {})
    dec = int(fmt.get("decimals", 1))
    suffix = fmt.get("suffix", "")
    ticks = scale.get("ticks") or nice_ticks(lo, hi)

    def num(v):
        return f"{v:.{dec}f}{suffix}"

    def pos(v):
        return (v - lo) / (hi - lo)

    warnings = [f"label longer than {LABEL_SOFT_MAX} chars, may be cut on desktop (check_benchmark.cjs decides): {r['label']!r}"
                for r in rows if len(r["label"]) > LABEL_SOFT_MAX]

    # ── Build the figure ────────────────────────────────────────────────────
    cur_l, tgt_l = series["primary"], series.get("secondary", "")
    gap_l = series.get("gap", "Brecha")
    # "to_target": secondary − primary (distance still to close, e.g. objective 2030);
    # "vs_secondary": primary − secondary (how far ahead/behind a reference, e.g. sector average).
    gap_mode = spec.get("gap_mode", "to_target")
    if gap_mode not in ("to_target", "vs_secondary"):
        fail("gap_mode must be 'to_target' or 'vs_secondary'")
    gap = (lambda v, t: t - v) if gap_mode == "to_target" else (lambda v, t: v - t)
    signed = lambda d: ("+" if d > 0 else "\u2212" if d < 0 else "") + num(abs(d))
    grid = 100 / (len(ticks) - 1) if len(ticks) > 1 else 100

    row_html = []
    for i, r in enumerate(rows):
        v, t = r["value"], (r.get("target") if has_tgt else None)
        style = f"--cur:{pos(v):.3f};" + (f"--tgt:{pos(t):.3f};" if t is not None else "") + f"--i:{i}"
        if t is not None and pos(v) > 0 and 0 < pos(t) - pos(v) < NEAR:
            # Marker just past the bar end: move the value label beyond the marker so they don't overlap.
            style += f";--val-x:calc({pos(t) / pos(v) * 100:.2f}% + 8px)"
        data = f'data-label="{esc(r["label"])}" data-cur="{esc(num(v))}"'
        if t is not None:
            data += f' data-tgt="{esc(num(t))}" data-gap="{esc(signed(gap(v, t)))}"'
        track = ('<span class="bench-gap"></span>' if t is not None else "") + \
                f'<span class="bench-bar"><span class="bench-val">{esc(num(v))}</span></span>' + \
                ('<span class="bench-dot"></span>' if t is not None else "")
        row_html.append(
            f'            <li class="bench-row" style="{style}" {data}>\n'
            f'              <span class="bench-lbl">{esc(r["label"])}</span>\n'
            f'              <span class="bench-track">{track}</span>\n'
            f'              <span class="bench-goal">{esc(num(t)) if t is not None else ""}</span>\n'
            f'            </li>')

    tick_html = "".join(
        f'<span style="left:{pos(tk) * 100:.4g}%">{esc(f"{tk:g}{suffix}")}</span>' for tk in ticks)

    legend = [f'            <li><span class="bench-sw bench-sw--cur"></span>{esc(cur_l)}</li>']
    if has_tgt:
        legend.append(f'            <li><span class="bench-sw bench-sw--tgt"></span>{esc(tgt_l)}</li>')

    cols = [cur_l] + ([tgt_l, gap_l] if has_tgt else [])
    head = "".join(f'<th scope="col">{esc(c)}</th>' for c in ["Dimensión"] + cols)
    trs = []
    for r in rows:
        v, t = r["value"], (r.get("target") if has_tgt else None)
        cells = [num(v)] + ([num(t) if t is not None else "—",
                            signed(gap(v, t)) if t is not None else "—"] if has_tgt else [])
        trs.append(f'              <tr><th scope="row">{esc(r["label"])}</th>' +
                   "".join(f"<td>{esc(c)}</td>" for c in cells) + "</tr>")

    caption = spec.get("caption") or f'{spec["title"]}: {", ".join(cols)} ({lo:g}–{hi:g}{suffix})'
    src = f'\n        <p class="bench-src">{esc(spec["source"])}</p>' if spec.get("source") else ""
    sub = f'\n          <p class="bench-sub">{esc(spec["subtitle"])}</p>' if spec.get("subtitle") else ""

    figure = f'''<figure class="hero-bench" id="benchmark" aria-labelledby="benchTitle" data-cur-label="{esc(cur_l)}" data-tgt-label="{esc(tgt_l)}" data-gap-label="{esc(gap_l)}" style="--bench-grid:{grid:.4g}%">
        <figcaption class="bench-hd">
          <p class="bench-k">Benchmark · {esc(spec["topic"])}</p>
          <h2 class="bench-t" id="benchTitle">{esc(spec["title"])}</h2>{sub}
          <ul class="bench-legend" aria-hidden="true">
{chr(10).join(legend)}
          </ul>
        </figcaption>
        <div class="bench-plot" aria-hidden="true">
          <ol class="bench-rows">
{chr(10).join(row_html)}
          </ol>
          <div class="bench-axis"><span></span><span class="bench-ticks">{tick_html}</span><span></span></div>
          <div class="bench-tip" role="presentation"></div>
        </div>{src}
        <table class="sr-only">
          <caption>{esc(caption)}</caption>
          <thead><tr>{head}</tr></thead>
          <tbody>
{chr(10).join(trs)}
          </tbody>
        </table>
      </figure>'''

    if a.dry_run:
        print(figure)
    else:
        page = open(a.html, encoding="utf-8").read()
        m = re.search(r'<figure class="hero-bench" id="benchmark"[^>]*>.*?</figure>', page, re.S)
        if not m:
            fail(f'no <figure class="hero-bench" id="benchmark"> found in {a.html}')
        if page.count('id="benchmark"') != 1:
            fail('expected exactly one id="benchmark" in the page')
        page = page[:m.start()] + figure + page[m.end():]
        open(a.html, "w", encoding="utf-8").write(page)

    print(f"OK  topic='{spec['topic']}'  rows={len(rows)}  series={cols}  scale={lo:g}–{hi:g}{suffix}  ticks={ticks}"
          + ("" if a.dry_run else f"  → {a.html} updated"), file=sys.stderr)
    for w in warnings:
        print("WARN", w, file=sys.stderr)


if __name__ == "__main__":
    main()
