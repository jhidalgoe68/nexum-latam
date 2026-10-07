#!/usr/bin/env python3
"""
verify_perspectivas.py — Regression gate for Section 05 / Perspectivas.

Run this after ANY change to index.html that touches an article's markup
or its scoped <style id="art-scoped-css-..."> block — a new article via
integrate_article.py, a hand edit, or a CSS tweak. It catches the two
classes of defect that have actually shipped to this site before:

  1. STATIC CSS AUDIT (no browser) — every article's CSS is scoped under
     `.art-frame` so it can't leak into the main site, but for a long time
     nothing stopped two DIFFERENT articles from both defining the same
     bare class (`.art-frame .thesis{...}`, `.art-frame .b{...}`, ...) for
     their own, unrelated components. Because they all shared one
     `.art-frame` prefix, same-specificity properties resolved by
     DOCUMENT ORDER, not by which article "owns" the name — so article A's
     rule could silently win a property inside article B's component.
     This happened for real, repeatedly: `.b` (badges) and `.lvl`/`.f`
     (maturity dots) were caught and renamed in one integration; a
     `.reveal` override and a `.shell` grid bug broke two more articles
     in a later pass; a static audit then found 43 more colliding bare
     classes across the six articles, one of which (`.finding`/
     `.findings`) was live-breaking "Sostenibilidad y Creación de Valor"'s
     layout (a 120px grid column meant for a DIFFERENT article's
     component was leaking into this one, crushing its findings cards).

     Rather than keep renaming classes one collision at a time, every
     scoped block's selectors were migrated from `.art-frame .X` to
     `.art-frame#<that-article's-root-id> .X` — an ID selector has higher
     specificity than a two-class one, so each article's own rules now
     ALWAYS win inside its own panel regardless of source order, and the
     whole class of bug is closed structurally rather than patched
     instance by instance. This pass enforces that invariant going
     forward: it flags any `.art-frame .X{...}` rule in a scoped block
     that is missing its `#<root-id>` anchor (a regression — e.g. a
     future integration run on an un-migrated copy of the script, or a
     hand-added rule that forgot the id), and any rule whose `#id` doesn't
     match the block it lives in (a copy-paste mistake).

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
# Part 1 — static CSS scoping audit
# ════════════════════════════════════════════════════════════════

# style-block-id -> that article's own .art-frame root element id.
# Every selector inside a block should be anchored to its own entry here.
BLOCK_TO_ROOT = {
    "art-scoped-css": "art-resiliencia",
    "art-scoped-css-art-nuevos-modelos-negocio": "art-nuevos-modelos-negocio",
    "art-scoped-css-art-eficiencia-cognitiva": "art-eficiencia-cognitiva",
    "art-scoped-css-art-sostenibilidad-valor": "art-sostenibilidad-valor",
    "art-scoped-css-cx-video-ia": "cx-video-ia",
    "art-scoped-css-cx-growth-2027": "cx-growth-2027",
}


def extract_scoped_blocks(html: str):
    """Returns [(block_id, css_text), ...] for every art-scoped-css* block."""
    blocks = []
    for m in re.finditer(r'<style id="(art-scoped-css[^"]*)">(.*?)</style>', html, re.DOTALL):
        blocks.append((m.group(1), m.group(2)))
    return blocks


def audit_css_collisions(html: str):
    """
    Every selector in a scoped block should read `.art-frame#<root-id> ...`.
    Flags:
      - "unanchored": a `.art-frame` selector with no `#id` at all (the old,
        collision-prone form -- a regression if it reappears).
      - "wrong-anchor": a `.art-frame#X` selector where X isn't this block's
        own root id (points at a DIFFERENT article -- almost certainly a
        copy-paste mistake, and won't match anything in this block's own
        markup).
    """
    blocks = extract_scoped_blocks(html)
    findings = []

    for block_id, css_text in blocks:
        expected_root = BLOCK_TO_ROOT.get(block_id)
        if not expected_root:
            findings.append({
                "block": block_id,
                "issue": "unknown block id -- add it to BLOCK_TO_ROOT so it can be audited",
            })
            continue

        # Every occurrence of the literal token `.art-frame`, anchored or not.
        unanchored = []
        wrong_anchor = {}
        for m in re.finditer(r'\.art-frame(#([a-zA-Z0-9_-]+))?\b', css_text):
            anchor = m.group(2)
            # Grab a short snippet for context (up to the next '{' or 80 chars).
            snippet_end = css_text.find('{', m.end())
            snippet = css_text[m.start():snippet_end if 0 <= snippet_end - m.start() <= 120 else m.start() + 60].strip()
            if anchor is None:
                unanchored.append(snippet)
            elif anchor != expected_root:
                wrong_anchor.setdefault(anchor, []).append(snippet)

        if unanchored:
            findings.append({
                "block": block_id,
                "issue": f"{len(unanchored)} selector(s) missing '#{expected_root}' anchor "
                         f"(unscoped -- vulnerable to cross-article collisions again)",
                "examples": unanchored[:8],
            })
        if wrong_anchor:
            findings.append({
                "block": block_id,
                "issue": f"selector(s) anchored to a DIFFERENT article's id than this block's own "
                         f"('{expected_root}') -- likely copy-paste mistake, will match nothing here",
                "examples": {k: v[:5] for k, v in wrong_anchor.items()},
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
    print("STATIC CSS SCOPING AUDIT")
    print("=" * 70)
    css_findings = audit_css_collisions(html)
    if not css_findings:
        print("Every scoped selector is correctly anchored to its own article's #id.")
    else:
        for f in css_findings:
            print(f"\n[{f['block']}] {f['issue']}")
            if "examples" in f:
                print("   ", json.dumps(f["examples"], ensure_ascii=False)[:500])

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
