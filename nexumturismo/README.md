# NexumTurismo

`nexumturismo/index.html` es un índice independiente (DMC de Costa Rica) construido por reingeniería de la estructura de stcostaricadmc.com. No modifica la página principal de NEXUM LATAM.

- URL: `/nexumturismo/` (redirección 308 desde `/nexumturismo`, `X-Robots-Tag: noindex` mientras esté en prueba; ver `vercel.json`).
- Archivo único: HTML + CSS + JS en línea. Única dependencia externa: Google Fonts (Zilla Slab + Instrument Sans).
- Bilingüe ES/EN: el texto en español vive en el HTML (`data-t`); el inglés en el diccionario `EN` del script. Las regiones (Destinos) están en el arreglo `REGIONS`.
- Datos por publicar resaltados con la clase `.ph` (teléfono, correo, oficinas, cifras, testimonios, certificaciones). Reemplazar el texto y quitar la clase.
- El formulario "Planificar mi viaje" valida y genera un resumen copiable; no envía datos. Para envío real, conectar el `submit` a un endpoint (p. ej. una función en `api/`).
