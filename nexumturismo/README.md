# NexumTurismo

Sitio multipágina independiente (DMC de Costa Rica) construido por reingeniería del árbol completo de stcostaricadmc.com. Vive en `/nexumturismo/` y no modifica la página principal de NEXUM LATAM.

## Árbol del sitio

| Sitio original | NexumTurismo |
|---|---|
| Home | `index.html` |
| Tours › One Day Tours / The Tour Store | `tours/un-dia.html` (catálogo de 20 tours con filtros) |
| Tours › Multi-Day Programs | `tours/multidia.html` (6 programas día por día) |
| Services › Cruise Operations | `servicios/cruceros.html` |
| Services › FIT – Touring Experiences | `servicios/viajes-a-medida.html` |
| Services › Leisure Groups | `servicios/grupos.html` |
| Services › Incentive Trips | `servicios/incentivos.html` |
| Services › Corporate Services | `servicios/corporativos.html` |
| About Us › Who We Are | `nosotros/quienes-somos.html` |
| About Us › Company Profile | `nosotros/perfil.html` |
| Virtuoso Advisors + Travel Experts | `agencias.html` |
| ST Collection | `coleccion.html` |
| Sustainability | `sostenibilidad.html` |
| Blog (+ artículos) | `blog/index.html` + 5 artículos en `blog/` |
| Contact | `contacto.html` |

## Cómo se edita

- El contenido (ES y EN) de las subpáginas está en `tools/pages_*.py`; la cabecera, el menú y el pie en `tools/ntsite.py`.
- Regenerar después de cualquier cambio: `python3 nexumturismo/tools/build.py`. También refresca la cabecera y el pie de `index.html`, cuyo cuerpo sigue escrito a mano.
- Estilos compartidos: `assets/nt.css`. Comportamiento compartido (idioma recordado entre páginas, menús, formulario, ilustraciones): `assets/nt.js`.
- Idioma: cada texto lleva su versión inglesa en `data-en`; `nt.js` la aplica. En `index.html` el inglés sigue en el diccionario `EN` del script.

## Antes de publicar en abierto

- Reemplazar todo lo resaltado con la clase `.ph`: teléfonos, correos, direcciones, cifras, año de fundación, nombres del equipo, testimonios y certificaciones. No se copiaron del sitio original las reseñas, el personal, los sellos ni los convenios con hoteles de otra empresa.
- El formulario de `contacto.html` valida y prepara un resumen copiable; no envía datos. Para recibir leads, conectar el `submit` a una función en `api/`.
- Quitar `noindex` (meta en cada página y regla en `vercel.json`).
