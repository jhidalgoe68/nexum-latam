---
name: reporte-cierre
description: Genera el reporte ejecutivo de cierre de mes (compras por proveedor, IVA soportado, antigüedad de saldos, facturas vencidas y por vencer) en datos/salida/cierre_AAAA-MM.xlsx. Úsala cuando la persona diga "cierre de mes", "reporte del mes", "qué vence esta semana", "cuánto IVA tengo" o "antigüedad de saldos".
---

# Reporte de cierre

1. Recomienda correr antes `procesar-facturas` y `conciliar-banco` del mismo mes para que los saldos estén al día.
2. Ejecuta: `python3 scripts/reporte.py --mes AAAA-MM`
3. Entrega un resumen ejecutivo de máximo 8 líneas:
   - Compras del mes e IVA soportado (dato de referencia para la declaración D-104; la persona o su contador valida).
   - Top 3 proveedores por monto.
   - Vencidas sin pagar y facturas que vencen en ≤15 días (prioridad de pago).
   - Pendientes de revisión que bloquean el cierre.
4. Termina con 1 a 3 acciones concretas recomendadas.
