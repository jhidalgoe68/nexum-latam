# -*- coding: utf-8 -*-
"""Builds every NexumTurismo page from the content modules.

    python3 nexumturismo/tools/build.py

Writes the subpages and refreshes the shared header/footer of index.html
(the home page keeps its own hand-written body and script).
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from ntsite import header, footer  # noqa: E402
import pages_tours as T  # noqa: E402
import pages_services as SV  # noqa: E402
import pages_company as C  # noqa: E402
import pages_blog as B  # noqa: E402


def write(rel, html):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote", rel)


PAGES = {
    "tours/un-dia.html": T.page_un_dia,
    "tours/multidia.html": T.page_multidia,
    "servicios/cruceros.html": SV.page_cruceros,
    "servicios/viajes-a-medida.html": SV.page_fit,
    "servicios/grupos.html": SV.page_grupos,
    "servicios/incentivos.html": SV.page_incentivos,
    "servicios/corporativos.html": SV.page_corporativo,
    "nosotros/quienes-somos.html": C.page_quienes,
    "nosotros/perfil.html": C.page_perfil,
    "sostenibilidad.html": C.page_sostenibilidad,
    "agencias.html": C.page_agencias,
    "coleccion.html": C.page_coleccion,
    "contacto.html": C.page_contacto,
    "blog/index.html": B.page_blog_index,
}


def patch_index():
    path = os.path.join(ROOT, "index.html")
    s = open(path, encoding="utf-8").read()
    # shared stylesheet instead of the inline one
    s = re.sub(r"<style>.*?</style>", '<link rel="stylesheet" href="assets/nt.css">', s, count=1, flags=re.S)
    # shared header (skip link + utility bar + header) and footer
    s = re.sub(r'<a class="skip".*?</header>', lambda m: header("", "home", "#planificar"), s, count=1, flags=re.S)
    s = re.sub(r'<footer class="foot">.*?</footer>', lambda m: footer(""), s, count=1, flags=re.S)
    # shared script before the page script; the page no longer drives the mobile menu
    if 'src="assets/nt.js"' not in s:
        s = s.replace("<script>\n(function(){", '<script src="assets/nt.js"></script>\n<script>\n(function(){', 1)
    s = re.sub(r"  /\* ---------- Mobile menu ---------- \*/.*?(?=  /\* ---------- Form ---------- \*/)", "", s, count=1, flags=re.S)
    # service rows link to their own pages now
    targets = ["tours/un-dia.html", "servicios/viajes-a-medida.html", "servicios/grupos.html",
               "servicios/cruceros.html", "servicios/incentivos.html", "servicios/corporativos.html"]
    for t in targets:
        s = s.replace('<a class="txtlink" href="#planificar" data-t="s.c">Consultar</a>',
                      f'<a class="txtlink" href="{t}" data-t="s.c">Ver servicio</a>', 1)
    s = s.replace('"s.c":"Inquire"', '"s.c":"See service"')
    # guide cards open the real articles
    for key, href in [("r1", "blog/temporada-verde.html"), ("r2", "blog/caribe-sur.html"), ("r3", "tours/multidia.html")]:
        s = s.replace(f'<a href="#planificar"><span class="k" data-t="{key}.k">', f'<a href="{href}"><span class="k" data-t="{key}.k">', 1)
    open(path, "w", encoding="utf-8").write(s)
    print("patched index.html")


if __name__ == "__main__":
    for rel, fn in PAGES.items():
        write(rel, fn())
    for post in B.POSTS:
        write(f"blog/{post[0]}.html", B.page_post(post))
    patch_index()
