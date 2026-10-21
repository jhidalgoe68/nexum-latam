#!/usr/bin/env python3
"""
insert_assessment.py — Append one assessment object to the ASSESSMENTS array
in the NEXUM LATAM site file, with pre/post validation.

USAGE
  python3 scripts/insert_assessment.py --html index.html --object scripts/new-assessment.js --out index.html
  python3 scripts/insert_assessment.py --html index.html --list
"""

import argparse
import json
import re
import sys

def find_assessments_block(html):
    """Return (start, end) char offsets of the ASSESSMENTS array [...] in html."""
    m = re.search(r'var ASSESSMENTS = \[', html)
    if not m:
        return None, None
    start = m.end() - 1  # position of '['
    depth = 0
    in_str = False
    str_char = None
    i = start
    while i < len(html):
        c = html[i]
        if in_str:
            if c == '\\':
                i += 2
                continue
            if c == str_char:
                in_str = False
        else:
            if c in ('"', "'", '`'):
                in_str = True
                str_char = c
            elif c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    return start, i + 1
        i += 1
    return None, None

def list_assessments(html):
    start, end = find_assessments_block(html)
    if start is None:
        print("ERROR: No ASSESSMENTS array found.", file=sys.stderr)
        sys.exit(2)
    block = html[start:end]
    ids = re.findall(r"id:\s*'(a\d+)'", block)
    titles = re.findall(r"title:\s*'([^']+)'", block)
    nums = [int(i[1:]) for i in ids] if ids else [0]
    next_id = 'a' + str(max(nums) + 1)
    print(f"Found {len(ids)} assessment(s):")
    for i, (aid, title) in enumerate(zip(ids, titles)):
        print(f"  {aid}: {title}")
    print(f"Next free ID: {next_id}")
    return next_id

def validate_object(obj_text):
    """Basic structural validation of the JS object."""
    required = ['title:', 'subtitle:', 'type:', 'bands:']
    missing = [r for r in required if r not in obj_text]
    if missing:
        print(f"ERROR: Assessment object missing required fields: {missing}", file=sys.stderr)
        sys.exit(3)
    if 'scoreRanges:' in obj_text:
        print("ERROR: Found 'scoreRanges:' — use 'bands:' instead (scoreRanges silently breaks results).", file=sys.stderr)
        sys.exit(3)

def insert(html_path, obj_path, out_path):
    with open(html_path) as f:
        html = f.read()

    with open(obj_path) as f:
        obj_text = f.read().strip()

    validate_object(obj_text)

    start, end = find_assessments_block(html)
    if start is None:
        print("ERROR: No ASSESSMENTS array found in site file.", file=sys.stderr)
        sys.exit(2)

    block = html[start:end]

    # Check for duplicate title
    existing_titles = re.findall(r"title:\s*'([^']+)'", block)
    new_title_m = re.search(r"title:\s*'([^']+)'", obj_text)
    new_title = new_title_m.group(1) if new_title_m else ''
    if new_title and new_title in existing_titles:
        print(f"ERROR (exit 4): Assessment with title '{new_title}' already exists. Use --allow-duplicate-title to override.", file=sys.stderr)
        sys.exit(4)

    # Resolve 'auto' ID
    ids = re.findall(r"id:\s*'(a\d+)'", block)
    nums = [int(i[1:]) for i in ids] if ids else [0]
    next_id = 'a' + str(max(nums) + 1)
    obj_text = obj_text.replace("id: 'auto'", f"id: '{next_id}'")

    # Count existing assessments
    before_count = len(ids)

    # Build new block: insert before the closing ]
    # Find the last non-whitespace before ]
    inner = html[start+1:end-1].rstrip()
    # Add comma after last entry if needed
    if inner and inner[-1] not in (',', '['):
        comma = ',\n'
    else:
        comma = '\n'

    new_block = '[' + html[start+1:end-1].rstrip() + comma + obj_text + '\n]'
    new_html = html[:start] + new_block + html[end:]

    # Post-insert verification
    start2, end2 = find_assessments_block(new_html)
    if start2 is None:
        print("ERROR (exit 5): Post-insert parse failed — ASSESSMENTS array broken.", file=sys.stderr)
        sys.exit(5)
    new_block_check = new_html[start2:end2]
    after_ids = re.findall(r"id:\s*'(a\d+)'", new_block_check)
    after_count = len(after_ids)

    if after_count != before_count + 1:
        print(f"ERROR (exit 5): Expected {before_count+1} assessments after insert, found {after_count}.", file=sys.stderr)
        sys.exit(5)

    if f"id: '{next_id}'" not in new_html:
        print(f"ERROR (exit 5): New assessment id '{next_id}' not found after insert.", file=sys.stderr)
        sys.exit(5)

    with open(out_path, 'w') as f:
        f.write(new_html)

    print(json.dumps({
        "status": "ok",
        "new_id": next_id,
        "new_title": new_title,
        "before_count": before_count,
        "after_count": after_count,
        "out": out_path
    }, ensure_ascii=False, indent=2))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--html', required=True)
    parser.add_argument('--object', dest='obj')
    parser.add_argument('--out')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--allow-duplicate-title', action='store_true')
    args = parser.parse_args()

    with open(args.html) as f:
        html = f.read()

    if args.list:
        list_assessments(html)
        return

    if not args.obj:
        print("ERROR: --object required for insert mode.", file=sys.stderr)
        sys.exit(1)

    out = args.out or args.html
    insert(args.html, args.obj, out)

if __name__ == '__main__':
    main()
