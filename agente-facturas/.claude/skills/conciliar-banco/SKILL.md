---
name: conciliar-banco
description: Concilia el extracto bancario (.xlsx en datos/banco) de un mes con las facturas registradas y genera datos/salida/conciliacion_AAAA-MM.xlsx. Úsala cuando la persona diga "concilia", "conciliación bancaria", "cruza el banco", "qué pagos no tienen factura" o "qué facturas faltan por pagar".
---

# Conciliación bancaria

1. Confirma el mes (AAAA-MM). Verifica que exista en `datos/banco/` un `.xlsx` cuyo nombre contenga el mes
   (ej. `BCR_2026-10.xlsx`); si no, pide a la persona que lo descargue de su banca y lo guarde ahí.
   **Nunca** te conectes a la banca en línea.
2. Si el extracto es de un banco nuevo y el script no encuentra las columnas, abre el archivo, identifica los
   encabezados y dile a la persona qué valores poner en `banco.columnas` de `config.yaml` (no lo edites tú).
3. Simulación: `python3 scripts/conciliar.py --mes AAAA-MM`
4. Presenta: % conciliado por monto, cantidad de **Sugeridos** (a validar), **Débitos sin factura** (riesgo:
   pagos sin soporte) y **Facturas pendientes**. Muestra el top 5 de diferencias.
5. Pregunta explícitamente: "¿Apruebas marcar como conciliadas las N coincidencias de alta confianza?"
   Solo con un "sí" claro ejecuta: `python3 scripts/conciliar.py --mes AAAA-MM --confirmar`
6. Los "Sugeridos" nunca se confirman automáticamente: la persona los valida en el Excel.

## Notas
- Una cuenta equivale a una moneda (`banco.moneda_cuenta`). Las facturas en USD se concilian con el extracto
  de la cuenta en dólares.
- Re-ejecutar el mismo mes es seguro: se recalculan las marcas de ese mes.
