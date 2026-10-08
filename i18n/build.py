#!/usr/bin/env python3
"""
NEXUM LATAM — build de las versiones /es/ y /en/ a partir del maestro index.html

  index.html (maestro, en español)  +  i18n/en.json (diccionario ES → EN)
        └──► es/index.html   en/index.html   sitemap.xml   robots.txt

El maestro sigue siendo el único archivo que se edita (las demás skills del
proyecto siguen funcionando sobre él). Este script:
  1. normaliza el documento (el export tiene un envoltorio doble) en una sola
     página limpia con <head> y <body> reales;
  2. para EN, traduce textos visibles, atributos (placeholder, aria-label, alt…),
     cadenas de JavaScript (assessments, mensajes del formulario) y el JSON de
     sectores, siempre por coincidencia EXACTA con el diccionario;
  3. añade <html lang>, canonical, hreflang, Open Graph, Twitter y JSON-LD por idioma;
  4. ajusta rutas relativas (media/ → ../media/) y el selector ES | EN;
  5. genera sitemap.xml multilingüe y robots.txt.

Los artículos de Perspectivas (zona #artBody) NO se traducen en esta entrega:
quedan en español dentro de la página EN, con aviso y lang="es".

Uso:
  python3 i18n/build.py extract     # lista lo que falta en el diccionario
  python3 i18n/build.py build       # construye (falla si falta algo)
  python3 i18n/build.py build --allow-missing
  python3 i18n/build.py check       # build + validación (JS, ids, rutas)
Para marcar un texto como "se queda igual" basta una entrada con el mismo valor.
"""
import argparse, html, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'index.html')
DICT = os.path.join(ROOT, 'i18n', 'en.json')
DOMAIN = 'https://nexum-latam.com'
LANGS = ('es', 'en')

INLINE = {'strong', 'em', 'b', 'i', 'br', 'sup', 'sub', 'u', 'small'}     # <span> es frontera a propósito
ATTRS = ('placeholder', 'aria-label', 'title', 'alt', 'data-label', 'data-cur-label',
         'data-tgt-label', 'data-gap-label', 'aria-description')
TOK = re.compile(r'<!--.*?-->|<script\b[^>]*>.*?</script\s*>|<style\b[^>]*>.*?</style\s*>|<[^>]+>|[^<]+', re.S | re.I)
LETTERS = re.compile(r'[^\W\d_]{2}')
SP_ACC = re.compile(r'[áéíóúñÁÉÍÓÚÑ¿¡]')
SP_STOP = re.compile(r'\b(el|la|los|las|de|del|para|que|su|sus|con|una|por|al|más|nuestr\w+|usted|cuenta|existe|tiene)\b', re.I)

# ───────────────────────────── utilidades ─────────────────────────────

def norm(s):
    return ' '.join(s.split())

KEEP = set()      # textos revisados que se quedan igual (entrada "__keep__" del diccionario)

def load_dict():
    with open(DICT, encoding='utf-8') as f:
        data = json.load(f)
    KEEP.clear(); KEEP.update(data.pop('__keep__', []))
    return data

def split_source(raw):
    """Devuelve (skeleton, custom_head, nested_head_inner, body_inner)."""
    i = raw.find('<!DOCTYPE html>')
    if i < 0:
        sys.exit('ERROR: no se encontró el documento anidado (<!DOCTYPE html>) en index.html')
    wrapper, nested = raw[:i], raw[i:]
    m = re.search(r'<style>:root\{color-scheme:light\}.*?</style>', wrapper, re.S)
    skeleton = m.group(0) if m else ''
    a = wrapper.find('<style id="art-scoped-css">')
    b = wrapper.rfind('</head><body>')
    if a < 0 or b < 0 or b < a:
        sys.exit('ERROR: estructura del envoltorio inesperada (art-scoped-css / </head><body>)')
    custom = wrapper[a:b]
    h0 = nested.find('<head>') + len('<head>')
    h1 = nested.find('</head>')
    b0 = nested.find('<body>') + len('<body>')
    b1 = nested.rfind('</body>')
    if min(h0, h1, b0, b1) < 0 or not (h0 <= h1 < b0 <= b1):
        sys.exit('ERROR: head/body del documento anidado no encontrados')
    return skeleton, custom, nested[h0:h1], nested[b0:b1]

# ───────────────────────────── JavaScript ─────────────────────────────

def js_decode(s):
    def rep(m):
        t = m.group(1)
        if t[0] == 'u': return chr(int(t[1:], 16))
        if t[0] == 'x': return chr(int(t[1:], 16))
        return {'n': '\n', 't': '\t', 'r': '\r', 'b': '\b', 'f': '\f', 'v': '\v', '0': '\0'}.get(t, t)
    return re.sub(r'\\(u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|.)', rep, s, flags=re.S)

def js_encode(s, q):
    s = s.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    if q == '`':
        return s.replace('`', '\\`').replace('${', '\\${')
    return s.replace(q, '\\' + q)

def js_pieces(s):
    """Posiciones (ini, fin, comilla) del cuerpo de cada cadena; plantillas ⇒ trozos estáticos."""
    out = []
    n = len(s)

    def lex(i, in_expr):
        depth = 0
        prev = '\n'
        while i < n:
            c = s[i]
            if c == '/' and i + 1 < n and s[i + 1] == '/':
                j = s.find('\n', i); i = n if j < 0 else j; continue
            if c == '/' and i + 1 < n and s[i + 1] == '*':
                j = s.find('*/', i + 2); i = n if j < 0 else j + 2; continue
            if c in '\'"':
                j = i + 1
                while j < n and s[j] != c:
                    j += 2 if s[j] == '\\' else 1
                out.append((i + 1, j, c)); i = j + 1; prev = c; continue
            if c == '`':
                i = tpl(i + 1); prev = '`'; continue
            if c == '/' and prev in '(,=:[!&|?{};\n+-*%<>~^':      # literal de regex
                j = i + 1; cls = False
                while j < n and (s[j] != '/' or cls):
                    if s[j] == '\\': j += 1
                    elif s[j] == '[': cls = True
                    elif s[j] == ']': cls = False
                    j += 1
                i = j + 1; prev = '/'; continue
            if in_expr:
                if c == '{': depth += 1
                elif c == '}':
                    if depth == 0: return i
                    depth -= 1
            if not c.isspace(): prev = c
            i += 1
        return i

    def tpl(i):
        start = i
        while i < n:
            c = s[i]
            if c == '\\': i += 2; continue
            if c == '`':
                out.append((start, i, '`')); return i + 1
            if c == '$' and i + 1 < n and s[i + 1] == '{':
                out.append((start, i, '`'))
                i = lex(i + 2, True) + 1
                start = i
                continue
            i += 1
        return i

    lex(0, False)
    return out

def candidate(d):
    """¿Esta cadena de JS puede ser texto visible? (amplio a propósito: lo que sobre va a "__keep__")"""
    t = re.sub(r'<[^>]+>', ' ', d).strip()
    if d.startswith(('data:', 'http', '/', '.', '#', '$')): return False
    if not re.search(r'[A-Za-zÁ-ú]{2}', t): return False
    if ' ' in t or SP_ACC.search(t): return True
    if re.fullmatch(r'[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+', t.rstrip('….:')): return True
    return d != d.strip() and t.isalpha()

def looks_spanish(d):
    d2 = d.strip()
    if len(d2) < 4 or ' ' not in d2 or d2.startswith(('data:', 'http', '/', '.', '#')): return False
    if not re.search(r'[A-Za-zÁ-ú]{3}', d2): return False
    return bool(SP_ACC.search(d2) or SP_STOP.search(d2))

def tr_js(src, D, miss, tag):
    reps = []
    for a, b, q in js_pieces(src):
        dec = js_decode(src[a:b])
        if dec in D:
            if D[dec] != dec: reps.append((a, b, js_encode(D[dec], q)))
        elif dec.strip() in D and D[dec.strip()] != dec.strip():
            lead = dec[:len(dec) - len(dec.lstrip())]; trail = dec[len(dec.rstrip()):]
            reps.append((a, b, js_encode(lead + D[dec.strip()] + trail, q)))
        elif dec not in KEEP and dec.strip() not in KEEP and candidate(dec):
            miss.setdefault(dec, 'js:' + tag)
    for a, b, t in sorted(reps, reverse=True):
        src = src[:a] + t + src[b:]
    return src

def tr_json(txt, D, miss, tag):
    try:
        data = json.loads(txt)
    except Exception:
        miss.setdefault('<JSON no válido en ' + tag + '>', 'json'); return txt
    def walk(v):
        if isinstance(v, str):
            if v in D: return D[v]
            if v not in KEEP and LETTERS.search(v) and not v.startswith(('http', '/')): miss.setdefault(v, 'json:' + tag)
            return v
        if isinstance(v, list): return [walk(x) for x in v]
        if isinstance(v, dict): return {k: walk(x) for k, x in v.items()}
        return v
    out = json.dumps(walk(data), ensure_ascii=False, separators=(',', ':'))
    return out.replace('</', '<\\/')

# ───────────────────────────── HTML ─────────────────────────────

ATTR_RE = re.compile(r'(\s)([a-zA-Z:-]+)=("([^"]*)"|\'([^\']*)\')')

def tr_tag(tok, D, miss):
    m = re.match(r'<\s*([a-zA-Z0-9-]+)', tok)
    name = m.group(1).lower() if m else ''
    def rep(a):
        attr = a.group(2).lower()
        val = a.group(4) if a.group(4) is not None else a.group(5)
        ok = attr in ATTRS
        if name == 'meta' and attr == 'content':
            ok = bool(re.search(r'(name|property)=["\'](description|og:[a-z:]+|twitter:[a-z:]+)["\']', tok))
        if not ok: return a.group(0)
        key = norm(val)
        if not LETTERS.search(key) or re.match(r'^(https?:|mailto:|tel:|#|/)', key): return a.group(0)
        if key in D:
            q = '"' if a.group(4) is not None else "'"
            return a.group(1) + a.group(2) + '=' + q + D[key] + q
        if key not in KEEP: miss.setdefault(key, 'attr:' + attr)
        return a.group(0)
    return ATTR_RE.sub(rep, tok)

def flush_run(run, D, miss, out):
    """run: lista de (tipo, raw). Traduce por coincidencia exacta del HTML en línea normalizado."""
    raw = ''.join(r for _, r in run)
    plain = re.sub(r'<[^>]+>', '', raw)
    if not LETTERS.search(plain):
        out.append(raw); return
    core = raw.strip()
    lead = raw[:len(raw) - len(raw.lstrip())]; trail = raw[len(raw.rstrip()):]
    key = norm(core)
    if key in D:
        out.append(lead + D[key] + trail); return
    if any(t == 'tag' for t, _ in run):
        pieces = []; ok = True
        for t, r in run:
            if t == 'text' and LETTERS.search(r):
                k = norm(r)
                if k in D:
                    l = r[:len(r) - len(r.lstrip())]; tl = r[len(r.rstrip()):]
                    pieces.append(l + D[k] + tl)
                else:
                    ok = False; pieces.append(r)
            else:
                pieces.append(r)
        if ok:
            out.append(''.join(pieces)); return
    if key not in KEEP: miss.setdefault(key, 'html')
    out.append(raw)

def tr_html(src, D, miss, translate=True):
    """Traduce un fragmento HTML. Devuelve el nuevo texto. Salta la zona de artículos."""
    out, run = [], []
    skipping = False
    for m in TOK.finditer(src):
        tok = m.group(0)
        low = tok[:12].lower()
        if skipping:
            out.append(tok)
            if tok.startswith('<!--') and '/artBody' in tok: skipping = False
            continue
        if tok.startswith('<!--'):
            flush_run(run, D, miss, out); run = []
            out.append(tok); continue
        if low.startswith('<script'):
            flush_run(run, D, miss, out); run = []
            mm = re.match(r'(<script\b[^>]*>)(.*?)(</script\s*>)', tok, re.S | re.I)
            op, body, cl = mm.group(1), mm.group(2), mm.group(3)
            if 'src=' in op or not body.strip():
                out.append(tok)
            elif 'application/json' in op:
                idm = re.search(r'id="([^"]+)"', op)
                out.append(op + tr_json(body, D, miss, idm.group(1) if idm else 'json') + cl)
            elif 'ld+json' in op:
                out.append(tok)
            else:
                idm = re.search(r'id="([^"]+)"', op)
                out.append(op + tr_js(body, D, miss, idm.group(1) if idm else 'inline') + cl)
            continue
        if low.startswith('<style'):
            flush_run(run, D, miss, out); run = []
            out.append(tok); continue
        if tok.startswith('<'):
            nm = re.match(r'</?\s*([a-zA-Z0-9-]+)', tok)
            name = nm.group(1).lower() if nm else ''
            if name in INLINE:
                run.append(('tag', tr_tag(tok, D, miss))); continue
            flush_run(run, D, miss, out); run = []
            out.append(tr_tag(tok, D, miss))
            if re.match(r'<div\b[^>]*id="artBody"', tok): skipping = True
            continue
        run.append(('text', tok))
    flush_run(run, D, miss, out)
    return ''.join(out)

# ───────────────────────────── selector de idioma ─────────────────────────────

SW_RE = re.compile(r'<!--nx-lang-switch:(\w+)-->.*?<!--/nx-lang-switch-->', re.S)

def switch_html(variant, active, prefix):
    cls = 'lang-switch lang-switch--' + variant
    def a(code, label, name):
        cur = ' aria-current="true"' if code == active else ''
        return ('<a href="%s%s/" lang="%s" hreflang="%s" data-lang="%s" title="%s"%s>%s</a>'
                % (prefix, code, code, code, code, name, cur, label))
    return ('<!--nx-lang-switch:%s--><div class="%s" role="group" aria-label="Idioma">%s<span class="sep" aria-hidden="true"></span>%s</div><!--/nx-lang-switch-->'
            % (variant, cls, a('es', 'ES', 'Español'), a('en', 'EN', 'English')))

# ───────────────────────────── SEO ─────────────────────────────

LD = {
    'es': {'inLanguage': 'es', 'description': None, 'slogan': 'Transformando la complejidad en valor'},
    'en': {'inLanguage': 'en', 'description': None, 'slogan': 'Turning complexity into value'},
}

def seo_block(lang, title, desc):
    url = '%s/%s/' % (DOMAIN, lang)
    loc, alt = ('es_LA', 'en_US') if lang == 'es' else ('en_US', 'es_LA')
    esc = lambda s: html.escape(s, quote=True)
    ld = {
        '@context': 'https://schema.org', '@type': 'ProfessionalService',
        'name': 'NEXUM LATAM Advisory', 'url': url, 'inLanguage': lang,
        'description': desc, 'slogan': LD[lang]['slogan'],
        'email': 'contact@nexum-latam.com', 'telephone': '+506 7010-4381',
        'areaServed': 'Latin America',
        'founder': {'@type': 'Person', 'name': 'Javier Hidalgo Estévez'},
        'availableLanguage': ['es', 'en'],
        'address': {'@type': 'PostalAddress', 'addressLocality': 'San José', 'addressCountry': 'CR'},
    }
    ldj = json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')
    return '\n'.join([
        '<link rel="canonical" href="%s">' % url,
        '<link rel="alternate" hreflang="es" href="%s/es/">' % DOMAIN,
        '<link rel="alternate" hreflang="en" href="%s/en/">' % DOMAIN,
        '<link rel="alternate" hreflang="x-default" href="%s/">' % DOMAIN,
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="NEXUM LATAM Advisory">',
        '<meta property="og:title" content="%s">' % esc(title),
        '<meta property="og:description" content="%s">' % esc(desc),
        '<meta property="og:url" content="%s">' % url,
        '<meta property="og:locale" content="%s">' % loc,
        '<meta property="og:locale:alternate" content="%s">' % alt,
        '<meta name="twitter:card" content="summary">',
        '<meta name="twitter:title" content="%s">' % esc(title),
        '<meta name="twitter:description" content="%s">' % esc(desc),
        '<script type="application/ld+json">%s</script>' % ldj,
    ])

LANG_BOOT = ('<script>window.NX_LANG="%s";(function(){var P="%s";'
             'if(/bot|crawl|spider|slurp|bing|facebookexternalhit|lighthouse/i.test(navigator.userAgent))return;'
             'var p=null;try{p=localStorage.getItem("nx_lang")}catch(e){}'
             'if(p!=="es"&&p!=="en")p=null;'
             'if(!p){var n=(navigator.languages&&navigator.languages[0])||navigator.language||"";'
             'p=/^en/i.test(n)?"en":/^es/i.test(n)?"es":null}'
             'var S=/(^|\\.)nexum-latam\\.com$/.test(location.hostname)?"":"index.html";'
             'if(p&&p!==P){location.replace(location.pathname.replace(/\\/(es|en)(\\/(index\\.html)?)?$/,"/"+p+"/"+S)+location.search+location.hash)}'
             '})()</script>')

ART_NOTE = {
    'en': ('<p class="art-lang-note" lang="en" role="note">This article is currently available in Spanish only. '
           'An English edition is in preparation.</p>'),
}

# ───────────────────────────── ensamblado ─────────────────────────────

def build_page(raw, lang, D, miss):
    skeleton, custom, head, body = split_source(raw)
    if lang == 'en':
        head = tr_html(head, D, miss)
        body = tr_html(body, D, miss)
        body = body.replace('<div id="artBody">', ART_NOTE['en'] + '<div id="artBody" lang="es">', 1)
    # selector de idioma: activo + rutas relativas a /es/ y /en/
    body = SW_RE.sub(lambda m: switch_html(m.group(1), lang, '../'), body)
    # media/ relativo → ../media/
    body = re.sub(r'(["\'])media/', r'\1../media/', body)
    head = re.sub(r'(["\'])media/', r'\1../media/', head)
    tm = re.search(r'<title>(.*?)</title>', head, re.S)
    dm = re.search(r'<meta name="description" content="([^"]*)"', head)
    title = html.unescape(tm.group(1).strip()) if tm else 'NEXUM'
    desc = html.unescape(dm.group(1)) if dm else ''
    head = re.sub(r'<html[^>]*>', '', head)
    cm = re.search(r'<meta charset="[^"]*">', head)
    charset = cm.group(0) if cm else '<meta charset="UTF-8">'
    head = head.replace(charset, '', 1)
    return ('<!DOCTYPE html>\n<html lang="%s">\n<head>\n%s\n%s\n%s\n%s\n%s\n%s\n</head>\n<body>%s</body>\n</html>\n'
            % (lang, charset, LANG_BOOT % (lang, lang), skeleton, custom, head, seo_block(lang, title, desc), body))

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

def sitemap():
    today = __import__('datetime').date.today().isoformat()
    rows = []
    for l in LANGS:
        rows.append('  <url>\n    <loc>%s/%s/</loc>\n    <lastmod>%s</lastmod>\n'
                    '    <xhtml:link rel="alternate" hreflang="es" href="%s/es/"/>\n'
                    '    <xhtml:link rel="alternate" hreflang="en" href="%s/en/"/>\n'
                    '    <xhtml:link rel="alternate" hreflang="x-default" href="%s/"/>\n  </url>'
                    % (DOMAIN, l, today, DOMAIN, DOMAIN, DOMAIN))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n%s\n</urlset>\n'
            % '\n'.join(rows))

def run_check(outputs):
    bad = 0
    for lang, text in outputs.items():
        # 1) JS válido en cada script inline
        n = 0
        for m in re.finditer(r'<script(?![^>]*\bsrc=)(?![^>]*type="(?:application/json|application/ld\+json)")[^>]*>(.*?)</script>', text, re.S):
            body = m.group(1)
            if not body.strip(): continue
            n += 1
            with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
                f.write(body); p = f.name
            r = subprocess.run(['node', '--check', p], capture_output=True, text=True)
            os.unlink(p)
            if r.returncode:
                bad += 1; print('[%s] JS inválido:' % lang, r.stderr.strip().splitlines()[:3])
        # 2) JSON válido
        for m in re.finditer(r'<script[^>]*type="application/(?:json|ld\+json)"[^>]*>(.*?)</script>', text, re.S):
            try: json.loads(m.group(1))
            except Exception as e: bad += 1; print('[%s] JSON inválido: %s' % (lang, e))
        # 3) ids únicos (sin contar dentro de scripts)
        nos = re.sub(r'<script\b.*?</script>|<style\b.*?</style>', '', text, flags=re.S)
        ids = re.findall(r'\sid="([^"]+)"', nos)
        dup = sorted({i for i in ids if ids.count(i) > 1})
        if dup: bad += 1; print('[%s] ids duplicados:' % lang, dup[:10])
        # 4) rutas media/
        if re.search(r'["\']media/', text): bad += 1; print('[%s] queda una ruta media/ sin reescribir' % lang)
        print('[%s] scripts inline revisados: %d · ids: %d' % (lang, n, len(ids)))
    return bad

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['extract', 'build', 'check'])
    ap.add_argument('--allow-missing', action='store_true')
    a = ap.parse_args()
    raw = open(SRC, encoding='utf-8').read()
    D = load_dict() if os.path.exists(DICT) else {}
    miss = {}
    outputs = {l: build_page(raw, l, D, miss if l == 'en' else {}) for l in LANGS}
    if a.cmd == 'extract':
        print(json.dumps(miss, ensure_ascii=False, indent=1))
        print('\n%d cadenas sin entrada en el diccionario' % len(miss), file=sys.stderr)
        return
    if miss and not a.allow_missing:
        print('FALTAN %d traducciones (ejecute: extract):' % len(miss), file=sys.stderr)
        for k, v in list(miss.items())[:15]: print('  [%s] %s' % (v, k[:100]), file=sys.stderr)
        sys.exit(1)
    for l, t in outputs.items():
        write(os.path.join(ROOT, l, 'index.html'), t)
    write(os.path.join(ROOT, 'sitemap.xml'), sitemap())
    write(os.path.join(ROOT, 'robots.txt'), 'User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % DOMAIN)
    print('OK  es/index.html (%d KB)  en/index.html (%d KB)  sitemap.xml  robots.txt'
          % (len(outputs['es']) // 1024, len(outputs['en']) // 1024))
    if a.cmd == 'check':
        sys.exit(1 if run_check(outputs) else 0)

if __name__ == '__main__':
    main()
