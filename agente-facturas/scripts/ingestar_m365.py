"""Descarga adjuntos de facturas desde Microsoft 365 (Outlook) en modo SOLO LECTURA.

Uso:  python scripts/ingestar_m365.py [--dias 30] [--simular]

Seguridad:
- Permiso delegado mínimo: Mail.Read (o Mail.Read.Shared para un buzón compartido). Nunca Mail.ReadWrite ni Mail.Send.
- Solo lee UNA carpeta (por defecto "Facturas"), no toda la bandeja.
- Solo acepta remitentes de la lista permitida (si está configurada) y solo archivos .xml / .pdf de tamaño acotado.
- No marca como leído, no mueve ni borra correos: lleva su propio control en datos/.estado/.
- El token se guarda en datos/.secretos/ (fuera de git y bloqueado para el agente por el hook guardia.py).
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c  # noqa: E402

GRAPH = "https://graph.microsoft.com/v1.0"
EXT_PERMITIDAS = {".xml", ".pdf"}


def obtener_token(cfg: dict) -> str:
    import msal  # dependencia solo para la ingesta

    cache_ruta = c.SECRETOS / "token_cache.bin"
    cache = msal.SerializableTokenCache()
    if cache_ruta.exists():
        cache.deserialize(cache_ruta.read_text())
    app = msal.PublicClientApplication(
        cfg["client_id"], authority=f"https://login.microsoftonline.com/{cfg['tenant_id']}", token_cache=cache)
    scopes = ["Mail.Read.Shared"] if cfg.get("buzon") else ["Mail.Read"]
    cuentas = app.get_accounts()
    resultado = app.acquire_token_silent(scopes, account=cuentas[0]) if cuentas else None
    if not resultado:
        flujo = app.initiate_device_flow(scopes=scopes)
        if "user_code" not in flujo:
            raise SystemExit(f"No se pudo iniciar el inicio de sesión: {flujo.get('error_description')}")
        print(flujo["message"], flush=True)  # la persona abre microsoft.com/devicelogin e ingresa el código
        resultado = app.acquire_token_by_device_flow(flujo)
    if "access_token" not in resultado:
        raise SystemExit(f"Autenticación fallida: {resultado.get('error_description')}")
    if cache.has_state_changed:
        cache_ruta.write_text(cache.serialize())
        cache_ruta.chmod(0o600)
    return resultado["access_token"]


def get(sesion, url, **params):
    r = sesion.get(url, params=params or None, timeout=30)
    if r.status_code == 403:
        raise SystemExit("Acceso denegado por Microsoft 365: revisa el permiso Mail.Read / acceso al buzón.")
    r.raise_for_status()
    return r.json()


def buscar_carpeta(sesion, base: str, nombre: str) -> str:
    filtro = f"displayName eq '{nombre.replace(chr(39), chr(39) * 2)}'"
    for url in (f"{base}/mailFolders", f"{base}/mailFolders/inbox/childFolders"):
        datos = get(sesion, url, **{"$filter": filtro, "$select": "id,displayName"})
        if datos.get("value"):
            return datos["value"][0]["id"]
    raise SystemExit(f"No existe la carpeta '{nombre}'. Créala en Outlook y una regla que mueva ahí las facturas.")


def nombre_seguro(nombre: str) -> str:
    nombre = Path(nombre).name  # evita rutas tipo ../../
    return re.sub(r"[^A-Za-z0-9._-]", "_", nombre)[:120] or "adjunto"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dias", type=int, default=30, help="Revisar correos de los últimos N días")
    ap.add_argument("--simular", action="store_true", help="Lista lo que descargaría, sin guardar nada")
    args = ap.parse_args()

    import requests

    c.asegurar_carpetas()
    cfg = c.cargar_config().get("m365", {})
    if not cfg.get("tenant_id") or not cfg.get("client_id") or "x" * 8 in str(cfg.get("client_id")):
        raise SystemExit("Configura m365.tenant_id y m365.client_id en config.yaml (ver README).")
    permitidos = [d.lower().lstrip("@") for d in cfg.get("remitentes_permitidos", [])]
    max_bytes = int(cfg.get("tamano_max_mb", 10)) * 1024 * 1024

    estado_ruta = c.ESTADO / "mensajes_procesados.json"
    procesados = set(json.loads(estado_ruta.read_text())) if estado_ruta.exists() else set()

    sesion = requests.Session()
    sesion.headers["Authorization"] = f"Bearer {obtener_token(cfg)}"
    base = f"{GRAPH}/users/{cfg['buzon']}" if cfg.get("buzon") else f"{GRAPH}/me"
    carpeta = buscar_carpeta(sesion, base, cfg.get("carpeta", "Facturas"))

    desde = (datetime.now(timezone.utc) - timedelta(days=args.dias)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"{base}/mailFolders/{carpeta}/messages"
    params = {"$filter": f"receivedDateTime ge {desde} and hasAttachments eq true",
              "$select": "id,subject,from,receivedDateTime", "$top": "50"}
    descargados, omitidos, rechazados = 0, 0, []
    while url:
        datos = get(sesion, url, **params)
        params = {}
        for m in datos.get("value", []):
            if m["id"] in procesados:
                omitidos += 1
                continue
            remitente = (m.get("from", {}).get("emailAddress", {}).get("address") or "").lower()
            if permitidos and not any(remitente.endswith("@" + d) or remitente.endswith("." + d) for d in permitidos):
                rechazados.append(f"{remitente}: remitente no autorizado ({m.get('subject', '')[:60]})")
                continue
            adjuntos = get(sesion, f"{base}/messages/{m['id']}/attachments").get("value", [])
            destino = c.ENTRADA / f"{m['receivedDateTime'][:10]}_{m['id'][-12:].replace('/', '_').replace('=', '')}"
            for a in adjuntos:
                nombre = nombre_seguro(a.get("name", ""))
                ext = Path(nombre).suffix.lower()
                if a.get("@odata.type") != "#microsoft.graph.fileAttachment" or ext not in EXT_PERMITIDAS:
                    continue
                if int(a.get("size", 0)) > max_bytes:
                    rechazados.append(f"{nombre}: supera {cfg.get('tamano_max_mb', 10)} MB")
                    continue
                contenido = base64.b64decode(a.get("contentBytes", ""))
                if ext == ".pdf" and not contenido.startswith(b"%PDF"):
                    rechazados.append(f"{nombre}: no es un PDF válido")
                    continue
                if args.simular:
                    print(f"[simulación] {remitente} → {nombre}")
                    continue
                destino.mkdir(parents=True, exist_ok=True)
                (destino / nombre).write_bytes(contenido)
                descargados += 1
            if not args.simular:
                procesados.add(m["id"])
        url = datos.get("@odata.nextLink")

    if not args.simular:
        estado_ruta.write_text(json.dumps(sorted(procesados)))
    print(f"Adjuntos descargados: {descargados} | correos ya procesados: {omitidos} | rechazados: {len(rechazados)}")
    for r in rechazados:
        print(f"  [Rechazado] {r}")
    print(f"Carpeta: {c.ENTRADA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
