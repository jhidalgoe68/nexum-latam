# -*- coding: utf-8 -*-
"""Blog branch: blog/index.html and one page per article."""
from ntsite import (A, E, P, H, S, ph, head, header, page_hero, sec_head, cta_band, footer, tail)

P2 = "../"

# slug, date, cat_es, cat_en, scene, title_es, title_en, excerpt_es, excerpt_en, sections[(h_es,h_en,[(p_es,p_en)...])], cta(es,en,href)
POSTS = [
    ("temporada-verde", "2026-10-02", "Clima y temporadas", "Weather & seasons", "nuboso",
     "Temporada verde: otra forma de conocer Costa Rica", "Green season: another way to see Costa Rica",
     "Muchos viajeros la evitan porque creen que llueve todo el día. La realidad es otra, y tiene ventajas claras.",
     "Many travelers avoid it because they think it rains all day. The reality is different, and it has clear advantages.",
     [("No es solo lluvia", "It's not just rain", [
         ("La temporada verde va aproximadamente de mayo a noviembre. Los bosques están en su punto más verde, las cataratas llevan más agua y los ríos están ideales para el rafting.",
          "Green season runs roughly from May to November. Forests are at their greenest, waterfalls carry more water and rivers are ideal for rafting."),
         ("En la mayoría de las regiones la lluvia llega por la tarde y en aguaceros que van y vienen. Con un itinerario flexible, las mañanas quedan para las actividades al aire libre.",
          "In most regions rain arrives in the afternoon in showers that come and go. With a flexible itinerary, mornings are kept for outdoor activities.")]),
      ("Más accesible, no más barata", "More accessible, not cheaper", [
         ("Hay menos visitantes, más disponibilidad y tarifas más amables. Pero los hoteles, guías y tours mantienen el mismo estándar: es la misma experiencia a un precio más conveniente.",
          "There are fewer visitors, more availability and friendlier rates. But hotels, guides and tours keep the same standard: it's the same experience at a better price.")]),
      ("San José merece más que una escala", "San José deserves more than a layover", [
         ("Es buen momento para pasar un par de noches en la capital y el Valle Central: restaurantes de autor, mercados y tours de café en las colinas cercanas, con noches frescas y menos turistas.",
          "It's a good time to spend a couple of nights in the capital and the Central Valley: chef-driven restaurants, markets and coffee tours in the nearby hills, with cool evenings and fewer tourists.")]),
      ("Cómo lo planificamos", "How we plan it", [
         ("Organizamos traslados, hoteles, actividades y cenas pensando en la temporada: bosque nuboso con neblina por la mañana, termales por la tarde y cenas en San José.",
          "We arrange transfers, hotels, activities and dinners around the season: misty cloud forest in the morning, hot springs in the afternoon and dinners in San José.")])],
     ("Planificar un viaje en temporada verde", "Plan a green-season trip", "contacto.html?tipo=fit#planificar")),
    ("caribe-sur", "2026-08-04", "Destinos", "Destinations", "caribe",
     "Caribe Sur: cultura, playas y vida silvestre", "South Caribbean: culture, beaches and wildlife",
     "Puerto Viejo, Cocles, Cahuita y Manzanillo: el lado más tranquilo y con más identidad de Costa Rica.",
     "Puerto Viejo, Cocles, Cahuita and Manzanillo: Costa Rica's calmest side, and the one with the strongest identity.",
     [("Otra Costa Rica", "A different Costa Rica", [
         ("Al este del Valle Central, camino a Limón, el ritmo cambia. Cultura afrocaribeña, reggae y calipso, y casas de madera de colores frente al mar.",
          "East of the Central Valley, on the way to Limón, the pace changes. Afro-Caribbean culture, reggae and calypso, and colorful wooden houses by the sea.")]),
      ("El clima", "The weather", [
         ("Es cálido y húmedo todo el año, con lluvias cortas. A diferencia de Guanacaste, no tiene una temporada seca marcada. Lleve ropa ligera y una chaqueta impermeable.",
          "It's warm and humid year-round, with short rains. Unlike Guanacaste, there's no marked dry season. Pack light clothes and a rain jacket.")]),
      ("La cocina", "The food", [
         ("Mezcla influencias afrocaribeñas, indígenas y costarricenses: rice and beans con leche de coco, rondón de mariscos, patí y frutas tropicales.",
          "It blends Afro-Caribbean, Indigenous and Costa Rican influences: coconut rice and beans, rondón seafood stew, patí pastries and tropical fruit.")]),
      ("Qué hacer", "What to do", [
         ("Snorkel en las aguas tranquilas del Parque Nacional Cahuita, olas en Puerto Viejo, playas casi vacías cerca de Manzanillo y el Refugio Gandoca-Manzanillo, y paseos en bote por manglares para ver caimanes, perezosos, monos y aves.",
          "Snorkeling in the calm waters of Cahuita National Park, waves in Puerto Viejo, near-empty beaches by Manzanillo and the Gandoca-Manzanillo Refuge, and mangrove boat trips to see caimans, sloths, monkeys and birds."),
         ("También hay presentaciones culturales sobre la herencia afrocaribeña y bribri.", "There are also cultural presentations on Afro-Caribbean and Bribri heritage.")]),
      ("Moverse y dónde dormir", "Getting around and where to stay", [
         ("La región es extensa y conviene planificar los traslados. Recomendamos hoteles boutique, eco-lodges con acceso a la playa y lodges en la selva cerca de Puerto Viejo y Cahuita, que nuestro equipo inspecciona en persona.",
          "The region is spread out and transfers are worth planning. We recommend boutique hotels, beach-access eco-lodges and rainforest lodges near Puerto Viejo and Cahuita, which our team inspects in person.")])],
     ("Armar un itinerario por el Caribe Sur", "Build a South Caribbean itinerary", "tours/multidia.html#caribe")),
    ("tours-de-un-dia", "2026-05-05", "Aventura", "Adventure", "volcan",
     "Tours de un día en Costa Rica: la aventura le espera", "One-day tours in Costa Rica: adventure awaits",
     "Volcanes, playas, bosques nubosos y ciudad: cinco regiones que se pueden vivir en un solo día.",
     "Volcanoes, beaches, cloud forests and city: five regions you can experience in a single day.",
     [("Por qué en un día", "Why in a day", [
         ("Diseñamos cada tour para reflejar el carácter de su región, con recogida en los principales hoteles, guías locales y una combinación de naturaleza, cultura, aventura y cocina local.",
          "We design each tour to reflect its region's character, with pickup at the main hotels, local guides and a mix of nature, culture, adventure and local food.")]),
      ("Arenal y La Fortuna", "Arenal & La Fortuna", [("El volcán y su bosque: puentes colgantes, cataratas y aguas termales.", "The volcano and its forest: hanging bridges, waterfalls and hot springs.")]),
      ("Guanacaste", "Guanacaste", [("Sol y playas del Pacífico, navegación al atardecer y tradiciones sabaneras.", "Sun and Pacific beaches, sunset sailing and cowboy traditions.")]),
      ("Manuel Antonio", "Manuel Antonio", [("Selva y playa en el mismo parque, con monos y perezosos a pocos metros.", "Jungle and beach in the same park, with monkeys and sloths a few steps away.")]),
      ("Monteverde", "Monteverde", [("Bosque nuboso, senderos, aves y fauna en un ambiente de neblina.", "Cloud forest, trails, birds and wildlife in a misty setting.")]),
      ("Caribe", "Caribbean", [("Playas, arrecifes y cultura afrocaribeña con cocina y música propias.", "Beaches, reefs and Afro-Caribbean culture with its own food and music.")])],
     ("Ver el catálogo de tours", "See the tour catalog", "tours/un-dia.html")),
    ("los-santos", "2026-01-09", "Aventura", "Adventure", "valle",
     "Los Santos: la joya escondida del senderismo", "Los Santos: Costa Rica's hidden hiking gem",
     "Montañas de café, robledales y pueblos tranquilos a poco más de una hora de San José.",
     "Coffee mountains, oak forests and quiet villages a little over an hour from San José.",
     [("Una región para caminar", "A region made for walking", [
         ("Los Santos agrupa pueblos como San Marcos de Tarrazú, Santa María de Dota y San Pablo de León Cortés, entre montañas cubiertas de cafetales de altura.",
          "Los Santos groups villages such as San Marcos de Tarrazú, Santa María de Dota and San Pablo de León Cortés, among mountains covered in high-altitude coffee."),
         ("Sus caminos rurales y senderos entre fincas permiten caminatas de medio día o de varios días, con alojamiento en hoteles de montaña.",
          "Its rural roads and farm trails allow half-day or multi-day hikes, with lodging in mountain hotels.")]),
      ("Café de altura", "High-altitude coffee", [
         ("Tarrazú es una de las zonas cafetaleras más reconocidas del país. Una visita a una cooperativa o finca familiar completa la caminata.",
          "Tarrazú is one of the country's best-known coffee regions. A visit to a cooperative or family farm rounds off the hike.")]),
      ("Cuándo ir", "When to go", [
         ("La época seca, de diciembre a abril, ofrece cielos despejados y coincide con la cosecha del café.",
          "The dry season, from December to April, brings clear skies and coincides with the coffee harvest.")])],
     ("Pedir una ruta de senderismo", "Request a hiking route", "contacto.html?tipo=fit#planificar")),
    ("incentivos-costa-rica", "2026-01-16", "Incentivos", "Incentives", "playa",
     "Costa Rica para viajes de incentivo: aventura y descanso", "Costa Rica for incentive trips: adventure and rest",
     "Por qué cada vez más empresas eligen Costa Rica para premiar a sus mejores equipos.",
     "Why more and more companies choose Costa Rica to reward their best teams.",
     [("Un premio que se siente", "A reward that feels like one", [
         ("Un viaje de incentivo funciona cuando el destino ya es un premio en sí mismo. Costa Rica combina playa, volcán y bosque en distancias cortas, con hoteles preparados para grupos.",
          "An incentive trip works when the destination is a reward in itself. Costa Rica combines beach, volcano and forest within short distances, with hotels ready for groups.")]),
      ("Logística que acompaña", "Logistics that keep up", [
         ("Dos aeropuertos internacionales, vuelos directos desde Norteamérica y Europa y una red de proveedores certificados facilitan mover grupos grandes.",
          "Two international airports, direct flights from North America and Europe and a network of certified suppliers make it easy to move large groups.")]),
      ("Experiencias con propósito", "Purposeful experiences", [
         ("Team building en la naturaleza, proyectos solidarios con comunidades y cenas en lugares únicos convierten el viaje en algo que el equipo recuerda.",
          "Team building in nature, give-back projects with communities and dinners in unique places turn the trip into something the team remembers.")])],
     ("Ver viajes de incentivo", "See incentive trips", "servicios/incentivos.html")),
]


def fmt_date(d):
    y, m, dd = d.split("-")
    mes = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"][int(m) - 1]
    mon = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][int(m) - 1]
    return f"{int(dd)} de {mes} de {y}", f"{mon} {int(dd)}, {y}"


def card(post, i, p, lead=False):
    slug, d, ces, cen, sc, tes, ten, xes, xen = post[:9]
    des, den = fmt_date(d)
    return f'''<a class="post{" lead" if lead else ""}" href="{p}blog/{slug}.html"><div class="scene" data-scene="{sc}" data-seed="{i}"></div><div class="body">
<span class="k"><span data-en="{A(cen)}">{ces}</span> · <time datetime="{d}" data-en="{A(den)}">{des}</time></span>
<h3 data-en="{A(ten)}">{tes}</h3><p data-en="{A(xen)}">{xes}</p></div></a>'''


def page_blog_index():
    posts = sorted(POSTS, key=lambda x: x[1], reverse=True)
    cards = card(posts[0], 0, P2, True) + "".join(card(x, i + 1, P2) for i, x in enumerate(posts[1:]))
    body = head(P2, "Blog · NexumTurismo", "Blog · NexumTurismo", "Guías y artículos para planificar mejor su viaje a Costa Rica.")
    body += header(P2, "blog")
    body += '<main id="main">'
    body += page_hero(P2, [("Blog", "Blog", None)], "Guías para planificar mejor", "Guides to plan better",
                      "Temporadas, destinos, ideas de viaje y lo que aprendemos operando en todo el país.",
                      "Seasons, destinations, trip ideas and what we learn operating across the country.")
    body += f'<section class="sec" aria-label="Artículos"><div class="wrap"><div class="posts">{cards}</div></div></section>'
    body += cta_band(P2)
    body += "</main>" + footer(P2) + tail(P2)
    return body


def page_post(post):
    slug, d, ces, cen, sc, tes, ten, xes, xen, sections, cta = post
    des, den = fmt_date(d)
    secs = ""
    for hes, hen, paras in sections:
        secs += f'<h2 data-en="{A(hen)}">{hes}</h2>' + "".join(f'<p data-en="{A(pen)}">{pes}</p>' for pes, pen in paras)
    others = [x for x in sorted(POSTS, key=lambda x: x[1], reverse=True) if x[0] != slug][:2]
    rel = "".join(card(x, i + 5, P2) for i, x in enumerate(others))
    body = head(P2, f"{tes} · NexumTurismo", f"{ten} · NexumTurismo", xes)
    body += header(P2, "blog")
    body += f'''<main id="main"><article class="sec"><div class="wrap"><div class="article">
<nav class="crumbs" aria-label="Ruta"><ol><li><a href="{P2}index.html" data-en="Home">Inicio</a></li><li><a href="{P2}blog/index.html">Blog</a></li><li><span aria-current="page" data-en="{A(ten)}">{tes}</span></li></ol></nav>
<p class="k"><span data-en="{A(cen)}">{ces}</span> · <time datetime="{d}" data-en="{A(den)}">{des}</time></p>
<h1 style="font-size:clamp(2rem,4.4vw,3.2rem);line-height:1.06;letter-spacing:-.02em" data-en="{A(ten)}">{tes}</h1>
<p class="lede" data-en="{A(xen)}">{xes}</p>
<div class="scene" data-scene="{sc}" data-seed="2"></div>
{secs}
<p style="margin-top:2rem"><a class="btn btn--primary" href="{P2}{cta[2]}" data-en="{A(cta[1])}">{cta[0]}</a></p>
</div></div></article>
<section class="sec sec--tint" aria-labelledby="rl-h"><div class="wrap"><h2 id="rl-h" style="margin-bottom:1.5rem" data-en="Keep reading">Siga leyendo</h2><div class="related">{rel}</div></div></section>'''
    body += "</main>" + footer(P2) + tail(P2)
    return body
