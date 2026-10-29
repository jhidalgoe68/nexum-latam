# -*- coding: utf-8 -*-
"""Shared chrome for the NexumTurismo multi-page site: head, header (with
dropdown menus), page hero, closing CTA band and footer. Every visible string
is written once in Spanish and once in English; the English copy rides along
in a data-en attribute and assets/nt.js swaps it in when the visitor picks EN.
"""
from html import escape


def A(s):
    return escape(s, quote=True)


def E(tag, es, en, cls="", attrs=""):
    c = f' class="{cls}"' if cls else ""
    a = f" {attrs}" if attrs else ""
    return f'<{tag}{c}{a} data-en="{A(en)}">{es}</{tag}>'


def P(es, en, cls=""):
    return E("p", es, en, cls)


def H(n, es, en, cls="", attrs=""):
    return E(f"h{n}", es, en, cls, attrs)


def S(es, en, cls=""):
    return E("span", es, en, cls)


def ph(text):
    return f'<span class="ph">{text}</span>'


def link(href, es, en, cls="", attrs=""):
    return E("a", es, en, cls, f'href="{href}"' + (f" {attrs}" if attrs else ""))


CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'
CARET = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>'


def logo(fill_mid="var(--mist)"):
    return ('<svg viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="19" fill="var(--selva)"/>'
            f'<path d="M6 28 L15 15 L20 21 L25 12 L34 28 Z" fill="{fill_mid}"/><circle cx="28" cy="11" r="3" fill="var(--sol)"/></svg>')


# ---------------------------------------------------------------- site tree
# (key, path from site root, es label, en label)
TREE = [
    ("home", "index.html", "Inicio", "Home", None),
    ("tours", None, "Tours", "Tours", [
        ("tours-dia", "tours/un-dia.html", "Tours de un día", "One-day tours"),
        ("tours-multi", "tours/multidia.html", "Programas multidía", "Multi-day programs"),
    ]),
    ("servicios", None, "Servicios", "Services", [
        ("cruceros", "servicios/cruceros.html", "Operación de cruceros", "Cruise operations"),
        ("fit", "servicios/viajes-a-medida.html", "Viajes a medida (FIT)", "Tailor-made trips (FIT)"),
        ("grupos", "servicios/grupos.html", "Grupos de ocio", "Leisure groups"),
        ("incentivos", "servicios/incentivos.html", "Viajes de incentivo", "Incentive trips"),
        ("corporativo", "servicios/corporativos.html", "Servicios corporativos", "Corporate services"),
    ]),
    ("nosotros", None, "Nosotros", "About us", [
        ("quienes", "nosotros/quienes-somos.html", "Quiénes somos", "Who we are"),
        ("perfil", "nosotros/perfil.html", "Perfil de la empresa", "Company profile"),
        ("agencias", "agencias.html", "Agencias y travel advisors", "Agencies & travel advisors"),
        ("coleccion", "coleccion.html", "Colección de lujo", "Luxury collection"),
    ]),
    ("sostenibilidad", "sostenibilidad.html", "Sostenibilidad", "Sustainability", None),
    ("blog", "blog/index.html", "Blog", "Blog", None),
    ("contacto", "contacto.html", "Contacto", "Contact", None),
]

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zilla+Slab:wght@500;600;700&family=Instrument+Sans:wght@400;500;600;700&display=swap">')


def head(p, title_es, title_en, desc, extra_css=""):
    style = f"\n<style>\n{extra_css}\n</style>" if extra_css else ""
    return f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title data-en="{A(title_en)}">{title_es}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="{A(desc)}">
<meta name="robots" content="noindex">
{FONTS}
<link rel="stylesheet" href="{p}assets/nt.css">{style}
</head>
<body>'''


def header(p, active, cta_href=None):
    cta_href = cta_href or f"{p}contacto.html#planificar"
    nav, mnav = [], []
    for key, path, es, en, kids in TREE:
        if key == "home":
            continue
        if kids:
            on = any(k[0] == active for k in kids)
            items = "".join(
                f'<li><a href="{p}{kp}"{" aria-current=\"page\"" if kk == active else ""} data-en="{A(ken)}">{kes}</a></li>'
                for kk, kp, kes, ken in kids)
            nav.append(
                f'<div class="dd{" is-on" if on else ""}"><button type="button" class="dd-btn" aria-expanded="false" aria-controls="dd-{key}">'
                f'<span data-en="{A(en)}">{es}</span>{CARET}</button><ul class="dd-menu" id="dd-{key}">{items}</ul></div>')
            mitems = "".join(f'<li><a href="{p}{kp}" data-en="{A(ken)}">{kes}</a></li>' for kk, kp, kes, ken in kids)
            mnav.append(f'<li class="mgroup"><span class="mlabel" data-en="{A(en)}">{es}</span><ul>{mitems}</ul></li>')
        else:
            cur = ' aria-current="page"' if key == active else ""
            nav.append(f'<a class="nav-a" href="{p}{path}"{cur} data-en="{A(en)}">{es}</a>')
            mnav.append(f'<li><a href="{p}{path}" data-en="{A(en)}">{es}</a></li>')
    return f'''<a class="skip" href="#main" data-en="Skip to content">Saltar al contenido</a>
<div class="util" role="region" aria-label="Avisos">
  <div class="wrap">
    <span data-en="Destination Management Company · Costa Rica">Destination Management Company · Costa Rica</span>
    <span><a href="/" data-en="A NEXUM LATAM initiative">Una iniciativa de NEXUM LATAM</a></span>
  </div>
</div>
<header class="hdr">
  <div class="wrap">
    <a class="brand" href="{p}index.html" aria-label="NexumTurismo">
      {logo()}
      <span>NexumTurismo<small data-en="Costa Rica, made to measure">Costa Rica, a su medida</small></span>
    </a>
    <nav class="nav" aria-label="Navegación principal">
      {''.join(nav)}
    </nav>
    <div class="lang" role="group" aria-label="Idioma / Language">
      <button type="button" data-lang="es" aria-pressed="true">ES</button>
      <button type="button" data-lang="en" aria-pressed="false">EN</button>
    </div>
    <a class="btn btn--primary hdr-cta" href="{cta_href}" data-en="Plan my trip">Planificar mi viaje</a>
    <button class="burger" type="button" aria-expanded="false" aria-controls="mnav" aria-label="Menú"><span></span></button>
  </div>
  <nav class="mnav" id="mnav" aria-label="Menú móvil">
    <ul class="wrap">
      <li><a href="{p}index.html" data-en="Home">Inicio</a></li>
      {''.join(mnav)}
      <li><a class="mcta" href="{cta_href}" data-en="Plan my trip">Planificar mi viaje</a></li>
    </ul>
  </nav>
</header>'''


def crumbs(p, trail):
    """trail: list of (es, en, href or None)."""
    parts = [f'<a href="{p}index.html" data-en="Home">Inicio</a>']
    for es, en, href in trail:
        if href:
            parts.append(f'<a href="{href}" data-en="{A(en)}">{es}</a>')
        else:
            parts.append(f'<span aria-current="page" data-en="{A(en)}">{es}</span>')
    return '<nav class="crumbs" aria-label="Ruta"><ol>' + "".join(f"<li>{x}</li>" for x in parts) + "</ol></nav>"


def page_hero(p, trail, h1_es, h1_en, lede_es, lede_en, ctas="", aside=""):
    grid = " phero--split" if aside else ""
    return f'''<section class="phero{grid}" aria-labelledby="ph-h">
  <div class="wrap">
    <div class="phero-main">
      {crumbs(p, trail)}
      <h1 id="ph-h" data-en="{A(h1_en)}">{h1_es}</h1>
      <p class="lede" data-en="{A(lede_en)}">{lede_es}</p>
      {f'<div class="hero-cta">{ctas}</div>' if ctas else ''}
    </div>
    {aside}
  </div>
</section>'''


def sec_head(hid, h_es, h_en, sub_es="", sub_en=""):
    sub = f'<p class="sub" data-en="{A(sub_en)}">{sub_es}</p>' if sub_es else ""
    return f'<div class="shead"><h2 id="{hid}" data-en="{A(h_en)}">{h_es}</h2>{sub}</div>'


def checks(items):
    """items: list of (b_es, b_en, s_es, s_en)"""
    lis = "".join(
        f'<li>{CHECK}<div><b data-en="{A(ben)}">{bes}</b><span data-en="{A(sen)}">{ses}</span></div></li>'
        for bes, ben, ses, sen in items)
    return f'<ul class="checks">{lis}</ul>'


def team(p, roles):
    """roles: list of (role_es, role_en, focus_es, focus_en)"""
    cards = "".join(
        f'''<article class="member"><div class="avatar" aria-hidden="true">{logo("var(--card)")}</div>
<div><b>{ph("[Nombre y apellido]")}</b><span class="role" data-en="{A(ren)}">{res}</span><p data-en="{A(fen)}">{fes}</p></div></article>'''
        for res, ren, fes, fen in roles)
    return f'''<section class="sec" aria-labelledby="tm-h"><div class="wrap">
{sec_head("tm-h", "Su equipo para este servicio", "Your team for this service",
          "Personas con nombre y teléfono, no un buzón genérico. Complete los perfiles reales antes de publicar.",
          "People with a name and a phone number, not a generic inbox. Fill in the real profiles before publishing.")}
<div class="team">{cards}</div></div></section>'''


def cta_band(p, h_es="Cuéntenos su viaje y le enviamos una propuesta",
             h_en="Tell us about your trip and we'll send a proposal",
             s_es="Sin costo y sin compromiso. Un especialista le responde con un itinerario inicial en menos de un día hábil.",
             s_en="Free and with no commitment. A specialist replies with an initial itinerary within one business day.",
             btn_es="Planificar mi viaje", btn_en="Plan my trip", href=None,
             sec_es="Ver servicios", sec_en="See services", sec_href=None):
    href = href or f"{p}contacto.html#planificar"
    sec_href = sec_href or f"{p}index.html#servicios"
    return f'''<section class="sec band ctaband" aria-labelledby="cb-h"><div class="wrap">
<div><h2 id="cb-h" data-en="{A(h_en)}">{h_es}</h2><p class="sub" data-en="{A(s_en)}">{s_es}</p></div>
<div class="hero-cta"><a class="btn btn--primary" href="{href}" data-en="{A(btn_en)}">{btn_es}</a>
<a class="btn btn--ghost" href="{sec_href}" data-en="{A(sec_en)}">{sec_es}</a></div>
</div></section>'''


def footer(p):
    def col(title_es, title_en, keys):
        flat = {}
        for key, path, es, en, kids in TREE:
            if kids:
                for kk, kp, kes, ken in kids:
                    flat[kk] = (kp, kes, ken)
            else:
                flat[key] = (path, es, en)
        lis = "".join(f'<li><a href="{p}{flat[k][0]}" data-en="{A(flat[k][2])}">{flat[k][1]}</a></li>' for k in keys)
        return f'<div><h3 data-en="{A(title_en)}">{title_es}</h3><ul>{lis}</ul></div>'
    return f'''<footer class="foot">
  <div class="wrap">
    <div class="fgrid">
      <div>
        <a class="brand" href="{p}index.html">{logo("var(--band)")}<span>NexumTurismo<small data-en="Costa Rica, made to measure">Costa Rica, a su medida</small></span></a>
        <p class="fblurb" data-en="Trip design and operations in Costa Rica for travelers, agencies, companies and cruise lines.">Diseño y operación de viajes en Costa Rica para viajeros, agencias, empresas y líneas de crucero.</p>
        <dl class="foffices">
          <div><dt data-en="San José office">Oficina San José</dt><dd>{ph("[Dirección]")}</dd></div>
          <div><dt data-en="Guanacaste office">Oficina Guanacaste</dt><dd>{ph("[Dirección, Liberia]")}</dd></div>
        </dl>
      </div>
      {col("Tours y servicios", "Tours & services", ["tours-dia", "tours-multi", "cruceros", "fit", "grupos", "incentivos", "corporativo"])}
      {col("Empresa", "Company", ["quienes", "perfil", "agencias", "coleccion", "sostenibilidad", "blog"])}
      <div><h3 data-en="Contact">Contacto</h3><ul>
        <li>{ph("[+506 0000-0000]")}</li>
        <li>{ph("[reservas@nexumturismo.com]")}</li>
        <li><a href="{p}contacto.html" data-en="Contact page">Página de contacto</a></li>
        <li><a href="/" data-en="NEXUM LATAM">NEXUM LATAM</a></li>
      </ul></div>
    </div>
    <div class="legal"><span>© <span id="yr">2026</span> NexumTurismo. <span data-en="All rights reserved.">Todos los derechos reservados.</span></span><span data-en="Privacy policy · Terms of service">Política de privacidad · Términos de servicio</span></div>
  </div>
</footer>'''


def tail(p, extra_js=""):
    js = f"\n<script>\n{extra_js}\n</script>" if extra_js else ""
    return f'''<script src="{p}assets/nt.js"></script>{js}
</body>
</html>
'''
