"""Prueba de extremo a extremo con datos FICTICIOS (no corresponden a contribuyentes reales).

Uso:  python3 tests/prueba_extremo_a_extremo.py
Crea una carpeta temporal de datos, genera XML v4.4 + MensajeHacienda + extracto .xlsx,
ejecuta procesar → conciliar → reporte y verifica los resultados.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from openpyxl import Workbook, load_workbook

RAIZ = Path(__file__).resolve().parent.parent
NS = "https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica"
NS_NC = "https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/notaCreditoElectronica"
MI_CEDULA = "3101000000"


def clave(fecha, cedula, consecutivo):
    return f"506{fecha}{cedula.zfill(12)}{consecutivo}1{'12345678'}"


def comprobante(raiz, ns, fecha_iso, ddmmyy, emisor, ced, consecutivo, neto, iva, total, receptor=MI_CEDULA, plazo=None):
    cond = f"<CondicionVenta>02</CondicionVenta><PlazoCredito>{plazo}</PlazoCredito>" if plazo else "<CondicionVenta>01</CondicionVenta>"
    return f"""<?xml version="1.0" encoding="utf-8"?>
<{raiz} xmlns="{ns}">
  <Clave>{clave(ddmmyy, ced, consecutivo)}</Clave>
  <NumeroConsecutivo>{consecutivo}</NumeroConsecutivo>
  <FechaEmision>{fecha_iso}T10:00:00-06:00</FechaEmision>
  <Emisor><Nombre>{emisor}</Nombre><Identificacion><Tipo>02</Tipo><Numero>{ced}</Numero></Identificacion></Emisor>
  <Receptor><Nombre>Mi Empresa</Nombre><Identificacion><Tipo>02</Tipo><Numero>{receptor}</Numero></Identificacion></Receptor>
  {cond}
  <ResumenFactura>
    <CodigoTipoMoneda><CodigoMoneda>CRC</CodigoMoneda><TipoCambio>1</TipoCambio></CodigoTipoMoneda>
    <TotalVentaNeta>{neto}</TotalVentaNeta><TotalImpuesto>{iva}</TotalImpuesto>
    <MedioPago><TipoMedioPago>04</TipoMedioPago></MedioPago>
    <TotalComprobante>{total}</TotalComprobante>
  </ResumenFactura>
</{raiz}>"""


def mensaje(clave_, estado):
    return f"""<?xml version="1.0" encoding="utf-8"?>
<MensajeHacienda xmlns="https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/mensajeHacienda">
  <Clave>{clave_}</Clave><Mensaje>{estado}</Mensaje></MensajeHacienda>"""


def main():
    tmp = Path(tempfile.mkdtemp(prefix="facturas_prueba_"))
    entrada, banco, maestros = tmp / "entrada", tmp / "banco", tmp / "maestros"
    for d in (entrada, banco, maestros):
        d.mkdir(parents=True)

    casos = [  # carpeta, xml, (clave, estado hacienda)
        ("m1", comprobante("FacturaElectronica", NS, "2026-10-01", "011026", "Distribuidora Ficticia Alfa S.A.", "3101111111",
                           "00100001010000000101", "100000.00", "13000.00", "113000.00", plazo=30), "1"),
        ("m2", comprobante("FacturaElectronica", NS, "2026-10-05", "051026", "Servicios Ficticios Beta Ltda", "3102222222",
                           "00100001010000000202", "50000.00", "6500.00", "56500.00"), "1"),
        ("m3", comprobante("FacturaElectronica", NS, "2026-10-07", "071026", "Proveedor Desconocido Gamma", "3103333333",
                           "00100001010000000303", "20000.00", "2600.00", "22600.00"), "1"),
        ("m4", comprobante("FacturaElectronica", NS, "2026-10-08", "081026", "Distribuidora Ficticia Alfa S.A.", "3101111111",
                           "00100001010000000404", "10000.00", "1300.00", "99999.00"), "1"),            # no cuadra
        ("m5", comprobante("FacturaElectronica", NS, "2026-10-09", "091026", "Servicios Ficticios Beta Ltda", "3102222222",
                           "00100001010000000505", "8000.00", "1040.00", "9040.00", receptor="3109999999"), "1"),  # otro receptor
        ("m6", comprobante("FacturaElectronica", NS, "2026-10-10", "101026", "Servicios Ficticios Beta Ltda", "3102222222",
                           "00100001010000000606", "30000.00", "3900.00", "33900.00"), "3"),            # rechazada
        ("m7", comprobante("NotaCreditoElectronica", NS_NC, "2026-10-12", "121026", "Distribuidora Ficticia Alfa S.A.", "3101111111",
                           "00100001030000000707", "5000.00", "650.00", "5650.00"), "1"),
    ]
    import re
    for carpeta, xml, estado in casos:
        d = entrada / carpeta
        d.mkdir()
        (d / "comprobante.xml").write_text(xml, encoding="utf-8")
        k = re.search(r"<Clave>(\d+)</Clave>", xml).group(1)
        (d / "respuesta_mh.xml").write_text(mensaje(k, estado), encoding="utf-8")
        (d / "factura.pdf").write_bytes(b"%PDF-1.4 ficticio")
    (entrada / "m8").mkdir()
    (entrada / "m8" / "solo.pdf").write_bytes(b"%PDF-1.4 sin xml")
    # XML con entidad externa (ataque XXE): debe rechazarse sin leer /etc/passwd
    (entrada / "m9").mkdir()
    (entrada / "m9" / "malicioso.xml").write_text(
        '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><FacturaElectronica>&e;</FacturaElectronica>')

    wb = Workbook(); ws = wb.active; ws.title = "Proveedores"
    ws.append(["Cédula", "Nombre", "IBAN", "Estado"])
    ws.append(["3101111111", "Distribuidora Ficticia Alfa S.A.", "CR00000000000000000001", "Activo"])
    ws.append(["3102222222", "Servicios Ficticios Beta Ltda", "CR00000000000000000002", "Activo"])
    wb.save(maestros / "proveedores.xlsx")

    wb = Workbook(); ws = wb.active
    ws.append(["Banco Ficticio · Estado de cuenta"]); ws.append(["Cuenta CR00...0099"]); ws.append([])
    ws.append(["Fecha", "Descripción", "Referencia", "Débito", "Crédito"])
    ws.append(["15/10/2026", "TRANSF SINPE DISTRIBUIDORA ALFA FACT 101", "88001", "113.000,00", ""])
    ws.append(["20/10/2026", "PAGO PROVEEDOR", "88002", "56.500,00", ""])
    ws.append(["22/10/2026", "COMISION MANTENIMIENTO", "", "2.500,00", ""])
    ws.append(["25/10/2026", "DEPOSITO CLIENTE", "", "", "500.000,00"])
    wb.save(banco / "BancoFicticio_2026-10.xlsx")

    env = {**os.environ, "AGENTE_FACTURAS_DATOS": str(tmp)}
    def run(*a):
        r = subprocess.run([sys.executable, *a], cwd=RAIZ, env=env, capture_output=True, text=True)
        print(r.stdout, r.stderr)
        assert r.returncode == 0, a
        return r.stdout

    run("scripts/procesar.py")
    salida2 = run("scripts/procesar.py")  # idempotencia
    assert "nuevos: 0" in salida2, "La segunda ejecución no debe duplicar"

    filas = {r[0].value: [c.value for c in r] for r in load_workbook(tmp / "salida/facturas.xlsx")["Facturas"].iter_rows(min_row=2)}
    hdr = [c.value for c in next(load_workbook(tmp / "salida/facturas.xlsx")["Facturas"].iter_rows(max_row=1))]
    por_cons = {v[hdr.index("Consecutivo")]: dict(zip(hdr, v)) for v in filas.values()}
    assert por_cons["00100001010000000101"]["Estado"] == "Registrada"
    assert por_cons["00100001010000000202"]["Estado"] == "Registrada"
    assert "Proveedor nuevo" in por_cons["00100001010000000303"]["Observaciones"]
    assert "no cuadran" in por_cons["00100001010000000404"]["Observaciones"]
    assert "no es tu empresa" in por_cons["00100001010000000505"]["Observaciones"]
    assert por_cons["00100001010000000606"]["Estado"] == "Rechazada"
    assert por_cons["00100001030000000707"]["Total"] == -5650.0
    assert any(v.get("Tipo") == "PDF sin XML" for v in por_cons.values() if v) or \
        any(r[hdr.index("Tipo")] == "PDF sin XML" for r in filas.values())

    out = run("scripts/conciliar.py", "--mes", "2026-10")
    assert "Conciliados (alta confianza): 1" in out and "Sugeridos (validar a mano): 1" in out
    assert "Débitos sin factura: 1" in out and "No (simulación)" in out
    run("scripts/conciliar.py", "--mes", "2026-10", "--confirmar")
    run("scripts/reporte.py", "--mes", "2026-10", "--hoy", "2026-11-02")
    print(f"OK · todas las verificaciones pasaron · datos de prueba en {tmp}")


if __name__ == "__main__":
    main()
