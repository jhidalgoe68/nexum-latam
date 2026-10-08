-- =====================================================================
-- SINPEMarket · Esquema PostgreSQL 16 · MVP (Fase 1)
-- Multi-tenant por comercio (tenant_id) + Row Level Security.
-- Montos en colones como NUMERIC(14,2); cantidades NUMERIC(12,3)
-- (permite 0,5 kg o 1,250 kg). Los IDs son UUID generados en el
-- cliente móvil para soportar operación offline sin colisiones.
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

CREATE SCHEMA IF NOT EXISTS app;
SET search_path = app, public;

-- ---------- Tipos ---------------------------------------------------
CREATE TYPE rol_usuario    AS ENUM ('ADMIN_PLATAFORMA', 'DUENO', 'VENDEDOR');
CREATE TYPE estado_pago    AS ENUM ('PENDIENTE', 'PAGADO', 'CANCELADO', 'EXPIRADO');
CREATE TYPE metodo_pago    AS ENUM ('SINPE_MOVIL', 'EFECTIVO', 'TARJETA', 'OTRO');
CREATE TYPE origen_confirm AS ENUM ('MANUAL', 'SMS_PARSER', 'INTEGRACION_BANCARIA');

-- ---------- Comercio (tenant) ---------------------------------------
CREATE TABLE comercio (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre_comercial   TEXT        NOT NULL,
  identificacion     TEXT,                         -- cédula física/jurídica
  telefono_sinpe     CHAR(8)     NOT NULL CHECK (telefono_sinpe ~ '^[2-8][0-9]{7}$'),
  titular_sinpe      TEXT        NOT NULL,         -- nombre que muestra el banco
  feria              TEXT,                         -- ej. "Feria de Zapote"
  prefijo_pedido     TEXT        NOT NULL DEFAULT 'PED',
  activo             BOOLEAN     NOT NULL DEFAULT TRUE,
  creado_en          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- Usuarios ------------------------------------------------
CREATE TABLE usuario (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  comercio_id    UUID REFERENCES comercio(id),    -- NULL sólo para ADMIN_PLATAFORMA
  nombre         TEXT        NOT NULL,
  telefono       CHAR(8)     NOT NULL UNIQUE,      -- login por OTP
  email          CITEXT      UNIQUE,
  rol            rol_usuario NOT NULL,
  activo         BOOLEAN     NOT NULL DEFAULT TRUE,
  creado_en      TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (rol = 'ADMIN_PLATAFORMA' OR comercio_id IS NOT NULL)
);

-- Código de activación: vincula un dispositivo a un comercio (un solo uso).
CREATE TABLE codigo_activacion (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  comercio_id   UUID        NOT NULL REFERENCES comercio(id),
  codigo_hash   TEXT        NOT NULL,              -- nunca en texto plano
  expira_en     TIMESTAMPTZ NOT NULL,
  usado_en      TIMESTAMPTZ,
  usado_por     UUID REFERENCES usuario(id)
);

CREATE TABLE dispositivo (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  comercio_id     UUID        NOT NULL REFERENCES comercio(id),
  usuario_id      UUID        NOT NULL REFERENCES usuario(id),
  plataforma      TEXT        NOT NULL CHECK (plataforma IN ('android','ios','web')),
  ultimo_sync     TIMESTAMPTZ,
  revocado_en     TIMESTAMPTZ,
  creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- Catálogos -----------------------------------------------
CREATE TABLE unidad_medida (
  id            SMALLSERIAL PRIMARY KEY,
  nombre        TEXT    NOT NULL UNIQUE,
  abreviatura   TEXT    NOT NULL UNIQUE,
  permite_decimales BOOLEAN NOT NULL            -- kilo: sí · manojo: no
);

INSERT INTO unidad_medida (nombre, abreviatura, permite_decimales) VALUES
  ('Kilo','kg',TRUE), ('Libra','lb',TRUE), ('Unidad','und',FALSE),
  ('Manojo','mnj',FALSE), ('Rollo','rll',FALSE), ('Tajo','tjo',FALSE),
  ('Caja','cja',FALSE), ('Saco','sco',FALSE), ('Paquete','paq',FALSE);

CREATE TABLE categoria (
  id       SMALLSERIAL PRIMARY KEY,
  nombre   TEXT NOT NULL UNIQUE
);

INSERT INTO categoria (nombre) VALUES
  ('Verduras'), ('Frutas'), ('Hierbas'), ('Granos'), ('Lácteos'),
  ('Carnes'), ('Abarrotes'), ('Limpieza e higiene'), ('Otros');

-- Catálogo maestro global (gobernado por el administrador) → habilita
-- comparación de precios entre comercios en Fase 3 (Marketplace).
CREATE TABLE producto_maestro (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre            TEXT     NOT NULL,
  categoria_id      SMALLINT NOT NULL REFERENCES categoria(id),
  unidad_sugerida   SMALLINT NOT NULL REFERENCES unidad_medida(id),
  cabys             CHAR(13),                      -- código Hacienda (factura electrónica)
  UNIQUE (nombre, unidad_sugerida)
);

-- Producto tal como lo vende un comercio concreto.
CREATE TABLE producto (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  comercio_id          UUID     NOT NULL REFERENCES comercio(id),
  producto_maestro_id  UUID REFERENCES producto_maestro(id),
  nombre               TEXT     NOT NULL,
  categoria_id         SMALLINT NOT NULL REFERENCES categoria(id),
  unidad_medida_id     SMALLINT NOT NULL REFERENCES unidad_medida(id),
  activo               BOOLEAN  NOT NULL DEFAULT TRUE,
  creado_en            TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (comercio_id, nombre, unidad_medida_id)
);

-- ---------- Jornada + precios diarios -------------------------------
-- Una jornada = un día de venta de un comercio (apertura/cierre de caja).
CREATE TABLE jornada (
  id            UUID PRIMARY KEY,                 -- generado en el móvil
  comercio_id   UUID        NOT NULL REFERENCES comercio(id),
  fecha         DATE        NOT NULL,
  abierta_por   UUID        NOT NULL REFERENCES usuario(id),
  abierta_en    TIMESTAMPTZ NOT NULL,
  cerrada_en    TIMESTAMPTZ,
  UNIQUE (comercio_id, fecha)
);

CREATE TABLE precio_diario (
  id                   UUID PRIMARY KEY,          -- generado en el móvil
  comercio_id          UUID          NOT NULL REFERENCES comercio(id),
  jornada_id           UUID          NOT NULL REFERENCES jornada(id),
  producto_id          UUID          NOT NULL REFERENCES producto(id),
  precio               NUMERIC(14,2) NOT NULL CHECK (precio > 0),
  cantidad_disponible  NUMERIC(12,3) CHECK (cantidad_disponible >= 0),
  registrado_por       UUID          NOT NULL REFERENCES usuario(id),
  registrado_en        TIMESTAMPTZ   NOT NULL,
  UNIQUE (jornada_id, producto_id)
);

-- ---------- Clientes ------------------------------------------------
CREATE TABLE cliente (
  id                     UUID PRIMARY KEY,         -- generado en el móvil
  comercio_id            UUID        NOT NULL REFERENCES comercio(id),
  nombre                 TEXT,
  telefono               CHAR(8)     CHECK (telefono ~ '^[2-8][0-9]{7}$'),
  consentimiento_datos   BOOLEAN     NOT NULL DEFAULT FALSE,   -- Ley 8968
  consentimiento_en      TIMESTAMPTZ,
  creado_en              TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (comercio_id, telefono),
  CHECK (telefono IS NULL OR consentimiento_datos)
);

-- ---------- Ventas --------------------------------------------------
CREATE TABLE venta (
  id                 UUID PRIMARY KEY,             -- generado en el móvil (idempotencia)
  comercio_id        UUID          NOT NULL REFERENCES comercio(id),
  jornada_id         UUID          NOT NULL REFERENCES jornada(id),
  numero_pedido      TEXT          NOT NULL,       -- PED-20261011-00001
  vendedor_id        UUID          NOT NULL REFERENCES usuario(id),
  dispositivo_id     UUID          REFERENCES dispositivo(id),
  cliente_id         UUID          REFERENCES cliente(id),
  subtotal           NUMERIC(14,2) NOT NULL CHECK (subtotal >= 0),
  descuento          NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (descuento >= 0),
  total              NUMERIC(14,2) NOT NULL CHECK (total >= 0),
  metodo_pago        metodo_pago   NOT NULL DEFAULT 'SINPE_MOVIL',
  estado_pago        estado_pago   NOT NULL DEFAULT 'PENDIENTE',
  creada_en          TIMESTAMPTZ   NOT NULL,       -- hora del dispositivo
  recibida_en        TIMESTAMPTZ   NOT NULL DEFAULT now(),  -- hora del servidor
  version            INTEGER       NOT NULL DEFAULT 1,      -- control optimista
  UNIQUE (comercio_id, numero_pedido),
  CHECK (total = subtotal - descuento)
);

CREATE TABLE detalle_venta (
  id                UUID PRIMARY KEY,
  venta_id          UUID          NOT NULL REFERENCES venta(id) ON DELETE CASCADE,
  comercio_id       UUID          NOT NULL REFERENCES comercio(id),
  producto_id       UUID          NOT NULL REFERENCES producto(id),
  -- snapshot: el histórico no cambia si luego se edita el producto
  nombre_producto   TEXT          NOT NULL,
  unidad_abrev      TEXT          NOT NULL,
  cantidad          NUMERIC(12,3) NOT NULL CHECK (cantidad > 0),
  precio_unitario   NUMERIC(14,2) NOT NULL CHECK (precio_unitario > 0),
  subtotal          NUMERIC(14,2) NOT NULL,
  CHECK (subtotal = round(cantidad * precio_unitario, 2))
);

-- Bitácora inmutable de cambios de estado de pago (auditoría).
CREATE TABLE evento_pago (
  id              BIGSERIAL PRIMARY KEY,
  venta_id        UUID           NOT NULL REFERENCES venta(id),
  comercio_id     UUID           NOT NULL REFERENCES comercio(id),
  estado_anterior estado_pago,
  estado_nuevo    estado_pago    NOT NULL,
  origen          origen_confirm NOT NULL,
  referencia_banco TEXT,                          -- nº de comprobante SINPE si se captura
  usuario_id      UUID           REFERENCES usuario(id),
  ocurrido_en     TIMESTAMPTZ    NOT NULL DEFAULT now()
);

-- ---------- Índices -------------------------------------------------
CREATE INDEX ix_producto_comercio   ON producto (comercio_id) WHERE activo;
CREATE INDEX ix_precio_producto     ON precio_diario (producto_id, registrado_en DESC);
CREATE INDEX ix_venta_comercio_dia  ON venta (comercio_id, creada_en DESC);
CREATE INDEX ix_venta_pendientes    ON venta (comercio_id) WHERE estado_pago = 'PENDIENTE';
CREATE INDEX ix_venta_cliente       ON venta (cliente_id) WHERE cliente_id IS NOT NULL;
CREATE INDEX ix_detalle_venta       ON detalle_venta (venta_id);
CREATE INDEX ix_detalle_producto    ON detalle_venta (producto_id);
CREATE INDEX ix_evento_venta        ON evento_pago (venta_id, ocurrido_en);

-- ---------- Row Level Security --------------------------------------
-- La API fija `SET app.comercio_id = '<uuid>'` por transacción a partir
-- del JWT; ninguna consulta puede ver datos de otro comercio.
DO $$
DECLARE t TEXT;
BEGIN
  FOREACH t IN ARRAY ARRAY['producto','jornada','precio_diario','cliente',
                           'venta','detalle_venta','evento_pago','dispositivo']
  LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format($p$CREATE POLICY aislamiento_comercio ON %I
                     USING (comercio_id = current_setting('app.comercio_id', true)::uuid)
                     WITH CHECK (comercio_id = current_setting('app.comercio_id', true)::uuid)$p$, t);
  END LOOP;
END $$;

-- ---------- Vistas analíticas (Dashboard Fase 2) --------------------
CREATE VIEW v_ventas_diarias AS
SELECT v.comercio_id,
       (v.creada_en AT TIME ZONE 'America/Costa_Rica')::date AS fecha,
       count(*)                                    AS transacciones,
       sum(v.total)                                AS ingresos,
       round(avg(v.total), 2)                      AS ticket_promedio,
       count(DISTINCT v.cliente_id)                AS clientes_identificados
FROM venta v
WHERE v.estado_pago = 'PAGADO'
GROUP BY 1, 2;

CREATE VIEW v_ranking_productos AS
SELECT d.comercio_id,
       (v.creada_en AT TIME ZONE 'America/Costa_Rica')::date AS fecha,
       d.producto_id,
       d.nombre_producto,
       d.unidad_abrev,
       sum(d.cantidad)  AS cantidad_vendida,
       sum(d.subtotal)  AS ingresos
FROM detalle_venta d
JOIN venta v ON v.id = d.venta_id AND v.estado_pago = 'PAGADO'
GROUP BY 1, 2, 3, 4, 5;
