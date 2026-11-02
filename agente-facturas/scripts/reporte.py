"""Reporte de cierre de mes: compras, IVA (crédito fiscal), vencimientos y antigüedad de saldos.

Uso:  python scripts/reporte.py --mes 2026-10 [--hoy 2026-11-02]
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mes", required=True)
    ap.add_argument("--hoy", help="Fecha de corte AAAA-MM-DD (por defecto hoy)")
    args = ap.parse_args()
    hoy = c.a_fecha(args.hoy) if args.hoy else date.today()

    registro = [f for f in c.leer_registro() if f.get("Tipo") != "PDF sin XML"]
    del_mes = [f for f in registro if (d := c.a_fecha(f.get("Fecha emisión"))) and d.strftime("%Y-%m") == args.mes
               and f.get("Estado") == "Registrada"]  # solo validadas: lo que está en "Revisar" no suma IVA

    por_prov = defaultdict(lambda: {"Facturas": 0, "Total CRC": 0.0, "Impuesto": 0.0})
    for f in del_mes:
        p = por_prov[f.get("Proveedor") or "(sin nombre)"]
        p["Facturas"] += 1
        p["Total CRC"] += float(f.get("Total CRC") or 0)
        factor = float(f.get("Tipo cambio") or 1) if f.get("Moneda") not in (None, "CRC") else 1
        p["Impuesto"] += float(f.get("Impuesto") or 0) * factor
    proveedores = sorted(({"Proveedor": k, **v} for k, v in por_prov.items()), key=lambda x: -x["Total CRC"])

    abiertas = [f for f in registro if not f.get("Conciliación") and f.get("Estado") != "Rechazada"
                and float(f.get("Total") or 0) > 0]
    tramos = {"Por vencer": [], "1-30 días": [], "31-60 días": [], "61-90 días": [], "+90 días": []}
    for f in abiertas:
        venc = c.a_fecha(f.get("Vencimiento")) or c.a_fecha(f.get("Fecha emisión"))
        if venc is None:
            continue
        atraso = (hoy - venc).days
        tramo = ("Por vencer" if atraso <= 0 else "1-30 días" if atraso <= 30 else
                 "31-60 días" if atraso <= 60 else "61-90 días" if atraso <= 90 else "+90 días")
        tramos[tramo].append({**f, "Días atraso": max(atraso, 0)})
    antiguedad = [{"Tramo": t, "Facturas": len(v), "Total CRC": round(sum(float(x.get("Total CRC") or 0) for x in v), 2)}
                  for t, v in tramos.items()]
    proximas = sorted([f for f in tramos["Por vencer"] if (c.a_fecha(f.get("Vencimiento")) - hoy).days <= 15],
                      key=lambda f: c.a_fecha(f.get("Vencimiento")))

    total = sum(p["Total CRC"] for p in proveedores)
    iva = sum(p["Impuesto"] for p in proveedores)
    resumen = [
        {"Indicador": "Mes", "Valor": args.mes},
        {"Indicador": "Fecha de corte", "Valor": hoy.isoformat()},
        {"Indicador": "Comprobantes válidos del mes", "Valor": len(del_mes)},
        {"Indicador": "Compras del mes (CRC)", "Valor": round(total, 2)},
        {"Indicador": "IVA soportado (CRC)", "Valor": round(iva, 2)},
        {"Indicador": "Pendientes de revisión", "Valor": sum(1 for f in registro if f.get("Estado") == "Revisar")},
        {"Indicador": "Vencidas sin pagar", "Valor": sum(len(v) for t, v in tramos.items() if t != "Por vencer")},
        {"Indicador": "Vencen en ≤15 días", "Valor": len(proximas)},
    ]
    salida = c.SALIDA / f"cierre_{args.mes}.xlsx"
    c.escribir_hojas(salida, {
        "Resumen": (["Indicador", "Valor"], resumen),
        "Por proveedor": (["Proveedor", "Facturas", "Total CRC", "Impuesto"], proveedores),
        "Antigüedad": (["Tramo", "Facturas", "Total CRC"], antiguedad),
        "Vencen pronto": (["Proveedor", "Consecutivo", "Vencimiento", "Total", "Moneda"], proximas),
        "Vencidas": (["Proveedor", "Consecutivo", "Vencimiento", "Días atraso", "Total", "Moneda"],
                     [x for t, v in tramos.items() if t != "Por vencer" for x in v]),
    })
    for r in resumen:
        v = r["Valor"]
        print(f"{r['Indicador']}: {c.colones(v) if isinstance(v, float) else v}")
    print("Top 5 proveedores:")
    for p in proveedores[:5]:
        print(f"  {p['Proveedor']}: ₡{c.colones(p['Total CRC'])} ({p['Facturas']} comprobantes)")
    print(f"Reporte: {salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
