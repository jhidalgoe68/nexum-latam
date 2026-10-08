#!/usr/bin/env python3
"""Instala (una sola vez, idempotente) el selector ES | EN y su CSS/JS en el maestro index.html."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import switch_html, SRC

CSS = r'''<style id="nx-lang-css">
/* ── Selector de idioma ES | EN ── minimalista, mismo lenguaje visual que la navegación */
.lang-switch{display:inline-flex;align-items:center;gap:.55rem;font-family:var(--font-body);font-size:var(--sm);
  letter-spacing:.07em;text-transform:uppercase;line-height:1;white-space:nowrap}
.lang-switch a{position:relative;color:var(--mid);text-decoration:none;padding:.3rem .05rem;font-weight:400;transition:color .3s var(--ease)}
.lang-switch a::after{content:'';position:absolute;left:0;bottom:-1px;width:0;height:1px;background:var(--gold);transition:width .35s var(--ease)}
.lang-switch a:hover{color:var(--ink)}
.lang-switch a:hover::after,.lang-switch a[aria-current="true"]::after{width:100%}
.lang-switch a[aria-current="true"]{color:var(--ink);font-weight:500}
.lang-switch .sep{display:block;width:1px;height:.95em;background:currentColor;opacity:.28}
.lang-switch a:focus-visible{outline:2px solid var(--gold);outline-offset:3px;border-radius:2px}
.lang-switch--desk{margin-left:.35rem;padding-left:clamp(.9rem,1.4vw,1.5rem);border-left:1px solid var(--border)}
.lang-switch--hdr{margin-left:auto;margin-right:1rem;z-index:100}
@media (min-width:1240px){.lang-switch--hdr{display:none}}
/* sobre el menú móvil abierto (fondo oscuro) */
body:has(#mobileNav.open) .lang-switch--hdr a{color:rgba(255,255,255,.75)}
body:has(#mobileNav.open) .lang-switch--hdr a:hover,body:has(#mobileNav.open) .lang-switch--hdr a[aria-current="true"]{color:var(--cream)}
/* aviso de artículo solo en español (página EN) */
.art-lang-note{margin:0 0 1.25rem;padding:.6rem .9rem;border-left:2px solid var(--gold);background:var(--gold-dim);
  font-family:var(--font-body);font-size:var(--sm);color:var(--mid);line-height:1.5}
</style>
<script id="nx-lang-js">
(function(){
  /* Guarda la preferencia (localStorage + cookie para la redirección de "/") y conserva el #ancla al cambiar de idioma. */
  function pref(l){
    try{localStorage.setItem('nx_lang',l)}catch(e){}
    try{document.cookie='nx_lang='+l+';path=/;max-age=31536000;SameSite=Lax'}catch(e){}
  }
  document.addEventListener('click',function(e){
    var a=e.target.closest&&e.target.closest('.lang-switch a[data-lang]'); if(!a)return;
    var l=a.getAttribute('data-lang'); pref(l);
    if(window.NX_LANG===l){e.preventDefault();return}
    var sfx=/(^|\.)nexum-latam\.com$/.test(location.hostname)?'':'index.html';
    a.setAttribute('href',a.getAttribute('href').split('#')[0].replace(/index\.html$/,'')+sfx+(location.hash||''));
  });
})();
</script>
'''

s = open(SRC, encoding='utf-8').read()
if 'id="nx-lang-css"' in s:
    print('ya instalado'); sys.exit(0)
nav_cta = '<a href="#contacto" class="nav-cta">Conversemos</a>\n'
assert s.count(nav_cta) == 1
s = s.replace(nav_cta, nav_cta + '      ' + switch_html('desk', 'es', '') + '\n', 1)
burger = '    <button class="burger" id="burgerBtn"'
assert s.count(burger) == 1
s = s.replace(burger, '    ' + switch_html('hdr', 'es', '') + '\n\n' + burger, 1)
assert s.rstrip().endswith('</body></html>')
k = s.rstrip().rfind('</body></html>')
s = s[:k] + '\n' + CSS + s[k:]
open(SRC, 'w', encoding='utf-8').write(s)
print('instalado')
