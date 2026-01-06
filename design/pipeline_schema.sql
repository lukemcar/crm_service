-- ====================================================================
-- Dyno CRM – Pipeline and Deal Domain Minimal Schema Export
--
-- This schema file consolidates the core domain objects required for
-- pipeline and deal reporting.  It extracts the essential tables,
-- columns, keys and relationships from the Dyno CRM baseline schema and
-- subsequent change requests.  The goal is to provide a canonical
-- reference for reporting logic without extraneous support tables.
--
-- NOTE: Only core tables relevant to deals, pipelines, stages and
-- related ownership/assignment are included.  Support tables (emails,
-- phones, notes, etc.) and support/helpdesk domain tables are omitted.

SET search_path TO public, dyno_crm;

-- ----------------------------------------------------------------------
-- Enum definitions (referenced by tables below)
-- ----------------------------------------------------------------------
-- These enums are defined in the consolidated CRM change request.  They
-- control pipeline semantics, movement modes, stage states, deal types
-- and participant roles.  They are listed here for completeness, but
-- should only be created once in the database.

-- Pipeline object type (which entity the pipeline applies to)
-- e.g. 'DEAL', 'LEAD', 'COMPANY', 'CONTACT', 'TICKET'
CREATE TYPE IF NOT EXISTS dyno_crm.pipeline_object_type AS ENUM (
    'COMPANY', 'CONTACT', 'DEAL', 'LEAD', 'TICKET'
);

-- Pipeline movement mode (flexible vs enforced movement)
CREATE TYPE IF NOT EXISTS dyno_crm.pipeline_movement_mode AS ENUM (
    'FLEXIBLE', 'ENFORCED'
);

-- Stage state (JIRA‑style semantics)
CREATE TYPE IF NOT EXISTS dyno_crm.pipeline_stage_state AS ENUM (
    'NOT_STARTED', 'IN_PROGRESS', 'DONE_SUCCESS', 'DONE_FAILED'
);

-- Deal type categorisation
CREATE TYPE IF NOT EXISTS dyno_crm.deal_type AS ENUM (
    'NEW', 'RENEWAL', 'UPSELL', 'OTHER'
);

-- ----------------------------------------------------------------------
-- Table: pipeline
-- ----------------------------------------------------------------------
-- Represents a sequence of stages that deals move through.  Enhanced
-- fields allow multiple pipelines per object type, ordering within a
-- tenant/object, archiving, stable keys and movement enforcement.

CREATE TABLE IF NOT EXISTS dyno_crm.pipeline (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    object_type dyno_crm.pipeline_object_type NOT NULL,
    display_order INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    pipeline_key VARCHAR(100) NOT NULL,
    movement_mode dyno_crm.pipeline_movement_mode NOT NULL DEFAULT 'FLEXIBLE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    -- Unique composite keys for tenant/object scoping
    CONSTRAINT ux_pipeline_tenant_id UNIQUE (tenant_id, id),
    CONSTRAINT ux_pipeline_tenant_object_key UNIQUE (tenant_id, object_type, pipeline_key),
    CONSTRAINT ux_pipeline_tenant_object_display_order UNIQUE (tenant_id, object_type, display_order)
);

CREATE INDEX IF NOT EXISTS ix_pipeline_tenant_object_type
    ON dyno_crm.pipeline (tenant_id, object_type);

-- ----------------------------------------------------------------------
-- Table: pipeline_stage
-- ----------------------------------------------------------------------
-- Defines individual stages within a pipeline.  Each stage belongs to
-- exactly one pipeline and has an order, probability and stage state.

CREATE TABLE IF NOT EXISTS dyno_crm.pipeline_stage (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    pipeline_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    display_order INTEGER NOT NULL,
    probability NUMERIC(5,2),
    stage_state dyno_crm.pipeline_stage_state NOT NULL DEFAULT 'NOT_STARTED',
    inherit_pipeline_actions BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    -- Foreign keys enforcing pipeline membership and tenant consistency
    CONSTRAINT fk_pipeline_stage_pipeline FOREIGN KEY (pipeline_id)
        REFERENCES dyno_crm.pipeline (id) ON DELETE CASCADE,
    CONSTRAINT fk_pipeline_stage_pipeline_tenant FOREIGN KEY (pipeline_id, tenant_id)
        REFERENCES dyno_crm.pipeline (id, tenant_id) ON DELETE CASCADE,
    -- Tenant‑safe identifiers for composite FK targets
    CONSTRAINT ux_pipeline_stage_tenant_id UNIQUE (tenant_id, id),
    -- Stage belongs to a pipeline via composite key (tenant_id, pipeline_id, id)
    CONSTRAINT ux_pipeline_stage_tenant_pipeline_stage UNIQUE (tenant_id, pipeline_id, id),
    -- Unique ordering within a pipeline
    CONSTRAINT ux_pipeline_stage_pipeline_display_order UNIQUE (pipeline_id, display_order),
    -- Probability range enforcement (0..1 when provided)
    CONSTRAINT ck_pipeline_stage_probability_range CHECK (
        probability IS NULL OR (probability >= 0 AND probability <= 1)
    )
);

CREATE INDEX IF NOT EXISTS ix_pipeline_stage_tenant
    ON dyno_crm.pipeline_stage (tenant_id);

CREATE INDEX IF NOT EXISTS ix_pipeline_stage_pipeline
    ON dyno_crm.pipeline_stage (pipeline_id);

-- ----------------------------------------------------------------------
-- Table: contact
-- ----------------------------------------------------------------------
-- Stores people involved in CRM activities.  Ownership fields allow
-- routing and reporting by owner.  Details beyond basic identity
-- (emails, phones, addresses, etc.) are stored in auxiliary tables.

CREATE TABLE IF NOT EXISTS dyno_crm.contact (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    owned_by_user_id UUID,
    owned_by_group_id UUID,
    CONSTRAINT ux_contact_tenant_id UNIQUE (tenant_id, id),
    CONSTRAINT fk_contact_owner_user FOREIGN KEY (tenant_id, owned_by_user_id)
        REFERENCES dyno_crm.tenant_user_shadow (tenant_id, user_id)
        ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_contact_owner_group FOREIGN KEY (tenant_id, owned_by_group_id)
        REFERENCES dyno_crm.tenant_group_shadow (tenant_id, id)
        ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS ix_contact_owner_user
    ON dyno_crm.contact (tenant_id, owned_by_user_id);

CREATE INDEX IF NOT EXISTS ix_contact_owner_group
    ON dyno_crm.contact (tenant_id, owned_by_group_id);

-- ----------------------------------------------------------------------
-- Table: company
-- ----------------------------------------------------------------------
-- Represents an account or organisation.  Ownership fields align with
-- contact ownership.  Additional company details live in auxiliary
-- tables.

CREATE TABLE IF NOT EXISTS dyno_crm.company (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    owned_by_user_id UUID,
    owned_by_group_id UUID,
    CONSTRAINT ux_company_tenant_id UNIQUE (tenant_id, id),
    CONSTRAINT fk_company_owner_user FOREIGN KEY (tenant_id, owned_by_user_id)
        REFERENCES dyno_crm.tenant_user_shadow (tenant_id, user_id)
        ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_company_owner_group FOREIGN KEY (tenant_id, owned_by_group_id)
        REFERENCES dyno_crm.tenant_group_shadow (tenant_id, id)
        ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS ix_company_owner_user
    ON dyno_crm.company (tenant_id, owned_by_user_id);

CREATE INDEX IF NOT EXISTS ix_company_owner_group
    ON dyno_crm.company (tenant_id, owned_by_group_id);

-- ----------------------------------------------------------------------
-- Table: lead
-- ----------------------------------------------------------------------
-- Captures early prospects before conversion to deals.  Includes
-- optional ownership and JSONB lead_data.  JSON schema validation is
-- enforced in the original schema; refer to 001_init_schema.sql for
-- details.  Here we define only the core columns and keys.

CREATE TABLE IF NOT EXISTS dyno_crm.lead (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    first_name VARCHAR(100),
    middle_name VARCHAR(100),
    last_name VARCHAR(100),
    source VARCHAR(255),
    lead_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    owned_by_user_id UUID,
    owned_by_group_id UUID,
    CONSTRAINT ux_lead_tenant_id UNIQUE (tenant_id, id),
    CONSTRAINT fk_lead_owner_user FOREIGN KEY (tenant_id, owned_by_user_id)
        REFERENCES dyno_crm.tenant_user_shadow (tenant_id, user_id)
        ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_lead_owner_group FOREIGN KEY (tenant_id, owned_by_group_id)
        REFERENCES dyno_crm.tenant_group_shadow (tenant_id, id)
        ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS ix_lead_owner_user
    ON dyno_crm.lead (tenant_id, owned_by_user_id);

CREATE INDEX IF NOT EXISTS ix_lead_owner_group
    ON dyno_crm.lead (tenant_id, owned_by_group_id);

-- ----------------------------------------------------------------------
-- Table: deal
-- ----------------------------------------------------------------------
-- Central CRM opportunity record.  Contains links to pipeline and
-- pipeline stage, ownership and assignment fields, provenance and
-- forecasting attributes.

CREATE TABLE IF NOT EXISTS dyno_crm.deal (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    amount NUMERIC(12,2),
    expected_close_date DATE,
    pipeline_id UUID NOT NULL,
    stage_id UUID NOT NULL,
    probability NUMERIC(5,2),
    source VARCHAR(200),
    initial_lead_id UUID,
    company_id UUID,
    owned_by_user_id UUID,
    owned_by_group_id UUID,
    assigned_user_id UUID,
    assigned_group_id UUID,
    deal_type dyno_crm.deal_type,
    forecast_probability NUMERIC(5,2),
    close_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    -- Unique per tenant for FK support
    CONSTRAINT ux_deal_tenant_id UNIQUE (tenant_id, id),
    -- Core foreign keys
    CONSTRAINT fk_deal_pipeline FOREIGN KEY (pipeline_id)
        REFERENCES dyno_crm.pipeline (id) ON DELETE CASCADE,
    CONSTRAINT fk_deal_stage FOREIGN KEY (stage_id)
        REFERENCES dyno_crm.pipeline_stage (id) ON DELETE CASCADE,
    CONSTRAINT fk_deal_company FOREIGN KEY (tenant_id, company_id)
        REFERENCES dyno_crm.company (tenant_id, id)
        ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_deal_initial_lead FOREIGN KEY (tenant_id, initial_lead_id)
        REFERENCES dyno_crm.lead (tenant_id, id)
        ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
    -- Ownership / assignment FKs
    CONSTRAINT fk_deal_owner_user FOREIGN KEY (tenant_id, owned_by_user_id)
        REFERENCES dyno_crm.tenant_user_shadow (tenant_id, user_id)
        ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_deal_owner_group FOREIGN KEY (tenant_id, owned_by_group_id)
        REFERENCES dyno_crm.tenant_group_shadow (tenant_id, id)
        ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_deal_assigned_user FOREIGN KEY (tenant_id, assigned_user_id)
        REFERENCES dyno_crm.tenant_user_shadow (tenant_id, user_id)
        ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_deal_assigned_group FOREIGN KEY (tenant_id, assigned_group_id)
        REFERENCES dyno_crm.tenant_group_shadow (tenant_id, id)
        ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS ix_deal_tenant_pipeline
    ON dyno_crm.deal (tenant_id, pipeline_id);

CREATE INDEX IF NOT EXISTS ix_deal_tenant_stage
    ON dyno_crm.deal (tenant_id, stage_id);

CREATE INDEX IF NOT EXISTS ix_deal_owner_user
    ON dyno_crm.deal (tenant_id, owned_by_user_id);

CREATE INDEX IF NOT EXISTS ix_deal_owner_group
    ON dyno_crm.deal (tenant_id, owned_by_group_id);

CREATE INDEX IF NOT EXISTS ix_deal_assigned_user
    ON dyno_crm.deal (tenant_id, assigned_user_id);

CREATE INDEX IF NOT EXISTS ix_deal_assigned_group
    ON dyno_crm.deal (tenant_id, assigned_group_id);



-- ----------------------------------------------------------------------
-- Table: deal_pipeline_stage_state
-- ----------------------------------------------------------------------
-- Represents a specific instance of a deal in a pipeline stage.  Each
-- row records entry/exit times and allows for re‑entry into stages.

CREATE TABLE IF NOT EXISTS dyno_crm.deal_pipeline_stage_state (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    deal_id UUID NOT NULL,
    pipeline_id UUID NOT NULL,
    pipeline_stage_id UUID NOT NULL,
    previous_pipeline_stage_id UUID,
    next_pipeline_stage_id UUID,
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    pipeline_stage_data JSONB,
    entered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    exited_at TIMESTAMPTZ,
    CONSTRAINT ux_dp_stage_state_tenant_id UNIQUE (tenant_id, id),
    CONSTRAINT fk_dp_stage_state_deal FOREIGN KEY (tenant_id, deal_id)
        REFERENCES dyno_crm.deal (tenant_id, id)
        ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_dp_stage_state_pipeline FOREIGN KEY (tenant_id, pipeline_id)
        REFERENCES dyno_crm.pipeline (tenant_id, id)
        ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_dp_stage_state_stage_belongs FOREIGN KEY (tenant_id, pipeline_id, pipeline_stage_id)
        REFERENCES dyno_crm.pipeline_stage (tenant_id, pipeline_id, id)
        ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_dp_stage_state_previous_stage FOREIGN KEY (tenant_id, previous_pipeline_stage_id)
        REFERENCES dyno_crm.pipeline_stage (tenant_id, id)
        ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_dp_stage_state_next_stage FOREIGN KEY (tenant_id, next_pipeline_stage_id)
        REFERENCES dyno_crm.pipeline_stage (tenant_id, id)
        ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT ck_dp_stage_state_exit_after_enter CHECK (exited_at IS NULL OR exited_at >= entered_at)
);

CREATE INDEX IF NOT EXISTS ix_dp_stage_state_deal
    ON dyno_crm.deal_pipeline_stage_state (tenant_id, deal_id);

CREATE INDEX IF NOT EXISTS ix_dp_stage_state_pipeline
    ON dyno_crm.deal_pipeline_stage_state (tenant_id, pipeline_id);

CREATE INDEX IF NOT EXISTS ix_dp_stage_state_stage
    ON dyno_crm.deal_pipeline_stage_state (tenant_id, pipeline_stage_id);

CREATE INDEX IF NOT EXISTS ix_dp_stage_state_current
    ON dyno_crm.deal_pipeline_stage_state (tenant_id, deal_id)
    WHERE is_current = TRUE;

CREATE UNIQUE INDEX IF NOT EXISTS ux_dp_stage_state_one_current
    ON dyno_crm.deal_pipeline_stage_state (tenant_id, deal_id)
    WHERE is_current = TRUE;

-- End of pipeline and deal minimal schema