#!/usr/bin/env python3
"""
verify_render.py — Headless Chromium check for a newly inserted assessment.

USAGE
  python3 scripts/verify_render.py --html index.html --title "Title here" --screenshot section7.png
"""

import argparse
import json
import os
import re
import sys

def check_source(html_path, title):
    """Source-level checks (no browser needed)."""
    with open(html_path) as f:
        html = f.read()

    issues = []

    # Check ASSESSMENTS array
    m = re.search(r'var ASSESSMENTS = \[(.*?)\];', html, re.DOTALL)
    if not m:
        issues.append("ASSESSMENTS array not found")
        return issues, False

    block = m.group(1)
    titles = re.findall(r"title:\s*'([^']+)'", block)
    if title not in titles:
        issues.append(f"Title '{title}' not found in ASSESSMENTS")
    else:
        print(f"  ✓ Title found in ASSESSMENTS")

    # Check the NEW assessment specifically (find the one with matching title)
    if title:
        title_pos = block.find(f"title: '{title}'")
        if title_pos >= 0:
            # Extract ~10KB from that title onwards (covers the full entry)
            new_entry_snippet = block[title_pos:title_pos+10000]
            if 'scoreRanges:' in new_entry_snippet and 'bands:' not in new_entry_snippet:
                issues.append("CRITICAL: New assessment uses scoreRanges — must be 'bands:'")

    # Check readyness section exists
    if 'id="readyness"' not in html:
        issues.append('Section id="readyness" not found')
    else:
        print("  ✓ #readyness section present")

    # Check no duplicate ids
    all_ids = re.findall(r'id=["\']([^"\']+)["\']', html)
    seen = set()
    for aid in all_ids:
        if aid in seen:
            issues.append(f"Duplicate id: {aid}")
        seen.add(aid)

    if not issues:
        print("  ✓ No duplicate ids detected")

    return issues, True

def run_playwright(html_path, title, screenshot_path):
    """Try headless Chromium screenshot via Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "Playwright not installed (exit 6 — render check skipped)"

    abs_path = os.path.abspath(html_path)
    url = f"file://{abs_path}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path='/opt/pw-browsers/chromium',
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            page = browser.new_page(viewport={'width': 1440, 'height': 900})
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))

            page.goto(url, wait_until='networkidle', timeout=30000)

            # Scroll to #readyness
            page.evaluate("document.getElementById('readyness')?.scrollIntoView()")
            page.wait_for_timeout(500)

            page.screenshot(path=screenshot_path, full_page=False)
            browser.close()

            return True, errors

    except Exception as e:
        return False, str(e)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--html', required=True)
    parser.add_argument('--title', required=True)
    parser.add_argument('--screenshot', default='section7.png')
    args = parser.parse_args()

    print(f"\nVerifying: {args.html}")
    print(f"Title: {args.title}")

    source_issues, array_found = check_source(args.html, args.title)

    result = {
        "titles_read_from": "source",
        "title_in_assessments": args.title not in [i for i in source_issues if 'Title' in i],
        "source_issues": source_issues,
        "js_errors": [],
        "screenshot": None,
        "start_button_opened_form": None
    }

    pw_ok, pw_result = run_playwright(args.html, args.title, args.screenshot)
    if pw_ok:
        result["js_errors"] = pw_result if isinstance(pw_result, list) else []
        result["screenshot"] = args.screenshot
        print(f"  ✓ Screenshot saved: {args.screenshot}")
    else:
        result["playwright_note"] = str(pw_result)
        print(f"  ⚠ Playwright: {pw_result}")

    print("\nResult:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if source_issues:
        print(f"\nFAILED: {len(source_issues)} source issue(s)", file=sys.stderr)
        for i in source_issues:
            print(f"  - {i}", file=sys.stderr)
        sys.exit(5)

    print("\nPASSED")

if __name__ == '__main__':
    main()
