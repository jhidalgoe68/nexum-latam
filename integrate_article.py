#!/usr/bin/env python3
"""
integrate_article.py — Add one "informe ejecutivo"-style HTML article to
Section 05 / Perspectivas of the NEXUM LATAM site, natively (no iframe, no
modal, no separate page), adapted to the site's own design system.

USAGE
  python3 integrate_article.py --html SITE.html --article ARTICLE.html \
      [--out OUT.html] [--category "Resiliencia Empresarial"] [--id my-slug]

  --html      The current site file (index.html / a saved copy of the live
              artifact). Required.
  --article   The uploaded article export to integrate. Required.
  --out       Where to write the result. Defaults to overwriting --html.
  --category  Short label shown on the card's category chip (e.g.
              "Resiliencia Empresarial"). Defaults to a guess from the
              article's eyebrow/title; always sanity-check this.
  --id        Slug used for the article's element id (art-<id>) and DOM
              hooks. Auto-derived from the title if omitted. Must be
              unique among articles already in the site.

WHAT THIS DOES (see SKILL.md for the full rationale)
  1. Parses the article: masthead (H1/dek/date), its own <style> block
     (the one with dark-navy CSS custom properties), and its body content.
  2. Retheme, not rewrite: remaps the article's CSS custom properties
     (--navy-900, --ink, --gold-1, --f-body, ...) to the site's own design
     tokens, so every bespoke component (KPI tiles, debate cards, tables,
     maturity matrices, roadmaps, institution cards) re-themes for free.
     Scopes all of it under `.art-frame` so it can never leak into the
     main site, and fixes the handful of hardcoded `color:#fff` rules
     that are invisible once the background goes from navy to cream.
  3. Bootstraps the shared hub/panel/nav infrastructure the FIRST time
     this runs on a given site file (adds #perspectivasHub, #artPanel,
     #artBody, #artSticky/#artNav, and the buildArticleNav() JS that
     auto-generates the sticky section nav from whichever article is
     open). On every later run that infrastructure already exists, so the
     script only APPENDS: one new .blog-item row + one new `.art-frame`
     block + one new scoped <style>. Every article — first or fifth — is
     the same row type; there is no featured/secondary distinction.
  4. Never touches any other article already integrated. Verifies no
     stray <body> tags, no duplicate ids, and the new article's id is
     actually present before writing anything.

This script does not publish or push anything — see SKILL.md Step 7-8.
"""

import argparse
import re
import sys
import unicodedata
from bs4 import BeautifulSoup


# ════════════════════════════════════════════════════════════════
# 1. CSS scoper — state machine, prefixes every selector with
#    `.art-frame`, recurses into @media/@supports, leaves
#    @keyframes/@font-face verbatim. Used on EVERY article.
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
# 2. Retheme — remap this article template's custom properties to
#    the site's own design tokens. This is the piece that makes a
#    dark-navy "informe ejecutivo" export look native on the cream
#    site without hand-rewriting any component.
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
    css = css.replace(MOBILE_TOC_BLOCK, '')  # TOC is dropped; nav is auto-built

    # Every hardcoded white text color was readable on this template's
    # dark-navy background and is invisible on the site's cream one.
    css = re.sub(r'color:#fff\b', 'color:var(--ink)', css)

    # Maturity/level badges (.l1-.l5): hardcoded dark chips -> light tinted
    # pills matching the site's own tag/chip idiom. Harmless no-op if this
    # particular article doesn't have a matrix (selectors just won't match).
    css = re.sub(r'\.l1\{[^}]*\}', '.l1{background:rgba(179,67,58,.12);color:#B3433A}', css)
    css = re.sub(r'\.l2\{[^}]*\}', '.l2{background:rgba(200,122,24,.14);color:#C87A18}', css)
    css = re.sub(r'\.l3\{[^}]*\}', '.l3{background:rgba(9,27,56,.08);color:#1A3252}', css)
    css = re.sub(r'\.l4\{[^}]*\}', '.l4{background:rgba(0,192,220,.14);color:#00AFC9}', css)
    css = re.sub(r'\.l5\{[^}]*\}', '.l5{background:rgba(31,138,76,.12);color:#1F8A4C}', css)

    # Debate "stance" highlight wash + badge borders — hardcoded rgba
    # literals tied to the OLD palette; update to match the new hues.
    css = css.replace('background:rgba(201,169,97,.06)', 'background:rgba(200,122,24,.07)')
    css = css.replace('rgba(95,179,168,.45)', 'rgba(0,192,220,.45)')   # .b.alta  (old --teal)
    css = css.replace('rgba(224,164,88,.45)', 'rgba(200,122,24,.45)')  # .b.media (old --amber)
    css = css.replace('rgba(232,200,116,.4)', 'rgba(0,175,201,.4)')    # .b.ed    (old --gold-1)

    full_css = RETHEME_ROOT + css
    return scope_css(full_css, '.art-frame')


MANUAL_OVERRIDES = '''
  /* ── Native-integration overrides (not part of the article's own CSS) ── */
  .art-frame .thesis{padding-inline:0;max-width:none;margin:0}
  .art-frame .shell{padding-inline:0;max-width:none;margin:0;grid-template-columns:minmax(0,1fr);gap:0}
  .art-frame section{scroll-margin-top:190px}
  .art-frame footer{padding-inline:0}
  .art-frame footer .in{max-width:none;margin:0}
  .art-frame .meta{margin-top:0.75rem;padding-bottom:1.75rem;border-bottom:1px solid var(--line)}
'''


# ════════════════════════════════════════════════════════════════
# 3. Parse one article export into its pieces
# ════════════════════════════════════════════════════════════════

def slugify(text, fallback='articulo'):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^a-zA-Z0-9]+', '-', text).strip('-').lower()
    return text[:40] or fallback


class ParsedArticle:
    pass


def parse_article(article_path, art_id):
    with open(article_path, 'r', encoding='utf-8') as f:
        article_html = f.read()

    art = BeautifulSoup(article_html, 'html.parser')
    body_el = art.find('body')
    assert body_el, "No <body> found in the article file"

    # The real stylesheet is the one that defines --navy-900. (The file may
    # also carry a tiny artifact-wrapper reset <style> in <head> — ignore it.)
    real_style_text = ''
    for s in art.find_all('style'):
        if s.string and '--navy-900' in s.string:
            real_style_text = s.string
            break
    assert real_style_text, (
        "Could not find the article's main <style> block (expected a "
        "`--navy-900` custom property). This script targets the "
        "'informe ejecutivo' template used so far — if the article's "
        "structure is different, adapt the extraction step first."
    )

    mast = body_el.find('header', class_='mast')
    h1_el = mast.find('h1') if mast else art.find('h1')
    dek_el = mast.find(class_='dek') if mast else art.find(class_='dek')
    meta_el = mast.find(class_='meta') if mast else None
    title_tag = art.find('title')

    p = ParsedArticle()
    p.title = title_tag.get_text(strip=True) if title_tag else 'Artículo'
    p.h1_text = h1_el.get_text(' ', strip=True) if h1_el else p.title
    p.h1_html = h1_el.decode_contents() if h1_el else p.title
    p.excerpt_text = dek_el.get_text(strip=True) if dek_el else ''
    p.excerpt_html = dek_el.decode_contents() if dek_el else ''

    p.date = ''
    if meta_el:
        first_span = meta_el.find('span')
        if first_span:
            label = first_span.find('b')
            txt = first_span.get_text(' ', strip=True)
            if label:
                txt = txt.replace(label.get_text(strip=True), '', 1).strip()
            if txt:
                p.date = txt
    if not p.date:
        p.date = ''  # leave blank rather than guess

    # Pull meta out before destroying mast so it survives for the panel header
    if meta_el:
        meta_el.extract()
    if mast:
        mast.decompose()

    # Strip script/link/title tags, all <style> tags, the article's own
    # progress bar and its own hand-authored TOC — all superseded by the
    # site's shared nav component.
    for tag in body_el(['script', 'link', 'title']):
        tag.decompose()
    for s in body_el.find_all('style'):
        s.decompose()
    prog = body_el.find(id='progress')
    if prog:
        prog.decompose()
    prog2 = body_el.find(id='progressBar')
    if prog2:
        prog2.decompose()
    toc_nav = body_el.find('nav', class_='toc')
    if toc_nav:
        toc_nav.decompose()

    rest_content = body_el.decode_contents()
    rest_content = re.sub(r'</?(?:body|html)[^>]*>', '', rest_content, flags=re.IGNORECASE)
    assert rest_content.lower().count('<body') == 0, "stray <body> tag survived extraction"

    # Namespace every internal id (and any #anchor referencing it) with this
    # article's own id. Different articles built from the same "informe
    # ejecutivo" template reuse the same generic section ids (resumen,
    # hallazgos, datos, ...) — without this, a second article collides
    # with the first one's ids document-wide.
    local_ids = sorted(set(re.findall(r'\bid="([^"]+)"', rest_content)), key=len, reverse=True)
    for old_id in local_ids:
        new_id = f'{art_id}-{old_id}'
        rest_content = re.sub(rf'\bid="{re.escape(old_id)}"', f'id="{new_id}"', rest_content)
        rest_content = re.sub(rf'href="#{re.escape(old_id)}"', f'href="#{new_id}"', rest_content)

    p.rest_content = rest_content
    p.meta_html = str(meta_el) if meta_el else ''
    p.scoped_css = retheme_css(real_style_text)
    p.art_id = art_id

    # Sanity: the article should have at least one section[id] for the
    # nav to auto-build from.
    section_ids = re.findall(r'<section[^>]*\bid="([^"]+)"', rest_content)
    assert section_ids, (
        "No <section id=\"...\"> elements found in the article body — "
        "buildArticleNav() needs these to generate the sticky nav. If this "
        "article doesn't use that convention, add ids to its top-level "
        "<section> wrappers before running this script."
    )
    p.section_count = len(section_ids)

    return p


# ════════════════════════════════════════════════════════════════
# 4. Card + frame markup
# ════════════════════════════════════════════════════════════════

def article_item_html(p, category, art_id):
    """Every article — the first one and every one after it — renders as
    one of these: a full-width, equal-weight row in the Perspectivas list.
    There is no 'featured' vs 'secondary' variant; do not reintroduce one.
    The whole <article> is the click/keyboard target (role=button,
    tabindex, aria-label), so the CTA is a plain span, not a nested
    button — nesting an interactive control inside another is an
    accessibility anti-pattern and would also fight the card's own click
    handler."""
    return f'''        <article class="blog-item" onclick="nexumOpenArticle('{art_id}')" style="cursor:pointer" role="button" tabindex="0" aria-label="Leer: {p.h1_text}">
          <div class="blog-meta">
            <span class="blog-cat">{category}</span>
            <span class="blog-date">{p.date}</span>
          </div>
          <h3 class="blog-item-title">
            {p.h1_text}
          </h3>
          <p class="blog-item-excerpt">
            {p.excerpt_text}
          </p>
          <span class="blog-cta" aria-hidden="true">Leer Perspectiva <span class="arr">→</span></span>
        </article>'''


def art_frame_html(p):
    panel_header = f'''      <div id="{p.art_id}" class="art-frame" hidden>
        <div class="air-panel-title">
          <h3>{p.h1_html}</h3>
          <p>{p.excerpt_html}</p>
        </div>
        {p.meta_html}
{p.rest_content}
      </div>'''
    return panel_header


# ════════════════════════════════════════════════════════════════
# 5. Bootstrap (first article ever) — builds the hub/panel/nav shell
# ════════════════════════════════════════════════════════════════

SHARED_NAV_CSS = '''
    /* ════════════════════════════════════════════════════════
       ARTICLE NAVIGATION — shared component, reused by every
       article opened from Perspectivas. Applied automatically by
       buildArticleNav() to whichever .art-frame is open — do not
       duplicate this per article.
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
    .art-nav-btn:hover { background: var(--gold); color: var(--ink); transform: translateY(-1px); }
    .art-nav-btn:hover .num { color: var(--ink); }
    .art-nav-btn.active { background: var(--gold); color: var(--ink); box-shadow: 0 4px 14px rgba(0,192,220,0.35); }
    .art-nav-btn.active .num { color: var(--ink); }
    .art-nav-btn:focus-visible { outline: 2px solid var(--gold); outline-offset: 2px; }
    #artProgressTrack { height: 2px; background: var(--border); border-radius: 1px; margin-top: 0.9rem; overflow: hidden; }
    #artProgressFill { height: 100%; width: 0%; background: linear-gradient(90deg, var(--amber), var(--gold)); transition: width 0.1s linear; }
    @media (max-width: 900px) {
      .art-sticky { top: 64px; padding: 0.85rem 0 0.75rem; }
      .art-nav { flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; padding-bottom: 2px; }
      .art-nav::-webkit-scrollbar { display: none; }
      .art-nav-btn { flex-shrink: 0; }
    }
    #artPanel{scroll-margin-top:96px}
'''

SHARED_JS = '''
  <script>
  (function() {
    var elHub   = document.getElementById('perspectivasHub');
    var elPanel = document.getElementById('artPanel');
    var elBack  = document.getElementById('artBack');
    var elNav   = document.getElementById('artNav');
    var elFill  = document.getElementById('artProgressFill');
    var scrollBound = false;
    var currentFrame = null;

    function pad2(n) { return (n < 10 ? '0' : '') + n; }

    /* Shared, reusable: builds the sticky section nav for whichever
       .art-frame is open, from its section[id] + .eyebrow elements.
       Any future article that follows the same convention gets this
       automatically — nothing to wire up per article. */
    function buildArticleNav(frame) {
      var sections = [].slice.call(frame.querySelectorAll('section[id]'));
      var items = sections.map(function(s, i) {
        var num = pad2(i);
        var label = '';
        var eyebrow = s.querySelector('.eyebrow');
        if (eyebrow) {
          var parts = eyebrow.textContent.split('\\u00b7').map(function(p) { return p.trim(); });
          if (parts.length && /^\\d+$/.test(parts[0])) {
            num = parts[0];
            if (parts[1]) label = parts[1];
          } else if (parts[0]) {
            label = parts[0];
          }
        }
        if (!label) {
          var h = s.querySelector('h2, h3');
          label = h ? h.textContent.trim() : s.id;
          if (label.length > 30) label = label.slice(0, 28) + '\\u2026';
        }
        return { id: s.id, num: num, label: label, el: s };
      });

      elNav.innerHTML = items.map(function(it) {
        return '<button type="button" class="art-nav-btn" data-target="' + it.id + '">' +
                 '<span class="num">' + it.num + '</span>' + it.label +
               '</button>';
      }).join('');

      return items;
    }

    function artScrollHandler() {
      if (!currentFrame || elPanel.hidden) return;
      var rect = currentFrame.getBoundingClientRect();
      var articleTop = window.scrollY + rect.top;
      var total = currentFrame.scrollHeight - window.innerHeight;
      var scrolled = window.scrollY - articleTop;
      var pct = total > 0 ? Math.max(0, Math.min(100, (scrolled / total) * 100)) : 0;
      if (elFill) elFill.style.width = pct + '%';

      var btns = [].slice.call(elNav.querySelectorAll('.art-nav-btn'));
      var y = window.scrollY + 200, cur = 0;
      btns.forEach(function(btn, i) {
        var target = document.getElementById(btn.dataset.target);
        if (target) {
          var tTop = window.scrollY + target.getBoundingClientRect().top;
          if (tTop <= y) cur = i;
        }
      });
      btns.forEach(function(btn, i) { btn.classList.toggle('active', i === cur); });
    }

    elNav.addEventListener('click', function(e) {
      var btn = e.target.closest('.art-nav-btn');
      if (!btn) return;
      var target = document.getElementById(btn.dataset.target);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    function nexumOpenArticle(id) {
      var frame = document.getElementById(id);
      if (!frame) return;

      [].slice.call(document.querySelectorAll('#artBody .art-frame')).forEach(function(f) {
        f.hidden = (f !== frame);
      });
      currentFrame = frame;

      buildArticleNav(frame);

      elHub.style.display = 'none';
      elPanel.removeAttribute('hidden');
      elPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });

      if (!scrollBound) {
        window.addEventListener('scroll', artScrollHandler, { passive: true });
        scrollBound = true;
      }
      setTimeout(artScrollHandler, 50);
    }

    function nexumCloseArticle() {
      elPanel.setAttribute('hidden', '');
      elHub.style.display = '';
      var sec = document.getElementById('perspectivas');
      if (sec) sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    elBack.addEventListener('click', nexumCloseArticle);

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && !elPanel.hidden) nexumCloseArticle();
      if ((e.key === 'Enter' || e.key === ' ') && e.target.closest('[onclick*="nexumOpenArticle"]')) {
        e.preventDefault();
        e.target.closest('[onclick*="nexumOpenArticle"]').click();
      }
    });

    window.nexumOpenArticle = nexumOpenArticle;
    window.nexumCloseArticle = nexumCloseArticle;
  })();
  </script>'''


def bootstrap_section5(page, p, category):
    """First article ever added to this site file: build the whole
    hub/panel/nav shell plus the one card + one .art-frame."""

    section5_new = f'''  <section class="section" id="perspectivas" aria-label="Perspectivas">
    <div class="wrap">
      <div class="marker reveal">05 / Perspectivas</div>

      <div class="blog-hdr">
        <h2 class="blog-title reveal">
          Ideas que<br>mueven <i>decisiones.</i>
        </h2>
        <p class="blog-intro reveal d1">
          Reflexiones estratégicas sobre transformación, liderazgo y el valor de la complejidad bien gestionada. Sin tendencias pasajeras — solo perspectiva ejecutiva de largo plazo.
        </p>
      </div>

      <div class="blog-list reveal d1" id="perspectivasHub">

{article_item_html(p, category, p.art_id)}

        <!-- Próximas perspectivas se agregan aquí automáticamente, cada una como .blog-item -->

      </div><!-- /blog-list -->

      <!-- ── ACTIVE ARTICLE PANEL (shared by every article) ── -->
      <div class="air-panel" id="artPanel" hidden>
        <button class="air-back" id="artBack" type="button">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M9 2L4 7L9 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          Volver a Perspectivas
        </button>

        <!-- Shared article-navigation component (auto-built per open article) -->
        <div class="art-sticky" id="artSticky">
          <div class="art-nav-label">Contenido del artículo</div>
          <nav class="art-nav" id="artNav" aria-label="Navegación del artículo"></nav>
          <div id="artProgressTrack"><div id="artProgressFill"></div></div>
        </div>

        <div id="artBody">
{art_frame_html(p)}
        </div><!-- /artBody -->
      </div>

      <div class="blog-foot reveal d2">
        <a href="#" class="btn btn-arrow">Ver todas las perspectivas <span class="arr">→</span></a>
      </div>

    </div>
  </section>'''

    scoped_style_tag = f'''  <style id="art-scoped-css">
  /* ── SCOPED + RETHEMED ARTICLE CSS: {p.art_id} ── */
  {p.scoped_css}
  {MANUAL_OVERRIDES}
  </style>'''

    style_end = page.find('</style>')
    assert style_end != -1
    page = page[:style_end] + SHARED_NAV_CSS + '\n  ' + scoped_style_tag + '\n  ' + page[style_end:]

    sec5_start = page.find('  <section class="section" id="perspectivas"')
    assert sec5_start != -1, "Section perspectivas not found in --html"
    sec5_end = page.find('  <!-- ════', sec5_start + 100)
    if sec5_end == -1:
        sec5_end = page.find('\n\n  <section', sec5_start + 100)
    assert sec5_end != -1, "Could not find end of Section 05"
    page = page[:sec5_start] + section5_new + '\n\n\n' + page[sec5_end:]

    body_close = page.find('</body>')
    assert body_close != -1
    page = page[:body_close] + '\n' + SHARED_JS + '\n\n' + page[body_close:]

    return page


# ════════════════════════════════════════════════════════════════
# 6. Append (shell already exists) — add one card + one .art-frame
#    + one scoped <style>, touching nothing else.
# ════════════════════════════════════════════════════════════════

def append_article(page, p, category):
    assert f'id="{p.art_id}"' not in page, (
        f"An element with id '{p.art_id}' already exists — pick a different "
        f"--id, or this article may already be integrated."
    )

    # 1. New scoped <style>, appended right after the existing one(s)
    style_end = page.find('</style>')
    assert style_end != -1
    new_style_tag = f'''  <style id="art-scoped-css-{p.art_id}">
  /* ── SCOPED + RETHEMED ARTICLE CSS: {p.art_id} ── */
  {p.scoped_css}
  </style>\n  '''
    page = page[:style_end] + new_style_tag + page[style_end:]

    # 2. New item into the shared .blog-list — every article is an equal
    #    .blog-item row; there is no featured slot to protect.
    list_marker = '<!-- Próximas perspectivas se agregan aquí automáticamente, cada una como .blog-item -->'
    lm_idx = page.find(list_marker)
    assert lm_idx != -1, "Could not find the .blog-list insertion marker — is the hub bootstrapped?"
    page = (page[:lm_idx] + article_item_html(p, category, p.art_id) + '\n\n        '
            + page[lm_idx:])

    # 3. New .art-frame appended inside #artBody, just before its closing
    #    comment marker
    body_close_marker = '</div><!-- /artBody -->'
    bc_idx = page.find(body_close_marker)
    assert bc_idx != -1, "Could not find #artBody closing marker — is the shell bootstrapped?"
    page = page[:bc_idx] + art_frame_html(p) + '\n      ' + page[bc_idx:]

    return page


# ════════════════════════════════════════════════════════════════
# 7. Main
# ════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--html', required=True, help='Site file to modify')
    ap.add_argument('--article', required=True, help='Article HTML export to integrate')
    ap.add_argument('--out', default=None, help='Output path (default: overwrite --html)')
    ap.add_argument('--category', default=None, help='Card category label, e.g. "Resiliencia Empresarial"')
    ap.add_argument('--id', dest='art_id', default=None, help='Slug for this article (default: derived from title)')
    args = ap.parse_args()

    with open(args.html, 'r', encoding='utf-8') as f:
        page = f.read()

    body_tags_before = len(re.findall(r'<body[^>]*>', page, re.IGNORECASE))

    is_bootstrap = 'id="artBody"' not in page

    # Need the title before we can default --id, so parse with a temp id first
    temp = parse_article(args.article, 'art-temp')
    art_id = args.art_id or ('art-' + slugify(temp.h1_text or temp.title))
    p = parse_article(args.article, art_id)  # re-parse so p.art_id is final
    category = args.category or 'Perspectiva Ejecutiva'

    print(f"Article   : {p.title}")
    print(f"H1        : {p.h1_text}")
    print(f"Date      : {p.date!r}")
    print(f"Sections  : {p.section_count}")
    print(f"Art id    : {p.art_id}")
    print(f"Category  : {category}")
    print(f"Mode      : {'BOOTSTRAP (first article)' if is_bootstrap else 'APPEND (existing shell found)'}")

    if is_bootstrap:
        assert 'id="perspectivas"' in page, "Section 05 (#perspectivas) not found in --html"
        page = bootstrap_section5(page, p, category)
    else:
        page = append_article(page, p, category)

    # ── Verify ──
    body_tags = len(re.findall(r'<body[^>]*>', page, re.IGNORECASE))
    assert body_tags == body_tags_before, (
        f"<body> tag count changed ({body_tags_before} -> {body_tags}) — this insertion "
        f"must not add or remove a stray <body> tag, whatever the file's starting count is."
    )
    assert page.count('<body') == page.lower().count('<body'), "case mismatch check"
    assert f'id="{p.art_id}"' in page, "new article id missing from output"
    assert 'nexum-art-modal' not in page, "a stale full-screen modal is still present — remove it first"
    ids = re.findall(r'\bid="([^"]+)"', page)
    dupes = {i for i in ids if ids.count(i) > 1}
    assert not dupes, f"Duplicate element ids after insertion: {sorted(dupes)}"

    out_path = args.out or args.html
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(page)

    print(f"\nOK — wrote {out_path} ({len(page.encode('utf-8')):,} bytes)")
    print("Next: verify headlessly (open the card, check the panel, the nav, "
          "and scroll-highlighting), then publish + push. See SKILL.md.")


if __name__ == '__main__':
    main()
