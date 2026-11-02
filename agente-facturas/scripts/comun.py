"""Utilidades compartidas: rutas, configuración y lectura/escritura de Excel."""
from __future__ import annotations

import hashlib
import os
from datetime import date, datetime
from pathlib import Path

import yaml
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

RAIZ = Path(__file__).resolve().parent.parent
# Permite apuntar a otra carpeta de datos (pruebas, otra empresa) sin tocar el código.
DATOS = Path(os.environ.get("AGENTE_FACTURAS_DATOS", RAIZ / "datos")).resolve()

ENTRADA = DATOS / "entrada"      # adjuntos descargados del correo (inmutables)
BANCO = DATOS / "banco"          # extractos bancarios descargados por la persona (inmutables)
SALIDA = DATOS / "salida"        # todo lo que genera el agente
MAESTROS = DATOS / "maestros"    # proveedores autorizados
ESTADO = DATOS / ".estado"       # control de mensajes ya procesados
SECRETOS = DATOS / ".secretos"   # caché de tokens (nunca a git, bloqueado al agente)
LOGS = DATOS / "logs"

REGISTRO = SALIDA / "facturas.xlsx"

COLUMNAS_FACTURA = [
    "Clave", "Tipo", "Consecutivo", "Fecha emisión", "Vencimiento",
    "Proveedor", "Cédula proveedor", "Tipo ID", "Cédula receptor",
    "Condición venta", "Medio pago", "Moneda", "Tipo cambio",
    "Venta neta", "Impuesto", "Otros cargos", "Total", "Total CRC",
    "Estado Hacienda", "Estado", "Observaciones", "Archivo", "SHA256",
    "Procesado", "Conciliación",
]

ROJO = PatternFill("solid", fgColor="F8D7DA")
AMARILLO = PatternFill("solid", fgColor="FFF3CD")
VERDE = PatternFill("solid", fgColor="D4EDDA")


def cargar_config() -> dict:
    for nombre in ("config.yaml", "config.example.yaml"):
        p = RAIZ / nombre
        if p.exists():
            with p.open(encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


def asegurar_carpetas() -> None:
    for c in (ENTRADA, BANCO, SALIDA, MAESTROS, ESTADO, SECRETOS, LOGS):
        c.mkdir(parents=True, exist_ok=True)


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


def solo_digitos(valor) -> str:
    return "".join(ch for ch in str(valor or "") if ch.isdigit())


def a_fecha(valor) -> date | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%Y/%m/%d"):
        try:
            return datetime.strptime(texto[:10], fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(texto).date()
    except ValueError:
        return None


def a_numero(valor) -> float:
    if valor is None or valor == "":
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip().replace("₡", "").replace("$", "").replace(" ", "")
    # Formatos "1.234.567,89" (es-CR) y "1,234,567.89" (en)
    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return 0.0


def leer_hoja(ruta: Path, hoja: str) -> list[dict]:
    if not ruta.exists():
        return []
    wb = load_workbook(ruta, data_only=True)
    if hoja not in wb.sheetnames:
        return []
    filas = list(wb[hoja].iter_rows(values_only=True))
    if not filas:
        return []
    encabezados = [str(h) if h is not None else "" for h in filas[0]]
    return [dict(zip(encabezados, f)) for f in filas[1:] if any(v is not None for v in f)]


def escribir_hojas(ruta: Path, hojas: dict[str, tuple[list[str], list[dict]]]) -> None:
    """Escribe un libro completo: {nombre_hoja: (columnas, filas)}."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    wb.remove(wb.active)
    for nombre, (columnas, filas) in hojas.items():
        ws = wb.create_sheet(nombre[:31])
        ws.append(columnas)
        for c in ws[1]:
            c.font = Font(bold=True)
        for fila in filas:
            ws.append([fila.get(col) for col in columnas])
        ws.freeze_panes = "A2"
        if columnas:
            ws.auto_filter.ref = f"A1:{get_column_letter(len(columnas))}{max(ws.max_row, 1)}"
        for i, col in enumerate(columnas, start=1):
            largo = max([len(str(col))] + [len(str(f.get(col) or "")) for f in filas[:500]])
            ws.column_dimensions[get_column_letter(i)].width = min(max(10, largo + 2), 60)
            if any(p in col for p in ("Total", "Venta", "Impuesto", "Monto", "cargos", "Débito", "Crédito")):
                for celda in ws.iter_cols(min_col=i, max_col=i, min_row=2):
                    for c in celda:
                        c.number_format = "#,##0.00"
        if "Estado" in columnas:
            idx = columnas.index("Estado") + 1
            for (c,) in ws.iter_rows(min_row=2, min_col=idx, max_col=idx):
                c.fill = VERDE if c.value == "Registrada" else AMARILLO if c.value == "Revisar" else ROJO if c.value == "Rechazada" else PatternFill()
    tmp = ruta.with_suffix(".tmp.xlsx")
    wb.save(tmp)
    tmp.replace(ruta)  # escritura atómica: nunca deja un Excel a medias


def leer_registro() -> list[dict]:
    return leer_hoja(REGISTRO, "Facturas")


def guardar_registro(filas: list[dict]) -> None:
    revisar = [f for f in filas if f.get("Estado") in ("Revisar", "Rechazada")]
    escribir_hojas(REGISTRO, {
        "Facturas": (COLUMNAS_FACTURA, filas),
        "Revisar": (COLUMNAS_FACTURA, revisar),
    })


def colones(valor: float) -> str:
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
