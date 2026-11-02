"""Procesa comprobantes electrónicos de Costa Rica (Hacienda v4.3 / v4.4) y los registra en Excel.

Uso:  python scripts/procesar.py [--carpeta datos/entrada]

- Lee XML con defusedxml (protege contra XXE y "billion laughs").
- Identifica el tipo por el elemento raíz, sin depender de la versión del namespace.
- Asocia el MensajeHacienda (aceptado/rechazado) a cada comprobante por su Clave.
- Valida: estructura de la clave, receptor = tu empresa, cuadre de totales, proveedor en el maestro.
- No duplica: la Clave (50 dígitos) es el identificador único.
- Los PDF sin XML se listan para revisión humana; nunca se "adivinan" montos.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from defusedxml import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c  # noqa: E402

TIPOS = {
    "FacturaElectronica": "Factura",
    "NotaCreditoElectronica": "Nota de crédito",
    "NotaDebitoElectronica": "Nota de débito",
    "TiqueteElectronico": "Tiquete",
    "FacturaElectronicaCompra": "Factura de compra",
}
TIPOS_ID = {"01": "Física", "02": "Jurídica", "03": "DIMEX", "04": "NITE", "05": "Extranjero"}
CONDICION = {"01": "Contado", "02": "Crédito", "03": "Consignación", "04": "Apartado",
             "05": "Arrendamiento opción compra", "06": "Arrendamiento función financiera",
             "07": "Cobro a favor de tercero", "08": "Servicios prestados al Estado a crédito",
             "09": "Pago del servicio prestado al Estado", "99": "Otros"}
MEDIO_PAGO = {"01": "Efectivo", "02": "Tarjeta", "03": "Cheque", "04": "Transferencia",
              "05": "Recaudado por terceros", "06": "SINPE Móvil", "07": "Plataforma digital", "99": "Otros"}
TAMANO_MAX = 5 * 1024 * 1024


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def hijo(el, *ruta):
    actual = el
    for nombre in ruta:
        if actual is None:
            return None
        actual = next((h for h in actual if local(h.tag) == nombre), None)
    return actual


def texto(el, *ruta, defecto=""):
    nodo = hijo(el, *ruta)
    return (nodo.text or "").strip() if nodo is not None and nodo.text else defecto


def parsear(ruta: Path):
    if ruta.stat().st_size > TAMANO_MAX:
        raise ValueError("XML demasiado grande")
    return ET.parse(ruta, forbid_dtd=True).getroot()


def extraer_comprobante(raiz, ruta: Path, cfg: dict) -> dict:
    tipo_raiz = local(raiz.tag)
    clave = texto(raiz, "Clave")
    consecutivo = texto(raiz, "NumeroConsecutivo")
    emision = c.a_fecha(texto(raiz, "FechaEmision"))
    emisor_id = texto(raiz, "Emisor", "Identificacion", "Numero")
    receptor_id = texto(raiz, "Receptor", "Identificacion", "Numero")
    condicion = texto(raiz, "CondicionVenta")
    plazo = c.a_numero(texto(raiz, "PlazoCredito", defecto="0"))
    resumen = hijo(raiz, "ResumenFactura")
    moneda = texto(resumen, "CodigoTipoMoneda", "CodigoMoneda", defecto="CRC") if resumen is not None else "CRC"
    tipo_cambio = c.a_numero(texto(resumen, "CodigoTipoMoneda", "TipoCambio", defecto="1")) or 1.0
    # v4.4: MedioPago dentro de ResumenFactura; v4.3: en la raíz
    medio = texto(resumen, "MedioPago", "TipoMedioPago") or texto(raiz, "MedioPago")

    venta_neta = c.a_numero(texto(resumen, "TotalVentaNeta"))
    impuesto = c.a_numero(texto(resumen, "TotalImpuesto"))
    otros = c.a_numero(texto(resumen, "TotalOtrosCargos"))
    iva_devuelto = c.a_numero(texto(resumen, "TotalIVADevuelto"))
    total = c.a_numero(texto(resumen, "TotalComprobante"))

    signo = -1 if tipo_raiz == "NotaCreditoElectronica" else 1
    obs = []

    # --- Validaciones -------------------------------------------------------
    if len(clave) != 50 or not clave.isdigit():
        obs.append("Clave inválida (no tiene 50 dígitos)")
    else:
        if consecutivo and clave[21:41] != consecutivo:
            obs.append("Consecutivo no coincide con la clave")
        if emisor_id and c.solo_digitos(clave[9:21]).lstrip("0") != c.solo_digitos(emisor_id).lstrip("0"):
            obs.append("Cédula del emisor no coincide con la clave")
    mi_cedula = c.solo_digitos(cfg.get("empresa", {}).get("cedula", ""))
    if mi_cedula and c.solo_digitos(receptor_id) != mi_cedula:
        obs.append(f"Receptor {receptor_id or '(vacío)'} no es tu empresa")
    tolerancia = float(cfg.get("procesamiento", {}).get("tolerancia_cuadre", 1.0))
    if abs(venta_neta + impuesto + otros - iva_devuelto - total) > tolerancia:
        obs.append("Totales no cuadran (venta neta + impuesto + otros cargos ≠ total)")
    if emision is None:
        obs.append("Fecha de emisión ilegible")

    vencimiento = emision + timedelta(days=int(plazo)) if emision and condicion == "02" and plazo else emision

    return {
        "Clave": clave,
        "Tipo": TIPOS.get(tipo_raiz, tipo_raiz),
        "Consecutivo": consecutivo,
        "Fecha emisión": emision,
        "Vencimiento": vencimiento,
        "Proveedor": texto(raiz, "Emisor", "Nombre"),
        "Cédula proveedor": emisor_id,
        "Tipo ID": TIPOS_ID.get(texto(raiz, "Emisor", "Identificacion", "Tipo"), ""),
        "Cédula receptor": receptor_id,
        "Condición venta": CONDICION.get(condicion, condicion),
        "Medio pago": MEDIO_PAGO.get(medio, medio),
        "Moneda": moneda,
        "Tipo cambio": tipo_cambio,
        "Venta neta": signo * venta_neta,
        "Impuesto": signo * impuesto,
        "Otros cargos": signo * otros,
        "Total": signo * total,
        "Total CRC": round(signo * total * (tipo_cambio if moneda != "CRC" else 1), 2),
        "Observaciones": obs,
        "Archivo": str(ruta.relative_to(c.DATOS)) if ruta.is_relative_to(c.DATOS) else ruta.name,
        "SHA256": c.sha256(ruta),
    }


def cargar_proveedores() -> dict[str, dict]:
    filas = c.leer_hoja(c.MAESTROS / "proveedores.xlsx", "Proveedores")
    return {c.solo_digitos(f.get("Cédula")): f for f in filas if f.get("Cédula")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carpeta", type=Path, default=c.ENTRADA)
    args = ap.parse_args()

    c.asegurar_carpetas()
    cfg = c.cargar_config()
    registro = c.leer_registro()
    claves_existentes = {str(f.get("Clave")) for f in registro}
    proveedores = cargar_proveedores()
    exigir_maestro = bool(cfg.get("procesamiento", {}).get("exigir_proveedor_en_maestro", True))

    comprobantes, mensajes, errores = [], {}, []
    carpetas_con_xml = set()

    for ruta in sorted(args.carpeta.rglob("*.xml")):
        try:
            raiz = parsear(ruta)
        except Exception as e:  # XML corrupto, malicioso o demasiado grande
            errores.append(f"{ruta.name}: {e}")
            continue
        nombre = local(raiz.tag)
        if nombre == "MensajeHacienda":
            estado = texto(raiz, "Mensaje")
            mensajes[texto(raiz, "Clave")] = {"1": "Aceptado", "2": "Aceptado parcial", "3": "Rechazado"}.get(estado, estado)
        elif nombre in TIPOS:
            comprobantes.append(extraer_comprobante(raiz, ruta, cfg))
            carpetas_con_xml.add(ruta.parent)

    nuevos, duplicados = [], 0
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
    for comp in comprobantes:
        if comp["Clave"] in claves_existentes:
            duplicados += 1
            continue
        claves_existentes.add(comp["Clave"])
        obs = comp["Observaciones"]
        estado_mh = mensajes.get(comp["Clave"], "Sin mensaje")
        comp["Estado Hacienda"] = estado_mh

        prov = proveedores.get(c.solo_digitos(comp["Cédula proveedor"]))
        if prov is None and exigir_maestro:
            obs.append("Proveedor nuevo: no está en el maestro de proveedores")
        elif prov is not None and str(prov.get("Estado", "")).lower() == "bloqueado":
            obs.append("Proveedor BLOQUEADO en el maestro")

        if estado_mh == "Rechazado":
            comp["Estado"] = "Rechazada"
            obs.append("Hacienda rechazó el comprobante: no debe pagarse ni usarse como crédito fiscal")
        else:
            comp["Estado"] = "Revisar" if obs else "Registrada"
        comp["Observaciones"] = "; ".join(obs)
        comp["Procesado"] = ahora
        nuevos.append(comp)

    # Actualiza el estado de Hacienda de facturas previas que recibieron su mensaje después
    for f in registro:
        nuevo_estado = mensajes.get(str(f.get("Clave")))
        if nuevo_estado and f.get("Estado Hacienda") != nuevo_estado:
            f["Estado Hacienda"] = nuevo_estado
            if nuevo_estado == "Rechazado":
                f["Estado"] = "Rechazada"

    pdf_sin_xml = [p for p in sorted(args.carpeta.rglob("*.pdf")) if p.parent not in carpetas_con_xml]
    for p in pdf_sin_xml:
        clave_pdf = f"PDF:{c.sha256(p)[:16]}"
        if clave_pdf in claves_existentes:
            continue
        claves_existentes.add(clave_pdf)
        nuevos.append({
            "Clave": clave_pdf, "Tipo": "PDF sin XML", "Estado": "Revisar",
            "Observaciones": "Llegó PDF sin XML: solicitar el XML al proveedor o validar manualmente",
            "Archivo": str(p.relative_to(c.DATOS)) if p.is_relative_to(c.DATOS) else p.name,
            "SHA256": c.sha256(p), "Procesado": ahora,
        })

    c.guardar_registro(registro + nuevos)

    registradas = sum(1 for n in nuevos if n["Estado"] == "Registrada")
    revisar = [n for n in nuevos if n["Estado"] != "Registrada"]
    print(f"Comprobantes leídos: {len(comprobantes)} | nuevos: {len(nuevos)} | duplicados omitidos: {duplicados}")
    print(f"Registradas OK: {registradas} | para revisar: {len(revisar)} | errores de lectura: {len(errores)}")
    for n in revisar:
        print(f"  [{n['Estado']}] {n.get('Proveedor') or n['Archivo']} {n.get('Consecutivo') or ''}: {n['Observaciones']}")
    for e in errores:
        print(f"  [Error] {e}")
    print(f"Registro: {c.REGISTRO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
