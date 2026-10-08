# SINPEMarket · Blueprint Técnico MVP

> Plataforma de comercio asistido para ferias del agricultor y mercados minoristas de Costa Rica, con cobro vía SINPE Móvil.
> Objetivo: MVP listo para piloto en **10 semanas**.
> Artefactos: este documento + [`schema.sql`](./schema.sql) (PostgreSQL 16, validado: creación, restricciones de cálculo y aislamiento RLS entre comercios).

---

## 0. Ajustes críticos a la visión original

La visión de producto es sólida. Antes de construir hay que corregir seis supuestos, porque cada uno cambia la arquitectura:

| # | Supuesto original | Realidad / riesgo | Decisión de blueprint |
|---|---|---|---|
| 1 | Un QR con `SINPE\|88888888\|5100\|...` se escanea desde la app del banco | Las apps bancarias **no leen un formato inventado**. Sólo leen el estándar que adopten el BCCR y las entidades. Si el formato no es el suyo, el cliente ve un texto y no puede pagar. | El **generador de cobro es un módulo con varias estrategias** (ver §5). El MVP sale con una estrategia que funciona hoy y deja lista la conexión al estándar oficial cuando se valide con el BCCR y los bancos. |
| 2 | Confirmación de pago "manual" ahora y "integración bancaria" después | Para confirmar automáticamente hay que hacerlo **a través de una entidad participante de SINPE** (banco o PSP regulado). No es una API pública. Es un tema de negocio y regulación, no sólo técnico. | MVP: confirmación manual con el número de pedido en el detalle de la transferencia. Fase 2: piloto con un banco aliado. Toda confirmación queda en la bitácora `evento_pago`. |
| 3 | La app opera siempre conectada | En ferias la cobertura es mala y los picos son altos (sábados de 6 a 11 a. m.). Si la app depende de la red, **no vende**. | **Offline-first**: base local en el móvil, IDs generados en el dispositivo y sincronización idempotente (§4). |
| 4 | Microservicios | Para un MVP con un equipo de 3 o 4 personas, los microservicios multiplican el costo operativo y no aportan valor. | **Monolito modular NestJS** con límites de dominio claros, para separar servicios después sin reescribir (§2). |
| 5 | Tabla `Productos` global + `PrecioDiario` | Cada vendedor nombra y vende distinto, pero el Marketplace (Fase 3) necesita comparar productos equivalentes. | **Catálogo maestro gobernado** (`producto_maestro`) + producto por comercio. Precios ligados a una **jornada** (apertura y cierre del día). |
| 6 | Registrar teléfono y nombre del cliente | Son datos personales y aplica la **Ley 8968** (PRODHAB). Además, cobrar como comercio activa obligaciones con Hacienda (factura electrónica, CAByS). | Consentimiento explícito guardado en BD. Campo `cabys` listo en el catálogo. Facturación electrónica en Fase 2 vía un proveedor autorizado. |

**Preguntas abiertas que debe responder el negocio** (no bloquean el inicio, pero sí el piloto):
- ¿Qué es exactamente el "Código de Activación"? Este blueprint lo interpreta como **código de un solo uso para vincular un dispositivo a un comercio** (onboarding seguro). Si es otra cosa (por ejemplo, un código de feria), cambia el modelo.
- ¿Los vendedores cobrarán a su SINPE personal o a uno comercial? Esto afecta los límites transaccionales y el cumplimiento tributario.
- ¿Habrá ayudantes por puesto (varios vendedores en un mismo comercio)? El modelo ya lo soporta con los roles `DUENO` y `VENDEDOR`.

---

## 1. Principios de arquitectura

1. **La venta nunca se bloquea**: offline-first y tolerancia a fallos de red.
2. **El dato es el activo**: cada transacción queda inmutable, auditable y lista para analítica e IA (Fases 2 a 4).
3. **Multi-tenant seguro desde el día 1**: aislamiento por `comercio_id` impuesto en la base de datos (RLS), no sólo en el código.
4. **Simplicidad operativa**: servicios gestionados de Azure y un solo despliegue en el MVP.
5. **UX para manos ocupadas**: botones grandes, mínimos toques y uso con una mano bajo el sol.

---

## 2. Arquitectura de solución

```
 ┌──────────────────────────────┐        ┌───────────────────────────┐
 │  App móvil (React Native/Expo)│        │  Backoffice web (Next.js)  │
 │  · SQLite local (WatermelonDB)│        │  · Admin plataforma        │
 │  · Cola de sync               │        │  · Dashboard del comercio  │
 │  · Generador de cobro (QR)    │        └─────────────┬─────────────┘
 └──────────────┬───────────────┘                      │
                │ HTTPS · JWT · /v1                    │
        ┌───────▼──────────────────────────────────────▼───────┐
        │ Azure Front Door (WAF, TLS, rate limiting)           │
        └───────────────────────┬──────────────────────────────┘
        ┌───────────────────────▼──────────────────────────────┐
        │  API NestJS · monolito modular (Azure Container Apps) │
        │  ┌────────┐ ┌────────┐ ┌────────┐ ┌───────┐ ┌──────┐ │
        │  │Identity│ │Catálogo│ │Jornada │ │Ventas │ │Pagos │ │
        │  └────────┘ └────────┘ └────────┘ └───────┘ └──────┘ │
        │  ┌────────┐ ┌──────────┐ ┌──────────────────────────┐ │
        │  │Clientes│ │Analítica │ │Sync (push/pull idempot.) │ │
        │  └────────┘ └──────────┘ └──────────────────────────┘ │
        └──┬───────────────┬──────────────┬──────────────┬──────┘
           │               │              │              │
   ┌───────▼──────┐ ┌──────▼─────┐ ┌──────▼──────┐ ┌─────▼───────────┐
   │ PostgreSQL 16│ │ Redis      │ │ Blob Storage│ │ Service Bus     │
   │ Flexible Srv │ │ (OTP, rate,│ │ (fotos,     │ │ (eventos de     │
   │ RLS + vistas │ │  caché)    │ │  exports)   │ │  dominio)       │
   └───────┬──────┘ └────────────┘ └─────────────┘ └─────┬───────────┘
           │ réplica de lectura / CDC                     │
   ┌───────▼──────────────────────────────┐    ┌──────────▼──────────┐
   │ Analítica: vistas → Fabric/Power BI   │    │ Workers: notific.,  │
   │ (Fase 2) → Azure ML (Fase 4)          │    │ facturación (F2)    │
   └──────────────────────────────────────┘    └─────────────────────┘
   Transversal: Entra ID (staff) · Key Vault · App Insights · Defender for Cloud
```

### Stack definitivo

| Capa | Tecnología | Justificación |
|---|---|---|
| Móvil | React Native + **Expo** (SDK estable), TypeScript | Una base para Android e iOS. Las builds OTA con EAS aceleran el piloto. |
| Persistencia local | **WatermelonDB** (SQLite) | Diseñada para sync offline y rápida con miles de registros. |
| Estado / formularios | Zustand + React Hook Form + Zod | Esquemas Zod compartidos con el backend (monorepo). |
| Backend | **NestJS** + TypeScript, Prisma o Drizzle | Módulos, DI, guards y OpenAPI automático. |
| BD | **PostgreSQL 16** (Azure Flexible Server) | Integridad, RLS, vistas analíticas y JSONB si se necesita. |
| Caché | Azure Cache for Redis | OTP, rate limiting y caché de catálogo. |
| Mensajería | Azure Service Bus | Desacopla notificaciones, facturación e integración bancaria futura. |
| Backoffice | Next.js | Dashboard y administración. Reutiliza el cliente OpenAPI. |
| Infra como código | **Bicep** o Terraform | Ambientes `dev`, `staging` y `prod` reproducibles. |
| CI/CD | GitHub Actions | Lint, test, migraciones, build de contenedores y EAS. |
| Observabilidad | Application Insights + OpenTelemetry | Trazas extremo a extremo, desde el móvil hasta la BD. |

> **Monorepo** (pnpm + Turborepo): `apps/mobile`, `apps/api`, `apps/backoffice`, `packages/contracts` (Zod + tipos), `packages/payment-strategies`, `infra/`.

---

## 3. Modelo de datos

El DDL completo está en [`schema.sql`](./schema.sql). Estas son las decisiones clave:

```
comercio ─┬─ usuario ── dispositivo
          ├─ codigo_activacion
          ├─ producto ──(opcional)── producto_maestro ── categoria / unidad_medida
          ├─ jornada ── precio_diario ── producto
          ├─ cliente
          └─ venta ─┬─ detalle_venta (snapshot de nombre, unidad y precio)
                    └─ evento_pago  (bitácora inmutable)
```

- **UUID generados en el móvil** para `venta`, `detalle_venta`, `jornada`, `precio_diario` y `cliente`. Así el reintento de sync es idempotente y no hay colisiones offline.
- **Montos** en `NUMERIC(14,2)` y **cantidades** en `NUMERIC(12,3)`. Nunca `float`. `unidad_medida.permite_decimales` controla si se aceptan 1,5 kg pero no 1,5 manojos.
- **Snapshot en `detalle_venta`**: el historial no cambia si mañana se renombra un producto.
- **Restricciones de integridad matemática**: `detalle.subtotal = round(cantidad × precio, 2)` y `venta.total = subtotal − descuento`. Un cliente móvil defectuoso no puede corromper la contabilidad.
- **`creada_en` (dispositivo) y `recibida_en` (servidor)** se guardan por separado. La analítica usa la hora real de la venta, y la auditoría detecta relojes alterados.
- **RLS** en todas las tablas con datos de un comercio. La API ejecuta `SET LOCAL app.comercio_id` por transacción a partir del JWT.
- **Vistas analíticas** `v_ventas_diarias` y `v_ranking_productos`, en zona horaria `America/Costa_Rica`. Son la base del Dashboard (Fase 2).

---

## 4. Estrategia offline-first y sincronización

```
 Móvil                                         API
 ─────                                         ───
 1. Venta se guarda en SQLite (estado PENDIENTE)
 2. Se encola en outbox local
 3. Cuando hay red ──► POST /v1/sync/push  { changes[], lastPulledAt }
                        · upsert idempotente por UUID
                        · valida totales y precios
                        · conflicto → gana servidor en estado_pago
                                      (PAGADO nunca retrocede)
                   ◄── { accepted[], rejected[{id, motivo}] }
 4. GET /v1/sync/pull?since=ts ──► catálogo, precios, cambios de estado
```

- **Número de pedido offline**: `PED-YYYYMMDD-<códigoDispositivo(2)>-<secuencia(3)>`, por ejemplo `PED-20261011-A7-014`. Es único sin consultar al servidor y lo bastante corto para escribirlo en el detalle de la transferencia SINPE.
- **Reglas de conflicto**: catálogo y precios → gana la última escritura del dueño. Estado de pago → máquina de estados monotónica (`PENDIENTE → PAGADO | CANCELADO | EXPIRADO`, sin vuelta atrás salvo reverso auditado).
- **Pendientes visibles**: la UI muestra un contador "3 ventas por sincronizar". La confianza del vendedor depende de ver que nada se pierde.

---

## 5. Módulo de cobro SINPE (patrón Strategy)

```ts
interface PaymentRequestStrategy {
  id: 'MANUAL_CARD' | 'SMS_DEEPLINK' | 'QR_OFICIAL' | 'BANK_API';
  isAvailable(ctx: DeviceContext): boolean;
  build(req: { telefono: string; titular: string; monto: number; pedido: string }): PaymentPresentation;
}
```

| Estrategia | Cómo funciona | Estado |
|---|---|---|
| **MANUAL_CARD** (MVP, siempre disponible) | Pantalla de cobro de alto contraste: **monto gigante**, número SINPE con botón "copiar", titular y nº de pedido para el detalle. Incluye un QR que **abre una página web ligera** (`pay.sinpemarket.cr/p/<token>`) con los mismos datos y botones "copiar número" y "copiar monto". El cliente la abre con la cámara del teléfono y paga desde su app bancaria. | Funciona hoy con cualquier banco. |
| **SMS_DEEPLINK** | Botón que abre la app de mensajes con el SMS de SINPE Móvil precargado (`sms:` URI) hacia el número corto del banco del **cliente**. | Hay que validar el formato de SMS y el número corto de cada banco. Opcional en el MVP. |
| **QR_OFICIAL** | Genera el QR en el formato estándar que lean las apps bancarias costarricenses (probablemente basado en EMVCo, si el BCCR o las entidades lo publican). | **Bloqueado por validación con el BCCR y los bancos.** Es la pieza de mayor impacto: debe ser la primera gestión de negocio. |
| **BANK_API** | Un banco o PSP aliado genera el cobro y notifica el pago por webhook → `evento_pago` con origen `INTEGRACION_BANCARIA`. | Fase 2 a 3. Requiere convenio. |

**Seguridad del enlace de pago**: el token es opaco (128 bits) y expira en 30 minutos. La página no expone datos del cliente ni el historial, y no tiene formularios de pago: **la plataforma nunca toca el dinero**, sólo presenta los datos. Así se reduce el alcance regulatorio del MVP.

---

## 6. API REST (v1)

Contrato OpenAPI generado por NestJS (`/v1/docs`). Autenticación con `Authorization: Bearer <JWT>`. Todas las escrituras aceptan `Idempotency-Key`.

### Identidad y onboarding
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/v1/auth/otp/request` | Envía OTP por SMS al teléfono (rate limit en Redis: 3/10 min). |
| POST | `/v1/auth/otp/verify` | Devuelve `access_token` (15 min) y `refresh_token` (30 días, rotativo). |
| POST | `/v1/auth/refresh` | Rota el refresh token y detecta reutilización. |
| POST | `/v1/devices/activate` | `{ codigoActivacion }` → vincula el dispositivo al comercio. Código de un solo uso, guardado como hash. |
| DELETE | `/v1/devices/{id}` | Revoca un dispositivo perdido o robado. |

### Catálogo y jornada
| Método | Ruta | Descripción |
|---|---|---|
| GET | `/v1/catalog/master?q=` | Búsqueda en el catálogo maestro (autocompletar). |
| GET/POST/PATCH | `/v1/products` | Productos del comercio. |
| GET | `/v1/units` · `/v1/categories` | Catálogos de referencia. |
| POST | `/v1/journeys` | Abre la jornada del día. |
| PUT | `/v1/journeys/{id}/prices` | Carga masiva de precios y disponibilidad del día. |
| POST | `/v1/journeys/{id}/close` | Cierre con resumen (ventas, pendientes, efectivo vs. SINPE). |

### Ventas y pagos
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/v1/sales` | Crea una venta con sus líneas. El servidor recalcula y valida los totales. |
| GET | `/v1/sales?date=&status=` | Historial paginado (cursor). |
| GET | `/v1/sales/{id}` | Detalle de la venta y su bitácora de pago. |
| POST | `/v1/sales/{id}/payment-request` | Genera la presentación de cobro (estrategia + token). |
| POST | `/v1/sales/{id}/confirm` | Confirmación manual `{ referenciaBanco? }` → `PAGADO`. |
| POST | `/v1/sales/{id}/cancel` | Cancelación con motivo. |
| POST | `/v1/webhooks/bank/{provider}` | (Fase 2) Webhook firmado (HMAC) y con lista de IPs permitidas. |

### Clientes, analítica y sync
| Método | Ruta | Descripción |
|---|---|---|
| GET/POST | `/v1/customers` | Registro con consentimiento obligatorio. |
| DELETE | `/v1/customers/{id}` | Derecho de supresión (Ley 8968). |
| GET | `/v1/analytics/summary?from=&to=` | KPIs: ventas, ticket promedio y ranking de productos. |
| POST | `/v1/sync/push` · GET `/v1/sync/pull` | Sincronización offline (§4). |

**Ejemplo `POST /v1/sales`**
```json
{
  "id": "6f1c…",
  "jornadaId": "a2b9…",
  "numeroPedido": "PED-20261011-A7-014",
  "creadaEn": "2026-10-11T07:42:10-06:00",
  "clienteId": null,
  "lineas": [
    { "id": "…", "productoId": "…", "cantidad": 2,   "precioUnitario": 1200 },
    { "id": "…", "productoId": "…", "cantidad": 3,   "precioUnitario": 500  },
    { "id": "…", "productoId": "…", "cantidad": 4,   "precioUnitario": 300  }
  ]
}
```
Respuesta `201`: `{ "total": 5100, "estadoPago": "PENDIENTE", ... }`. Si el total enviado no coincide con el recalculado, responde `422`.

---

## 7. Arquitectura de seguridad

| Dominio | Control |
|---|---|
| Identidad | OTP por SMS + JWT de corta duración. Refresh token rotativo con detección de reutilización. Biometría local (Face ID o huella) para reabrir la app. Staff interno vía **Entra ID** con MFA. |
| Autorización | RBAC (`ADMIN_PLATAFORMA`, `DUENO`, `VENDEDOR`) en guards de NestJS **y** RLS en PostgreSQL (defensa en profundidad). |
| Dispositivos | Vinculación con código de un solo uso, revocación remota y almacenamiento cifrado (Keychain / Android Keystore) para los tokens. |
| Datos | TLS 1.2 o superior. Cifrado en reposo (gestionado por Azure). Secretos en **Key Vault** con Managed Identity, sin credenciales en el código. Mínimo dato personal de clientes. |
| Perímetro | Front Door + WAF (OWASP CRS). Rate limiting por IP y por usuario. Validación estricta con Zod en todas las entradas. |
| Integridad financiera | Recalcular siempre en el servidor. Restricciones `CHECK` en la BD. `evento_pago` inmutable. `PAGADO` no retrocede sin reverso auditado. |
| Cumplimiento | Ley 8968 / PRODHAB (consentimiento, acceso, supresión). Retención definida. Preparación para factura electrónica (CAByS). |
| SDLC | SAST (CodeQL), escaneo de dependencias (Dependabot), escaneo de secretos y de contenedores. OWASP MASVS como checklist móvil. Pentest antes de producción. |
| Observabilidad | Logs estructurados sin datos personales. Alertas por picos de errores, OTP fallidos o volumen anómalo de cancelaciones (posible fraude interno). |

**Modelo de amenazas (top 5)**: (1) un vendedor marca como pagada una venta no cobrada → bitácora con usuario y hora + conciliación diaria; (2) un cliente muestra un comprobante falso → la UI enseña a verificar en la app del banco del comercio; en Fase 2, confirmación bancaria; (3) robo del teléfono → biometría + revocación remota; (4) fuga de datos entre comercios → RLS; (5) abuso de OTP (SMS pumping) → rate limit + CAPTCHA en el backoffice.

---

## 8. UX móvil (flujos y pantallas)

Diseño para **uso con una mano, sol directo y prisa**: tipografía de 18 px o más, objetivos táctiles de 56 px o más, alto contraste y modo de color por categoría.

1. **Onboarding** (una sola vez): teléfono → OTP → código de activación → confirmar número SINPE y titular.
2. **Abrir jornada** (cada mañana, menos de 2 minutos): lista de productos con los precios de ayer prellenados; sólo se tocan los que cambiaron. Botón "Igual que ayer".
3. **POS (pantalla principal)**:
   - Cuadrícula de productos frecuentes (los más vendidos primero) con buscador.
   - Al tocar un producto se abre un **teclado numérico propio** con atajos (½, 1, 2, 3, 5) y la unidad visible ("kg", "manojo").
   - Carrito fijo abajo con el total grande en tiempo real: `₡5 100`.
4. **Cobrar**: selector SINPE / efectivo → pantalla de cobro (§5) en **modo presentación**, con brillo al máximo y la pantalla girada hacia el cliente.
5. **Pendientes**: lista de ventas `PENDIENTE` con un swipe para "Pagado ✓". Así el vendedor puede atender al siguiente cliente mientras el anterior transfiere.
6. **Cierre de jornada**: total del día, SINPE vs. efectivo, pendientes sin confirmar y producto estrella.

Indicadores UX del piloto: **tiempo por venta ≤ 20 s** (de 3 productos a pantalla de cobro) y **≤ 5 toques** para una venta de un producto.

---

## 9. Infraestructura Azure y ambientes

| Recurso | Dev | Prod (piloto ≤ 200 comercios) |
|---|---|---|
| API | Container Apps (scale to zero) | Container Apps, 2 réplicas mínimo, autoescala por solicitudes HTTP |
| PostgreSQL | Flexible Server Burstable B1ms | General Purpose D2ds, HA zone-redundant, PITR de 14 días |
| Redis | Basic C0 | Standard C1 |
| Front Door + WAF | — | Standard |
| Storage, Key Vault, App Insights, Service Bus (Basic) | ✓ | ✓ |

Región sugerida: **East US 2** (latencia razonable hacia Costa Rica y catálogo de servicios completo). Hay que validar requisitos de residencia de datos antes de producción. Los costos se estiman con la Azure Pricing Calculator una vez fijado el SKU. Para el piloto, la mayor parte del gasto se va en PostgreSQL con HA.

**CI/CD**: PR → lint + tests + escaneo de seguridad → merge → build de imagen → migraciones (con revisión) → despliegue a `staging` → smoke tests → aprobación manual → `prod`. El móvil usa canales EAS `preview` y `production`, con OTA sólo para cambios JS.

---

## 10. Plan de entrega · 10 semanas

Equipo mínimo: 1 tech lead full stack, 1 dev móvil, 1 dev backend, 1 UX/QA (50 %) y un product owner por parte del negocio.

| Semana | Entregable | Hito |
|---|---|---|
| 0 (en paralelo) | **Gestión con BCCR y bancos** sobre el QR interoperable y aliado bancario. Validación legal (8968, Hacienda). | Decisión de estrategia de cobro |
| 1 | Monorepo, IaC, CI/CD, esquema BD, autenticación OTP | Ambientes `dev` y `staging` vivos |
| 2 | Catálogo maestro, productos, unidades. Diseño UX validado con 5 vendedores reales. | Prototipo navegable probado en una feria |
| 3–4 | Jornada y precios diarios. POS con carrito y motor de cálculo. SQLite local. | **Venta completa offline** |
| 5 | Sincronización push/pull, numeración de pedidos offline, conflictos | Prueba de 50 ventas sin red |
| 6 | Módulo de cobro (MANUAL_CARD + página de pago), confirmación manual, pendientes | **Ciclo de cobro de punta a punta** |
| 7 | Historial, clientes con consentimiento, cierre de jornada | Funcionalidad MVP completa |
| 8 | Backoffice: admin y KPIs básicos (vistas analíticas) | Dashboard v0 |
| 9 | Endurecimiento: pentest, pruebas de carga (pico de 300 ventas/min), accesibilidad, observabilidad | Go/No-Go técnico |
| 10 | **Piloto** en una feria con 10 a 20 vendedores, soporte en sitio y medición de KPIs | Lecciones → backlog de Fase 2 |

**KPIs del piloto**: vendedores activos semanales, ventas por vendedor por jornada, % de ventas cobradas por SINPE, tiempo medio por venta, % de pendientes sin confirmar al cierre y NPS del vendedor.

---

## 11. Roadmap evolutivo (alineado a la visión)

| Fase | Capacidad | Habilitador técnico ya incluido en el MVP |
|---|---|---|
| 2 · Digitalización | Inventario, clientes frecuentes, dashboard, factura electrónica, banco aliado | `cantidad_disponible`, `cliente`, vistas analíticas, `cabys`, Service Bus, `BANK_API` |
| 3 · Marketplace | Consulta de disponibilidad y comparación de precios entre vendedores | `producto_maestro` (equivalencia entre comercios) + `precio_diario` por jornada |
| 4 · IA | Predicción de demanda, precio sugerido, rentabilidad por producto | Serie temporal limpia (`creada_en` real, snapshots y zona horaria) lista para Azure ML o Fabric |
| Regional | Panamá (Yappy/ACH), Guatemala, Honduras, Nicaragua | Patrón Strategy de pagos + `telefono_sinpe` generalizable a "identificador de cobro por país" |

---

## 12. Riesgos principales

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| No existe o no se obtiene acceso a un QR interoperable | Media | Alto | Estrategia MANUAL_CARD funcional desde el día 1. Gestión con el BCCR desde la semana 0. |
| Baja adopción por parte de vendedores mayores o poco digitales | Alta | Alto | Co-diseño en feria, onboarding asistido y "precios de ayer" para reducir la digitación. |
| Fraude con comprobantes falsos | Media | Medio | Educación en la UI, conciliación al cierre e integración bancaria en Fase 2. |
| Conectividad en ferias | Alta | Alto | Offline-first y pruebas de campo reales en la semana 5. |
| Regulación (datos y tributario) | Media | Medio | Revisión legal en la semana 0. Consentimiento y supresión implementados. |
