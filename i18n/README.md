# NEXUM · sitio bilingüe ES / EN

`index.html` (español) sigue siendo el **único archivo que se edita**. Las páginas publicadas se generan:

```
index.html + i18n/en.json  ──python3 i18n/build.py check──►  es/index.html  en/index.html  sitemap.xml  robots.txt
```

* `/es/` y `/en/` son páginas independientes (URLs, canonical, hreflang, Open Graph y JSON-LD por idioma).
* `/` redirige (`vercel.json`): cookie `nx_lang` → cabecera `Accept-Language` → `/es/`.
* Selector **ES | EN** en el header (escritorio: a la derecha de «Conversemos»; móvil: junto a la hamburguesa).
  Guarda la elección en `localStorage` + cookie y conserva el `#ancla`. En la primera visita sin elección previa,
  el navegador decide el idioma (los bots no son redirigidos).
* El diseño, animaciones, formulario (`/api/contact`, Resend) y lógica son idénticos: solo cambia el texto.

## Después de cambiar `index.html`
Ejecute `python3 i18n/build.py check`. Si añadió texto nuevo (una perspectiva, un assessment, un párrafo) el build
**falla y lo lista**: añada la traducción en `i18n/en.json` (`"texto en español": "English text"`) y repita.
Un texto que debe quedarse igual (marcas, siglas) va en la lista `"__keep__"`. Luego haga commit de `es/`, `en/`,
`sitemap.xml` y `robots.txt`.

## Alcance actual
Traducido: navegación, 8 secciones, formulario y mensajes, footer, términos y privacidad, sectores, los 5
assessments de Executive Insights, metadatos. **Los artículos de Perspectivas siguen en español** dentro de la página
EN (con aviso y `lang="es"`); sus tarjetas del listado sí están traducidas.

`python3 i18n/install_switcher.py` instala el selector en el maestro (ya hecho; es idempotente).
