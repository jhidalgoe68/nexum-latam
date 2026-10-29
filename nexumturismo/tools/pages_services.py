# -*- coding: utf-8 -*-
"""Services branch: cruise operations, FIT, leisure groups, incentives, corporate."""
from ntsite import (A, E, P, H, S, ph, head, header, page_hero, sec_head, cta_band, footer, tail, checks, team, CHECK)

P2 = "../"
SV = ("Servicios", "Services", None)


def blocks(items, cols=""):
    """items: (tag_es, tag_en, h_es, h_en, p_es, p_en) — tag may be empty."""
    out = []
    for tes, ten, hes, hen, pes, pen in items:
        tag = f'<span class="tag" data-en="{A(ten)}">{tes}</span>' if tes else ""
        out.append(f'<div class="block">{tag}<h3 data-en="{A(hen)}">{hes}</h3><p data-en="{A(pen)}">{pes}</p></div>')
    return f'<div class="blocks {cols}">{"".join(out)}</div>'


def factbox(rows):
    return '<dl class="factbox">' + "".join(
        f'<div><dt data-en="{A(en)}">{es}</dt><dd{(" data-en=" + chr(34) + A(ven) + chr(34)) if ven else ""}>{v}</dd></div>'
        for es, en, v, ven in rows) + "</dl>"


GUIDES = [  # shared "why us" operating standards (from the source's 4 guideline blocks)
    ("Lineamientos generales", "General guidelines", "Operación sostenible", "Sustainable operations",
     "Un programa de gestión sostenible y sus certificaciones previenen y reducen el impacto de cada operación.",
     "A sustainability management program and its certifications prevent and reduce the impact of every operation."),
    ("Lineamientos socioeconómicos", "Social & economic guidelines", "Guías certificados", "Certified guides",
     "Guías bilingües (español e inglés) acreditados por el Instituto Costarricense de Turismo; varios hablan alemán, francés, italiano o portugués.",
     "Bilingual guides (Spanish and English) accredited by the Costa Rican Tourism Board; several also speak German, French, Italian or Portuguese."),
    ("Lineamientos de oferta turística", "Tourism offer guidelines", "Flota moderna y propia", "A modern, owned fleet",
     "Desde buses de 50 pasajeros hasta microbuses privados, con aire acondicionado, asientos reclinables y comunicación por radio.",
     "From 50-passenger coaches to private minibuses, with air conditioning, reclining seats and radio communication."),
    ("Lineamientos de oferta turística", "Tourism offer guidelines", "Soporte operativo", "Operational support",
     "Agentes de operaciones coordinan cada salida con precisión y resuelven cambios en tiempo real.",
     "Operations agents coordinate every departure precisely and handle changes in real time."),
]


def page_cruceros():
    pac = [("Puntarenas", "Golfo de Nicoya · bosque, manglar y Valle Central", "Gulf of Nicoya · forest, mangroves and Central Valley"),
           ("Caldera", "Muelle principal del Pacífico · Carara, café, San José", "Main Pacific pier · Carara, coffee, San José"),
           ("Quepos", "Manuel Antonio y Pacífico Central", "Manuel Antonio and Central Pacific"),
           ("Golfito", "Golfo Dulce, Osa y selva del sur", "Golfo Dulce, Osa and southern rainforest"),
           ("Playas del Coco", "Guanacaste · playas, Rincón de la Vieja", "Guanacaste · beaches, Rincón de la Vieja"),
           ("Bahía Drake", "Barcos de expedición · Corcovado e isla del Caño", "Expedition ships · Corcovado and Caño Island")]
    car = [("Puerto Limón", "Tortuguero, canales, banano y cacao", "Tortuguero, canals, bananas and cocoa"),
           ("Moín", "Terminal de cruceros del Caribe · Cahuita y selva", "Caribbean cruise terminal · Cahuita and rainforest")]

    def coast(h_es, h_en, ports):
        lis = "".join(f'<li><b>{n}</b><span data-en="{A(en)}">{es}</span></li>' for n, es, en in ports)
        return f'<div class="coast"><h3 data-en="{A(h_en)}">{h_es}</h3><ul>{lis}</ul></div>'

    body = head(P2, "Operación de cruceros · NexumTurismo", "Cruise operations · NexumTurismo",
                "Excursiones en tierra, turnarounds y programas pre y post crucero en todos los puertos de Costa Rica.")
    body += header(P2, "cruceros")
    body += '<main id="main">'
    body += page_hero(P2, [SV, ("Operación de cruceros", "Cruise operations", None)],
                      "Excursiones en tierra que regresan a tiempo al barco", "Shore excursions that get back to the ship on time",
                      "Operamos excursiones, turnarounds y programas antes y después del crucero en los puertos del Pacífico y del Caribe, desde barcos de expedición de lujo hasta grandes navieras.",
                      "We run shore excursions, turnarounds and pre- and post-cruise programs at Pacific and Caribbean ports, from luxury expedition ships to large cruise lines.",
                      f'<a class="btn btn--primary" href="{P2}contacto.html?tipo=crucero#planificar" data-en="Talk to cruise operations">Hablar con operaciones de cruceros</a>',
                      factbox([("Puertos que cubrimos", "Ports we cover", "8", ""),
                               ("Cruceros por temporada", "Cruise calls per season", ph("[000]"), ""),
                               ("Pasajeros por día en temporada alta", "Passengers per day in peak season", ph("[0 000]"), ""),
                               ("Experiencia en cruceros desde", "Cruise experience since", ph("[año]"), "")]))
    body += f'''<section class="sec" aria-labelledby="pt-h"><div class="wrap">
{sec_head("pt-h", "Nuestros puertos de entrada", "Our ports of entry", "Dos costas, una sola operación. Cada puerto tiene su propio menú de excursiones y tiempos de ruta medidos.", "Two coasts, one operation. Each port has its own excursion menu and measured route times.")}
<div class="ports">{coast("Pacífico", "Pacific", pac)}{coast("Caribe", "Caribbean", car)}</div></div></section>
<section class="sec band" aria-labelledby="sv2-h"><div class="wrap">
{sec_head("sv2-h", "Tres servicios para la línea de crucero", "Three services for the cruise line")}
{blocks([("", "", "Excursiones en tierra", "Shore excursions", "Fauna, paisajes, cultura y gente de Costa Rica en experiencias que además generan ingresos para comunidades rurales.", "Costa Rica's wildlife, landscapes, culture and people in experiences that also bring income to rural communities."),
         ("", "", "Turnarounds", "Turnarounds", "Equipos locales gestionan el recorrido completo del huésped entre aeropuerto, hotel y puerto, en escalas regulares y no programadas.", "Local teams manage the guest's full journey between airport, hotel and port, on scheduled and unscheduled calls."),
         ("", "", "Programas pre y post crucero", "Pre- and post-cruise programs", "Paquetes en tierra antes o después del viaje para conocer cultura, cocina y naturaleza con calma.", "Land packages before or after the cruise to experience culture, food and nature without rushing.")])}
</div></section>
<section class="sec" aria-labelledby="ex-h"><div class="wrap two">
<div>{sec_head("ex-h", "Compromiso con la excelencia", "Commitment to excellence", "Un operador confiable e innovador para barcos de todos los tamaños, con un equipo que aporta conocimiento y creatividad a cada escala.", "A reliable, innovative operator for ships of every size, with a team that brings knowledge and creativity to every call.")}</div>
{checks([("Puntualidad como regla", "Punctuality as a rule", "Tiempos de ruta medidos y planes alternos por clima o tráfico.", "Measured route times and backup plans for weather or traffic."),
         ("Capacidad para volumen", "Built for volume", "Flota y guías coordinados para recibir a cientos de pasajeros el mismo día.", "Fleet and guides coordinated to welcome hundreds of passengers on the same day."),
         ("Accesibilidad real", "Real accessibility", "Buses con rampa y vehículo especializado para pasajeros con movilidad reducida, con choferes capacitados.", "Buses with ramps and a specialized vehicle for passengers with reduced mobility, with trained drivers."),
         ("Cobertura de seguros", "Insurance coverage", "Pólizas amplias para la tranquilidad de la naviera y de sus huéspedes.", "Broad policies for the peace of mind of the cruise line and its guests.")])}
</div></section>
<section class="sec sec--tint" aria-labelledby="gd-h"><div class="wrap">
{sec_head("gd-h", "Cómo operamos", "How we operate")}
{blocks([(a, b, c, d, e, f) for a, b, c, d, e, f in GUIDES], "b4")}
</div></section>'''
    body += team(P2, [("Gerencia de cruceros", "Cruise division manager", "Relación con navieras y planificación de temporada.", "Cruise line relations and season planning."),
                      ("Ventas, división cruceros", "Sales, cruise division", "Propuestas de excursiones y tarifas por puerto.", "Excursion proposals and rates per port."),
                      ("Supervisión de cruceros", "Cruise supervisor", "Coordinación en muelle el día de cada escala.", "Pier coordination on every call day."),
                      ("Coordinación de cruceros", "Cruise coordinator", "Asignación de flota y guías por excursión.", "Fleet and guide assignment per excursion."),
                      ("Cuentas", "Account management", "Seguimiento comercial y facturación con la naviera.", "Commercial follow-up and invoicing with the cruise line."),
                      ("Asistencia de cruceros", "Cruise assistant", "Manifiestos, documentación y soporte al equipo.", "Manifests, documentation and team support.")])
    body += f'''<section class="sec" aria-labelledby="fq-h"><div class="wrap">
{sec_head("fq-h", "Preguntas frecuentes", "Frequently asked questions")}
<div class="faq">
<details><summary data-en="When is the cruise season in Costa Rica?">¿Cuándo es la temporada de cruceros en Costa Rica?</summary><p data-en="The main season runs roughly from October to April, with calls on both coasts. We also handle repositioning and expedition ships outside those months.">La temporada principal va aproximadamente de octubre a abril, con escalas en ambas costas. También atendemos reposicionamientos y barcos de expedición fuera de esos meses.</p></details>
<details><summary data-en="Can you guarantee the return to the ship?">¿Pueden garantizar el regreso al barco?</summary><p data-en="We plan every excursion with a time margin and a contingency plan. If something unforeseen happens, the operations team coordinates directly with the ship's agent.">Planificamos cada excursión con margen de tiempo y un plan de contingencia. Si ocurre un imprevisto, el equipo de operaciones coordina directamente con el agente del barco.</p></details>
<details><summary data-en="Do you have options for passengers with reduced mobility?">¿Tienen opciones para pasajeros con movilidad reducida?</summary><p data-en="Yes. We have buses with ramps and a specialized vehicle, and we design low-difficulty excursions.">Sí. Contamos con buses con rampa y un vehículo especializado, y diseñamos excursiones de baja dificultad.</p></details>
</div></div></section>'''
    body += cta_band(P2, "Planifiquemos su próxima temporada", "Let's plan your next season",
                     "Envíenos el calendario de escalas y le respondemos con una propuesta por puerto.",
                     "Send us your call schedule and we'll reply with a proposal per port.",
                     "Hablar con operaciones de cruceros", "Talk to cruise operations", f"{P2}contacto.html?tipo=crucero#planificar")
    body += "</main>" + footer(P2) + tail(P2)
    return body


def page_fit():
    body = head(P2, "Viajes a medida (FIT) · NexumTurismo", "Tailor-made trips (FIT) · NexumTurismo",
                "Itinerarios privados y flexibles para familias, parejas, lunas de miel y amigos en Costa Rica.")
    body += header(P2, "fit")
    body += '<main id="main">'
    body += page_hero(P2, [SV, ("Viajes a medida (FIT)", "Tailor-made trips (FIT)", None)],
                      "La libertad de viajar solo, con un experto a su lado", "The freedom of independent travel, with an expert by your side",
                      "Viajes FIT (Fully Independent Travel) para familias, amigos, lunas de miel y viajeros solos. Usted decide el ritmo; nosotros resolvemos hoteles, traslados y experiencias.",
                      "FIT (Fully Independent Travel) trips for families, friends, honeymooners and solo travelers. You set the pace; we handle hotels, transfers and experiences.",
                      f'<a class="btn btn--primary" href="{P2}contacto.html?tipo=fit#planificar" data-en="Design my itinerary">Diseñar mi itinerario</a>'
                      f'<a class="btn btn--ghost" href="{P2}tours/multidia.html" data-en="See sample programs">Ver programas de ejemplo</a>')
    body += f'''<section class="sec" aria-labelledby="uv-h"><div class="wrap">
{sec_head("uv-h", "Vacaciones únicas, en cuatro compromisos", "Unique vacations, in four commitments")}
{blocks([("", "", "Viajes personalizados", "Personalized journeys", "Cada viaje parte de sus sueños y preferencias, no de un paquete fijo.", "Each trip starts from your dreams and preferences, not a fixed package."),
         ("", "", "Flexibilidad total", "Total flexibility", "Itinerarios construidos alrededor de su agenda, con cambios posibles antes y durante el viaje.", "Itineraries built around your schedule, with changes possible before and during the trip."),
         ("", "", "Auténtico y sostenible", "Authentic & sustainable", "Cultura local real y apoyo a iniciativas ecológicas y comunitarias.", "Real local culture and support for eco-friendly and community initiatives."),
         ("", "", "Alianzas estratégicas", "Strategic partnerships", "Acuerdos con hoteles y proveedores locales que se traducen en mejores condiciones para usted.", "Agreements with hotels and local suppliers that mean better conditions for you.")], "b4")}
</div></section>
<section class="sec sec--tint" aria-labelledby="ty-h"><div class="wrap">
{sec_head("ty-h", "Para cada forma de viajar", "For every way of traveling")}
<div class="rows">
<div><h3 data-en="Honeymoons">Lunas de miel</h3><p data-en="Boutique hotels, private dinners and a calm pace between volcano and beach.">Hoteles boutique, cenas privadas y un ritmo tranquilo entre volcán y playa.</p><span class="meta" data-en="7–12 days">7–12 días</span></div>
<div><h3 data-en="Families with children">Familias con niños</h3><p data-en="Short drives, family rooms and activities matched to each child's age.">Trayectos cortos, habitaciones familiares y actividades según la edad de cada niño.</p><span class="meta" data-en="6–10 days">6–10 días</span></div>
<div><h3 data-en="Multigenerational trips">Viajes multigeneracionales</h3><p data-en="Villas or connecting rooms and options for every pace within the same day.">Villas o habitaciones conectadas y opciones para cada ritmo dentro del mismo día.</p><span class="meta" data-en="7–10 days">7–10 días</span></div>
<div><h3 data-en="Friends and active travelers">Amigos y viajeros activos</h3><p data-en="Rafting, zip lines, surf and hikes with transfers already solved.">Rafting, canopy, surf y caminatas con los traslados ya resueltos.</p><span class="meta" data-en="5–9 days">5–9 días</span></div>
<div><h3 data-en="Solo travelers">Viajeros solos</h3><p data-en="Safe routes, small-group tours and a contact available at all times.">Rutas seguras, tours en grupos pequeños y un contacto disponible en todo momento.</p><span class="meta" data-en="5–14 days">5–14 días</span></div>
</div></div></section>
<section class="sec" aria-labelledby="hw2-h"><div class="wrap two">
<div>{sec_head("hw2-h", "Cómo lo diseñamos", "How we design it", "De la idea al itinerario confirmado en cuatro pasos.", "From idea to confirmed itinerary in four steps.")}</div>
<ol class="ol-steps">
<li><span data-en="You tell us dates, who is traveling, budget and what you can't miss.">Nos cuenta fechas, quiénes viajan, presupuesto y lo que no se quiere perder.</span></li>
<li><span data-en="We send a day-by-day itinerary with hotel options and an itemized price.">Le enviamos un itinerario día por día con opciones de hotel y precio desglosado.</span></li>
<li><span data-en="We refine until it's right and book everything in your name.">Ajustamos hasta que esté perfecto y reservamos todo a su nombre.</span></li>
<li><span data-en="We welcome you at the airport and stay with you on WhatsApp until your flight home.">Lo recibimos en el aeropuerto y lo acompañamos por WhatsApp hasta su vuelo de regreso.</span></li>
</ol></div></section>'''
    body += team(P2, [("Coordinación FIT", "FIT coordinator", "Diseño de itinerarios y control de calidad de cada propuesta.", "Itinerary design and quality control of every proposal."),
                      ("Ejecutiva de cuentas", "Account manager", "Su contacto directo para cotizar, ajustar y confirmar.", "Your direct contact to quote, adjust and confirm."),
                      ("Asistente de cuentas", "Account assistant", "Reservas, vouchers y documentación de viaje.", "Bookings, vouchers and travel documents.")])
    body += cta_band(P2, "Empecemos a planificar hoy", "Let's start planning today",
                     "Cuéntenos cómo quiere viajar y le enviamos la primera versión de su itinerario.",
                     "Tell us how you want to travel and we'll send the first version of your itinerary.",
                     "Diseñar mi itinerario", "Design my itinerary", f"{P2}contacto.html?tipo=fit#planificar")
    body += "</main>" + footer(P2) + tail(P2)
    return body


def page_grupos():
    body = head(P2, "Grupos de ocio · NexumTurismo", "Leisure groups · NexumTurismo",
                "Programas para grupos en Costa Rica: observación de aves, naturaleza y aventura, fotosafari, voluntariado y familias.")
    body += header(P2, "grupos")
    body += '<main id="main">'
    body += page_hero(P2, [SV, ("Grupos de ocio", "Leisure groups", None)],
                      "Aventuras en grupo que se recuerdan juntos", "Group adventures remembered together",
                      "Bosques lluviosos, playas y una biodiversidad enorme para grupos de todo el mundo. Diseñamos itinerarios según el interés del grupo: canopy, vida silvestre, aguas termales o una pasión especial.",
                      "Rainforests, beaches and enormous biodiversity for groups from around the world. We design itineraries around the group's interest: zip lines, wildlife, hot springs or a special passion.",
                      f'<a class="btn btn--primary" href="{P2}contacto.html?tipo=grupo#planificar" data-en="Quote a group">Cotizar un grupo</a>',
                      factbox([("Especies de aves registradas en el país", "Bird species recorded in the country", "900+", ""),
                               ("Tamaño de grupo", "Group size", "10–200", ""),
                               ("Idiomas de guiado", "Guiding languages", "ES · EN · +", "")]))
    body += f'''<section class="sec" aria-labelledby="eg-h"><div class="wrap">
{sec_head("eg-h", "Experiencias exclusivas para grupos", "Exclusive group experiences", "Programas creativos con actividades fuera de lo común.", "Creative programs with uncommon activities.")}
{blocks([("", "", "Observación de aves", "Birdwatching", "Costa Rica registra más de 900 especies de aves, más que toda Norteamérica. Rutas por altitud y hábitat con guías especialistas.", "Costa Rica has recorded more than 900 bird species, more than all of North America. Routes by altitude and habitat with specialist guides."),
         ("", "", "Naturaleza y aventura", "Nature & adventure", "Volcanes, cataratas, ríos y playas en programas a la medida del nivel del grupo.", "Volcanoes, waterfalls, rivers and beaches in programs matched to the group's level."),
         ("", "", "Fotosafaris", "Photo safaris", "Salidas con guías naturalistas pensadas para fotografiar flora, fauna y paisaje.", "Outings with naturalist guides designed for photographing flora, fauna and landscapes."),
         ("", "", "Voluntariado", "Volunteering", "Proyectos comunitarios, clases de español, comidas con familias locales y costumbres tradicionales.", "Community projects, Spanish lessons, meals with local families and traditional customs."),
         ("", "", "Familias numerosas", "Large families", "Viajes para familias grandes con actividades para todas las edades.", "Trips for large families with activities for every age."),
         ("", "", "Bienestar y retiros", "Wellness & retreats", "Yoga, termales y alimentación saludable para grupos que viajan a reconectar.", "Yoga, hot springs and healthy food for groups traveling to reconnect.")])}
</div></section>
<section class="sec sec--tint" aria-labelledby="wg-h"><div class="wrap">
{sec_head("wg-h", "Por qué viajar en grupo con NexumTurismo", "Why travel as a group with NexumTurismo")}
{blocks(GUIDES, "b4")}
</div></section>'''
    body += team(P2, [("Coordinación de grupos", "Group coordinator", "Logística de rooming, transporte y guías por grupo.", "Rooming, transport and guide logistics per group."),
                      ("Ejecutiva de ventas", "Sales executive", "Propuestas para operadores, clubes y asociaciones.", "Proposals for operators, clubs and associations."),
                      ("Ejecutiva de ventas", "Sales executive", "Atención a mercados de Europa y Norteamérica.", "Coverage for European and North American markets.")])
    body += cta_band(P2, "Cuéntenos quién viaja y qué les apasiona", "Tell us who's traveling and what they love",
                     "Con el tamaño del grupo, las fechas y el interés principal le enviamos una propuesta.",
                     "With the group size, dates and main interest we'll send you a proposal.",
                     "Cotizar un grupo", "Quote a group", f"{P2}contacto.html?tipo=grupo#planificar")
    body += "</main>" + footer(P2) + tail(P2)
    return body


def page_incentivos():
    dests = [
        ("Guanacaste", "Guanacaste", "playa", "Playas del Pacífico, volcanes y parques nacionales. Canopy, cabalgatas y días de spa.", "Pacific beaches, volcanoes and national parks. Zip lines, horseback riding and spa days.",
         "Resorts de playa de gran capacidad y hoteles de lujo en Papagayo", "Large beach resorts and luxury hotels in Papagayo"),
        ("San José", "San José", "ciudad", "La capital entre montañas: mercados, museos, teatros y tours de café cercanos.", "The capital among mountains: markets, museums, theaters and nearby coffee tours.",
         "Hoteles de cadena con salones de convenciones", "Chain hotels with convention halls"),
        ("Pacífico Central", "Central Pacific", "pacifico", "Playas, bosque y fauna. Catamarán a isla Tortuga, Manuel Antonio, cuadraciclos y canopy.", "Beaches, forest and wildlife. Catamaran to Tortuga Island, Manuel Antonio, ATVs and zip lines.",
         "Resorts con marina y hoteles boutique sobre el acantilado", "Marina resorts and clifftop boutique hotels"),
        ("Arenal", "Arenal", "volcan", "El volcán como escenario: aguas termales, canopy, caminatas y puentes colgantes.", "The volcano as a backdrop: hot springs, zip lines, hikes and hanging bridges.",
         "Resorts termales con vista al volcán", "Thermal resorts with volcano views"),
        ("Tortuguero", "Tortuguero", "caribe", "Canales y selva remota con lodges ecológicos, paseos en bote y caminatas en la jungla.", "Canals and remote rainforest with eco-lodges, boat trips and jungle hikes.",
         "Eco-lodges accesibles solo por agua o avioneta", "Eco-lodges reachable only by water or small plane")]
    cards = "".join(f'''<article class="region"><div class="scene" data-scene="{sc}" data-seed="{i}"></div><div class="body">
<h3 data-en="{A(nen)}">{nes}</h3><p data-en="{A(den)}">{des}</p><p class="note"><b data-en="Lodging:">Alojamiento:</b> <span data-en="{A(hen)}">{hes}</span></p></div></article>'''
                    for i, (nes, nen, sc, des, den, hes, hen) in enumerate(dests))
    body = head(P2, "Viajes de incentivo · NexumTurismo", "Incentive trips · NexumTurismo",
                "Viajes de incentivo en Costa Rica: excursiones, eventos, team building y regalos locales para premiar a su equipo o clientes.")
    body += header(P2, "incentivos")
    body += '<main id="main">'
    body += page_hero(P2, [SV, ("Viajes de incentivo", "Incentive trips", None)],
                      "Premie a su equipo con un viaje que no va a olvidar", "Reward your team with a trip they won't forget",
                      "Costa Rica combina naturaleza, hoteles de primer nivel y experiencias con propósito. Nosotros nos ocupamos de toda la logística para que usted se ocupe de su gente.",
                      "Costa Rica combines nature, top-tier hotels and purposeful experiences. We handle all the logistics so you can focus on your people.",
                      f'<a class="btn btn--primary" href="{P2}contacto.html?tipo=incentivo#planificar" data-en="Plan an incentive program">Planificar un programa de incentivo</a>')
    body += f'''<section class="sec" aria-labelledby="wc-h"><div class="wrap two">
<div>{sec_head("wc-h", "Por qué Costa Rica para viajes de incentivo", "Why Costa Rica for incentive travel", "Un destino que ya es en sí mismo un premio, y que funciona logísticamente para grupos grandes.", "A destination that is a reward in itself, and works logistically for large groups.")}</div>
{checks([("Accesibilidad", "Accessibility", "Dos aeropuertos internacionales (San José y Liberia) con vuelos directos desde Estados Unidos, Canadá y Europa.", "Two international airports (San José and Liberia) with direct flights from the US, Canada and Europe."),
         ("Belleza natural", "Natural beauty", "Bosques lluviosos, volcanes, playas y una biodiversidad excepcional.", "Rainforests, volcanoes, beaches and exceptional biodiversity."),
         ("Aventura para integrar equipos", "Adventure that builds teams", "Canopy, rafting, caminatas y tours de fauna que unen al grupo.", "Zip lines, rafting, hikes and wildlife tours that bring the group together."),
         ("Liderazgo en sostenibilidad", "Leadership in sustainability", "Un referente mundial en turismo responsable.", "A global reference in responsible tourism."),
         ("Hoteles de alto nivel", "High-end hotels", "Resorts y hoteles con servicios de lujo y espacios para eventos.", "Resorts and hotels with luxury amenities and event spaces."),
         ("Estabilidad y seguridad", "Stability and safety", "Una democracia estable, sin ejército desde 1948, y gente amable.", "A stable democracy, without an army since 1948, and welcoming people."),
         ("Cultura viva", "Living culture", "Cocina local, música y arte para momentos auténticos.", "Local cuisine, music and art for authentic moments.")])}
</div></section>
<section class="sec band" aria-labelledby="is-h"><div class="wrap">
{sec_head("is-h", "Nuestros servicios de incentivo", "Our incentive services")}
{blocks([("", "", "Excursiones", "Excursions", "Tours a la medida, de la playa al bosque, que mezclan aventura y descanso.", "Custom tours, from beach to forest, mixing adventure and rest."),
         ("", "", "Personal especializado e inspecciones", "Specialized staff & site inspections", "Acompañamiento en la planificación y visitas previas para validar cada sede.", "Planning support and site visits to validate every venue."),
         ("", "", "Transporte y guías especializados", "Transport & specialized guides", "Flota confiable y guías que conocen a fondo cada destino.", "A reliable fleet and guides who know every destination in depth."),
         ("", "", "Eventos, sedes y decoración", "Events, venues & décor", "Selección de sede, ambientación y entretenimiento para cada noche del programa.", "Venue selection, styling and entertainment for every night of the program."),
         ("", "", "Team building y proyectos solidarios", "Team building & give-back projects", "Actividades de equipo que además apoyan a comunidades locales.", "Team activities that also support local communities."),
         ("", "", "Regalos locales personalizados", "Personalized local gifts", "Detalles inspirados en cada región, hechos por artesanos costarricenses.", "Region-inspired gifts made by Costa Rican artisans.")])}
</div></section>
<section class="sec" aria-labelledby="md-h"><div class="wrap">
{sec_head("md-h", "Destinos principales", "Main destinations", "Cinco escenarios probados para programas de incentivo, combinables entre sí.", "Five proven settings for incentive programs, which can be combined.")}
<div class="regions">{cards}</div></div></section>'''
    body += team(P2, [("Gerencia de incentivos", "Incentive manager", "Estrategia del programa y relación con la empresa cliente.", "Program strategy and client company relationship."),
                      ("Supervisión de incentivos", "Incentive supervisor", "Ejecución en sitio y control de cada actividad.", "On-site execution and control of every activity."),
                      ("Asistente de cuentas", "Account assistant", "Rooming, vuelos y documentación de participantes.", "Rooming, flights and participant documentation.")])
    body += cta_band(P2, "Diseñemos el programa de su próximo premio", "Let's design your next reward program",
                     "Cuéntenos el número de participantes, las fechas y el objetivo del viaje.",
                     "Tell us the number of participants, the dates and the goal of the trip.",
                     "Planificar un programa", "Plan a program", f"{P2}contacto.html?tipo=incentivo#planificar",
                     "Ver servicios corporativos", "See corporate services", f"{P2}servicios/corporativos.html")
    body += "</main>" + footer(P2) + tail(P2)
    return body


def page_corporativo():
    body = head(P2, "Servicios corporativos · NexumTurismo", "Corporate services · NexumTurismo",
                "Planificación de eventos corporativos en Costa Rica: reuniones, convenciones, congresos, team building y transporte VIP.")
    body += header(P2, "corporativo")
    body += '<main id="main">'
    body += page_hero(P2, [SV, ("Servicios corporativos", "Corporate services", None)],
                      "Especialistas en eventos corporativos", "Corporate event specialists",
                      "Un equipo con experiencia en turismo y gestión de eventos, proactivo y comprometido con la excelencia, para eventos grandes, medianos y pequeños dentro y fuera de Costa Rica.",
                      "A team experienced in tourism and event management, proactive and committed to excellence, for large, medium and small events in and outside Costa Rica.",
                      f'<a class="btn btn--primary" href="{P2}contacto.html?tipo=incentivo#planificar" data-en="Plan a corporate event">Planificar un evento corporativo</a>')
    types = [("Reuniones", "Meetings"), ("Convenciones", "Conventions"), ("Congresos", "Congresses"),
             ("Eventos sociales", "Social events"), ("Team building", "Team building"), ("Tours para delegaciones", "Delegation tours")]
    chips = "".join(f'<span class="chip" data-en="{A(en)}">{es}</span>' for es, en in types)
    body += f'''<section class="sec" aria-labelledby="cl-h"><div class="wrap">
{sec_head("cl-h", "Eventos de todos los tamaños", "Events of every size", "Coordinamos eventos para empresas nacionales e internacionales.", "We coordinate events for national and international companies.")}
<div class="chips">{chips}</div></div></section>
<section class="sec sec--tint" aria-labelledby="cs-h"><div class="wrap">
{sec_head("cs-h", "Servicios corporativos", "Corporate services")}
{blocks([("Lineamientos generales", "General guidelines", "Planificación y gestión de eventos", "Event planning & management", "Logística de principio a fin: sede, presupuesto, agenda y ejecución.", "End-to-end logistics: venue, budget, schedule and execution."),
         ("Lineamientos de oferta", "Tourism offer guidelines", "Búsqueda de sedes", "Venue sourcing", "Espacios según capacidad, acceso y servicios requeridos.", "Spaces matched to capacity, access and required services."),
         ("Lineamientos de oferta", "Tourism offer guidelines", "Hospedaje y transporte", "Lodging & transport", "Viajes, alojamiento, traslados y transporte terrestre de los participantes.", "Travel, lodging, transfers and ground transport for participants."),
         ("Calidad y servicio", "Quality & service", "Soporte en sitio", "On-site support", "Personal y recursos para gestionar el evento en tiempo real.", "Staff and resources to manage the event in real time."),
         ("Calidad y servicio", "Quality & service", "Soluciones tecnológicas", "Technology solutions", "Equipo audiovisual, plataformas para eventos virtuales e híbridos y soporte técnico.", "Audiovisual equipment, virtual and hybrid event platforms and technical support."),
         ("Lineamientos socioeconómicos", "Social & economic guidelines", "Alimentación y hospitalidad", "Catering & hospitality", "Servicio de alimentos y bebidas que respeta cada requerimiento dietético.", "Food and beverage service that meets every dietary requirement.")])}
</div></section>
<section class="sec" aria-labelledby="cp-h"><div class="wrap two">
<div>{sec_head("cp-h", "Eventos con prácticas sostenibles", "Events with sustainable practices", "Opciones de bajo impacto que apoyan la economía local y los ecosistemas.", "Low-impact options that support the local economy and ecosystems.")}</div>
{checks([("Proveedores locales", "Local suppliers", "Alimentos, decoración y regalos de productores costarricenses.", "Food, décor and gifts from Costa Rican producers."),
         ("Menos residuos", "Less waste", "Materiales reutilizables y reducción de plásticos de un solo uso.", "Reusable materials and less single-use plastic."),
         ("Compensación de huella", "Footprint offsetting", "Cálculo y compensación de emisiones del evento a solicitud.", "Event emissions calculated and offset on request.")])}
</div></section>'''
    body += team(P2, [("Ejecutiva de ventas corporativas", "Corporate sales executive", "Su contacto para propuesta, contrato y seguimiento.", "Your contact for proposal, contract and follow-up."),
                      ("Producción de eventos", "Event production", "Montaje, proveedores y guion del evento.", "Setup, suppliers and run of show."),
                      ("Transporte VIP", "VIP transport", "Flota ejecutiva y coordinación de traslados.", "Executive fleet and transfer coordination.")])
    body += cta_band(P2, "Cuéntenos su evento", "Tell us about your event",
                     "Tipo de evento, número de asistentes y fechas tentativas son suficientes para empezar.",
                     "Event type, number of attendees and tentative dates are enough to start.",
                     "Planificar un evento", "Plan an event", f"{P2}contacto.html?tipo=incentivo#planificar",
                     "Ver viajes de incentivo", "See incentive trips", f"{P2}servicios/incentivos.html")
    body += "</main>" + footer(P2) + tail(P2)
    return body
