/**
 * NEXUM — Secure contact form proxy
 * ──────────────────────────────────────────────────────────────────────────
 * Runtime  : Vercel Serverless Function (Node.js)
 * Route    : POST /api/contact
 * Purpose  : Receives the "Solicitar conversación ejecutiva" form submission
 *            from index.html, validates it, and forwards a formatted HTML
 *            email to contact@nexum-latam.com via the Resend API. The API
 *            key is read ONLY from a server-side environment variable — it
 *            is never present in this file and never reaches the browser.
 *
 * ── ONE-TIME SETUP (required before this works) ────────────────────────
 *   1. Vercel dashboard → this project → Settings → Environment Variables
 *      → add RESEND_API_KEY = <your Resend API key> (all environments).
 *   2. In Resend, verify the sending domain nexum-latam.com (Domains tab)
 *      so mail can be sent "from" no-reply@nexum-latam.com. Until it's
 *      verified, Resend will reject sends from that address — you can
 *      temporarily set FROM_ADDRESS below to onboarding@resend.dev to test
 *      the wiring end-to-end.
 *   3. Redeploy (env var changes require a new deployment to take effect).
 *
 * This file alone does nothing without step 1 — Resend will return a 401
 * and the form will show its generic error message until the key is set.
 * ─────────────────────────────────────────────────────────────────────────
 */

const RESEND_API_URL = 'https://api.resend.com/emails';
const TO_ADDRESS      = 'contact@nexum-latam.com';
const FROM_ADDRESS    = 'NEXUM <no-reply@nexum-latam.com>';
const EMAIL_SUBJECT   = 'Nuevo mensaje desde el formulario Conversemos';

// Origins allowed to call this endpoint (adjust if the domain changes).
const ALLOWED_ORIGINS = [
  'https://nexum-latam.com',
  'https://www.nexum-latam.com',
];

// ── Validation helpers ───────────────────────────────────────────────────

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function sanitize(str = '') {
  return String(str)
    .trim()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function validateBody(body) {
  const errors = [];
  if (!body.fn?.trim())             errors.push('Nombre completo requerido');
  if (!body.em?.trim())             errors.push('Email requerido');
  else if (!EMAIL_RE.test(body.em)) errors.push('Email no válido');
  if (!body.ph?.trim())             errors.push('Teléfono requerido');
  if (!body.ch?.trim())             errors.push('Área de desafío requerida');
  if (!body.ms?.trim())             errors.push('Contexto requerido');
  return errors;
}

// ── HTML email template ──────────────────────────────────────────────────

function buildHtml(f) {
  const rows = [
    ['Nombre completo', f.fn],
    ['Empresa',         f.co || '—'],
    ['Cargo',           f.ro || '—'],
    ['Email',           `<a href="mailto:${f.em}" style="color:#00C0DC">${f.em}</a>`],
    ['Teléfono',        f.ph],
    ['Desafío / Área',  f.ch],
  ].map(([label, value]) => `
    <tr>
      <td style="padding:10px 16px;font-family:monospace;font-size:11px;
                 letter-spacing:.1em;text-transform:uppercase;color:#8ab;
                 white-space:nowrap;vertical-align:top;border-bottom:1px solid #1e3458">
        ${sanitize(label)}
      </td>
      <td style="padding:10px 16px;font-size:15px;font-weight:300;
                 color:#edf3f9;border-bottom:1px solid #1e3458">
        ${value.startsWith('<a') ? value : sanitize(value)}
      </td>
    </tr>`).join('');

  return `<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#050e1c;font-family:system-ui,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#050e1c;padding:40px 20px">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#091b38;border:1px solid #1e3458;max-width:600px;width:100%">

        <tr>
          <td style="padding:32px 36px;border-bottom:1px solid #1e3458">
            <p style="margin:0;font-family:monospace;font-size:10px;letter-spacing:.18em;
                      text-transform:uppercase;color:#00C0DC">NEXUM — Formulario Conversemos</p>
            <h1 style="margin:8px 0 0;font-size:22px;font-weight:300;color:#edf3f9;letter-spacing:-.01em">
              Nueva solicitud de conversación ejecutiva
            </h1>
          </td>
        </tr>

        <tr>
          <td style="padding:0">
            <table width="100%" cellpadding="0" cellspacing="0">${rows}</table>
          </td>
        </tr>

        <tr>
          <td style="padding:28px 36px;border-top:1px solid #1e3458">
            <p style="margin:0 0 10px;font-family:monospace;font-size:10px;letter-spacing:.15em;
                      text-transform:uppercase;color:#00C0DC">Contexto</p>
            <p style="margin:0;font-size:15px;font-weight:300;color:rgba(237,243,249,.88);line-height:1.7">
              ${sanitize(f.ms).replace(/\n/g, '<br>')}
            </p>
          </td>
        </tr>

        <tr>
          <td style="padding:24px 36px;background:#050e1c;border-top:1px solid #1e3458">
            <p style="margin:0;font-size:12px;color:rgba(237,243,249,.4)">
              Mensaje recibido en ${new Date().toLocaleString('es-CR',
                { timeZone: 'America/Costa_Rica', dateStyle: 'full', timeStyle: 'short' })}
              — nexum-latam.com
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body></html>`;
}

// ── CORS helper ───────────────────────────────────────────────────────────

function applyCors(res, origin) {
  const allowed = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  res.setHeader('Access-Control-Allow-Origin', allowed);
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Vary', 'Origin');
}

// ── Handler ───────────────────────────────────────────────────────────────

export default async function handler(req, res) {
  const origin = req.headers.origin || '';
  applyCors(res, origin);

  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }

  if (req.method !== 'POST') {
    res.status(405).json({ ok: false, message: 'Método no permitido' });
    return;
  }

  let body;
  try {
    body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
  } catch {
    res.status(400).json({ ok: false, message: 'JSON inválido' });
    return;
  }

  const errors = validateBody(body || {});
  if (errors.length) {
    res.status(422).json({ ok: false, message: errors.join('; ') });
    return;
  }

  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    console.error('[nexum/contact] RESEND_API_KEY env variable not set');
    res.status(500).json({ ok: false, message: 'Error de configuración del servidor' });
    return;
  }

  const f = {
    fn: body.fn.trim(),
    co: (body.co || '').trim(),
    ro: (body.ro || '').trim(),
    em: body.em.trim(),
    ph: body.ph.trim(),
    ch: body.ch.trim(),
    ms: body.ms.trim(),
  };

  const payload = {
    from: FROM_ADDRESS,
    to: [TO_ADDRESS],
    reply_to: f.em,
    subject: EMAIL_SUBJECT,
    html: buildHtml(f),
  };

  let resendRes;
  try {
    resendRes = await fetch(RESEND_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify(payload),
    });
  } catch (networkErr) {
    console.error('[nexum/contact] Network error calling Resend:', networkErr);
    res.status(502).json({ ok: false, message: 'Error al conectar con el servicio de envío' });
    return;
  }

  if (!resendRes.ok) {
    const errBody = await resendRes.json().catch(() => ({}));
    console.error('[nexum/contact] Resend error:', resendRes.status, errBody);
    res.status(502).json({ ok: false, message: 'No se pudo enviar el mensaje. Intenta de nuevo.' });
    return;
  }

  res.status(200).json({ ok: true, message: 'Mensaje enviado correctamente' });
}
