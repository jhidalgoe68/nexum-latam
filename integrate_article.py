#!/usr/bin/env python3
"""
integrate_article.py — Add one "informe ejecutivo"-style HTML article to
Section 05 / Perspectivas of the NEXUM LATAM site, natively (no iframe, no
modal, no separate page), adapted to the site's own design system.

USAGE
  python3 integrate_article.py --html SITE.html --article ARTICLE.html \
      [--out OUT.html] [--category "Resiliencia Empresarial"] [--id my-slug]
"""

import argparse
import re
import sys
import unicodedata
from bs4 import BeautifulSoup


# ════════════════════════════════════════════════════════════════
# 1. CSS scoper
# ════════════════════════════════════════════════════════════════

def scope_css(css, prefix):
    out = []
    i = 0
    n = len(css)

    def skip_block(start):
        depth = 0
        j = start
        while j < n:
            if css[j] == '{':
                depth += 1
            elif css[j] == '}':
                depth -= 1
                if depth == 0:
                    return css[start:j + 1], j + 1
            j += 1
        return css[start:], n

    while i < n:
        if css[i] in ' \t\n\r':
            out.append(css[i]); i += 1; continue

        if css[i:i + 2] == '/*':
            end = css.find('*/', i + 2)
            if end == -1: out.append(css[i:]); break
            out.append(css[i:end + 2]); i = end + 2; continue

        if re.match(r'@(charset|import)\b', css[i:]):
            semi = css.find(';', i)
            if semi == -1: out.append(css[i:]); break
            out.append(css[i:semi + 1]); i = semi + 1; continue

        if re.match(r'@(keyframes|font-face|-webkit-keyframes)\b', css[i:]):
            brace = css.find('{', i)
            if brace == -1: out.append(css[i:]); break
            out.append(css[i:brace])
            block, end = skip_block(brace)
            out.append(block); i = end; continue

        if re.match(r'@(media|supports)\b', css[i:]):
            brace = css.find('{', i)
            if brace == -1: out.append(css[i:]); break
            out.append(css[i:brace + 1])
            depth = 1; j = brace + 1; inner_start = j
            while j < n:
                if css[j] == '{': depth += 1
                elif css[j] == '}':
                    depth -= 1
                    if depth == 0:
                        inner = css[inner_start:j]
                        out.append(scope_css(inner, prefix))
                        out.append('}')
                        i = j + 1; break
                j += 1
            else:
                i = n
            continue

        brace = css.find('{', i)
        if brace == -1: out.append(css[i:]); break

        sel_text = css[i:brace].strip()
        new_sels = []
        for sel in sel_text.split(','):
            sel = sel.strip()
            if not sel:
                continue
            if sel in (':root', 'body', 'html', '*'):
                new_sels.append(prefix if sel != '*' else f'{prefix} *')
            elif sel.startswith(':root'):
                new_sels.append(prefix + sel[5:])
            elif re.match(r'^(html|body)(\s|>|\.|\:|\+|~|$)', sel):
                new_sels.append(re.sub(r'^(html|body)', prefix, sel, count=1))
            else:
                new_sels.append(f'{prefix} {sel}')

        out.append(', '.join(new_sels))
        block, end = skip_block(brace)
        out.append(block)
        i = end

    return ''.join(out)


# ════════════════════════════════════════════════════════════════
# 2. Retheme
# ════════════════════════════════════════════════════════════════

RETHEME_ROOT = '''
:root{
  --navy-950:#DEE9F5;
  --navy-900:#EDF3F9;
  --navy-800:#FFFFFF;
  --navy-700:#DEE9F5;
  --line:rgba(9,27,56,.14);
  --ink:#091B38;
  --ink-2:#1A3252;
  --ink-3:#4A5A72;
  --gold-1:#00AFC9;
  --gold-2:#0C2B5C;
  --gold-3:#C87A18;
  --teal:#00C0DC;
  --amber:#C87A18;
  --red:#B3433A;
  --f-display: var(--font-heading);
  --f-body: var(--font-body);
  --f-mono: var(--font-body);
  color-scheme: light;
}
'''

MOBILE_TOC_BLOCK = '''@media (max-width:980px){
  .shell{grid-template-columns:minmax(0,1fr);gap:8px}
  .toc{position:sticky;top:env(safe-area-inset-top,0px);z-index:20;background:var(--navy-900);margin-inline:-20px;padding:10px 20px;border-bottom:1px solid var(--line)}
  .toc h2{display:none}
  .toc ol{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none}
  .toc ol::-webkit-scrollbar{display:none}
  .toc a{display:block;white-space:nowrap;border:1px solid var(--line);border-radius:999px;padding:5px 12px}
  .toc a span{margin-right:6px}
}'''


def retheme_css(raw_css: str) -> str:
    css = raw_css
    css = re.sub(r':root\s*\{[^}]*\}', '', css, count=1)
    css = css.replace(MOBILE_TOC_BLOCK, '')

    css = re.sub(r'color:#fff\b', 'color:var(--ink)', css)

    css = re.sub(r'\.l1\{[^}]*\}', '.l1{background:rgba(179,67,58,.12);color:#B3433A}', css)
    css = re.sub(r'\.l2\{[^}]*\}', '.l2{background:rgba(200,122,24,.14);color:#C87A18}', css)
    css = re.sub(r'\.l3\{[^}]*\}', '.l3{background:rgba(9,27,56,.08);color:#1A3252}', css)
    css = re.sub(r'\.l4\{[^}]*\}', '.l4{background:rgba(0,192,220,.14);color:#00AFC9}', css)
    css = re.sub(r'\.l5\{[^}]*\}', '.l5{background:rgba(31,138,76,.12);color:#1F8A4C}', css)

    css = css.replace('background:rgba(201,169,97,.06)', 'background:rgba(200,122,24,.07)')
    css = css.replace('rgba(95,179,168,.45)', 'rgba(0,192,220,.45)')
    css = css.replace('rgba(224,164,88,.45)', 'rgba(200,122,24,.45)')
    css = css.replace('rgba(232,200,116,.4)', 'rgba(0,175,201,.4)')

    # Fix any remaining hardcoded dark font references
    css = re.sub(r"'Cormorant Garamond'[^;]*", 'var(--font-heading)', css)
    css = re.sub(r"'DM Mono'[^;]*", 'var(--font-body)', css)
    css = re.sub(r"'DM Sans'[^;]*", 'var(--font-body)', css)
    css = re.sub(r"'Jost'[^;]*", 'var(--font-body)', css)

    full_css = RETHEME_ROOT + css
    return scope_css(full_css, '.art-frame')


# ════════════════════════════════════════════════════════════════
# 3. Shared hub/nav infrastructure (injected once)
# ════════════════════════════════════════════════════════════════

SHARED_NAV_CSS = '''
    /* ════════════════════════════════════════════════════════════
       ARTICLE NAVIGATION — shared component, reused by every
       article opened from Perspectivas. Do not duplicate this
       per article; it is applied automatically by
       buildArticleNav() to whichever .art-frame is open.
       ════════════════════════════════════════════════════════ */
    .art-sticky {
      position: sticky;
      top: 80px;
      z-index: 15;
      background: rgba(237,243,249,0.94);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--border);
      margin: 0 0 2.5rem;
      padding: 1rem 0 0.9rem;
    }
    .art-nav-label {
      font-family: var(--font-body);
      font-size: 0.65rem;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: var(--mid-lt);
      margin-bottom: 0.7rem;
    }
    .art-nav {
      display: flex;
      flex-wrap: wrap;
      gap: 0.55rem;
      list-style: none;
    }
    .art-nav-btn {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: transparent;
      border: 1.5px solid var(--gold);
      border-radius: 3px;
      color: var(--ink);
      font-family: var(--font-body);
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.01em;
      padding: 0.5rem 1rem;
      cursor: pointer;
      white-space: nowrap;
      transition: background 0.2s var(--ease), color 0.2s var(--ease), transform 0.15s var(--ease);
    }
    .art-nav-btn .num {
      font-family: var(--font-body);
      font-weight: 500;
      font-size: 0.68rem;
      color: var(--gold);
      transition: color 0.2s var(--ease);
    }
    .art-nav-btn:hover {
      background: var(--gold);
      color: var(--ink);
      transform: translateY(-1px);
    }
    .art-nav-btn:hover .num { color: var(--ink); }
    .art-nav-btn.active {
      background: var(--gold);
      color: var(--ink);
      box-shadow: 0 4px 14px rgba(0,192,220,0.35);
    }
    .art-nav-btn.active .num { color: var(--ink); }
    .art-nav-btn:focus-visible {
      outline: 2px solid var(--gold);
      outline-offset: 2px;
    }
    #artProgressTrack {
      height: 2px;
      background: var(--border);
      border-radius: 1px;
      margin-top: 0.9rem;
      overflow: hidden;
    }
    #artProgressFill {
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, var(--amber), var(--gold));
      transition: width 0.1s linear;
    }
    @media (max-width: 900px) {
      .art-sticky { top: 64px; padding: 0.85rem 0 0.75rem; }
      .art-nav { flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; padding-bottom: 2px; }
      .art-nav::-webkit-scrollbar { display: none; }
      .art-nav-btn { flex-shrink: 0; }
    }
'''

SHARED_HUB_JS = r'''
  <!-- ── Perspectivas hub/panel logic ── -->
  <script>
  (function(){
    const hub   = document.getElementById('perspectivasHub');
    const panel = document.getElementById('artPanel');
    const body  = document.getElementById('artBody');
    const sticky= document.getElementById('artSticky');
    const nav   = document.getElementById('artNav');
    const fill  = document.getElementById('artProgressFill');
    if(!hub||!panel||!body||!sticky||!nav) return;

    let activeFrame = null;

    function buildArticleNav(frame){
      nav.innerHTML = '';
      const sections = frame.querySelectorAll('section[id]');
      sections.forEach(function(sec,idx){
        const ew = sec.querySelector('.eyebrow,.section-tag');
        const label = ew ? ew.textContent.trim() : (sec.querySelector('h2')||{}).textContent||('§'+(idx+1));
        const li  = document.createElement('li');
        const btn = document.createElement('button');
        btn.className = 'art-nav-btn';
        const num = label.match(/^(\d+\s*[·\-]\s*)/);
        if(num){
          const sp = document.createElement('span');
          sp.className = 'num';
          sp.textContent = num[1].trim();
          btn.appendChild(sp);
          btn.appendChild(document.createTextNode(label.slice(num[0].length).trim()));
        } else {
          btn.textContent = label;
        }
        btn.addEventListener('click', function(){
          sec.scrollIntoView({behavior:'smooth',block:'start'});
        });
        li.appendChild(btn);
        nav.appendChild(li);
      });
    }

    function updateProgress(){
      if(!activeFrame) return;
      const r = activeFrame.getBoundingClientRect();
      const total = activeFrame.offsetHeight - window.innerHeight;
      if(total <= 0){ fill.style.width='100%'; return; }
      const pct = Math.min(100, Math.max(0, (-r.top / total)*100));
      fill.style.width = pct + '%';
      const sections = activeFrame.querySelectorAll('section[id]');
      const btns = nav.querySelectorAll('.art-nav-btn');
      sections.forEach(function(sec,i){
        const sr = sec.getBoundingClientRect();
        if(btns[i]) btns[i].classList.toggle('active', sr.top <= 200 && sr.bottom > 0);
      });
    }

    window.addEventListener('scroll', updateProgress, {passive:true});

    function openArticle(id){
      document.querySelectorAll('.art-frame').forEach(function(f){ f.hidden=true; });
      const frame = document.getElementById(id);
      if(!frame) return;
      frame.hidden = false;
      activeFrame = frame;
      hub.hidden   = true;
      panel.hidden = false;
      sticky.hidden= false;
      buildArticleNav(frame);
      panel.scrollIntoView({behavior:'smooth',block:'start'});
      updateProgress();
    }

    function closeArticle(){
      document.querySelectorAll('.art-frame').forEach(function(f){ f.hidden=true; });
      activeFrame  = null;
      panel.hidden = true;
      sticky.hidden= true;
      hub.hidden   = false;
      fill.style.width='0%';
      hub.scrollIntoView({behavior:'smooth',block:'start'});
    }

    document.querySelectorAll('[data-art]').forEach(function(btn){
      btn.addEventListener('click', function(e){
        e.preventDefault();
        openArticle(btn.dataset.art);
      });
    });

    const backBtn = document.getElementById('artBack');
    if(backBtn) backBtn.addEventListener('click', closeArticle);

    document.addEventListener('keydown', function(e){
      if(e.key==='Escape' && activeFrame) closeArticle();
    });
  })();
  </script>
'''

PANEL_SHELL = '''
  <!-- ── Perspectivas article panel ── -->
  <div id="artSticky" class="wrap art-sticky" hidden>
    <p class="art-nav-label">Secciones del informe</p>
    <ul class="art-nav" id="artNav" role="list"></ul>
    <div id="artProgressTrack"><div id="artProgressFill"></div></div>
  </div>
  <div id="artPanel" hidden>
    <div class="wrap" style="padding-block:1.25rem 0;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:1rem">
      <button id="artBack" style="display:inline-flex;align-items:center;gap:0.5rem;font-family:var(--font-body);font-size:0.78rem;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;color:var(--ink-mid);background:none;border:1px solid var(--border);padding:0.5rem 1.1rem;cursor:pointer;">
        &#8592; Perspectivas
      </button>
    </div>
    <div id="artBody">
      <!-- art-frame blocks inserted here by the script -->
    </div>
  </div>
'''


# ════════════════════════════════════════════════════════════════
# 4. Slug / id helpers
# ════════════════════════════════════════════════════════════════

def slugify(text: str) -> str:
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')[:60]


# ════════════════════════════════════════════════════════════════
# 5. Article parser  — handles both header.mast and header.cover
# ════════════════════════════════════════════════════════════════

def parse_article(art_soup):
    """
    Returns (h1_html, dek_html, date_str, style_text, body_html, sections)
    Handles:
      - header.mast  (original template)
      - header.cover (this article's variant)
    """
    # --- Style block ---
    style_tag = art_soup.find('style')
    style_text = style_tag.string or style_tag.get_text() if style_tag else ''

    # --- Masthead: try .mast first, then .cover ---
    mast = art_soup.find('header', class_='mast') or art_soup.find('header', class_='cover')

    h1_tag = mast.find('h1') if mast else art_soup.find('h1')
    h1_html = str(h1_tag) if h1_tag else '<h1>(sin título)</h1>'

    # dek: .dek or p.lead (cover variant) or first <p> after h1
    dek_html = ''
    if mast:
        dek_tag = (mast.find(class_='dek') or
                   mast.find('p', class_='lead') or
                   mast.find('p'))
        if dek_tag:
            dek_html = dek_tag.get_text(strip=True)

    # date from .meta or spans inside .cover
    date_str = ''
    if mast:
        meta = mast.find(class_='meta')
        if meta:
            date_str = meta.get_text(' ', strip=True)[:120]
        else:
            # cover variant: spans in the header
            spans = mast.find_all('span')
            if spans:
                date_str = ' · '.join(s.get_text(strip=True) for s in spans if s.get_text(strip=True))[:120]

    # Remove the masthead from the soup so it doesn't appear in body
    if mast:
        mast.decompose()

    # Also remove nav, .toc, #progress, scripts
    for tag in art_soup.find_all(['nav', 'script', 'footer']):
        tag.decompose()
    toc = art_soup.find(class_='toc')
    if toc:
        toc.decompose()
    prog = art_soup.find(id='progress')
    if prog:
        prog.decompose()

    # Collect sections
    sections = [(s.get('id', ''), s) for s in art_soup.find_all('section', id=True)]

    # Body HTML (everything remaining inside <body> or the soup root)
    body_tag = art_soup.find('body') or art_soup
    body_html = body_tag.decode_contents()

    return h1_html, dek_html, date_str, style_text, body_html, sections


# ════════════════════════════════════════════════════════════════
# 6. Build the card row + art-frame block
# ════════════════════════════════════════════════════════════════

def build_card(art_id, h1_html, dek_html, date_str, category):
    h1_text = BeautifulSoup(h1_html, 'html.parser').get_text(strip=True)
    return f'''
      <article class="blog-item" style="cursor:pointer;" data-art="{art_id}" tabindex="0" role="button" aria-label="Leer: {h1_text}">
        <div class="blog-item-header">
          <span class="blog-category">{category}</span>
          <span class="blog-date">{date_str}</span>
        </div>
        <h3 class="blog-title">{h1_html}</h3>
        <p class="blog-excerpt">{dek_html}</p>
        <div class="blog-item-footer">
          <button class="btn-read" data-art="{art_id}" tabindex="-1">Leer Perspectiva <span class="arr">&#8594;</span></button>
        </div>
      </article>'''


def build_art_frame(art_id, scoped_css, body_html, h1_html, dek_html, date_str):
    return f'''
    <style id="art-scoped-css-{art_id}">
  /* ── SCOPED + RETHEMED ARTICLE CSS: {art_id} ── */

{scoped_css}

.art-frame#{art_id} .fade{{opacity:1!important;transform:none!important}}
  </style>
    <div class="art-frame" id="{art_id}" hidden>
{body_html}
    </div>'''


# ════════════════════════════════════════════════════════════════
# 7. Main integration logic
# ════════════════════════════════════════════════════════════════

def integrate(site_html: str, article_html: str, category: str, art_id: str) -> str:
    site = BeautifulSoup(site_html, 'html.parser')
    art  = BeautifulSoup(article_html, 'html.parser')

    # Parse article
    h1_html, dek_html, date_str, style_text, body_html, sections = parse_article(art)

    print(f"  H1: {BeautifulSoup(h1_html,'html.parser').get_text(strip=True)[:80]}")
    print(f"  Dek: {dek_html[:80]}")
    print(f"  Date: {date_str}")
    print(f"  Sections: {len(sections)}")

    # Namespace section ids
    body_html_ns = body_html
    for sec_id, _ in sections:
        if sec_id:
            body_html_ns = re.sub(
                rf'\bid=(["\']){re.escape(sec_id)}\1',
                f'id=\\1{art_id}-{sec_id}\\1',
                body_html_ns
            )
            body_html_ns = re.sub(
                rf'\bhref=(["\'])#{re.escape(sec_id)}\1',
                f'href=\\1#{art_id}-{sec_id}\\1',
                body_html_ns
            )

    # Retheme CSS
    scoped_css = retheme_css(style_text)

    # Native-integration overrides
    scoped_css += f'''

  /* ── Native-integration overrides (not part of the article's own CSS) ── */
  /* .progress now handled by the shared #artSticky component */
  .art-frame#{art_id} .thesis{{padding-inline:0;max-width:none;margin:0}}
  .art-frame#{art_id} .shell{{padding-inline:0;max-width:none;margin:0;grid-template-columns:minmax(0,1fr);gap:0}}
  /* .toc nav replaced by the shared, auto-generated #artNav component */
  .art-frame#{art_id} section{{scroll-margin-top:190px}}
  .art-frame#{art_id} footer{{padding-inline:0}}
  .art-frame#{art_id} footer .in{{max-width:none;margin:0}}
  .art-frame#{art_id} .meta{{margin-top:0.75rem;padding-bottom:1.75rem;border-bottom:1px solid var(--line)}}
  #artPanel{{scroll-margin-top:96px}}
  #artSticky{{scroll-margin-top:0}}
  #perspectivasHub{{scroll-margin-top:96px}}
'''

    # Check if hub already exists (APPEND mode)
    hub_exists = bool(site.find(id='perspectivasHub'))
    panel_exists = bool(site.find(id='artPanel'))

    if not hub_exists:
        print("  → Bootstrap mode: injecting hub/panel/nav infrastructure")
    else:
        print("  → Append mode: hub already exists, adding card + frame")

    # ── Inject shared nav CSS (once, into first <style> or <head>) ──
    if not hub_exists:
        head = site.find('head')
        if head:
            nav_style = BeautifulSoup(
                f'<style id="art-shared-nav-css">{SHARED_NAV_CSS}</style>', 'html.parser'
            ).find('style')
            head.append(nav_style)

    # ── Find the perspectivas section ──
    # Try id="perspectivas" or id="05" or section containing "Perspectivas" heading
    persp_section = (
        site.find(id='perspectivas') or
        site.find(id='05') or
        site.find('section', id=lambda x: x and 'perspectiv' in x.lower())
    )
    if not persp_section:
        # Fallback: look for a section whose heading text contains "Perspectivas"
        for sec in site.find_all('section'):
            h = sec.find(['h2','h3','h4'])
            if h and 'perspectiva' in h.get_text().lower():
                persp_section = sec
                break

    if not persp_section:
        print("ERROR: Could not find Perspectivas section in site HTML", file=sys.stderr)
        sys.exit(1)

    print(f"  Perspectivas section id: {persp_section.get('id','(no id)')}")

    # ── Find or create blog-list container ──
    blog_list = persp_section.find(class_='blog-list')
    if not blog_list:
        blog_list = persp_section.find(class_='blog-grid')
    if not blog_list:
        # Create one before the first closing tag area
        bl_tag = BeautifulSoup('<div class="blog-list"></div>', 'html.parser').find('div')
        persp_section.append(bl_tag)
        blog_list = persp_section.find(class_='blog-list')

    # ── Build and inject the card ──
    card_html = build_card(art_id, h1_html, dek_html, date_str, category)
    card_soup = BeautifulSoup(card_html, 'html.parser')
    blog_list.append(card_soup)

    # ── Bootstrap hub/panel shell if first article ──
    if not hub_exists:
        # Wrap existing blog-list in #perspectivasHub
        hub_wrapper = BeautifulSoup(
            '<div id="perspectivasHub"></div>', 'html.parser'
        ).find('div')
        blog_list.replace_with(hub_wrapper)
        hub_wrapper.append(blog_list)

        # Insert panel shell after the perspectivas section
        panel_soup = BeautifulSoup(PANEL_SHELL, 'html.parser')
        persp_section.insert_after(panel_soup)

    # ── Inject art-frame block ──
    art_frame_html = build_art_frame(art_id, scoped_css, body_html_ns, h1_html, dek_html, date_str)
    art_frame_soup = BeautifulSoup(art_frame_html, 'html.parser')

    art_body = site.find(id='artBody')
    if art_body:
        art_body.append(art_frame_soup)
    else:
        # fallback: append after panel
        art_panel = site.find(id='artPanel')
        if art_panel:
            art_panel.append(art_frame_soup)

    # ── Inject hub JS (once) ──
    if not hub_exists:
        js_soup = BeautifulSoup(SHARED_HUB_JS, 'html.parser')
        body = site.find('body')
        if body:
            body.append(js_soup)

    # ── Duplicate-id check ──
    all_ids = [tag.get('id') for tag in site.find_all(id=True)]
    dupes = [i for i in all_ids if all_ids.count(i) > 1 and i]
    if dupes:
        print(f"WARNING: Duplicate ids found: {set(dupes)}", file=sys.stderr)

    # ── Verify new art-frame is present ──
    if not site.find(id=art_id):
        print(f"ERROR: {art_id} not found in output!", file=sys.stderr)
        sys.exit(1)

    return str(site)


# ════════════════════════════════════════════════════════════════
# 8. CLI
# ════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--html',     required=True)
    parser.add_argument('--article',  required=True)
    parser.add_argument('--out',      default=None)
    parser.add_argument('--category', default='Perspectiva')
    parser.add_argument('--id',       default=None)
    args = parser.parse_args()

    with open(args.html,    encoding='utf-8') as f: site_html    = f.read()
    with open(args.article, encoding='utf-8') as f: article_html = f.read()

    # Derive id from title if not given
    if not args.id:
        soup = BeautifulSoup(article_html, 'html.parser')
        h1 = soup.find('h1')
        title_text = h1.get_text(strip=True) if h1 else 'articulo'
        art_id = 'art-' + slugify(title_text)
    else:
        art_id = args.id if args.id.startswith('art-') else 'art-' + args.id

    print(f"Integrating article id={art_id} category='{args.category}'")

    result = integrate(site_html, article_html, args.category, art_id)

    out_path = args.out or args.html
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"Written to {out_path} ({len(result):,} bytes)")


if __name__ == '__main__':
    main()
