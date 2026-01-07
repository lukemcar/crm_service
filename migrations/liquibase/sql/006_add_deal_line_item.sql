-- ======================================================================
-- Dyno CRM - Product Catalog/Deal Line Item
-- ======================================================================
-- liquibase formatted sql
-- changeset crm_service:006_add_deal_line_item
--
-- PURPOSE
--   This migration enhances the CRM deal model by introducing a lightweight
--   tenant-scoped product catalog and deal line items. Deals can optionally
--   derive their total amount from associated line items (e.g., SUM of
--   deal_line_item.extended_amount) without removing or changing deal.amount.
--
-- NOTES
--   - product_catalog_item is intentionally NOT an inventory model.
--   - deal_line_item stores snapshot fields (name/sku/description) to preserve
--     historical accuracy when product definitions change.
--   - extended_amount is stored for reporting performance; it can be computed
--     in service code and persisted.
--   - A helper view (v_deal_amount_derived) is included for derived totals.
--
-- ======================================================================

SET search_path TO public, dyno_crm;

-- ----------------------------------------------------------------------
-- Product Catalog Item (lightweight, tenant-scoped)
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_crm.product_catalog_item (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100),
    description TEXT,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    default_unit_price NUMERIC(12,2),
    currency_code CHAR(3),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_product_catalog_item_tenant_id UNIQUE (tenant_id, id),

    CONSTRAINT ux_product_catalog_item_tenant_sku UNIQUE (tenant_id, sku)
        DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS ix_product_catalog_item_tenant_active
    ON dyno_crm.product_catalog_item (tenant_id, is_active);

CREATE INDEX IF NOT EXISTS ix_product_catalog_item_tenant_name
    ON dyno_crm.product_catalog_item (tenant_id, name);

-- ----------------------------------------------------------------------
-- Deal Line Item (association + snapshot + pricing)
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_crm.deal_line_item (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    deal_id UUID NOT NULL,
    product_catalog_item_id UUID,

    display_order INTEGER NOT NULL DEFAULT 0,

    item_name VARCHAR(255) NOT NULL,
    item_sku VARCHAR(100),
    item_description TEXT,

    quantity NUMERIC(12,3) NOT NULL DEFAULT 1,
    unit_price NUMERIC(12,2) NOT NULL DEFAULT 0,

    discount_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    discount_percent NUMERIC(5,2) NOT NULL DEFAULT 0,

    tax_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    tax_percent NUMERIC(5,2) NOT NULL DEFAULT 0,

    extended_amount NUMERIC(12,2) NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_deal_line_item_tenant_id UNIQUE (tenant_id, id),

    CONSTRAINT fk_deal_line_item_deal
        FOREIGN KEY (tenant_id, deal_id)
        REFERENCES dyno_crm.deal (tenant_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED,

    CONSTRAINT fk_deal_line_item_product
        FOREIGN KEY (tenant_id, product_catalog_item_id)
        REFERENCES dyno_crm.product_catalog_item (tenant_id, id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED,

    CONSTRAINT ck_deal_line_item_quantity_nonneg CHECK (quantity >= 0),
    CONSTRAINT ck_deal_line_item_discount_percent CHECK (discount_percent >= 0 AND discount_percent <= 100),
    CONSTRAINT ck_deal_line_item_tax_percent CHECK (tax_percent >= 0 AND tax_percent <= 100),
    CONSTRAINT ck_deal_line_item_unit_price_nonneg CHECK (unit_price >= 0),
    CONSTRAINT ck_deal_line_item_discount_amount_nonneg CHECK (discount_amount >= 0),
    CONSTRAINT ck_deal_line_item_tax_amount_nonneg CHECK (tax_amount >= 0)
);

CREATE INDEX IF NOT EXISTS ix_deal_line_item_tenant_deal
    ON dyno_crm.deal_line_item (tenant_id, deal_id);

CREATE INDEX IF NOT EXISTS ix_deal_line_item_tenant_product
    ON dyno_crm.deal_line_item (tenant_id, product_catalog_item_id);

CREATE INDEX IF NOT EXISTS ix_deal_line_item_tenant_deal_order
    ON dyno_crm.deal_line_item (tenant_id, deal_id, display_order);

-- ----------------------------------------------------------------------
-- Derived Deal Amount View (optional helper for reporting)
-- ----------------------------------------------------------------------

CREATE OR REPLACE VIEW dyno_crm.v_deal_amount_derived AS
SELECT
    d.tenant_id,
    d.id AS deal_id,
    COALESCE(SUM(li.extended_amount), 0) AS derived_amount
FROM dyno_crm.deal d
LEFT JOIN dyno_crm.deal_line_item li
    ON li.tenant_id = d.tenant_id
   AND li.deal_id = d.id
GROUP BY d.tenant_id, d.id;