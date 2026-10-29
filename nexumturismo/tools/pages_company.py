# -*- coding: utf-8 -*-
"""Company branch: who we are, profile, sustainability, agencies, collection, contact."""
from ntsite import (A, E, P, H, S, ph, head, header, page_hero, sec_head, cta_band, footer, tail, checks, team, CHECK)
from pages_services import blocks, factbox

AB = ("Nosotros", "About us", None)


def glist(items):
    return '<ul class="glist">' + "".join(f'<li>{CHECK}<span data-en="{A(en)}">{es}</span></li>' for es, en in items) + "</ul>"


def page_quienes():
    p = "../"
    body = head(p, "Quiénes somos · NexumTurismo", "Who we are · NexumTurismo",
                "Historia, valores y visión de NexumTurismo, DMC en Costa Rica.")
    body += header(p, "quienes")
    body += '<main id="main">'
    body += page_hero(p, [AB, ("Quiénes somos", "Who we are", None)],
                      "Un legado de servicio en un país que nació para recibir viajeros", "A legacy of service in a country made for welcoming travelers",
                      "Somos una empresa de gestión de destinos en Costa Rica: diseñamos y operamos viajes con un foco absoluto en el servicio, la sostenibilidad y superar expectativas.",
                      "We are a destination management company in Costa Rica: we design and operate trips with an absolute focus on service, sustainability and exceeding expectations.",
                      f'<a class="btn btn--primary" href="{p}contacto.html" data-en="Get in touch">Contáctenos</a>'
                      f'<a class="btn btn--ghost" href="{p}nosotros/perfil.html" data-en="Company profile">Perfil de la empresa</a>')
    body += f'''<section class="sec" aria-labelledby="hi-h"><div class="wrap two">
<div>{sec_head("hi-h", "Nuestros comienzos", "Our beginnings", "Costa Rica eligió la paz, la educación y la naturaleza. Ese mismo camino abrió la puerta al turismo.", "Costa Rica chose peace, education and nature. That same path opened the door to tourism.")}</div>
<ol class="timeline">
<li><time>1948</time><p data-en="Costa Rica abolishes its army and invests in education and health, the foundation of the country's stability.">Costa Rica abolió su ejército y apostó por la educación y la salud, la base de la estabilidad del país.</p></li>
<li><time data-en="1970s">Década de 1970</time><p data-en="The first national parks are created. Travelers from around the world begin to notice a small Central American country that stands out for its nature, peace and relaxed way of life.">Se crean los primeros parques nacionales. Viajeros de todo el mundo empiezan a fijarse en un pequeño país centroamericano que destaca por su naturaleza, su paz y su estilo de vida tranquilo.</p></li>
<li><time>{ph("[Año de fundación]")}</time><p data-en="NexumTurismo is founded to give travelers what was missing: one operator that designs, books and accompanies the whole trip to the standard they expect.">Nace NexumTurismo para dar a los viajeros lo que faltaba: un operador que diseñe, reserve y acompañe el viaje completo con el estándar que esperan.</p></li>
<li><time data-en="Today">Hoy</time><p data-en="We serve travelers, agencies, companies and cruise lines with our own fleet, certified guides and a 24/7 operations team.">Atendemos a viajeros, agencias, empresas y líneas de crucero con flota propia, guías certificados y un equipo de operaciones 24/7.</p></li>
</ol></div></section>
<section class="sec sec--tint" aria-labelledby="va-h"><div class="wrap">
{sec_head("va-h", "Nuestros valores y compromiso", "Our values and commitment")}
{blocks([("", "", "Acento en el servicio", "Accent on service", "Superar las expectativas del cliente, mejorar continuamente nuestros procesos y servicios y sostener buenas prácticas de sostenibilidad.", "Exceed client expectations, continuously improve our processes and services and uphold good sustainability practices."),
         ("", "", "Compromiso con la sostenibilidad", "Commitment to sustainability", "Sabemos que nuestra actividad afecta a la naturaleza y a la sociedad. Por eso aplicamos prácticas sostenibles en toda la operación.", "We know our activity affects nature and society. That's why we apply sustainable practices across the whole operation."),
         ("", "", "Innovación y futuro", "Innovation and the future", "Invertimos en tecnología, protocolos de salud para proteger a nuestros clientes y formación continua de nuestros expertos de viaje.", "We invest in technology, health protocols to protect our clients and ongoing training for our travel experts.")])}
</div></section>
<section class="sec" aria-labelledby="pl2-h"><div class="wrap">
{sec_head("pl2-h", "Lo que prometemos", "What we promise")}
<div class="pledges">
<blockquote data-en="Our service and quality will live up to the attractions we take you to.">Nuestro servicio y nuestra calidad estarán a la altura de los atractivos a los que lo llevamos.</blockquote>
<blockquote data-en="What we promise in our materials and offers is exactly what you will get.">Lo que prometemos en nuestros materiales y ofertas es exactamente lo que va a recibir.</blockquote>
</div></div></section>'''
    body += cta_band(p, "Creemos juntos recuerdos inolvidables", "Let's create unforgettable memories together",
                     "Súmese a una forma de viajar sostenible, con impacto y memorable.",
                     "Join a way of traveling that is sustainable, meaningful and memorable.",
                     "Contáctenos", "Get in touch", f"{p}contacto.html", "Ver sostenibilidad", "See sustainability", f"{p}sostenibilidad.html")
    body += "</main>" + footer(p) + tail(p)
    return body


def page_perfil():
    p = "../"
    body = head(p, "Perfil de la empresa · NexumTurismo", "Company profile · NexumTurismo",
                "Ficha corporativa de NexumTurismo: líneas de servicio, oficinas, departamentos, documentos y canales.")
    body += header(p, "perfil")
    body += '<main id="main">'
    body += page_hero(p, [AB, ("Perfil de la empresa", "Company profile", None)],
                      "Perfil de la empresa", "Company profile",
                      "La ficha que piden agencias, navieras y departamentos de compras: quiénes somos, qué operamos, dónde estamos y cómo trabajamos.",
                      "The fact sheet agencies, cruise lines and procurement teams ask for: who we are, what we operate, where we are and how we work.",
                      aside=factbox([("Razón social", "Legal name", ph("[Razón social]"), ""),
                                     ("Fundación", "Founded", ph("[Año]"), ""),
                                     ("Oficinas", "Offices", "San José · Liberia", ""),
                                     ("Idiomas de atención", "Service languages", "ES · EN", ""),
                                     ("Colaboradores", "Staff", ph("[000]"), "")]))
    body += f'''<section class="sec" aria-labelledby="dp-h"><div class="wrap">
{sec_head("dp-h", "Departamentos", "Departments", "Cada línea de negocio tiene su propio equipo y un responsable con nombre.", "Each business line has its own team and a named lead.")}
<div class="rows">
<div><h3 data-en="Cruise operations">Operación de cruceros</h3><p data-en="Shore excursions, turnarounds and pre/post programs at every port.">Excursiones en tierra, turnarounds y programas pre/post en todos los puertos.</p><a class="txtlink" href="{p}servicios/cruceros.html" data-en="View">Ver</a></div>
<div><h3 data-en="FIT">FIT</h3><p data-en="Private, tailor-made trips for independent travelers and agencies.">Viajes privados a la medida para viajeros independientes y agencias.</p><a class="txtlink" href="{p}servicios/viajes-a-medida.html" data-en="View">Ver</a></div>
<div><h3 data-en="Groups">Grupos</h3><p data-en="Leisure and special-interest group circuits.">Circuitos para grupos de ocio y de interés especial.</p><a class="txtlink" href="{p}servicios/grupos.html" data-en="View">Ver</a></div>
<div><h3 data-en="Incentives & corporate">Incentivos y corporativo</h3><p data-en="Reward trips, meetings, conventions and events.">Viajes de premiación, reuniones, convenciones y eventos.</p><a class="txtlink" href="{p}servicios/incentivos.html" data-en="View">Ver</a></div>
<div><h3 data-en="Operations & fleet">Operaciones y flota</h3><p data-en="24/7 coordination, transport and guide assignment.">Coordinación 24/7, transporte y asignación de guías.</p><span class="meta">{ph("[00 vehículos]")}</span></div>
<div><h3 data-en="Sustainability">Sostenibilidad</h3><p data-en="Policy, certifications, annual report and supplier code.">Política, certificaciones, reporte anual y código de proveedores.</p><a class="txtlink" href="{p}sostenibilidad.html" data-en="View">Ver</a></div>
</div></div></section>
<section class="sec sec--tint" aria-labelledby="dc-h"><div class="wrap two">
<div>{sec_head("dc-h", "Documentos corporativos", "Corporate documents", "Disponibles a solicitud para procesos de homologación de proveedores.", "Available on request for supplier onboarding processes.")}</div>
{checks([("Política de sostenibilidad", "Sustainability policy", "Compromisos ambientales, sociales y económicos.", "Environmental, social and economic commitments."),
         ("Reporte anual de sostenibilidad", "Annual sustainability report", "Resultados del último año, en español e inglés.", "Results for the last year, in Spanish and English."),
         ("Código de ética para proveedores", "Supplier code of ethics", "Principios que pedimos a cada proveedor.", "Principles we ask of every supplier."),
         ("Pólizas y permisos", "Insurance and permits", "Seguros de responsabilidad y licencias de operación turística.", "Liability insurance and tour operating licenses.")])}
</div></section>
<section class="sec" aria-labelledby="ca-h"><div class="wrap two">
<div>{sec_head("ca-h", "Trabaje con nosotros", "Work with us", "Buscamos guías, choferes, coordinadores y ejecutivos que disfruten mostrar Costa Rica.", "We look for guides, drivers, coordinators and executives who love showing Costa Rica.")}</div>
<div class="prose"><p data-en="Send your résumé to the email below, mentioning the area you're interested in.">Envíe su hoja de vida al correo indicado, mencionando el área que le interesa.</p><p><b>{ph("[talento@nexumturismo.com]")}</b></p></div>
</div></section>'''
    body += cta_band(p)
    body += "</main>" + footer(p) + tail(p)
    return body


def page_sostenibilidad():
    p = ""
    general = [("Reafirmar el compromiso de sostenibilidad en toda la empresa.", "Reaffirm the sustainability commitment across the company."),
               ("Actuar con ética y respetar nuestros valores.", "Act ethically and uphold our values."),
               ("Cumplir la normativa nacional vigente.", "Comply with national regulations."),
               ("Rechazar y denunciar la explotación sexual de personas menores de edad.", "Reject and report the sexual exploitation of minors."),
               ("Proteger la biodiversidad y los hábitats naturales.", "Protect biodiversity and natural habitats."),
               ("Resguardar el patrimonio arqueológico.", "Safeguard archaeological heritage."),
               ("Integrar la cultura local en nuestras instalaciones.", "Integrate local culture into our facilities.")]
    social = [("Promover la tolerancia y el respeto por las comunidades locales.", "Promote tolerance and respect for local communities."),
              ("Apoyar el crecimiento socioeconómico de las zonas donde operamos.", "Support socioeconomic growth where we operate."),
              ("Contratar de forma inclusiva.", "Hire inclusively."),
              ("Proteger la salud y la seguridad de nuestro personal.", "Protect our staff's health and safety."),
              ("Impulsar el desarrollo profesional del equipo.", "Foster the team's professional development."),
              ("Invitar a todos a participar en las iniciativas de sostenibilidad.", "Invite everyone to take part in sustainability initiatives.")]
    oferta = [("Brindar un servicio excelente.", "Provide excellent service."),
              ("Diseñar experiencias memorables.", "Design memorable experiences."),
              ("Ser transparentes con nuestros clientes.", "Be transparent with our clients."),
              ("Investigar productos y mercados.", "Research products and markets."),
              ("Tratar a todos los clientes por igual.", "Treat all clients equally."),
              ("Ofrecer experiencias compartidas con las comunidades.", "Offer experiences shared with communities."),
              ("Alinear los productos con el desarrollo de las comunidades.", "Align products with community development goals.")]
    calidad = [("Evaluar el desempeño de forma continua.", "Evaluate performance continuously."),
               ("Entregar un servicio de calidad constante.", "Deliver consistently high-quality service."),
               ("Mejorar con el ciclo Planificar-Hacer-Verificar-Actuar.", "Improve with the Plan-Do-Check-Act cycle.")]
    tips = [("Respete la cultura y las leyes locales.", "Respect local culture and laws."),
            ("Ahorre agua y energía.", "Save water and energy."),
            ("Siga las indicaciones de guías y personal en áreas protegidas.", "Follow guides and staff in protected areas."),
            ("Compre productos locales.", "Buy local products."),
            ("No compre artículos hechos con partes de animales o maderas en peligro.", "Don't buy items made from animal parts or endangered wood."),
            ("Prefiera productos amigables con el ambiente.", "Choose eco-friendly products."),
            ("Nunca alimente a la fauna silvestre.", "Never feed wildlife."),
            ("Deposite los residuos en su lugar.", "Dispose of waste properly."),
            ("Reporte cualquier caso de explotación infantil al personal o a las autoridades.", "Report any child exploitation to staff or the authorities."),
            ("Reporte el consumo o venta de sustancias ilegales.", "Report the use or sale of illegal substances.")]
    heritage = [("Respete el modo de vida de la comunidad.", "Respect the community's way of life."),
                ("Apoye a los artesanos sin copiar sus creaciones culturales.", "Support artisans without copying their cultural creations."),
                ("Conozca otras culturas sin discriminar.", "Learn about other cultures without discrimination."),
                ("Si tiene dudas, pregunte a su guía.", "If in doubt, ask your guide."),
                ("Llévese todos sus residuos; no los deje en la comunidad.", "Take all your waste with you; don't leave it in the community.")]

    def gcard(t_es, t_en, items):
        return f'<div class="gcard"><h3 data-en="{A(t_en)}">{t_es}</h3><span class="count" data-en="{len(items)} guidelines">{len(items)} lineamientos</span>{glist(items)}</div>'

    certs = "".join(f'<span class="chip ph">{c}</span>' for c in
                    ["[Certificación de Sostenibilidad Turística · nivel]", "[Bandera Azul Ecológica]", "[Carbono neutral]", "[Código de conducta contra la explotación sexual]"])
    body = head(p, "Sostenibilidad · NexumTurismo", "Sustainability · NexumTurismo",
                "Política, lineamientos, reportes, certificaciones y guía para el viajero sostenible de NexumTurismo.")
    body += header(p, "sostenibilidad")
    body += '<main id="main">'
    body += page_hero(p, [("Sostenibilidad", "Sustainability", None)],
                      "Nuestro compromiso con el planeta", "Our commitment to the planet",
                      "La sostenibilidad guía cada área de la operación. Buscamos que cada viaje deje un efecto positivo en el ambiente y en las comunidades que lo hacen posible.",
                      "Sustainability guides every area of the operation. We want every trip to leave a positive effect on the environment and on the communities that make it possible.",
                      f'<a class="btn btn--primary" href="#viajero" data-en="Sustainable traveler guide">Guía del viajero sostenible</a>'
                      f'<a class="btn btn--ghost" href="#reportes" data-en="Reports and documents">Reportes y documentos</a>')
    body += f'''<section class="sec" aria-labelledby="po-h"><div class="wrap two">
<div>{sec_head("po-h", "Política de sostenibilidad", "Sustainability policy")}</div>
<div class="prose"><p data-en="Our sustainability management aims to raise client satisfaction, comply with the law and prevent negative environmental and social effects.">Nuestra gestión sostenible busca elevar la satisfacción del cliente, cumplir la ley y prevenir efectos ambientales y sociales negativos.</p>
<p data-en="We contribute to the communities where we operate, and we know that contribution is part of our own economic success.">Contribuimos con las comunidades donde operamos, y sabemos que esa contribución es parte de nuestro propio éxito económico.</p></div>
</div></section>
<section class="sec sec--tint" aria-labelledby="li-h"><div class="wrap">
{sec_head("li-h", "Lineamientos sostenibles", "Sustainable guidelines", "La herramienta práctica de la política: cada área los aplica para reducir impactos y riesgos y aumentar los efectos positivos.", "The practical tool of the policy: every area applies them to reduce impacts and risks and increase positive effects.")}
<div class="ggrid">{gcard("Generales", "General", general)}{gcard("Sociales y económicos", "Social & economic", social)}{gcard("Oferta turística", "Tourism product", oferta)}{gcard("Calidad y servicio", "Quality & service", calidad)}</div>
</div></section>
<section class="sec" id="reportes" aria-labelledby="re-h"><div class="wrap">
{sec_head("re-h", "Reportes, código y certificaciones", "Reports, code and certifications")}
<div class="rows">
<div><h3 data-en="Annual sustainability report">Reporte anual de sostenibilidad</h3><p data-en="Environmental and social results for the year, in Spanish and English.">Resultados ambientales y sociales del año, en español e inglés.</p><span class="meta">{ph("[PDF ES · EN]")}</span></div>
<div><h3 data-en="Supplier code of ethics">Código de ética para proveedores</h3><p data-en="Principles that encourage our suppliers to act ethically, responsibly and sustainably.">Principios que invitan a nuestros proveedores a actuar con ética, responsabilidad y sostenibilidad.</p><span class="meta">{ph("[PDF]")}</span></div>
<div><h3 data-en="Flight footprint offsetting">Compensación de la huella del vuelo</h3><p data-en="We show you how to calculate and offset the emissions of your flight to Costa Rica.">Le mostramos cómo calcular y compensar las emisiones de su vuelo a Costa Rica.</p><span class="meta" data-en="On request">A solicitud</span></div>
</div>
<p class="note" style="margin:1.6rem 0 .8rem" data-en="Certifications (replace with the real ones and their level):">Certificaciones (reemplazar por las reales y su nivel):</p>
<div class="chips">{certs}</div>
</div></section>
<section class="sec band" id="viajero" aria-labelledby="vj-h"><div class="wrap">
{sec_head("vj-h", "Sea un viajero sostenible", "Be a sustainable traveler", "Diez gestos que hacen la diferencia en cada destino.", "Ten gestures that make a difference in every destination.")}
<div class="ggrid"><div>{glist(tips[:5])}</div><div>{glist(tips[5:])}</div></div>
</div></section>
<section class="sec" aria-labelledby="pc-h"><div class="wrap two">
<div>{sec_head("pc-h", "Al visitar sitios de patrimonio cultural", "When visiting cultural heritage sites")}</div>
{glist(heritage)}
</div></section>
<section class="sec sec--tint" aria-labelledby="fb-h"><div class="wrap two">
<div>{sec_head("fb-h", "Su opinión nos ayuda a mejorar", "Your feedback helps us improve", "Comentarios sobre nuestra gestión sostenible, nuestros reportes o cualquier impacto de nuestra operación en una comunidad: queremos saberlo.", "Comments on our sustainability management, our reports or any impact of our operation on a community: we want to know.")}</div>
<div class="prose"><p data-en="Write to the sustainability team:">Escriba al equipo de sostenibilidad:</p><p><b>{ph("[sostenibilidad@nexumturismo.com]")}</b></p>
<p><a class="btn btn--ghost" href="contacto.html" data-en="Send a comment">Enviar un comentario</a></p></div>
</div></section>'''
    body += cta_band(p)
    body += "</main>" + footer(p) + tail(p)
    return body


def page_agencias():
    p = ""
    body = head(p, "Agencias y travel advisors · NexumTurismo", "Agencies & travel advisors · NexumTurismo",
                "Programa para agencias, travel advisors y redes de lujo: tarifas, operación con su marca y soporte en ruta.")
    body += header(p, "agencias")
    body += '<main id="main">'
    body += page_hero(p, [AB, ("Agencias y travel advisors", "Agencies & travel advisors", None)],
                      "Su socio local en Costa Rica", "Your local partner in Costa Rica",
                      "Para agencias, travel advisors, redes de lujo y operadores mayoristas. Cotizamos rápido, operamos con su marca en primer plano y facturamos con la claridad que su contabilidad espera.",
                      "For travel agencies, advisors, luxury networks and wholesale operators. We quote fast, operate with your brand up front and invoice with the clarity your accounting expects.",
                      f'<a class="btn btn--primary" href="contacto.html?tipo=agencia#planificar" data-en="Request agency rates">Solicitar tarifas para agencias</a>'
                      f'<a class="btn btn--ghost" href="coleccion.html" data-en="See the luxury collection">Ver la colección de lujo</a>')
    body += f'''<section class="sec" aria-labelledby="ad-h"><div class="wrap">
{sec_head("ad-h", "Dos programas, un mismo estándar", "Two programs, one standard")}
<div class="ggrid">
<div class="gcard"><h3 data-en="Luxury advisors">Advisors de lujo</h3><p data-en="For members of luxury travel networks who need a DMC that meets their standards and protects the client relationship.">Para miembros de redes de viaje de lujo que necesitan un DMC a la altura de sus estándares y que cuide la relación con su cliente.</p>
{checks([("Amenidades y beneficios para sus clientes", "Amenities and perks for your clients", "Upgrades, bienvenidas especiales y experiencias privadas según disponibilidad.", "Upgrades, special welcomes and private experiences subject to availability."),
         ("Reporte de servicio", "Service report", "Encuesta posviaje compartida con usted.", "Post-trip survey shared with you.")])}</div>
<div class="gcard"><h3 data-en="Travel experts">Expertos de viaje</h3><p data-en="For agencies and operators that sell Costa Rica regularly and want a reliable local partner.">Para agencias y operadores que venden Costa Rica de forma recurrente y quieren un socio local confiable.</p>
{checks([("Tarifas netas y comisiones claras", "Clear net rates and commissions", "Condiciones por escrito desde la primera cotización.", "Written terms from the first quote."),
         ("Viajes de familiarización", "Familiarization trips", "Recorridos para conocer destinos y hoteles en persona.", "Trips to experience destinations and hotels in person.")])}</div>
</div></div></section>
<section class="sec sec--tint" aria-labelledby="ag-h"><div class="wrap">
{sec_head("ag-h", "Lo que resolvemos por usted", "What we take care of for you")}
{blocks([("", "", "Respuesta comercial ágil", "Fast commercial response", "Propuestas con opciones de hotel y precio listas para presentar a su cliente.", "Proposals with hotel and price options ready to present to your client."),
         ("", "", "Facturación sin fricción", "Frictionless invoicing", "Procesos pensados para agencias de Norteamérica, Europa y Latinoamérica.", "Processes built for agencies in North America, Europe and Latin America."),
         ("", "", "Su marca primero", "Your brand first", "Itinerarios y documentos de viaje que pueden ir con su identidad.", "Itineraries and travel documents that can carry your branding."),
         ("", "", "Bienvenida y repaso del programa", "Welcome and program briefing", "Recepción en el aeropuerto y explicación del itinerario el primer día.", "Airport welcome and an itinerary walkthrough on day one."),
         ("", "", "Soporte en ruta 24/7", "24/7 on-the-road support", "Sus clientes siempre tienen a quién escribir por WhatsApp.", "Your clients always have someone to message on WhatsApp."),
         ("", "", "Visibilidad para usted", "Visibility for you", "Le informamos de cualquier incidencia antes de que su cliente tenga que hacerlo.", "We tell you about any issue before your client has to.")])}
</div></section>'''
    body += cta_band(p, "Hablemos de su próximo cliente", "Let's talk about your next client",
                     "Envíenos la solicitud y le respondemos con una propuesta lista para presentar.",
                     "Send us the request and we'll reply with a proposal ready to present.",
                     "Solicitar tarifas para agencias", "Request agency rates", "contacto.html?tipo=agencia#planificar")
    body += "</main>" + footer(p) + tail(p)
    return body


def page_coleccion():
    p = ""
    dests = [("Volcán Arenal", "Arenal Volcano", "volcan"), ("Tierras altas centrales", "Central Highlands", "valle"),
             ("Playas de Guanacaste", "Guanacaste beaches", "playa"), ("Tierras altas de Guanacaste", "Guanacaste Highlands", "volcan"),
             ("Jacó", "Jacó", "pacifico"), ("Manuel Antonio", "Manuel Antonio", "pacifico"), ("Monteverde", "Monteverde", "nuboso"),
             ("Golfo de Nicoya", "Gulf of Nicoya", "playa"), ("Península de Osa", "Osa Peninsula", "selva"), ("Río Pacuare", "Pacuare River", "rio"),
             ("San José", "San José", "ciudad"), ("Caribe Sur", "South Caribbean", "caribe"), ("Pacífico Sur", "South Pacific", "selva")]
    tiles = "".join(f'''<article class="dest"><div class="scene" data-scene="{sc}" data-seed="{i}"></div><div class="body"><h3 data-en="{A(en)}">{es}</h3>
<p><a class="txtlink" href="contacto.html?tipo=fit&tour={A(es)}#planificar" data-en="Stays and experiences">Estancias y experiencias</a></p></div></article>'''
                    for i, (es, en, sc) in enumerate(dests))
    cats = [("Aventura", "Adventure"), ("Conservación", "Conservation"), ("Cultural", "Cultural"), ("Educación", "Education"),
            ("Experiencias", "Experiences"), ("Gastronomía y bebidas", "Food & drink"), ("Hotel", "Hotel"), ("Naturaleza", "Nature"),
            ("Aventura suave", "Soft adventure"), ("Bienestar", "Wellness")]
    chips = "".join(f'<span class="chip" data-en="{A(en)}">{es}</span>' for es, en in cats)
    stays = [("Lodge de bosque nuboso con spa", "Cloud forest lodge & spa", "nuboso", "Cabañas de montaña rodeadas de áreas protegidas, con senderos privados y spa.", "Mountain cabins surrounded by protected areas, with private trails and a spa."),
             ("Eco-lodge en el río Pacuare", "Pacuare River eco-lodge", "rio", "Suites en la selva a las que se llega en balsa, sin carreteras ni ruido.", "Rainforest suites reached by raft, with no roads and no noise."),
             ("Refugio de lujo frente al Arenal", "Luxury hideaway facing Arenal", "volcan", "Villas con arte local, piscinas privadas y el volcán desde la cama.", "Villas with local art, private pools and the volcano from your bed."),
             ("Resort termal con vista al volcán", "Thermal resort with volcano views", "volcan", "Suites y villas en el bosque, con aguas termales naturales.", "Suites and villas in the forest, with natural hot springs.")]
    cards = "".join(f'''<article class="region"><div class="scene" data-scene="{sc}" data-seed="{i+3}"></div><div class="body"><h3 data-en="{A(en)}">{es}</h3><p data-en="{A(den)}">{des}</p></div></article>'''
                    for i, (es, en, sc, des, den) in enumerate(stays))
    body = head(p, "Colección de lujo · NexumTurismo", "Luxury collection · NexumTurismo",
                "La colección de lujo de NexumTurismo: alojamientos y experiencias seleccionados en 13 destinos de Costa Rica.")
    body += header(p, "coleccion")
    body += '<main id="main">'
    body += page_hero(p, [AB, ("Colección de lujo", "Luxury collection", None)],
                      "La experiencia costarricense, en su versión más exclusiva", "The Costa Rican experience, at its most exclusive",
                      "Alojamientos y experiencias que seleccionamos a mano en 13 destinos, con un experto en lujo que planifica cada detalle con usted.",
                      "Hand-picked stays and experiences in 13 destinations, with a luxury expert who plans every detail with you.",
                      f'<a class="btn btn--primary" href="contacto.html?tipo=fit#planificar" data-en="Book a one-on-one consultation">Agendar una consulta personal</a>'
                      f'<a class="btn btn--ghost" href="agencias.html" data-en="I am a travel advisor">Soy travel advisor</a>')
    body += f'''<section class="sec" aria-labelledby="ts-h"><div class="wrap">
{sec_head("ts-h", "Selección del momento", "Current selection", "Estilos de estancia que más piden nuestros viajeros. Le proponemos la propiedad exacta según fechas y disponibilidad.", "The stay styles our travelers ask for most. We suggest the exact property based on dates and availability.")}
<div class="regions" style="grid-template-columns:repeat(4,minmax(0,1fr))">{cards}</div></div></section>
<section class="sec sec--tint" aria-labelledby="ad2-h"><div class="wrap">
{sec_head("ad2-h", "Elija su aventura", "Choose your adventure", "Trece destinos, cada uno con su selección de estancias y experiencias.", "Thirteen destinations, each with its own selection of stays and experiences.")}
<div class="dests">{tiles}</div></div></section>
<section class="sec" aria-labelledby="ex2-h"><div class="wrap two">
<div>{sec_head("ex2-h", "Tipos de experiencia", "Experience types", "Combinamos categorías para armar días que tienen sentido.", "We combine categories to build days that make sense.")}</div>
<div class="chips">{chips}</div></div></section>
<section class="sec band" aria-labelledby="lx-h"><div class="wrap">
{sec_head("lx-h", "Lo que incluye viajar con la colección", "What traveling with the collection includes")}
{blocks([("", "", "Consulta personal", "One-on-one consultation", "Una llamada con su experto en lujo para entender cómo quiere viajar.", "A call with your luxury expert to understand how you want to travel."),
         ("", "", "Beneficios exclusivos", "Exclusive benefits", "Amenidades y accesos que no están en la venta pública.", "Amenities and access not available to the public."),
         ("", "", "Viajero sostenible", "Sustainable traveler", "Lujo que respeta el entorno y deja valor en cada destino.", "Luxury that respects its surroundings and leaves value in every destination.")])}
</div></section>'''
    body += cta_band(p, "Hablemos de su próximo viaje", "Let's talk about your next trip",
                     "Agende una consulta personal con un experto en viajes de lujo.",
                     "Book a one-on-one consultation with a luxury travel expert.",
                     "Agendar consulta", "Book a consultation", "contacto.html?tipo=fit#planificar",
                     "Guía del viajero sostenible", "Sustainable traveler guide", "sostenibilidad.html#viajero")
    body += "</main>" + footer(p) + tail(p)
    return body


def request_form(fid="tripForm"):
    opts = [("fit", "Viaje a medida", "Tailor-made trip"), ("dia", "Tours de un día", "One-day tours"),
            ("grupo", "Grupo de ocio", "Leisure group"), ("incentivo", "Incentivo o evento corporativo", "Incentive or corporate event"),
            ("crucero", "Operación de crucero", "Cruise operations"), ("agencia", "Soy agencia o advisor", "I'm an agency or advisor")]
    o = "".join(f'<option value="{v}" data-en="{A(en)}">{es}</option>' for v, es, en in opts)
    return f'''<form class="nt-form" id="{fid}" novalidate>
<div class="f"><label for="cName" data-en="Name">Nombre</label><input id="cName" name="name" autocomplete="name" required><span class="err" data-err="name"></span></div>
<div class="f"><label for="cMail" data-en="Email">Correo</label><input id="cMail" name="email" type="email" autocomplete="email" required><span class="err" data-err="email"></span></div>
<div class="f"><label for="cPhone" data-en="Phone or WhatsApp (optional)">Teléfono o WhatsApp (opcional)</label><input id="cPhone" name="phone" type="tel" autocomplete="tel"></div>
<div class="f"><label for="cType" data-en="Type of trip">Tipo de viaje</label><select id="cType" name="type">{o}</select></div>
<div class="f"><label for="cPax" data-en="Number of people">Número de personas</label><input id="cPax" name="pax" type="number" min="1" max="5000" inputmode="numeric" value="2"></div>
<div class="f"><label for="cFrom" data-en="Approximate arrival">Llegada aproximada</label><input id="cFrom" name="from" type="date"></div>
<div class="f full"><label for="cMsg" data-en="Tell us about your trip">Cuéntenos su viaje</label><textarea id="cMsg" name="msg" placeholder="Destinos, intereses, presupuesto, ocasión especial…" data-en-ph="Destinations, interests, budget, special occasion…"></textarea></div>
<label class="consent"><input type="checkbox" id="cOk" name="consent" required><span data-en="I agree that NexumTurismo may use this data only to reply to my request.">Acepto que NexumTurismo use estos datos solo para responder a mi solicitud.</span></label>
<span class="err" data-err="consent" style="grid-column:1/-1"></span>
<button class="btn btn--primary" type="submit" data-en="Prepare my request">Preparar mi solicitud</button>
<div class="done" hidden><b data-en="Your request is ready">Su solicitud está lista</b>
<span data-en="Copy it and send it to our email or WhatsApp. We reply within one business day.">Cópiela y envíela a nuestro correo o WhatsApp. Le respondemos en menos de un día hábil.</span>
<pre></pre><button class="btn btn--ghost copy" type="button" data-en="Copy request">Copiar solicitud</button></div>
</form>'''


def page_contacto():
    p = ""
    body = head(p, "Contacto · NexumTurismo", "Contact · NexumTurismo",
                "Contacte a NexumTurismo: solicitud de viaje, departamentos, oficinas en San José y Guanacaste.")
    body += header(p, "contacto", "#planificar")
    body += '<main id="main">'
    body += page_hero(p, [("Contacto", "Contact", None)],
                      "Hablemos de su viaje", "Let's talk about your trip",
                      "Complete la solicitud y un especialista le responde en menos de un día hábil. Si ya sabe con qué área quiere hablar, escríbale directamente.",
                      "Fill in the request and a specialist will reply within one business day. If you already know which team you need, write to them directly.")
    body += f'''<section class="sec" id="planificar" aria-labelledby="fm-h"><div class="wrap contact-grid">
<div>
<h2 id="fm-h" data-en="Departments">Departamentos</h2>
<dl class="depts" style="margin-top:1.4rem">
<div><dt data-en="Reservations and tailor-made trips">Reservas y viajes a medida</dt><dd>{ph("[reservas@nexumturismo.com]")}</dd></div>
<div><dt data-en="Groups and incentives">Grupos e incentivos</dt><dd>{ph("[grupos@nexumturismo.com]")}</dd></div>
<div><dt data-en="Cruise operations">Operación de cruceros</dt><dd>{ph("[cruceros@nexumturismo.com]")}</dd></div>
<div><dt data-en="One-day tours (Guanacaste)">Tours de un día (Guanacaste)</dt><dd>{ph("[tours@nexumturismo.com]")}</dd></div>
<div><dt data-en="24/7 operations (travelers on the road)">Operaciones 24/7 (viajeros en ruta)</dt><dd>{ph("[+506 0000-0000]")}</dd></div>
<div><dt data-en="San José office">Oficina San José</dt><dd>{ph("[Dirección y horario]")}</dd></div>
<div><dt data-en="Guanacaste office">Oficina Guanacaste</dt><dd>{ph("[Dirección cerca del aeropuerto de Liberia y horario]")}</dd></div>
</dl></div>
<div>{request_form()}<p class="note" style="margin-top:.8rem" data-en="The form does not send data yet: it prepares your request so you can send it by email or WhatsApp.">El formulario todavía no envía datos: prepara su solicitud para que la envíe por correo o WhatsApp.</p></div>
</div></section>
<section class="sec sec--tint" aria-labelledby="pr2-h"><div class="wrap">
{sec_head("pr2-h", "Nuestro compromiso", "Our commitment")}
<div class="pledges">
<blockquote data-en="Our service and quality will live up to the attractions we take you to.">Nuestro servicio y nuestra calidad estarán a la altura de los atractivos a los que lo llevamos.</blockquote>
<blockquote data-en="What we promise in our materials and offers is exactly what you will get.">Lo que prometemos en nuestros materiales y ofertas es exactamente lo que va a recibir.</blockquote>
</div></div></section>'''
    body += "</main>" + footer(p) + tail(p)
    return body
