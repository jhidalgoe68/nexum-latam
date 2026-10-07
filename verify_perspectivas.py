#!/usr/bin/env python3
"""
verify_perspectivas.py — Regression gate for Section 05 / Perspectivas.

Run this after ANY change to index.html that touches an article's markup
or its scoped <style id="art-scoped-css-..."> block — a new article via
integrate_article.py, a hand edit, or a CSS tweak. It catches the two
classes of defect that have actually shipped to this site before:

  1. STATIC CSS AUDIT (no browser) — every article's CSS is scoped under
     `.art-frame` so it can't leak into the main site, but nothing stops
     two DIFFERENT articles from both defining the same bare class
     (`.art-frame .thesis{...}`, `.art-frame .b{...}`, ...) for their own,
     unrelated components. Because these all share one `.art-frame`
     prefix, same-specificity properties resolve by DOCUMENT ORDER, not
     by which article "owns" the name — so article A's rule can silently
     win a property inside article B's component. This has happened for
     real: `.b` (badges) and `.lvl`/`.f` (maturity dots) were caught and
     renamed in an earlier integration; `.thesis`/`.thesis-grid` was
     found still colliding across four articles by this very script.
     This pass extracts every `.art-frame .<class>{...}` rule from every
     `art-scoped-css*` block, groups by class name, and flags any class
     declared in more than one block where the declared property sets
     differ (a strong signal one article's rule is clobbering another's).

  2. RUNTIME AUDIT (Playwright, headless) — for every article, at three
     breakpoints (desktop/tablet/mobile):
       - every top-level content section has non-trivial visible text
         (catches "renders but is empty/invisible" bugs like the .lede
         color bug and the .reveal-opacity-stuck-at-0 bug)
       - the main content column is not squeezed into a narrow
         "sidebar-width" column on desktop (catches the .shell grid
         auto-placement bug: a 2-column grid-template-columns with only
         one grid child falls into column 1 unless forced into column 2)
       - all `.reveal` elements reach opacity > 0.5 once scrolled past
         (catches any reveal/intersection-observer regression)
       - no JS console/page errors fire while opening the article

Exit code is non-zero if anything is flagged. This script does not fix
anything — it only reports, so a human/agent can decide the right fix
(usually: rename one side's bare class, like `.b` -> `.evb` was, or make
a layout rule unconditional across viewports, like `.shell` was).

USAGE
  python3 verify_perspectivas.py --html index.html [--skip-runtime]
"""

import argparse
import json
import os
import re
import sys


# ════════════════════════════════════════════════════════════════
# Part 1 — static CSS collision audit
# ════════════════════════════════════════════════════════════════

def extract_scoped_blocks(html: str):
    """Returns [(block_id, css_text), ...] for every art-scoped-css* block."""
    blocks = []
    for m in re.finditer(r'<style id="(art-scoped-css[^"]*)">(.*?)</style>', html, re.DOTALL):
        blocks.append((m.group(1), m.group(2)))
    return blocks


def extract_bare_class_rules(css_text: str):
    """
    Returns {class_name: {prop_name: raw_value, ...}} for every single-class
    `.art-frame .X{...}` rule (ignores compound/descendant selectors like
    `.art-frame .card .n` or `.art-frame .card:hover` — those are already
    namespaced by their parent and much less likely to collide).
    """
    out = {}
    for m in re.finditer(r'\.art-frame \.([a-zA-Z0-9_-]+)\s*\{([^}]*)\}', css_text):
        cls, body = m.group(1), m.group(2)
        props = {}
        for decl in body.split(';'):
            decl = decl.strip()
            if not decl or ':' not in decl:
                continue
            prop, _, val = decl.partition(':')
            props[prop.strip()] = val.strip()
        out.setdefault(cls, {})
        # last declaration in this one rule wins for same-block duplicates
        out[cls].update(props)
    return out


def audit_css_collisions(html: str):
    blocks = extract_scoped_blocks(html)
    # class_name -> {block_id: {prop: val}}
    by_class = {}
    for block_id, css_text in blocks:
        rules = extract_bare_class_rules(css_text)
        for cls, props in rules.items():
            by_class.setdefault(cls, {})[block_id] = props

    findings = []
    for cls, per_block in by_class.items():
        if len(per_block) < 2:
            continue
        # Compare property sets pairwise. Flag if:
        #  - the SAME property has a different value across blocks, or
        #  - one block declares a property another doesn't (a "leak" risk:
        #    whichever block is NOT last in source order will silently
        #    inherit the other's value for that property).
        block_ids = list(per_block.keys())
        all_props = set()
        for p in per_block.values():
            all_props |= set(p.keys())
        diffs = {}
        for prop in sorted(all_props):
            values = {b: per_block[b].get(prop) for b in block_ids}
            distinct = set(values.values())
            if len(distinct) > 1:
                diffs[prop] = values
        if diffs:
            findings.append({
                "class": cls,
                "blocks": block_ids,
                "conflicting_properties": diffs,
            })
    return findings


# ════════════════════════════════════════════════════════════════
# Part 2 — runtime audit (Playwright)
# ════════════════════════════════════════════════════════════════

VIEWPORTS = {
    "desktop": {"width": 1400, "height": 1000},
    "tablet": {"width": 834, "height": 1100},
    "mobile": {"width": 390, "height": 844},
}

MIN_SECTION_TEXT_CHARS = 20
NARROW_MAIN_RATIO = 0.5  # main column narrower than this fraction of the panel is suspect


def run_runtime_audit(html_path: str):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"skipped": "playwright not installed"}

    findings = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        for vp_name, vp in VIEWPORTS.items():
            page = browser.new_page(viewport=vp)
            page_errors = []
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            page.goto(f"file://{os.path.abspath(html_path)}")
            page.wait_for_timeout(1000)

            art_ids = page.evaluate("""() => {
                const frames = document.querySelectorAll('.art-frame');
                return Array.from(frames).map(f => f.id).filter(Boolean);
            }""")

            for art_id in art_ids:
                clicked = page.evaluate(f"""() => {{
                    const rows = document.querySelectorAll('.blog-item');
                    for (const r of rows) {{ if (r.outerHTML.includes('{art_id}')) {{ r.click(); return true; }} }}
                    return false;
                }}""")
                if not clicked:
                    findings.append({"viewport": vp_name, "article": art_id,
                                      "issue": "could not open article (no matching .blog-item row)"})
                    continue
                page.wait_for_timeout(600)

                # 1. empty/invisible top-level sections
                empty_sections = page.evaluate("""(artId) => {
                    const frame = document.getElementById(artId);
                    if (!frame) return ['frame-not-found'];
                    const sections = frame.querySelectorAll('section, [id$="-resumen"], [id$="-resumen-ejecutivo"]');
                    const bad = [];
                    sections.forEach(s => {
                        const text = (s.innerText || '').trim();
                        if (text.length < %d) bad.push(s.id || s.className || '(unnamed section)');
                    });
                    return bad;
                }""" % MIN_SECTION_TEXT_CHARS, art_id)
                if empty_sections:
                    findings.append({"viewport": vp_name, "article": art_id,
                                      "issue": "sections with little/no visible text",
                                      "detail": empty_sections[:10]})

                # 2. narrow main column on desktop (shell grid auto-placement bug)
                if vp_name == "desktop":
                    layout = page.evaluate("""(artId) => {
                        const frame = document.getElementById(artId);
                        const shell = frame.querySelector('.shell');
                        if (!shell) return null;
                        const main = shell.querySelector('main');
                        if (!main) return null;
                        return {
                            frameWidth: frame.getBoundingClientRect().width,
                            mainWidth: main.getBoundingClientRect().width
                        };
                    }""", art_id)
                    if layout and layout["frameWidth"] > 0:
                        ratio = layout["mainWidth"] / layout["frameWidth"]
                        if ratio < NARROW_MAIN_RATIO:
                            findings.append({"viewport": vp_name, "article": art_id,
                                              "issue": "main content column abnormally narrow "
                                                       "(possible .shell grid auto-placement bug)",
                                              "detail": layout})

                # 3. .reveal elements: scroll through fully, confirm all reach opacity>0.5
                height = page.evaluate("document.body.scrollHeight")
                steps = 15
                for i in range(steps):
                    page.evaluate(f"window.scrollTo(0, {height} * {i + 1} / {steps})")
                    page.wait_for_timeout(150)
                page.wait_for_timeout(400)
                reveal_info = page.evaluate("""(artId) => {
                    const frame = document.getElementById(artId);
                    const els = frame.querySelectorAll('.reveal');
                    let stuck = 0;
                    els.forEach(el => {
                        if (parseFloat(getComputedStyle(el).opacity) <= 0.5) stuck++;
                    });
                    return {total: els.length, stuck};
                }""", art_id)
                if reveal_info["total"] > 0 and reveal_info["stuck"] > 0:
                    findings.append({"viewport": vp_name, "article": art_id,
                                      "issue": "some .reveal elements never reach visible opacity "
                                               "after full scroll (possible CSS override of the "
                                               "shared .reveal/.reveal.in mechanism)",
                                      "detail": reveal_info})
                page.evaluate("window.scrollTo(0, 0)")

            if page_errors:
                findings.append({"viewport": vp_name, "article": None,
                                  "issue": "JS page errors", "detail": page_errors})
            page.close()
        browser.close()
    return {"findings": findings}


# ════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--skip-runtime", action="store_true",
                     help="Only run the static CSS collision audit (fast, no browser).")
    args = ap.parse_args()

    html = open(args.html, encoding="utf-8").read()

    print("=" * 70)
    print("STATIC CSS COLLISION AUDIT")
    print("=" * 70)
    css_findings = audit_css_collisions(html)
    if not css_findings:
        print("No bare-class collisions with conflicting properties found.")
    else:
        for f in css_findings:
            print(f"\n.{f['class']}  — declared in {len(f['blocks'])} article blocks: {f['blocks']}")
            for prop, values in f["conflicting_properties"].items():
                print(f"    {prop}:")
                for block, val in values.items():
                    print(f"        {block}: {val!r}")

    runtime_result = {}
    if not args.skip_runtime:
        print("\n" + "=" * 70)
        print("RUNTIME AUDIT (desktop / tablet / mobile)")
        print("=" * 70)
        runtime_result = run_runtime_audit(args.html)
        if runtime_result.get("skipped"):
            print("Skipped:", runtime_result["skipped"])
        elif not runtime_result.get("findings"):
            print("No runtime issues found across all articles and breakpoints.")
        else:
            for f in runtime_result["findings"]:
                print(f"\n[{f['viewport']}] {f.get('article') or '(site-wide)'}: {f['issue']}")
                if "detail" in f:
                    print("   ", json.dumps(f["detail"], ensure_ascii=False)[:500])

    print("\n" + "=" * 70)
    total_issues = len(css_findings) + len(runtime_result.get("findings", []))
    print(f"TOTAL ISSUES FLAGGED: {total_issues}")
    print("=" * 70)
    sys.exit(1 if total_issues else 0)


if __name__ == "__main__":
    main()
