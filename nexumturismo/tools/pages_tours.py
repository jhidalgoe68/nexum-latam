# -*- coding: utf-8 -*-
"""Tours branch: tours/un-dia.html (catalog with filters) and tours/multidia.html."""
import json
from ntsite import (A, E, P, H, S, ph, head, header, page_hero, sec_head, cta_band, footer, tail, checks, CHECK)

P2 = "../"

# name_es, name_en, region key, place, duration key, category key, desc_es, desc_en, scene
TOURS = [
    ("Buceo en Playa Hermosa", "Scuba diving at Playa Hermosa", "gte", "Playa Hermosa, Guanacaste", "full", "agua",
     "Dos inmersiones guiadas en los islotes del golfo de Papagayo, con equipo y embarcación incluidos.",
     "Two guided dives at the Gulf of Papagayo islets, with gear and boat included.", "playa"),
    ("Pesca deportiva", "Sport fishing", "gte", "Playa Hermosa, Guanacaste", "full", "agua",
     "Salida en lancha equipada con capitán local y modalidad de captura y liberación.",
     "Trip on an equipped boat with a local captain, catch-and-release.", "playa"),
    ("Catamarán y snorkel al atardecer", "Sunset catamaran & snorkeling", "gte", "Tamarindo, Guanacaste", "full", "agua",
     "Navegación por la costa, parada para snorkel en bahía protegida y atardecer a bordo.",
     "Coastal sailing, a snorkel stop in a sheltered bay and sunset on board.", "playa"),
    ("Moto acuática", "Jet ski", "gte", "Playa Hermosa, Guanacaste", "half", "agua",
     "Recorrido guiado por la bahía con instrucción previa y chaleco salvavidas.",
     "Guided ride around the bay with a safety briefing and life jacket.", "playa"),
    ("Clases de surf", "Surf lessons", "gte", "Playa Hermosa, Guanacaste", "half", "agua",
     "Instructor certificado, tabla y licra incluidos. Para principiantes y niveles intermedios.",
     "Certified instructor, board and rash guard included. For beginners and intermediates.", "playa"),
    ("Cuadraciclos todoterreno", "Off-road ATV ride", "gte", "Matapalo, Guanacaste", "half", "aventura",
     "Caminos rurales, bosque seco y miradores al Pacífico en cuadraciclo con guía.",
     "Rural roads, dry forest and Pacific lookouts on a guided ATV.", "valle"),
    ("Canopy y santuario de vida silvestre", "Zip lines & wildlife sanctuary", "gte", "Matapalo, Guanacaste", "full", "naturaleza",
     "Cables sobre el bosque y visita a un proyecto de rescate de fauna nativa.",
     "Lines over the forest and a visit to a native wildlife rescue project.", "selva"),
    ("Canopy en Guanacaste", "Guanacaste zip lines", "gte", "Nuevo Colón, Carrillo", "half", "aventura",
     "Circuito de cables y plataformas entre árboles, a pocos minutos de las playas del norte.",
     "Zip-line and platform circuit through the trees, minutes from the northern beaches.", "selva"),
    ("Río Perdido: canopy, tubing y aguas termales", "Río Perdido: zip lines, tubing & hot springs", "gte", "Bagaces, Guanacaste", "full", "aventura",
     "Cañón volcánico, río de aguas termales y descenso en neumático en un solo día.",
     "Volcanic canyon, thermal river and tubing in a single day.", "rio"),
    ("Combo Rincón de la Vieja", "Rincón de la Vieja combo", "gte", "Liberia, Guanacaste", "full", "aventura",
     "Cabalgata, canopy y aguas termales al pie del volcán Rincón de la Vieja.",
     "Horseback riding, zip lines and hot springs at the foot of Rincón de la Vieja volcano.", "volcan"),
    ("Río Celeste y puentes colgantes", "Celeste River & hanging bridges", "norte", "Bijagua, Alajuela", "full", "naturaleza",
     "Caminata al río de color turquesa del Parque Nacional Tenorio y puentes sobre el bosque lluvioso.",
     "Hike to the turquoise river in Tenorio National Park and bridges over the rainforest.", "rio"),
    ("Adrenalina en Rincón de la Vieja", "Rincón de la Vieja adrenaline", "gte", "Liberia, Guanacaste", "full", "aventura",
     "Cabalgata, tubing en río y canopy para quienes quieren el día más activo.",
     "Horseback riding, river tubing and zip lines for the most active day.", "volcan"),
    ("Volcán Arenal y aguas termales", "Arenal Volcano & hot springs", "norte", "La Fortuna, Alajuela", "full", "naturaleza",
     "Caminata por coladas de lava antiguas, mirador del volcán y cierre en aguas termales.",
     "Walk over old lava flows, volcano lookout and an evening in hot springs.", "volcan"),
    ("Puentes colgantes y catarata La Fortuna", "Hanging bridges & La Fortuna waterfall", "norte", "La Fortuna, Alajuela", "half", "naturaleza",
     "Puentes sobre el dosel del bosque y descenso a la catarata para nadar.",
     "Bridges over the forest canopy and a walk down to the waterfall for a swim.", "selva"),
    ("Caminata nocturna en bosque nuboso", "Cloud forest night walk", "norte", "Monteverde, Puntarenas", "2h", "naturaleza",
     "Con linterna y guía naturalista: ranas, insectos, aves dormidas y, con suerte, perezosos.",
     "With flashlights and a naturalist guide: frogs, insects, sleeping birds and, with luck, sloths.", "noche"),
    ("Parque Nacional Manuel Antonio", "Manuel Antonio National Park", "pacifico", "Quepos, Puntarenas", "half", "naturaleza",
     "Senderos con guía y telescopio para ver monos, perezosos y aves, con tiempo de playa dentro del parque.",
     "Guided trails with a spotting scope for monkeys, sloths and birds, plus beach time inside the park.", "pacifico"),
    ("Tour de café en el Valle Central", "Central Valley coffee tour", "valle", "Heredia / Alajuela", "half", "cultura",
     "De la planta a la taza: cultivo, beneficio, tueste y catación en una finca familiar.",
     "From plant to cup: growing, milling, roasting and tasting on a family farm.", "valle"),
    ("San José histórico", "Historic San José", "valle", "San José", "half", "cultura",
     "Teatro Nacional, museos del Oro y del Jade, mercado central y arquitectura de la ciudad.",
     "National Theatre, Gold and Jade museums, the central market and the city's architecture.", "ciudad"),
    ("Canales de Tortuguero", "Tortuguero canals", "caribe", "Tortuguero, Limón", "full", "naturaleza",
     "Navegación por canales de selva con guía para observar caimanes, monos, aves y perezosos.",
     "Boat trip through jungle canals with a guide to spot caimans, monkeys, birds and sloths.", "caribe"),
    ("Termales y bienestar", "Hot springs & wellness", "norte", "La Fortuna, Alajuela", "3q", "relax",
     "Tarde de piscinas termales, masaje y cena con vista al volcán.",
     "An afternoon of thermal pools, a massage and dinner with a volcano view.", "volcan"),
]

REGIONS = {"gte": ("Guanacaste", "Guanacaste"), "norte": ("Zona norte", "Northern zone"),
           "pacifico": ("Pacífico Central", "Central Pacific"), "valle": ("Valle Central", "Central Valley"),
           "caribe": ("Caribe", "Caribbean")}
DUR = {"2h": ("2 horas", "2 hours"), "half": ("Medio día", "Half day"), "3q": ("3/4 de día", "3/4 day"), "full": ("Día completo", "Full day")}
CATS = {"aventura": ("Aventura", "Adventure"), "agua": ("Deportes acuáticos", "Water sports"), "cultura": ("Cultura", "Culture"),
        "naturaleza": ("Naturaleza", "Nature"), "relax": ("Relax", "Relax")}


def page_un_dia():
    data = [dict(n=[t[0], t[1]], r=t[2], pl=t[3], d=t[4], c=t[5], x=[t[6], t[7]], s=t[8]) for t in TOURS]
    region_opts = "".join(f'<option value="{k}" data-en="{A(v[1])}">{v[0]}</option>' for k, v in REGIONS.items())
    dur_opts = "".join(f'<option value="{k}" data-en="{A(v[1])}">{v[0]}</option>' for k, v in DUR.items())
    chips = "".join(f'<button type="button" class="chip" data-cat="{k}" aria-pressed="false" data-en="{A(v[1])}">{v[0]}</button>' for k, v in CATS.items())
    js = "var TOURS=" + json.dumps(data, ensure_ascii=False) + ";\nvar REG=" + json.dumps(REGIONS, ensure_ascii=False) + \
         ";\nvar DUR=" + json.dumps(DUR, ensure_ascii=False) + ";\nvar CATS=" + json.dumps(CATS, ensure_ascii=False) + r""";
(function(){
  var grid=document.getElementById('tourGrid'),cnt=document.getElementById('tourCount'),q=document.getElementById('fq'),
      reg=document.getElementById('freg'),dur=document.getElementById('fdur'),sort=document.getElementById('fsort'),
      empty=document.getElementById('tourEmpty'),cats={};
  function L(p){return NT.lang==='en'?p[1]:p[0];}
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function norm(s){return String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'');}
  function render(){
    var term=norm(q.value.trim()),active=Object.keys(cats).filter(function(k){return cats[k];});
    var list=TOURS.filter(function(t){
      if(reg.value&&t.r!==reg.value)return false;
      if(dur.value&&t.d!==dur.value)return false;
      if(active.length&&active.indexOf(t.c)<0)return false;
      if(term&&norm(t.n[0]+' '+t.n[1]+' '+t.pl+' '+t.x[0]+' '+t.x[1]).indexOf(term)<0)return false;
      return true;});
    var order=['2h','half','3q','full'];
    if(sort.value==='az')list.sort(function(a,b){return L(a.n).localeCompare(L(b.n));});
    if(sort.value==='dur')list.sort(function(a,b){return order.indexOf(a.d)-order.indexOf(b.d);});
    cnt.textContent=NT.lang==='en'?(list.length+' of '+TOURS.length+' tours'):(list.length+' de '+TOURS.length+' tours');
    empty.hidden=list.length>0;grid.hidden=list.length===0;
    grid.innerHTML=list.map(function(t,i){
      var href='../contacto.html?tipo=dia&tour='+encodeURIComponent(t.n[0])+'#planificar';
      return '<article class="tour"><div class="scene">'+NT.scene(t.s,TOURS.indexOf(t))+'</div><div class="body">'+
        '<div class="meta"><span>'+esc(t.pl)+'</span><span>'+esc(L(DUR[t.d]))+'</span></div>'+
        '<h3>'+esc(L(t.n))+'</h3><p>'+esc(L(t.x))+'</p>'+
        '<div class="foot-row"><span class="cat">'+esc(L(CATS[t.c]))+'</span>'+
        '<a class="txtlink" href="'+href+'">'+(NT.lang==='en'?'Check availability':'Consultar disponibilidad')+'</a></div></div></article>';
    }).join('');
  }
  Array.prototype.forEach.call(document.querySelectorAll('.chip[data-cat]'),function(b){
    b.addEventListener('click',function(){cats[b.dataset.cat]=!cats[b.dataset.cat];b.setAttribute('aria-pressed',String(!!cats[b.dataset.cat]));render();});});
  [q,reg,dur,sort].forEach(function(el){el.addEventListener('input',render);el.addEventListener('change',render);});
  function reset(){q.value='';reg.value='';dur.value='';sort.value='az';cats={};Array.prototype.forEach.call(document.querySelectorAll('.chip[data-cat]'),function(b){b.setAttribute('aria-pressed','false');});render();}
  document.getElementById('fclear').addEventListener('click',reset);
  document.getElementById('fclear2').addEventListener('click',reset);
  document.addEventListener('nt:lang',render);
  render();
})();"""
    body = head(P2, "Tours de un día · NexumTurismo", "One-day tours · NexumTurismo",
                "Catálogo de tours de un día en Costa Rica: aventura, deportes acuáticos, cultura, naturaleza y relax.")
    body += header(P2, "tours-dia")
    body += '<main id="main">'
    body += page_hero(P2, [("Tours", "Tours", None), ("Tours de un día", "One-day tours", None)],
                      "Tours de un día en todo el país", "One-day tours across the country",
                      "Medio día o día completo, con recogida en su hotel y guías certificados. Filtre por región, duración o tipo de experiencia y consulte disponibilidad en un clic.",
                      "Half or full days, with hotel pickup and certified guides. Filter by region, duration or type of experience and check availability in one click.",
                      aside=f'''<dl class="factbox">
<div><dt data-en="Tours in the catalog">Tours en el catálogo</dt><dd>{len(TOURS)}</dd></div>
<div><dt data-en="Regions">Regiones</dt><dd>{len(REGIONS)}</dd></div>
<div><dt data-en="Languages">Idiomas</dt><dd>ES · EN</dd></div>
<div><dt data-en="Price">Precio</dt><dd data-en="On request">A consultar</dd></div></dl>''')
    body += f'''<section class="sec" aria-labelledby="cat-h"><div class="wrap">
<h2 id="cat-h" class="sr" data-en="Tour catalog">Catálogo de tours</h2>
<div class="chips" role="group" aria-label="Tipo de experiencia" style="margin-bottom:1.2rem">{chips}</div>
<div class="filters">
  <label for="fq"><span data-en="Search">Buscar</span><input id="fq" type="search" placeholder="Volcán, canopy, café…" data-en-ph="Volcano, zip line, coffee…"></label>
  <label for="freg"><span data-en="Region">Región</span><select id="freg"><option value="" data-en="All">Todas</option>{region_opts}</select></label>
  <label for="fdur"><span data-en="Duration">Duración</span><select id="fdur"><option value="" data-en="Any">Cualquiera</option>{dur_opts}</select></label>
  <label for="fsort"><span data-en="Sort by">Ordenar por</span><select id="fsort"><option value="az" data-en="Name (A–Z)">Nombre (A–Z)</option><option value="dur" data-en="Duration">Duración</option></select></label>
</div>
<div class="count-line"><span id="tourCount" aria-live="polite"></span><button type="button" class="linkbtn" id="fclear" data-en="Clear filters">Limpiar filtros</button></div>
<div class="tours" id="tourGrid"></div>
<div class="empty" id="tourEmpty" hidden><b data-en="No tour matches those filters.">Ningún tour coincide con esos filtros.</b>
<p data-en="Clear the filters or tell us what you're looking for: we design custom tours too.">Limpie los filtros o cuéntenos qué busca: también diseñamos tours a la medida.</p>
<button type="button" class="btn btn--ghost" id="fclear2" data-en="Clear filters">Limpiar filtros</button></div>
</div></section>
<section class="sec sec--tint" aria-labelledby="why-h"><div class="wrap two">
<div>{sec_head("why-h", "Elegidos por calidad y seguridad", "Chosen for quality and safety",
               "Costa Rica ofrece aventura, playas solitarias, volcanes activos, bosques y bienestar. Solo incluimos actividades que revisamos en persona.",
               "Costa Rica offers adventure, secluded beaches, active volcanoes, forests and wellness. We only include activities we have checked in person.")}</div>
{checks([("Operadores verificados", "Vetted operators", "Revisamos equipos, seguros y protocolos de cada proveedor antes de venderlo.", "We review each supplier's equipment, insurance and protocols before we sell it."),
         ("Guías certificados", "Certified guides", "Guías naturalistas acreditados por el Instituto Costarricense de Turismo.", "Naturalist guides accredited by the Costa Rican Tourism Board."),
         ("Recogida en su hotel", "Hotel pickup", "Salidas desde las principales zonas turísticas y hoteles del país.", "Departures from the main tourist areas and hotels in the country."),
         ("Plan B por clima", "A weather plan B", "Si la lluvia o el oleaje lo exigen, le proponemos una alternativa o reprogramamos.", "If rain or surf require it, we offer an alternative or reschedule.")])}
</div></section>'''
    body += cta_band(P2, "¿Quiere combinar varios tours en un viaje?", "Want to combine several tours into one trip?",
                     "Los convertimos en un programa multidía con hoteles y traslados incluidos.",
                     "We turn them into a multi-day program with hotels and transfers included.",
                     "Ver programas multidía", "See multi-day programs", f"{P2}tours/multidia.html",
                     "Pedir un tour a la medida", "Request a custom tour", f"{P2}contacto.html?tipo=dia#planificar")
    body += "</main>" + footer(P2) + tail(P2, js)
    return body


# key, days, title_es, title_en, route, ideal_es, ideal_en, scene, [(days, t_es, t_en, d_es, d_en)]
PROGRAMS = [
    ("esencial", 8, "Costa Rica esencial", "Essential Costa Rica", "San José · Arenal · Monteverde · Guanacaste",
     "Primer viaje, parejas y familias", "First trips, couples and families", "volcan", [
        ("1", "Llegada a San José", "Arrival in San José", "Recepción en el aeropuerto, repaso del programa y noche en el Valle Central.", "Airport welcome, program walkthrough and a night in the Central Valley."),
        ("2–3", "Volcán Arenal", "Arenal Volcano", "Puentes colgantes, catarata La Fortuna y aguas termales.", "Hanging bridges, La Fortuna waterfall and hot springs."),
        ("4–5", "Monteverde", "Monteverde", "Bosque nuboso, canopy y caminata nocturna.", "Cloud forest, zip lines and a night walk."),
        ("6–8", "Playas de Guanacaste", "Guanacaste beaches", "Días de playa, catamarán al atardecer y salida desde Liberia.", "Beach days, a sunset catamaran and departure from Liberia.")]),
    ("volcanes", 7, "Volcanes y Pacífico norte", "Volcanoes & North Pacific", "Liberia · Rincón de la Vieja · Río Celeste · Papagayo",
     "Viajeros activos que vuelan a Liberia", "Active travelers flying into Liberia", "playa", [
        ("1", "Llegada a Liberia", "Arrival in Liberia", "Traslado a su hotel en el golfo de Papagayo.", "Transfer to your hotel on the Gulf of Papagayo."),
        ("2–3", "Rincón de la Vieja", "Rincón de la Vieja", "Senderos de fumarolas, cabalgata y aguas termales.", "Fumarole trails, horseback riding and hot springs."),
        ("4", "Río Celeste", "Celeste River", "Caminata al río turquesa y puentes colgantes en Bijagua.", "Hike to the turquoise river and hanging bridges in Bijagua."),
        ("5–7", "Papagayo", "Papagayo", "Snorkel, buceo opcional y días libres de playa.", "Snorkeling, optional diving and free beach days.")]),
    ("caribe", 7, "Caribe y selva", "Caribbean & rainforest", "San José · Tortuguero · Cahuita · Puerto Viejo",
     "Amantes de la naturaleza y la cultura", "Nature and culture lovers", "caribe", [
        ("1", "San José", "San José", "Llegada y noche en la capital.", "Arrival and a night in the capital."),
        ("2–3", "Tortuguero", "Tortuguero", "Canales en lancha, caminatas y, en temporada, desove de tortugas.", "Boat trips through the canals, hikes and, in season, turtle nesting."),
        ("4–6", "Cahuita y Puerto Viejo", "Cahuita & Puerto Viejo", "Arrecife de Cahuita, cocina afrocaribeña y playas de Manzanillo.", "Cahuita reef, Afro-Caribbean cooking and the beaches of Manzanillo."),
        ("7", "Regreso", "Return", "Traslado privado a San José para su vuelo.", "Private transfer to San José for your flight.")]),
    ("salvaje", 9, "Pacífico sur salvaje", "Wild South Pacific", "Manuel Antonio · Uvita · Península de Osa",
     "Viajeros con espíritu explorador", "Travelers with an explorer's spirit", "selva", [
        ("1–3", "Manuel Antonio", "Manuel Antonio", "Parque nacional con guía y playas dentro del bosque.", "Guided national park visit and beaches inside the forest."),
        ("4–5", "Uvita y Marino Ballena", "Uvita & Marino Ballena", "Playa Cola de Ballena y, en temporada, avistamiento de ballenas.", "Whale's Tail beach and, in season, whale watching."),
        ("6–8", "Península de Osa", "Osa Peninsula", "Lodge en bahía Drake, Corcovado e isla del Caño.", "Lodge in Drake Bay, Corcovado and Caño Island."),
        ("9", "Regreso", "Return", "Vuelo doméstico a San José.", "Domestic flight to San José.")]),
    ("aves", 10, "Aves de Costa Rica", "Birds of Costa Rica", "Valle Central · San Gerardo de Dota · Arenal · Caño Negro",
     "Grupos y viajeros de observación de aves", "Birding groups and travelers", "nuboso", [
        ("1–2", "Valle Central", "Central Valley", "Jardines y fincas de café con colibríes y tangaras.", "Gardens and coffee farms with hummingbirds and tanagers."),
        ("3–5", "San Gerardo de Dota", "San Gerardo de Dota", "Robledales de altura y búsqueda del quetzal.", "Highland oak forests and the search for the quetzal."),
        ("6–8", "Arenal", "Arenal", "Senderos de bosque lluvioso y torres de observación.", "Rainforest trails and observation towers."),
        ("9–10", "Caño Negro", "Caño Negro", "Humedal en bote para aves acuáticas y regreso.", "Wetland boat trip for waterbirds and return.")]),
    ("bienestar", 6, "Bienestar y termales", "Wellness & hot springs", "Arenal · Monteverde · Nosara",
     "Parejas y viajeros que buscan descanso", "Couples and travelers looking to unwind", "nuboso", [
        ("1–2", "Arenal", "Arenal", "Hotel termal, masaje y yoga al amanecer.", "Thermal hotel, massage and sunrise yoga."),
        ("3", "Monteverde", "Monteverde", "Caminata lenta en el bosque nuboso y cena de cocina local.", "A slow cloud-forest walk and a dinner of local cooking."),
        ("4–6", "Nosara", "Nosara", "Retiro frente al mar con clases de yoga y surf suave.", "Beachfront retreat with yoga classes and gentle surfing.")]),
]


def page_multidia():
    cards = []
    for i, (k, days, tes, ten, route, ies, ien, scene, steps) in enumerate(PROGRAMS):
        det = "".join(f'<details><summary><span data-en="{A("Day" if "–" not in d else "Days")} {d}">{"Día" if "–" not in d else "Días"} {d}</span>'
                      f'<b data-en="{A(sen)}">{ses}</b></summary><p data-en="{A(den)}">{des}</p></details>'
                      for d, ses, sen, des, den in steps)
        cards.append(f'''<article class="program" id="{k}">
<div class="ptop"><div class="days">{days}<small data-en="days">días</small></div>
<h3 data-en="{A(ten)}">{tes}</h3><p class="route">{route}</p>
<p><b data-en="Best for:">Ideal para:</b> <span data-en="{A(ien)}">{ies}</span></p>
<a class="btn btn--primary" href="{P2}contacto.html?tipo=fit&tour={A(tes)}#planificar" data-en="Request this program">Solicitar este programa</a></div>
<div class="pbody">{det}</div></article>''')
    body = head(P2, "Programas multidía · NexumTurismo", "Multi-day programs · NexumTurismo",
                "Itinerarios de varios días por Costa Rica: aventura, naturaleza, cultura y bienestar, adaptables a cada viajero.")
    body += header(P2, "tours-multi")
    body += '<main id="main">'
    body += page_hero(P2, [("Tours", "Tours", None), ("Programas multidía", "Multi-day programs", None)],
                      "Programas multidía listos para adaptar", "Multi-day programs ready to adapt",
                      "Aventura, naturaleza, cultura o bienestar. Cada programa es un punto de partida: cambiamos días, hoteles y actividades hasta que el viaje sea suyo.",
                      "Adventure, nature, culture or wellness. Each program is a starting point: we change days, hotels and activities until the trip is yours.",
                      f'<a class="btn btn--primary" href="{P2}contacto.html?tipo=fit#planificar" data-en="Design my own program">Diseñar mi propio programa</a>'
                      f'<a class="btn btn--ghost" href="{P2}tours/un-dia.html" data-en="See one-day tours">Ver tours de un día</a>')
    body += f'''<section class="sec" aria-labelledby="pr-h"><div class="wrap">
{sec_head("pr-h", "Seis rutas probadas", "Six proven routes", "Abra cada etapa para ver qué incluye. Los precios dependen de la temporada, los hoteles elegidos y el tamaño del grupo.", "Open each stage to see what's included. Prices depend on the season, the hotels you choose and group size.")}
<div class="programs">{''.join(cards)}</div></div></section>
<section class="sec sec--tint" aria-labelledby="inc-h"><div class="wrap two">
<div>{sec_head("inc-h", "Qué incluye cada programa", "What every program includes")}</div>
{checks([("Hoteles seleccionados", "Selected hotels", "Opciones por categoría en cada destino, inspeccionadas por nuestro equipo.", "Options by category in each destination, inspected by our team."),
         ("Traslados privados o compartidos", "Private or shared transfers", "Vehículos con aire acondicionado y choferes bilingües.", "Air-conditioned vehicles and bilingual drivers."),
         ("Actividades con guía", "Guided activities", "Las experiencias clave de cada región, con guías certificados.", "The key experiences of each region, with certified guides."),
         ("Asistencia 24/7", "24/7 assistance", "Un coordinador por WhatsApp durante todo el viaje.", "A coordinator on WhatsApp for the whole trip.")])}
</div></section>'''
    body += cta_band(P2)
    body += "</main>" + footer(P2) + tail(P2)
    return body
