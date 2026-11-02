"""Conciliación bancaria: cruza el extracto (.xlsx) con el registro de facturas.

Uso:
  python scripts/conciliar.py --mes 2026-10                  # simulación: solo genera el reporte
  python scripts/conciliar.py --mes 2026-10 --confirmar      # además marca en facturas.xlsx lo conciliado

- El extracto original NUNCA se modifica.
- Solo se marcan como conciliadas las coincidencias de alta confianza, y solo con --confirmar
  (la persona revisa primero el reporte).
- Reglas: misma moneda, monto dentro de tolerancia, fecha de pago dentro de la ventana,
  y puntos extra si la descripción menciona el consecutivo, la cédula o el nombre del proveedor.
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from datetime import timedelta
from pathlib import Path

from openpyxl import load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c  # noqa: E402

PALABRAS_VACIAS = {"sociedad", "anonima", "limitada", "srl", "s.a.", "sa", "ltda", "de", "del", "la", "el",
                   "los", "las", "y", "cia", "compania", "servicios", "comercial", "grupo", "costa", "rica"}


def normalizar(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", t)


def leer_extracto(ruta: Path, cfg: dict) -> list[dict]:
    col = cfg["columnas"]
    wb = load_workbook(ruta, data_only=True, read_only=True)
    ws = wb[cfg["hoja"]] if cfg.get("hoja") else wb.worksheets[0]
    filas = list(ws.iter_rows(values_only=True))
    # Los bancos suelen poner un encabezado de varias líneas: buscamos la fila con la columna de fecha.
    objetivo = normalizar(col["fecha"])
    inicio = next((i for i, f in enumerate(filas[:40])
                   if any(normalizar(v).strip() == objetivo for v in f if v is not None)), None)
    if inicio is None:
        raise SystemExit(f"No encontré la columna '{col['fecha']}' en {ruta.name}. Ajusta banco.columnas en config.yaml")
    enc = [normalizar(v).strip() if v is not None else "" for v in filas[inicio]]

    def idx(nombre):
        if not nombre:
            return None
        n = normalizar(nombre).strip()
        return enc.index(n) if n in enc else None

    i_fecha, i_desc, i_ref = idx(col["fecha"]), idx(col.get("descripcion")), idx(col.get("referencia"))
    i_deb, i_cred, i_monto = idx(col.get("debito")), idx(col.get("credito")), idx(col.get("monto"))
    movimientos = []
    for n, f in enumerate(filas[inicio + 1:], start=inicio + 2):
        fecha = c.a_fecha(f[i_fecha]) if i_fecha is not None and i_fecha < len(f) else None
        if fecha is None:
            continue
        if i_monto is not None:
            monto = c.a_numero(f[i_monto])
            debito, credito = (-monto, 0.0) if monto < 0 else (0.0, monto)
        else:
            debito = abs(c.a_numero(f[i_deb])) if i_deb is not None else 0.0
            credito = abs(c.a_numero(f[i_cred])) if i_cred is not None else 0.0
        movimientos.append({
            "Fila": n, "Fecha": fecha,
            "Descripción": str(f[i_desc] or "") if i_desc is not None else "",
            "Referencia": str(f[i_ref] or "") if i_ref is not None else "",
            "Débito": debito, "Crédito": credito,
        })
    return movimientos


def puntaje(mov: dict, fac: dict, tol: float, ventana: int) -> tuple[int, list[str]] | None:
    total = abs(float(fac.get("Total") or 0))
    if abs(mov["Débito"] - total) > tol:
        return None
    emision = c.a_fecha(fac.get("Fecha emisión"))
    venc = c.a_fecha(fac.get("Vencimiento")) or emision
    if emision is None or not (emision - timedelta(days=3) <= mov["Fecha"] <= venc + timedelta(days=ventana)):
        return None
    motivos, pts = ["monto"], 50
    texto = normalizar(f"{mov['Descripción']} {mov['Referencia']}")
    digitos = c.solo_digitos(texto)
    consecutivo = c.solo_digitos(fac.get("Consecutivo"))
    if consecutivo and (consecutivo[-10:].lstrip("0") or "x") in digitos:
        pts += 30; motivos.append("consecutivo")
    cedula = c.solo_digitos(fac.get("Cédula proveedor"))
    if cedula and cedula in digitos:
        pts += 25; motivos.append("cédula")
    palabras = [p for p in normalizar(fac.get("Proveedor")).replace(",", " ").replace(".", " ").split()
                if len(p) >= 4 and p not in PALABRAS_VACIAS]
    if any(p in texto for p in palabras):
        pts += 20; motivos.append("nombre")
    dias = abs((mov["Fecha"] - venc).days)
    pts -= min(dias // 7, 10)  # leve preferencia por pagos cercanos al vencimiento
    return pts, motivos


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mes", required=True, help="AAAA-MM")
    ap.add_argument("--extracto", type=Path, help="Ruta del .xlsx (por defecto: el más reciente de datos/banco que contenga el mes)")
    ap.add_argument("--confirmar", action="store_true", help="Marca en facturas.xlsx las coincidencias de alta confianza")
    args = ap.parse_args()
    if not re.fullmatch(r"\d{4}-\d{2}", args.mes):
        raise SystemExit("--mes debe tener formato AAAA-MM")

    cfg = c.cargar_config()
    banco = cfg.get("banco", {})
    tol = float(banco.get("tolerancia_monto", 1.0))
    ventana = int(banco.get("ventana_dias", 60))
    umbral = int(banco.get("umbral_confianza", 70))
    moneda = banco.get("moneda_cuenta", "CRC")

    extracto = args.extracto
    if extracto is None:
        candidatos = sorted([p for p in c.BANCO.glob("*.xlsx") if args.mes in p.name or args.mes.replace("-", "") in p.name],
                            key=lambda p: p.stat().st_mtime)
        if not candidatos:
            raise SystemExit(f"No hay extracto en {c.BANCO} cuyo nombre contenga {args.mes}. Usa --extracto.")
        extracto = candidatos[-1]

    movimientos = [m for m in leer_extracto(extracto, banco) if m["Fecha"].strftime("%Y-%m") == args.mes]
    registro = c.leer_registro()
    # Re-ejecutar el mismo mes es seguro: se liberan las marcas previas de ese mes.
    for f in registro:
        if str(f.get("Conciliación") or "").startswith(args.mes + ":"):
            f["Conciliación"] = None
    pendientes = [f for f in registro
                  if not f.get("Conciliación") and f.get("Estado") != "Rechazada"
                  and f.get("Tipo") not in ("PDF sin XML",) and (f.get("Moneda") or "CRC") == moneda
                  and float(f.get("Total") or 0) > 0]

    pares = []
    for mi, mov in enumerate(movimientos):
        if mov["Débito"] <= 0:
            continue
        for fi, fac in enumerate(pendientes):
            r = puntaje(mov, fac, tol, ventana)
            if r:
                pares.append((r[0], mi, fi, r[1]))
    pares.sort(key=lambda x: -x[0])

    usados_m, usados_f, conciliado, sugerido = set(), set(), [], []
    for pts, mi, fi, motivos in pares:
        if mi in usados_m or fi in usados_f:
            continue
        usados_m.add(mi); usados_f.add(fi)
        mov, fac = movimientos[mi], pendientes[fi]
        fila = {
            "Fecha banco": mov["Fecha"], "Descripción": mov["Descripción"], "Referencia": mov["Referencia"],
            "Monto": mov["Débito"], "Proveedor": fac.get("Proveedor"), "Consecutivo": fac.get("Consecutivo"),
            "Fecha factura": c.a_fecha(fac.get("Fecha emisión")), "Total factura": fac.get("Total"),
            "Diferencia": round(mov["Débito"] - abs(float(fac.get("Total") or 0)), 2),
            "Confianza": pts, "Criterios": ", ".join(motivos), "Clave": fac.get("Clave"), "Fila extracto": mov["Fila"],
        }
        (conciliado if pts >= umbral else sugerido).append(fila)
        if pts >= umbral and args.confirmar:
            fac["Conciliación"] = f"{args.mes}:fila{mov['Fila']}"

    sin_factura = [m for i, m in enumerate(movimientos) if m["Débito"] > 0 and i not in usados_m]
    no_pagadas = [f for i, f in enumerate(pendientes) if i not in usados_f]
    otras_monedas = [f for f in registro if (f.get("Moneda") or "CRC") != moneda and not f.get("Conciliación")]

    total_deb = sum(m["Débito"] for m in movimientos)
    monto_conc = sum(f["Monto"] for f in conciliado)
    resumen = [
        {"Indicador": "Extracto", "Valor": extracto.name},
        {"Indicador": "Mes", "Valor": args.mes},
        {"Indicador": "Moneda de la cuenta", "Valor": moneda},
        {"Indicador": "Débitos del mes", "Valor": sum(1 for m in movimientos if m["Débito"] > 0)},
        {"Indicador": "Monto debitado", "Valor": round(total_deb, 2)},
        {"Indicador": "Conciliados (alta confianza)", "Valor": len(conciliado)},
        {"Indicador": "Monto conciliado", "Valor": round(monto_conc, 2)},
        {"Indicador": "% conciliado (monto)", "Valor": f"{(monto_conc / total_deb * 100) if total_deb else 0:.1f}%"},
        {"Indicador": "Sugeridos (validar a mano)", "Valor": len(sugerido)},
        {"Indicador": "Débitos sin factura", "Valor": len(sin_factura)},
        {"Indicador": "Facturas pendientes de pago", "Valor": len(no_pagadas)},
        {"Indicador": "Facturas en otra moneda (no evaluadas)", "Valor": len(otras_monedas)},
        {"Indicador": "Marcado en registro", "Valor": "Sí" if args.confirmar else "No (simulación)"},
    ]
    col_par = ["Fecha banco", "Descripción", "Referencia", "Monto", "Proveedor", "Consecutivo", "Fecha factura",
               "Total factura", "Diferencia", "Confianza", "Criterios", "Clave", "Fila extracto"]
    salida = c.SALIDA / f"conciliacion_{args.mes}.xlsx"
    c.escribir_hojas(salida, {
        "Resumen": (["Indicador", "Valor"], resumen),
        "Conciliado": (col_par, conciliado),
        "Sugerido": (col_par, sugerido),
        "Banco sin factura": (["Fila", "Fecha", "Descripción", "Referencia", "Débito"], sin_factura),
        "Facturas pendientes": (["Proveedor", "Consecutivo", "Fecha emisión", "Vencimiento", "Total", "Moneda", "Clave"], no_pagadas),
    })
    if args.confirmar:
        c.guardar_registro(registro)

    for r in resumen:
        print(f"{r['Indicador']}: {r['Valor']}")
    print(f"Reporte: {salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
