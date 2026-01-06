-- ======================================================================
-- Dyno CRM - Deal/Pipeline Enhancements Migration
-- ======================================================================
-- liquibase formatted sql
-- changeset crm_service:005_pipeline_improvements
--
-- PURPOSE
--   This migration enhances the Deal + Pipeline domain to support:
--     - Linking a deal to a primary company (optional) and an initial lead (optional)
--     - Associating one deal to many contacts (deal_contact)
--     - Deal-scoped notes/attachments (persist for the life of the deal)
--     - Stage-instance state + stage-scoped notes/attachments (historical per stage entry)
--     - Strong integrity: ensure pipeline_stage belongs to pipeline for stage-instance rows
--
-- NOTES
--   - created_by / updated_by are intentionally soft links (strings), no FKs
--   - All tables include tenant_id for multi-tenant isolation
--
-- BUG FIXES INCLUDED
--   - Composite foreign keys like (tenant_id, some_id) require a UNIQUE or PRIMARY KEY
--     on the referenced table with the same column order (tenant_id, id).
--   - Composite FK enforcing "stage belongs to pipeline" requires UNIQUE (tenant_id, pipeline_id, id)
--     on pipeline_stage.
-- ======================================================================

-- ----------------------------------------------------------------------
-- 0) ENUM TYPES
-- ----------------------------------------------------------------------
-- Deal participant role scope enum
--   CONTACT = role applies only to contacts
--   USER    = role applies only to users (internal Dyno CRM users)
--   BOTH    = role applies to both contacts and users

SET search_path TO public, dyno_crm;


CREATE TYPE dyno_crm.deal_participant_role_scope AS ENUM (
    'CONTACT',
    'USER',
    'BOTH'
);


-- ----------------------------------------------------------------------
-- PRECONDITIONS FOR COMPOSITE FOREIGN KEYS (tenant_id + id)
-- ----------------------------------------------------------------------
-- Many FKs below reference (tenant_id, id). Postgres requires a UNIQUE/PK on
-- the referenced table for that exact column list and order.
--
-- These constraints do NOT change the logical model. They simply make
-- (tenant_id, id) a legal FK target.
ALTER TABLE dyno_crm.pipeline
  ADD CONSTRAINT ux_pipeline_tenant_id UNIQUE (tenant_id, id);

ALTER TABLE dyno_crm.pipeline_stage
  ADD CONSTRAINT ux_pipeline_stage_tenant_id UNIQUE (tenant_id, id);

ALTER TABLE dyno_crm.deal
  ADD CONSTRAINT ux_deal_tenant_id UNIQUE (tenant_id, id);

ALTER TABLE dyno_crm.contact
  ADD CONSTRAINT ux_contact_tenant_id UNIQUE (tenant_id, id);

ALTER TABLE dyno_crm.company
  ADD CONSTRAINT ux_company_tenant_id UNIQUE (tenant_id, id);

ALTER TABLE dyno_crm.lead
  ADD CONSTRAINT ux_lead_tenant_id UNIQUE (tenant_id, id);


-- ----------------------------------------------------------------------
-- 0) PIPELINE STAGE: composite uniqueness to support "stage belongs to pipeline"
-- ----------------------------------------------------------------------
-- Ensures a stage can be referenced by (tenant_id, pipeline_id, stage_id).
-- This enables a composite FK that guarantees the stage belongs to the pipeline.
ALTER TABLE dyno_crm.pipeline_stage
  ADD CONSTRAINT ux_pipeline_stage_tenant_pipeline_stage
  UNIQUE (tenant_id, pipeline_id, id);


-- ----------------------------------------------------------------------
-- 1) DEAL: add buyer context and provenance
-- ----------------------------------------------------------------------
-- source:
--   Free-form origin descriptor (e.g., "web_form", "partner_referral", "import", etc.)
-- initial_lead_id:
--   Provenance pointer to the lead that originated this deal (optional; may remain after conversion).
-- company_id:
--   Primary buyer company/account for the deal (optional; B2C deals may not have a company).
ALTER TABLE dyno_crm.deal
    ADD COLUMN source VARCHAR(200),
    ADD COLUMN initial_lead_id UUID,
    ADD COLUMN company_id UUID,
    ADD CONSTRAINT fk_deal_company
        FOREIGN KEY (tenant_id, company_id)
        REFERENCES dyno_crm.company (tenant_id, id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED,
    ADD CONSTRAINT fk_deal_initial_lead
        FOREIGN KEY (tenant_id, initial_lead_id)
        REFERENCES dyno_crm.lead (tenant_id, id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED;

-- Company-based deal queries (account view, filters, reporting)
CREATE INDEX IF NOT EXISTS ix_deal_company
    ON dyno_crm.deal (tenant_id, company_id);




-- ======================================================================
-- Deal Participant Roles (Tenant-scoped role catalog)
-- ======================================================================
-- PURPOSE
--   Defines the set of roles that a participant can play on a deal (per tenant).
--   Roles are data-driven (not enums) so tenants can add/rename roles without migrations.
--
-- DESIGN NOTES
--   - role_key is the stable identifier for APIs/automation (snake_case recommended).
--   - role_name is the human display label.
--   - role_scope indicates whether the role applies to contacts, users, or both.
--   - role_data is optional JSONB metadata for automation/UX (keep keys small and intentional).
--   - created_by / updated_by are soft links (VARCHAR), no foreign keys.
-- ======================================================================
CREATE TABLE IF NOT EXISTS dyno_crm.deal_participant_role (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    -- Stable identifier for programmatic use (automation rules, API references).
    role_key  VARCHAR(100) NOT NULL,

    -- Human-friendly label displayed in UI.
    role_name VARCHAR(255) NOT NULL,

    role_scope dyno_crm.deal_participant_role_scope NOT NULL DEFAULT 'BOTH',

    -- Optional metadata for automation/UX.
    -- Example keys: { "category": "buyer", "forecast_relevant": true, "priority": 10 }
    role_data JSONB,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_deal_participant_role_key UNIQUE (tenant_id, role_key),
    CONSTRAINT ux_deal_participant_role_name UNIQUE (tenant_id, role_name),

    -- Required so role-assignment table can FK to (tenant_id, id)
    CONSTRAINT ux_deal_participant_role_tenant_id UNIQUE (tenant_id, id)
);

CREATE INDEX IF NOT EXISTS ix_deal_participant_role_tenant_active
    ON dyno_crm.deal_participant_role (tenant_id, is_active);

-- ----------------------------------------------------------------------
-- 2) DEAL_CONTACT: many-to-many deal <-> contact association
-- ----------------------------------------------------------------------
-- Purpose:
--   Deals usually involve multiple people (decision maker, champion, procurement, etc.).
--   This table represents membership (a contact participates in a deal).
CREATE TABLE IF NOT EXISTS dyno_crm.deal_contact (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    deal_id UUID NOT NULL,
    contact_id UUID NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Ensure the deal exists in the same tenant
    CONSTRAINT fk_deal_contact_deal
        FOREIGN KEY (tenant_id, deal_id)
        REFERENCES dyno_crm.deal (tenant_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED,

    -- Ensure the contact exists in the same tenant
    CONSTRAINT fk_deal_contact_contact
        FOREIGN KEY (tenant_id, contact_id)
        REFERENCES dyno_crm.contact (tenant_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED,

    -- Prevent duplicate membership rows for the same deal-contact pair
    CONSTRAINT ux_deal_contact UNIQUE (tenant_id, deal_id, contact_id),

    -- Required so role-assignment table can FK to (tenant_id, id)
    CONSTRAINT ux_deal_contact_tenant_id UNIQUE (tenant_id, id)
);

CREATE INDEX IF NOT EXISTS ix_deal_contact_contact
    ON dyno_crm.deal_contact (tenant_id, contact_id);

CREATE INDEX IF NOT EXISTS ix_deal_contact_deal
    ON dyno_crm.deal_contact (tenant_id, deal_id);


-- ======================================================================
-- Deal Contact Role Assignment
-- ======================================================================
-- PURPOSE
--   Assigns one or more tenant-defined roles to a specific deal-contact pair.
--   This keeps deal_contact as the membership link and role assignment as an extensible layer.
--
-- NOTES
--   - A deal_contact can have multiple role assignments.
--   - contact_role_data captures per-assignment metadata useful for automation.
--   - created_by / updated_by are soft links (VARCHAR), no foreign keys.
-- ======================================================================
CREATE TABLE IF NOT EXISTS dyno_crm.deal_contact_role_assignment (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    -- The deal-contact relationship being assigned a role
    deal_contact_id UUID NOT NULL,

    -- The role being assigned (from tenant-scoped role catalog)
    deal_contact_role_id UUID NOT NULL,

    -- Optional metadata for automation on this specific assignment
    -- Example keys: { "influence": "high", "confidence": 0.85, "verified_at": "..." }
    contact_role_data JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT fk_dcra_deal_contact
        FOREIGN KEY (tenant_id, deal_contact_id)
        REFERENCES dyno_crm.deal_contact (tenant_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED,

    CONSTRAINT fk_dcra_role
        FOREIGN KEY (tenant_id, deal_contact_role_id)
        REFERENCES dyno_crm.deal_participant_role (tenant_id, id)
        ON DELETE RESTRICT
        DEFERRABLE INITIALLY DEFERRED,

    -- Prevent duplicate role assignment to the same deal_contact
    CONSTRAINT ux_dcra_unique UNIQUE (tenant_id, deal_contact_id, deal_contact_role_id)
);

CREATE INDEX IF NOT EXISTS ix_dcra_by_deal_contact
    ON dyno_crm.deal_contact_role_assignment (tenant_id, deal_contact_id);

CREATE INDEX IF NOT EXISTS ix_dcra_by_role
    ON dyno_crm.deal_contact_role_assignment (tenant_id, deal_contact_role_id);


-- ----------------------------------------------------------------------
-- Deal User
-- ----------------------------------------------------------------------
-- PURPOSE
--   Many-to-many deal <-> user association (internal Dyno CRM users).
--   Similar to deal_contact but for internal users (sales reps, account managers, etc.).  
CREATE TABLE IF NOT EXISTS dyno_crm.deal_user (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    deal_id UUID NOT NULL,
    user_id UUID NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Ensure the deal exists in the same tenant
    CONSTRAINT fk_deal_user_deal
        FOREIGN KEY (tenant_id, deal_id)
        REFERENCES dyno_crm.deal (tenant_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED,

    -- Ensure the user exists in the same tenant
    CONSTRAINT fk_deal_user_user
        FOREIGN KEY (tenant_id, user_id)
        REFERENCES dyno_crm.tenant_user_shadow (tenant_id, user_id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED,

    -- Prevent duplicate membership rows for the same deal-user pair
    CONSTRAINT ux_deal_user UNIQUE (tenant_id, deal_id, user_id),

    -- Required so role-assignment table can FK to (tenant_id, id)
    CONSTRAINT ux_deal_user_tenant_id UNIQUE (tenant_id, id)
);

-- ======================================================================
-- Deal User Role Assignment
-- ======================================================================
-- PURPOSE
--   Assigns one or more tenant-defined roles to a specific deal-user pair.
--   This keeps deal_user as the membership link and role assignment as an extensible layer.
CREATE TABLE IF NOT EXISTS dyno_crm.deal_user_role_assignment (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    -- The deal-user relationship being assigned a role
    deal_user_id UUID NOT NULL,

    -- The role being assigned (from tenant-scoped role catalog)
    deal_participant_role_id UUID NOT NULL,

    -- Optional metadata for automation on this specific assignment
    user_role_data JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT fk_dura_deal_user
        FOREIGN KEY (tenant_id, deal_user_id)
        REFERENCES dyno_crm.deal_user (tenant_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED,

    CONSTRAINT fk_dura_role
        FOREIGN KEY (tenant_id, deal_participant_role_id)
        REFERENCES dyno_crm.deal_participant_role (tenant_id, id)
        ON DELETE RESTRICT
        DEFERRABLE INITIALLY DEFERRED,

    -- Prevent duplicate role assignment to the same deal_user
    CONSTRAINT ux_dura_unique UNIQUE (tenant_id, deal_user_id, deal_participant_role_id)
);

CREATE INDEX IF NOT EXISTS ix_dura_by_deal_user
    ON dyno_crm.deal_user_role_assignment (tenant_id, deal_user_id);
CREATE INDEX IF NOT EXISTS ix_dura_by_role
    ON dyno_crm.deal_user_role_assignment (tenant_id, deal_participant_role_id);



-- ----------------------------------------------------------------------
-- 3) DEAL_NOTE: deal-scoped notes (persist across all stages)
-- ----------------------------------------------------------------------
-- Purpose:
--   Notes that travel with the deal regardless of stage; useful for handoff after close.
-- deleted/deleted_at:
--   Soft delete for UI behavior; retained for audit/history.
CREATE TABLE IF NOT EXISTS dyno_crm.deal_note (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    deal_id UUID NOT NULL,

    -- The note body
    note TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by VARCHAR(100),

    CONSTRAINT fk_deal_note_deal
        FOREIGN KEY (tenant_id, deal_id)
        REFERENCES dyno_crm.deal (tenant_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS ix_deal_note_deal
    ON dyno_crm.deal_note (tenant_id, deal_id);

CREATE INDEX IF NOT EXISTS ix_deal_note_active
    ON dyno_crm.deal_note (tenant_id, deal_id, created_at)
    WHERE deleted = FALSE;


-- ----------------------------------------------------------------------
-- 4) DEAL_ATTACHMENT: deal-scoped attachments (persist across all stages)
-- ----------------------------------------------------------------------
-- Purpose:
--   Attachments that travel with the deal regardless of stage (e.g., signed contract).
CREATE TABLE IF NOT EXISTS dyno_crm.deal_attachment (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    deal_id UUID NOT NULL,

    -- External URL reference to the file (S3, GCS, etc.)
    file_url VARCHAR(500) NOT NULL,
    file_name VARCHAR(255),
    file_size_bytes INTEGER,
    file_mime_type VARCHAR(100),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by VARCHAR(100),

    CONSTRAINT fk_deal_attachment_deal
        FOREIGN KEY (tenant_id, deal_id)
        REFERENCES dyno_crm.deal (tenant_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS ix_deal_attachment_deal
    ON dyno_crm.deal_attachment (tenant_id, deal_id);

CREATE INDEX IF NOT EXISTS ix_deal_attachment_active
    ON dyno_crm.deal_attachment (tenant_id, deal_id, created_at)
    WHERE deleted = FALSE;


-- ======================================================================
-- Stage-instance state + stage-scoped artifacts
-- ======================================================================

-- ----------------------------------------------------------------------
-- 5) DEAL_PIPELINE_STAGE_STATE: stage instance rows
-- ----------------------------------------------------------------------
-- Tracks each time a deal is in a given pipeline stage (re-entry supported).
-- Composite FK enforces that pipeline_stage_id belongs to pipeline_id.
CREATE TABLE IF NOT EXISTS dyno_crm.deal_pipeline_stage_state (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    -- The deal this stage-instance belongs to
    deal_id UUID NOT NULL,

    -- The pipeline context for this stage-instance
    pipeline_id UUID NOT NULL,

    -- The pipeline stage (must belong to pipeline_id via composite FK below)
    pipeline_stage_id UUID NOT NULL,

    -- The previous stage before entering this one (nullable for first stage)
    previous_pipeline_stage_id UUID,

    -- Next stage after this stage (nullable)
    next_pipeline_stage_id UUID,

    -- TRUE only for the currently active stage-instance for this deal
    is_current BOOLEAN NOT NULL DEFAULT FALSE,

    -- Stage-specific structured data (checklists, key values, workflow payload, etc.)
    pipeline_stage_data JSONB,

    -- When the deal entered this stage instance; when it exited (if closed out)
    entered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    exited_at TIMESTAMPTZ,

    CONSTRAINT fk_deal_pipeline_stage_state_deal
        FOREIGN KEY (tenant_id, deal_id)
        REFERENCES dyno_crm.deal (tenant_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED,

    CONSTRAINT fk_deal_pipeline_stage_state_pipeline
        FOREIGN KEY (tenant_id, pipeline_id)
        REFERENCES dyno_crm.pipeline (tenant_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED,

    -- Enforce that pipeline_stage_id belongs to pipeline_id (tenant safe)
    CONSTRAINT fk_dpstage_state_pipeline_stage_belongs_to_pipeline
        FOREIGN KEY (tenant_id, pipeline_id, pipeline_stage_id)
        REFERENCES dyno_crm.pipeline_stage (tenant_id, pipeline_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED,

    -- Previous stage FK (nullable)
    CONSTRAINT fk_deal_pipeline_stage_state_previous_stage
        FOREIGN KEY (tenant_id, previous_pipeline_stage_id)
        REFERENCES dyno_crm.pipeline_stage (tenant_id, id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED,

    -- Next stage FK (nullable)
    CONSTRAINT fk_deal_pipeline_stage_state_next_stage
        FOREIGN KEY (tenant_id, next_pipeline_stage_id)
        REFERENCES dyno_crm.pipeline_stage (tenant_id, id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED,

    -- Support tenant+id FKs from child tables
    CONSTRAINT ux_deal_pipeline_stage_state_tenant_id
        UNIQUE (tenant_id, id)
);

CREATE INDEX IF NOT EXISTS ix_deal_pipeline_stage_state_deal
    ON dyno_crm.deal_pipeline_stage_state (tenant_id, deal_id);

CREATE INDEX IF NOT EXISTS ix_deal_pipeline_stage_state_pipeline
    ON dyno_crm.deal_pipeline_stage_state (tenant_id, pipeline_id);

CREATE INDEX IF NOT EXISTS ix_deal_pipeline_stage_state_stage
    ON dyno_crm.deal_pipeline_stage_state (tenant_id, pipeline_stage_id);

CREATE INDEX IF NOT EXISTS ix_deal_pipeline_stage_state_current_by_deal
    ON dyno_crm.deal_pipeline_stage_state (tenant_id, deal_id)
    WHERE is_current = TRUE;

CREATE UNIQUE INDEX IF NOT EXISTS ux_deal_pipeline_stage_state_one_current
    ON dyno_crm.deal_pipeline_stage_state (tenant_id, deal_id)
    WHERE is_current = TRUE;

ALTER TABLE dyno_crm.deal_pipeline_stage_state
    ADD CONSTRAINT ck_deal_pipeline_stage_state_exit_after_enter
    CHECK (exited_at IS NULL OR exited_at >= entered_at);


-- ----------------------------------------------------------------------
-- 6) DEAL_PIPELINE_STAGE_NOTE: stage-scoped notes (tied to a stage instance)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.deal_pipeline_stage_note (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    -- The specific stage instance this note belongs to
    deal_pipeline_stage_state_id UUID NOT NULL,

    -- Convenience pointer to the deal
    deal_id UUID NOT NULL,

    note TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by VARCHAR(100),

    CONSTRAINT fk_deal_pipeline_stage_note_state
        FOREIGN KEY (tenant_id, deal_pipeline_stage_state_id)
        REFERENCES dyno_crm.deal_pipeline_stage_state (tenant_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED,

    CONSTRAINT fk_deal_pipeline_stage_note_deal
        FOREIGN KEY (tenant_id, deal_id)
        REFERENCES dyno_crm.deal (tenant_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS ix_deal_pipeline_stage_note_state
    ON dyno_crm.deal_pipeline_stage_note (tenant_id, deal_pipeline_stage_state_id);

CREATE INDEX IF NOT EXISTS ix_deal_pipeline_stage_note_deal
    ON dyno_crm.deal_pipeline_stage_note (tenant_id, deal_id);

CREATE INDEX IF NOT EXISTS ix_deal_pipeline_stage_note_active
    ON dyno_crm.deal_pipeline_stage_note (tenant_id, deal_id, created_at)
    WHERE deleted = FALSE;


-- ----------------------------------------------------------------------
-- 7) DEAL_PIPELINE_STAGE_ATTACHMENT: stage-scoped attachments (tied to a stage instance)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.deal_pipeline_stage_attachment (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    -- The specific stage instance this attachment belongs to
    deal_pipeline_stage_state_id UUID NOT NULL,

    -- Convenience pointer to the deal
    deal_id UUID NOT NULL,

    file_url VARCHAR(500) NOT NULL,
    file_name VARCHAR(255),
    file_size_bytes INTEGER,
    file_mime_type VARCHAR(100),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by VARCHAR(100),

    CONSTRAINT fk_deal_pipeline_stage_attachment_state
        FOREIGN KEY (tenant_id, deal_pipeline_stage_state_id)
        REFERENCES dyno_crm.deal_pipeline_stage_state (tenant_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED,

    CONSTRAINT fk_deal_pipeline_stage_attachment_deal
        FOREIGN KEY (tenant_id, deal_id)
        REFERENCES dyno_crm.deal (tenant_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS ix_deal_pipeline_stage_attachment_state
    ON dyno_crm.deal_pipeline_stage_attachment (tenant_id, deal_pipeline_stage_state_id);

CREATE INDEX IF NOT EXISTS ix_deal_pipeline_stage_attachment_deal
    ON dyno_crm.deal_pipeline_stage_attachment (tenant_id, deal_id);

CREATE INDEX IF NOT EXISTS ix_deal_pipeline_stage_attachment_active
    ON dyno_crm.deal_pipeline_stage_attachment (tenant_id, deal_id, created_at)
    WHERE deleted = FALSE;


-- ----------------------------------------------------------------------
-- CLEANUP
-- ----------------------------------------------------------------------
-- Drops the legacy stage_history table. This should only be run if the new
-- stage-instance model is the system of record and no remaining objects
-- reference dyno_crm.stage_history via foreign keys.
DROP TABLE IF EXISTS dyno_crm.stage_history;

-- ADD WORKFLOW to pipeline_movement_mode
ALTER TYPE dyno_crm.pipeline_movement_mode ADD VALUE IF NOT EXISTS 'WORKFLOW';

-- drop column object_type
ALTER TABLE dyno_crm.pipeline
    DROP CONSTRAINT IF EXISTS ux_pipeline_tenant_object,
    DROP COLUMN IF EXISTS object_type;

-- DROP pipeline_object_type
DROP TYPE IF EXISTS dyno_crm.pipeline_object_type;
DROP TYPE IF EXISTS dyno_crm.pipeline_stage_type;

-- ----------------------------------------------------------------------
-- MODIFY PIPELINE_STAGE.STATE ENUM
-- ----------------------------------------------------------------------
-- Migrate existing pipeline_stage.stage_state enum to new values:
--   NOT_STARTED  -> OPEN
--   IN_PROGRESS  -> OPEN
--   DONE_SUCCESS -> WON
--   DONE_FAILED  -> LOST

-- 1) Rename the existing enum type out of the way
ALTER TYPE dyno_crm.pipeline_stage_state
RENAME TO pipeline_stage_state_old;

-- 2) Create the new enum type
CREATE TYPE dyno_crm.pipeline_stage_state AS ENUM (
  'OPEN',
  'WON',
  'LOST'
);

-- 3) Drop the default temporarily (required because it references the old enum type)
ALTER TABLE dyno_crm.pipeline_stage
  ALTER COLUMN stage_state DROP DEFAULT;

-- 4) Convert the column to the new enum, mapping old values -> new values
ALTER TABLE dyno_crm.pipeline_stage
  ALTER COLUMN stage_state TYPE dyno_crm.pipeline_stage_state
  USING (
    CASE stage_state::text
      WHEN 'NOT_STARTED'  THEN 'OPEN'::dyno_crm.pipeline_stage_state
      WHEN 'IN_PROGRESS'  THEN 'OPEN'::dyno_crm.pipeline_stage_state
      WHEN 'DONE_SUCCESS' THEN 'WON'::dyno_crm.pipeline_stage_state
      WHEN 'DONE_FAILED'  THEN 'LOST'::dyno_crm.pipeline_stage_state
      ELSE NULL
    END
  );

-- 5) Re-apply an appropriate default
ALTER TABLE dyno_crm.pipeline_stage
  ALTER COLUMN stage_state SET DEFAULT 'OPEN';

-- 6) Drop the old enum type
DROP TYPE dyno_crm.pipeline_stage_state_old;
