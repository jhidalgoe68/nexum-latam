# Agente de facturas · Costa Rica (Claude Code)

Descarga facturas electrónicas de proveedores desde **Outlook / Microsoft 365** (solo lectura), las registra
en **Excel** a partir del **XML de Hacienda (v4.3/v4.4)** y las **concilia con el extracto bancario (.xlsx)**.

```
Outlook "Facturas" ──(Mail.Read)──► datos/entrada/ ──► procesar.py ──► datos/salida/facturas.xlsx
                                                                          │
datos/banco/BANCO_AAAA-MM.xlsx ─────────────────────► conciliar.py ◄──────┘
                                                          └─► conciliacion_AAAA-MM.xlsx · cierre_AAAA-MM.xlsx
```

> **Ubicación recomendada:** un repositorio **privado** propio. Para extraer esta carpeta con su historial:
> `git subtree split -P agente-facturas -b agente-facturas` y luego hacer push de esa rama a un repo privado nuevo.

## Instalación (una vez)

1. `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
2. `cp config.example.yaml config.yaml` y completa la cédula de tu empresa y las columnas de tu banco.
3. **Registrar la app en Microsoft Entra ID** (portal.azure.com → Entra ID → Registros de aplicaciones):
   - Nuevo registro → "Solo cuentas de este directorio".
   - *Autenticación* → **Permitir flujos de cliente público = Sí** (no requiere secreto).
   - *Permisos de API* → Microsoft Graph → **Delegado** → `Mail.Read`
     (o `Mail.Read.Shared` si usarás un buzón compartido `facturas@…`). **No** agregues `Mail.ReadWrite`/`Mail.Send`.
   - Copia *Id. de directorio (tenant)* e *Id. de aplicación (cliente)* a `config.yaml`.
4. En Outlook crea la carpeta **Facturas** y una regla que mueva ahí los correos de facturación.
5. Crea `datos/maestros/proveedores.xlsx`, hoja `Proveedores`, columnas `Cédula | Nombre | IBAN | Estado`.
6. Abre Claude Code **en esta carpeta** (`cd agente-facturas && claude`) para que carguen skills, hooks y permisos.

## Uso con Claude Code (skills)

| Dices… | Skill | Script |
|---|---|---|
| "trae las facturas nuevas" | `ingestar-facturas` | `ingestar_m365.py` |
| "procesa las facturas" | `procesar-facturas` | `procesar.py` |
| "concilia octubre" | `conciliar-banco` | `conciliar.py` (simulación → aprobación → `--confirmar`) |
| "cierre de mes" | `reporte-cierre` | `reporte.py` |

## Controles de seguridad

| Riesgo | Control |
|---|---|
| Acceso excesivo al correo | Permiso delegado `Mail.Read`, una sola carpeta, lista de remitentes, sin escritura en el buzón |
| Inyección de instrucciones en PDF/correo | Montos solo desde XML con parser determinista; `CLAUDE.md` define los documentos como datos; hook bloquea red y borrado |
| XML malicioso (XXE, bombas) | `defusedxml` con DTD prohibido y límite de tamaño |
| Fraude de proveedor o cambio de cuenta | Maestro de proveedores: un proveedor nuevo o bloqueado va a "Revisar" |
| Factura no dirigida a tu empresa | Validación de la cédula del receptor |
| Comprobante rechazado por Hacienda | Se lee `MensajeHacienda`: Rechazada = no pagar ni usar como crédito fiscal |
| Duplicados | Clave única de 50 dígitos más SHA-256 del archivo |
| Alteración de originales | `datos/entrada` y `datos/banco` son inmutables (permisos + hook) |
| Fuga de datos o secretos | `datos/` y `config.yaml` en `.gitignore`; token en `datos/.secretos` (0600) bloqueado al agente; repo privado |
| Trazabilidad | `datos/logs/auditoria.jsonl` (append-only, sin contenido sensible) |
| Decisiones financieras | Human-in-the-loop: la conciliación se confirma solo con aprobación explícita |

**Recomendado además:** cifrado de disco (BitLocker/FileVault), MFA en la cuenta M365, revocar el
consentimiento de la app si un equipo se pierde y retener los comprobantes 5 años (Código de Normas y
Procedimientos Tributarios). Los datos personales se tratan conforme a la Ley 8968.

## Prueba

`python3 tests/prueba_extremo_a_extremo.py` usa datos ficticios y valida el registro, las alertas
(proveedor nuevo, totales, receptor, rechazo de Hacienda, PDF sin XML, XXE), la idempotencia, la conciliación y el cierre.
