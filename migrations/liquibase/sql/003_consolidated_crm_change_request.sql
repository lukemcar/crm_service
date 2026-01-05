-- ======================================================================
-- Dyno CRM – Consolidated CRM Change Request (Domain-by-Domain)
-- ======================================================================
-- liquibase formatted sql
-- changeset crm_service:003_consolidated_crm_change_request

SET search_path TO public, dyno_crm;

-- ----------------------------------------------------------------------
-- 1. Enumeration types
-- ----------------------------------------------------------------------
-- These enums support record typing, automation scoping, action types,
-- pipeline/stage semantics (JIRA-style), list processing, deal categories
-- and principal identification.

-- Record typing (used by polymorphic tables; enforcement is application-layer)
DO $$ BEGIN
    CREATE TYPE dyno_crm.crm_record_type AS ENUM (
        'CONTACT', 'COMPANY', 'DEAL', 'LEAD', 'TICKET', 'ACTIVITY', 'PIPELINE', 'LIST'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Automation scope typing
DO $$ BEGIN
    CREATE TYPE dyno_crm.automation_scope_type AS ENUM (
        'RECORD', 'PIPELINE', 'PIPELINE_STAGE', 'LIST', 'ENTITY'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Automation action typing
DO $$ BEGIN
    CREATE TYPE dyno_crm.automation_action_type AS ENUM (
        'WEBHOOK', 'WORKFLOW', 'EVENT', 'AIWORKER'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Automation execution status
DO $$ BEGIN
    CREATE TYPE dyno_crm.action_execution_status AS ENUM (
        'PENDING', 'IN_PROGRESS', 'SUCCEEDED', 'FAILED'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ----------------------------------------------------------------------
-- Pipeline + Stage (JIRA-style) semantics
-- ----------------------------------------------------------------------
-- Pipeline object type defines which domain entity uses the pipeline.
DO $$ BEGIN
    CREATE TYPE dyno_crm.pipeline_object_type AS ENUM (
        'COMPANY', 'CONTACT', 'DEAL', 'LEAD', 'TICKET'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Pipeline movement mode controls whether transitions are flexible or enforced.
DO $$ BEGIN
    CREATE TYPE dyno_crm.pipeline_movement_mode AS ENUM (
        'FLEXIBLE', 'ENFORCED'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Stage semantic category (JIRA status category equivalent).
-- NOTE: This intentionally replaces sales-only 'won/lost' stage semantics.
DO $$ BEGIN
    CREATE TYPE dyno_crm.pipeline_stage_state AS ENUM (
        'NOT_STARTED',
        'IN_PROGRESS',
        'DONE_SUCCESS',
        'DONE_FAILED'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Backward-compatibility enum retained (existing draft used stage_type open/won/lost).
-- Not used by the updated pipeline/stage design (stage_state replaces it).
DO $$ BEGIN
    CREATE TYPE dyno_crm.pipeline_stage_type AS ENUM (
        'OPEN', 'SUCCESS', 'FAILED'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- List processing semantics
DO $$ BEGIN
    CREATE TYPE dyno_crm.list_processing_type AS ENUM (
        'STATIC', 'DYNAMIC'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Deal categorization
DO $$ BEGIN
    CREATE TYPE dyno_crm.deal_type AS ENUM (
        'NEW', 'RENEWAL', 'UPSELL', 'OTHER'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Principal typing for watcher subscriptions
DO $$ BEGIN
    CREATE TYPE dyno_crm.principal_type AS ENUM (
        'USER', 'GROUP'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ----------------------------------------------------------------------
-- 2. Dynamic linking registries
-- ----------------------------------------------------------------------
-- REMOVED per requirement:
--   - record_watcher_record_registry
--   - record_watcher_principal_registry
--   - automation_action_record_registry
--
-- Polymorphic integrity is enforced in the application layer (and optionally
-- via triggers if desired later). No registry tables are used.

-- ----------------------------------------------------------------------
-- 3. Record watcher
-- ----------------------------------------------------------------------
-- Unified watchers mechanism across all domains.
-- Watchers subscribe users or groups to changes on a record.
-- Polymorphic record/principal integrity is application-layer enforced.
CREATE TABLE IF NOT EXISTS dyno_crm.record_watcher (
    tenant_id          UUID                     NOT NULL,
    record_type        dyno_crm.crm_record_type NOT NULL,
    record_id          UUID                     NOT NULL,
    principal_type     dyno_crm.principal_type  NOT NULL,
    principal_id       UUID                     NOT NULL,
    created_at         TIMESTAMPTZ              NOT NULL DEFAULT NOW(),
    created_by_user_id UUID,
    PRIMARY KEY (tenant_id, record_type, record_id, principal_type, principal_id)
);

-- Indexes to retrieve watchers by principal or record quickly
CREATE INDEX IF NOT EXISTS ix_record_watcher_by_principal
    ON dyno_crm.record_watcher (tenant_id, principal_type, principal_id);

CREATE INDEX IF NOT EXISTS ix_record_watcher_by_record
    ON dyno_crm.record_watcher (tenant_id, record_type, record_id);

-- ----------------------------------------------------------------------
-- 4. Automation actions
-- ----------------------------------------------------------------------
-- Before creating automation actions we need to ensure that child tables
-- include tenant/id composite uniqueness for foreign keys.
ALTER TABLE dyno_crm.pipeline_stage
    ADD CONSTRAINT ux_pipeline_stage_id_tenant UNIQUE (id, tenant_id);

ALTER TABLE dyno_crm.list
    ADD CONSTRAINT ux_list_id_tenant UNIQUE (id, tenant_id);

-- ----------------------------------------------------------------------
-- automation_action – Declarative Automation Rules
-- ----------------------------------------------------------------------
-- PURPOSE
-- This table defines declarative automation rules of the form:
--
--     “When X happens, do Y.”
--
-- Where:
--   • X = trigger_event + optional condition_json
--   • Y = action_type + config_json
--   • The rule applies to exactly ONE scope, defined by scope_type
--
-- This table is intentionally generic and supports all automation in the CRM:
--   • pipeline automation
--   • pipeline stage automation
--   • list membership automation
--   • record-specific one-off automation
--   • global (entity-wide) automation
--
-- Polymorphic integrity (record existence, principal validity, etc.)
-- is enforced at the APPLICATION LAYER for performance reasons in a
-- multi-tenant system. The database enforces STRUCTURAL correctness only.
--
-- ----------------------------------------------------------------------
-- SCOPES (scope_type)
--
-- Each automation_action row MUST target exactly ONE scope.
-- The CHECK constraint ck_automation_action_scope_targets enforces this.
--
-- 1) ENTITY
--    Meaning:
--      Apply to ALL records of the given entity_type within the tenant.
--
--    Example:
--      “When ANY deal is created, run AI enrichment.”
--
--    Required:
--      • scope_type = 'ENTITY'
--      • entity_type = DEAL (or CONTACT, TICKET, etc.)
--
--    Forbidden (must be NULL):
--      • record_type, record_id
--      • pipeline_id
--      • pipeline_stage_id
--      • list_id
--
-- 2) PIPELINE
--    Meaning:
--      Apply to ALL records that belong to a specific pipeline.
--
--    Example:
--      “In the Enterprise Sales pipeline, when a deal is WON,
--       start onboarding workflow.”
--
--    Required:
--      • scope_type = 'PIPELINE'
--      • pipeline_id
--
--    Forbidden:
--      • record_type, record_id
--      • pipeline_stage_id
--      • list_id
--
-- 3) PIPELINE_STAGE
--    Meaning:
--      Apply ONLY when something happens at a specific pipeline stage.
--
--    Example:
--      “When a deal enters the ‘Proposal Sent’ stage,
--       send a proposal email.”
--
--    Required:
--      • scope_type = 'PIPELINE_STAGE'
--      • pipeline_stage_id
--
--    Forbidden:
--      • record_type, record_id
--      • pipeline_id
--      • list_id
--
--    NOTE: inherit_pipeline_actions applies ONLY to this scope.
--      • TRUE  = pipeline-level stage actions ALSO run
--      • FALSE = this stage overrides pipeline defaults
--
-- 4) LIST
--    Meaning:
--      Apply when membership changes for a specific list.
--
--    Example:
--      “When a contact is added to the ‘High Intent Leads’ list,
--       create an SDR task.”
--
--    Required:
--      • scope_type = 'LIST'
--      • list_id
--
--    Forbidden:
--      • record_type, record_id
--      • pipeline_id
--      • pipeline_stage_id
--
-- 5) RECORD
--    Meaning:
--      Apply ONLY to one specific record (rare but powerful).
--
--    Example:
--      “For this ONE VIP company record, notify executives
--       whenever it changes.”
--
--    Required:
--      • scope_type = 'RECORD'
--      • record_type
--      • record_id
--
--    Forbidden:
--      • pipeline_id
--      • pipeline_stage_id
--      • list_id
--
-- ----------------------------------------------------------------------
-- RUNTIME EVALUATION MODEL
--
-- When an event occurs (e.g., stage change, list membership change),
-- the automation engine evaluates actions in this logical order:
--
--   1) ENTITY actions (scope_type = ENTITY)
--   2) PIPELINE actions (matching pipeline_id)
--   3) PIPELINE_STAGE actions (matching stage_id)
--   4) LIST actions (matching list_id, for list events)
--   5) RECORD actions (matching record_type + record_id)
--
-- For each matching action:
--   • trigger_event must match
--   • condition_json (if present) must evaluate to true
--   • actions are sorted by priority (lower runs first)
--   • execution is recorded in automation_action_execution
--
-- ----------------------------------------------------------------------
-- WHY THE CHECK CONSTRAINT EXISTS
--
-- The CHECK constraint ensures:
--   • No action is ambiguous
--   • No action targets multiple scopes
--   • No action is missing its required target
--
-- Invalid examples that are BLOCKED:
--   • scope_type = PIPELINE but pipeline_id is NULL
--   • scope_type = LIST but both list_id and pipeline_id are set
--   • scope_type = RECORD but record_id is NULL
--
-- This keeps the automation system deterministic and debuggable.
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_crm.automation_action (
    id                  UUID                           PRIMARY KEY,
    tenant_id            UUID                           NOT NULL,

    -- The entity type the action is conceptually attached to (deal, ticket, etc.)
    entity_type          dyno_crm.crm_record_type        NOT NULL,

    -- Scope defines which target columns must be populated.
    scope_type           dyno_crm.automation_scope_type  NOT NULL,

    -- RECORD scope target (polymorphic; application-layer enforced)
    record_type          dyno_crm.crm_record_type,
    record_id            UUID,

    -- CONFIG scope targets (standard FKs)
    pipeline_id          UUID,
    pipeline_stage_id    UUID,
    list_id              UUID,

    trigger_event        VARCHAR(50)                    NOT NULL,
    condition_json       JSONB,
    action_type          dyno_crm.automation_action_type NOT NULL,
    config_json          JSONB                          NOT NULL,
    priority             INTEGER                        NOT NULL DEFAULT 100,
    enabled              BOOLEAN                        NOT NULL DEFAULT TRUE,

    -- Applies only to stage-scoped actions; governs additive vs override behavior.
    inherit_pipeline_actions BOOLEAN                     DEFAULT TRUE,

    created_at           TIMESTAMPTZ                    NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ                    NOT NULL DEFAULT NOW(),
    created_by           VARCHAR(100),
    updated_by           VARCHAR(100),

    CONSTRAINT ux_automation_action_tenant UNIQUE (tenant_id, id),

    -- Scope enforcement: exactly one target is set depending on scope_type.
    CONSTRAINT ck_automation_action_scope_targets CHECK (
        (
            scope_type = 'RECORD'
            AND record_type IS NOT NULL
            AND record_id IS NOT NULL
            AND pipeline_id IS NULL
            AND pipeline_stage_id IS NULL
            AND list_id IS NULL
        )
        OR (
            scope_type = 'PIPELINE'
            AND pipeline_id IS NOT NULL
            AND record_type IS NULL
            AND record_id IS NULL
            AND pipeline_stage_id IS NULL
            AND list_id IS NULL
        )
        OR (
            scope_type = 'PIPELINE_STAGE'
            AND pipeline_stage_id IS NOT NULL
            AND record_type IS NULL
            AND record_id IS NULL
            AND pipeline_id IS NULL
            AND list_id IS NULL
        )
        OR (
            scope_type = 'LIST'
            AND list_id IS NOT NULL
            AND record_type IS NULL
            AND record_id IS NULL
            AND pipeline_id IS NULL
            AND pipeline_stage_id IS NULL
        )
        OR (
            scope_type = 'ENTITY'
            AND record_type IS NULL
            AND record_id IS NULL
            AND pipeline_id IS NULL
            AND pipeline_stage_id IS NULL
            AND list_id IS NULL
        )
    )
);

-- Foreign keys for automation_action
-- PIPELINE
ALTER TABLE dyno_crm.automation_action
    ADD CONSTRAINT fk_automation_action_pipeline
        FOREIGN KEY (tenant_id, pipeline_id)
        REFERENCES dyno_crm.pipeline (tenant_id, id)
        ON DELETE RESTRICT
        DEFERRABLE INITIALLY DEFERRED;

-- PIPELINE_STAGE
ALTER TABLE dyno_crm.automation_action
    ADD CONSTRAINT fk_automation_action_pipeline_stage
        FOREIGN KEY (tenant_id, pipeline_stage_id)
        REFERENCES dyno_crm.pipeline_stage (tenant_id, id)
        ON DELETE RESTRICT
        DEFERRABLE INITIALLY DEFERRED;

-- LIST
ALTER TABLE dyno_crm.automation_action
    ADD CONSTRAINT fk_automation_action_list
        FOREIGN KEY (tenant_id, list_id)
        REFERENCES dyno_crm.list (tenant_id, id)
        ON DELETE RESTRICT
        DEFERRABLE INITIALLY DEFERRED;

-- Practical indexes (partial where possible)
CREATE INDEX IF NOT EXISTS ix_automation_action_record_target
    ON dyno_crm.automation_action (tenant_id, record_type, record_id)
    WHERE scope_type = 'RECORD';

CREATE INDEX IF NOT EXISTS ix_automation_action_pipeline_target
    ON dyno_crm.automation_action (tenant_id, pipeline_id)
    WHERE scope_type = 'PIPELINE';

CREATE INDEX IF NOT EXISTS ix_automation_action_stage_target
    ON dyno_crm.automation_action (tenant_id, pipeline_stage_id)
    WHERE scope_type = 'PIPELINE_STAGE';

CREATE INDEX IF NOT EXISTS ix_automation_action_list_target
    ON dyno_crm.automation_action (tenant_id, list_id)
    WHERE scope_type = 'LIST';

-- ----------------------------------------------------------------------
-- 5. Automation action execution
-- ----------------------------------------------------------------------

-- ----------------------------------------------------------------------
-- automation_action_execution – Execution Log + Idempotency Guard
-- ----------------------------------------------------------------------
-- PURPOSE
-- This table records EVERY attempt to execute an automation_action.
--
-- automation_action defines the rule ("When X happens, do Y").
-- automation_action_execution records the actual run ("We attempted to do Y
-- because X happened, here is what occurred").
--
-- This table exists for:
--   • auditability (what ran, when, and why)
--   • debugging (errors, response codes, outputs)
--   • idempotency (prevent duplicate side effects on retries)
--   • operational reporting (failure rates, average run time, backlog)
--
-- It is intentionally append-heavy:
--   • one row per action execution attempt
--   • updated in-place as status moves from PENDING -> IN_PROGRESS -> SUCCEEDED/FAILED
--
-- ----------------------------------------------------------------------
-- KEY CONCEPTS
--
-- 1) execution_key (IDEMPOTENCY)
-- execution_key is a deterministic identifier for "this exact execution."
-- It prevents duplicate execution caused by:
--   • message re-delivery
--   • automation engine retries
--   • race conditions
--
-- Uniqueness is enforced by:
--   CONSTRAINT ux_automation_action_execution_key UNIQUE (tenant_id, execution_key)
--
-- Operational meaning:
--   • If the automation engine attempts to create the same execution twice,
--     the second insert fails (or is treated as a no-op by the engine).
--   • This is how we guarantee "execute once" semantics at the DB layer,
--     even though the system is distributed.
--
-- Recommended execution_key composition (example):
--   tenant_id + action_id + trigger_event + entity_type + entity_id +
--   (optional transition id / list membership id / stage ids)
--
-- 2) STATUS LIFECYCLE
-- status is the state of the execution attempt:
--   • PENDING     = row created, execution not started yet
--   • IN_PROGRESS = execution started (webhook call in-flight, workflow running, etc.)
--   • SUCCEEDED   = execution completed successfully
--   • FAILED      = execution failed after retries or hard failure
--
-- 3) CONTEXT COLUMNS (WHY DID THIS RUN?)
-- These fields capture the triggering context so you can answer:
--   “What caused this to run?”
--
--   entity_type / entity_id:
--     The record the event relates to (deal, ticket, contact, etc.)
--
--   pipeline_id, from_stage_id, to_stage_id:
--     Present for stage-based events (stage transitions, dwell, won/lost style events)
--
--   list_id:
--     Present for list membership events (member added/removed)
--
--   trigger_event:
--     The specific event string that matched the action (ex: ON_STAGE_ENTER)
--
-- 4) RESULT CAPTURE (WHAT HAPPENED?)
-- response_code / response_body:
--   Captures outputs from the execution target:
--     • WEBHOOK: HTTP status + body
--     • WORKFLOW: engine result payload or status info
--     • EVENT: publish confirmation metadata
--     • AIWORKER: job id or result snapshot
--
-- error_message:
--   Set when status = FAILED (human-readable failure reason)
--
-- 5) TIMESTAMPS (WHEN DID IT RUN?)
-- triggered_at:
--   When the automation engine first processed the triggering event.
--
-- started_at / completed_at:
--   When execution began and ended (useful for latency + SLA reporting).
--
-- created_at:
--   DB audit timestamp for row creation.
--
-- ----------------------------------------------------------------------
-- FOREIGN KEY BEHAVIOR
--
-- action_id references automation_action via a tenant-scoped FK:
--   FOREIGN KEY (tenant_id, action_id) -> automation_action(tenant_id, id)
--
-- ON DELETE CASCADE:
--   If an automation_action is deleted, its execution history is deleted.
--   (If you later want long-term auditing independent of action definitions,
--   remove CASCADE and archive actions instead of deleting.)
--
-- DEFERRABLE INITIALLY DEFERRED:
--   Allows inserting execution rows in the same transaction as action changes
--   without immediate FK timing issues.
--
-- ----------------------------------------------------------------------
-- OPERATIONAL EXPECTATIONS
--
-- Insert pattern:
--   1) Insert row with status = PENDING and execution_key
--   2) Update status -> IN_PROGRESS when work starts
--   3) Update status -> SUCCEEDED/FAILED with response/error info
--
-- Query patterns:
--   • Find failures by tenant/time range/action_id/status
--   • Debug a specific entity_id timeline
--   • Measure average execution duration (completed_at - started_at)
--
-- This table is designed to support dashboards and troubleshooting without
-- requiring the automation engine logs to be the system of record.
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_crm.automation_action_execution (
    id                 UUID                          PRIMARY KEY,
    tenant_id           UUID                          NOT NULL,
    action_id           UUID                          NOT NULL,
    entity_type         dyno_crm.crm_record_type       NOT NULL,
    entity_id           UUID                          NOT NULL,
    pipeline_id         UUID,
    from_stage_id       UUID,
    to_stage_id         UUID,
    list_id             UUID,
    trigger_event       VARCHAR(50)                   NOT NULL,
    execution_key       VARCHAR(255)                  NOT NULL,
    status              dyno_crm.action_execution_status NOT NULL DEFAULT 'PENDING',
    response_code       INTEGER,
    response_body       JSONB,
    error_message       TEXT,
    triggered_at        TIMESTAMPTZ                   NOT NULL DEFAULT NOW(),
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ                   NOT NULL DEFAULT NOW(),
    CONSTRAINT ux_automation_action_execution_key UNIQUE (tenant_id, execution_key),
    CONSTRAINT fk_automation_action_execution_action
        FOREIGN KEY (tenant_id, action_id)
        REFERENCES dyno_crm.automation_action (tenant_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS ix_automation_action_execution_status
    ON dyno_crm.automation_action_execution (tenant_id, action_id, status);

CREATE INDEX IF NOT EXISTS ix_automation_action_execution_entity
    ON dyno_crm.automation_action_execution (tenant_id, entity_type, entity_id);

-- ----------------------------------------------------------------------
-- 6. Stage history
-- ----------------------------------------------------------------------
-- Records when a stage change happens for any stage-based entity.
CREATE TABLE IF NOT EXISTS dyno_crm.stage_history (
    id                 UUID                     PRIMARY KEY,
    tenant_id          UUID                     NOT NULL,
    entity_type        dyno_crm.crm_record_type NOT NULL,
    entity_id          UUID                     NOT NULL,
    pipeline_id        UUID,
    from_stage_id      UUID,
    to_stage_id        UUID,
    changed_at         TIMESTAMPTZ              NOT NULL DEFAULT NOW(),
    changed_by_user_id UUID,
    source             VARCHAR(50),
    CONSTRAINT fk_stage_history_pipeline
        FOREIGN KEY (tenant_id, pipeline_id)
        REFERENCES dyno_crm.pipeline (tenant_id, id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_stage_history_from_stage
        FOREIGN KEY (tenant_id, from_stage_id)
        REFERENCES dyno_crm.pipeline_stage (tenant_id, id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_stage_history_to_stage
        FOREIGN KEY (tenant_id, to_stage_id)
        REFERENCES dyno_crm.pipeline_stage (tenant_id, id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX IF NOT EXISTS ix_stage_history_entity
    ON dyno_crm.stage_history (tenant_id, entity_type, entity_id);

CREATE INDEX IF NOT EXISTS ix_stage_history_pipeline
    ON dyno_crm.stage_history (tenant_id, pipeline_id);

-- ----------------------------------------------------------------------
-- 7. Pipeline enhancements (JIRA-style)
-- ----------------------------------------------------------------------
-- Add fields to support multiple pipelines per object type, ordering,
-- archiving, stable API pipeline_key, and movement enforcement mode.

ALTER TABLE dyno_crm.pipeline
    ADD COLUMN IF NOT EXISTS object_type dyno_crm.pipeline_object_type,
    ADD COLUMN IF NOT EXISTS display_order INTEGER,
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS pipeline_key VARCHAR(100),
    ADD COLUMN IF NOT EXISTS movement_mode dyno_crm.pipeline_movement_mode NOT NULL DEFAULT 'FLEXIBLE';

-- Backfill for new NOT NULL expectations
UPDATE dyno_crm.pipeline
SET object_type = 'DEAL'
WHERE object_type IS NULL;

UPDATE dyno_crm.pipeline
SET pipeline_key = 'pipeline_' || left(replace(id::text, '-', ''), 12)
WHERE pipeline_key IS NULL;

WITH ranked AS (
    SELECT
        id,
        tenant_id,
        object_type,
        row_number() OVER (PARTITION BY tenant_id, object_type ORDER BY created_at, id) AS rn
    FROM dyno_crm.pipeline
    WHERE display_order IS NULL
)
UPDATE dyno_crm.pipeline p
SET display_order = r.rn
FROM ranked r
WHERE p.id = r.id AND p.tenant_id = r.tenant_id;

-- Enforce required columns
ALTER TABLE dyno_crm.pipeline
    ALTER COLUMN object_type SET NOT NULL,
    ALTER COLUMN display_order SET NOT NULL,
    ALTER COLUMN pipeline_key SET NOT NULL;

ALTER TABLE dyno_crm.pipeline
    ADD CONSTRAINT ux_pipeline_tenant_object_key
        UNIQUE (tenant_id, object_type, pipeline_key);

ALTER TABLE dyno_crm.pipeline
    ADD CONSTRAINT ux_pipeline_tenant_object_display_order
        UNIQUE (tenant_id, object_type, display_order);

CREATE INDEX IF NOT EXISTS ix_pipeline_tenant_object_type
    ON dyno_crm.pipeline (tenant_id, object_type);

-- ----------------------------------------------------------------------
-- 8. Pipeline stage enhancements (JIRA-style)
-- ----------------------------------------------------------------------
-- Rename stage_order to display_order if present.
ALTER TABLE dyno_crm.pipeline_stage RENAME COLUMN stage_order TO display_order;

-- Add stage_state and inherit_pipeline_actions.
ALTER TABLE dyno_crm.pipeline_stage
    ADD COLUMN IF NOT EXISTS stage_state dyno_crm.pipeline_stage_state NOT NULL DEFAULT 'NOT_STARTED',
    ADD COLUMN IF NOT EXISTS inherit_pipeline_actions BOOLEAN NOT NULL DEFAULT TRUE;

-- Enforce probability range [0,1] when provided.
ALTER TABLE dyno_crm.pipeline_stage
    ADD CONSTRAINT ck_pipeline_stage_probability_range
    CHECK (probability IS NULL OR (probability >= 0 AND probability <= 1));

-- Replace old ordering index with one on display_order.
DROP INDEX IF EXISTS dyno_crm.ux_pipeline_stage_pipeline_order;
DROP INDEX IF EXISTS dyno_crm.ux_pipeline_stage_pipeline_display_order;

CREATE UNIQUE INDEX IF NOT EXISTS ux_pipeline_stage_pipeline_display_order
    ON dyno_crm.pipeline_stage (pipeline_id, display_order);

-- ----------------------------------------------------------------------
-- 9. List enhancements
-- ----------------------------------------------------------------------
ALTER TABLE dyno_crm.list
    ADD COLUMN IF NOT EXISTS processing_type dyno_crm.list_processing_type NOT NULL DEFAULT 'STATIC',
    ADD COLUMN IF NOT EXISTS is_archived BOOLEAN NOT NULL DEFAULT FALSE;

-- ----------------------------------------------------------------------
-- 10. Ownership and assignment for core entities
-- ----------------------------------------------------------------------
-- Relationship-centric entities get ownership; work-centric entities get assignment.

-- Contact
ALTER TABLE dyno_crm.contact
    ADD COLUMN IF NOT EXISTS owned_by_user_id UUID,
    ADD COLUMN IF NOT EXISTS owned_by_group_id UUID;

ALTER TABLE dyno_crm.contact
    ADD CONSTRAINT fk_contact_owner_user
        FOREIGN KEY (tenant_id, owned_by_user_id)
        REFERENCES dyno_crm.tenant_user_shadow (tenant_id, user_id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE dyno_crm.contact
    ADD CONSTRAINT fk_contact_owner_group
        FOREIGN KEY (tenant_id, owned_by_group_id)
        REFERENCES dyno_crm.tenant_group_shadow (tenant_id, id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX IF NOT EXISTS ix_contact_owner_user
    ON dyno_crm.contact (tenant_id, owned_by_user_id);

CREATE INDEX IF NOT EXISTS ix_contact_owner_group
    ON dyno_crm.contact (tenant_id, owned_by_group_id);

-- Company
ALTER TABLE dyno_crm.company
    ADD COLUMN IF NOT EXISTS owned_by_user_id UUID,
    ADD COLUMN IF NOT EXISTS owned_by_group_id UUID;

ALTER TABLE dyno_crm.company
    ADD CONSTRAINT fk_company_owner_user
        FOREIGN KEY (tenant_id, owned_by_user_id)
        REFERENCES dyno_crm.tenant_user_shadow (tenant_id, user_id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE dyno_crm.company
    ADD CONSTRAINT fk_company_owner_group
        FOREIGN KEY (tenant_id, owned_by_group_id)
        REFERENCES dyno_crm.tenant_group_shadow (tenant_id, id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX IF NOT EXISTS ix_company_owner_user
    ON dyno_crm.company (tenant_id, owned_by_user_id);

CREATE INDEX IF NOT EXISTS ix_company_owner_group
    ON dyno_crm.company (tenant_id, owned_by_group_id);

-- Deal
ALTER TABLE dyno_crm.deal
    ADD COLUMN IF NOT EXISTS owned_by_user_id UUID,
    ADD COLUMN IF NOT EXISTS owned_by_group_id UUID,
    ADD COLUMN IF NOT EXISTS assigned_user_id UUID,
    ADD COLUMN IF NOT EXISTS assigned_group_id UUID,
    ADD COLUMN IF NOT EXISTS deal_type dyno_crm.deal_type,
    ADD COLUMN IF NOT EXISTS forecast_probability NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS close_date DATE;

ALTER TABLE dyno_crm.deal
    ADD CONSTRAINT fk_deal_owner_user
        FOREIGN KEY (tenant_id, owned_by_user_id)
        REFERENCES dyno_crm.tenant_user_shadow (tenant_id, user_id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE dyno_crm.deal
    ADD CONSTRAINT fk_deal_owner_group
        FOREIGN KEY (tenant_id, owned_by_group_id)
        REFERENCES dyno_crm.tenant_group_shadow (tenant_id, id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE dyno_crm.deal
    ADD CONSTRAINT fk_deal_assigned_user
        FOREIGN KEY (tenant_id, assigned_user_id)
        REFERENCES dyno_crm.tenant_user_shadow (tenant_id, user_id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE dyno_crm.deal
    ADD CONSTRAINT fk_deal_assigned_group
        FOREIGN KEY (tenant_id, assigned_group_id)
        REFERENCES dyno_crm.tenant_group_shadow (tenant_id, id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX IF NOT EXISTS ix_deal_owner_user
    ON dyno_crm.deal (tenant_id, owned_by_user_id);

CREATE INDEX IF NOT EXISTS ix_deal_owner_group
    ON dyno_crm.deal (tenant_id, owned_by_group_id);

CREATE INDEX IF NOT EXISTS ix_deal_assigned_user
    ON dyno_crm.deal (tenant_id, assigned_user_id);

CREATE INDEX IF NOT EXISTS ix_deal_assigned_group
    ON dyno_crm.deal (tenant_id, assigned_group_id);

-- Lead
ALTER TABLE dyno_crm.lead
    ADD COLUMN IF NOT EXISTS owned_by_user_id UUID,
    ADD COLUMN IF NOT EXISTS owned_by_group_id UUID;

ALTER TABLE dyno_crm.lead
    ADD CONSTRAINT fk_lead_owner_user
        FOREIGN KEY (tenant_id, owned_by_user_id)
        REFERENCES dyno_crm.tenant_user_shadow (tenant_id, user_id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE dyno_crm.lead
    ADD CONSTRAINT fk_lead_owner_group
        FOREIGN KEY (tenant_id, owned_by_group_id)
        REFERENCES dyno_crm.tenant_group_shadow (tenant_id, id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX IF NOT EXISTS ix_lead_owner_user
    ON dyno_crm.lead (tenant_id, owned_by_user_id);

CREATE INDEX IF NOT EXISTS ix_lead_owner_group
    ON dyno_crm.lead (tenant_id, owned_by_group_id);

-- ----------------------------------------------------------------------
-- 11. Activity enhancements
-- ----------------------------------------------------------------------
ALTER TABLE dyno_crm.activity RENAME COLUMN type TO activity_type;


ALTER TABLE dyno_crm.activity
    ADD COLUMN IF NOT EXISTS activity_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS created_by_user_id UUID,
    ADD COLUMN IF NOT EXISTS assigned_group_id UUID,
    ADD COLUMN IF NOT EXISTS details_json JSONB;

ALTER TABLE dyno_crm.activity
    ADD CONSTRAINT fk_activity_created_by_user
        FOREIGN KEY (tenant_id, created_by_user_id)
        REFERENCES dyno_crm.tenant_user_shadow (tenant_id, user_id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE dyno_crm.activity
    ADD CONSTRAINT fk_activity_assigned_group
        FOREIGN KEY (tenant_id, assigned_group_id)
        REFERENCES dyno_crm.tenant_group_shadow (tenant_id, id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX IF NOT EXISTS ix_activity_assigned_to_user
    ON dyno_crm.activity (tenant_id, assigned_user_id);

CREATE INDEX IF NOT EXISTS ix_activity_assigned_to_group
    ON dyno_crm.activity (tenant_id, assigned_group_id);

CREATE INDEX IF NOT EXISTS ix_activity_created_by_user
    ON dyno_crm.activity (tenant_id, created_by_user_id);

-- End of consolidated change request


-- ======================================================================
-- Dyno CRM – List Object Type Enum Migration
-- ======================================================================
-- liquibase formatted sql
-- changeset crm_service:004_list_object_type_enum

SET search_path TO public, dyno_crm;

-- ----------------------------------------------------------------------
-- 1) Define enum for list object/member types
-- ----------------------------------------------------------------------
DO $$ BEGIN
    CREATE TYPE dyno_crm.list_object_type AS ENUM (
        'CONTACT',
        'COMPANY',
        'DEAL',
        'LEAD',
        'TICKET',
        'ACTIVITY'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ----------------------------------------------------------------------
-- 2) Normalize existing data so it can safely cast to the enum
-- ----------------------------------------------------------------------
-- Normalize list.object_type
UPDATE dyno_crm.list
SET object_type = upper(object_type)
WHERE object_type IS NOT NULL
  AND object_type <> upper(object_type);

-- Normalize list_membership.member_type
UPDATE dyno_crm.list_membership
SET member_type = upper(member_type)
WHERE member_type IS NOT NULL
  AND member_type <> upper(member_type);

-- ----------------------------------------------------------------------
-- 3) Convert list.object_type from VARCHAR -> ENUM
-- ----------------------------------------------------------------------
-- Convert only if column is still varchar/text (idempotent safety)
DO $$ BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'dyno_crm'
          AND table_name = 'list'
          AND column_name = 'object_type'
          AND data_type IN ('character varying','text')
    ) THEN
        EXECUTE $sql$
            ALTER TABLE dyno_crm.list
            ALTER COLUMN object_type
            TYPE dyno_crm.list_object_type
            USING object_type::dyno_crm.list_object_type
        $sql$;
    END IF;
END $$;

-- ----------------------------------------------------------------------
-- 4) Convert list_membership.member_type from VARCHAR -> ENUM
-- ----------------------------------------------------------------------
DO $$ BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'dyno_crm'
          AND table_name = 'list_membership'
          AND column_name = 'member_type'
          AND data_type IN ('character varying','text')
    ) THEN
        EXECUTE $sql$
            ALTER TABLE dyno_crm.list_membership
            ALTER COLUMN member_type
            TYPE dyno_crm.list_object_type
            USING member_type::dyno_crm.list_object_type
        $sql$;
    END IF;
END $$;

-- ----------------------------------------------------------------------
-- 5) Optional: Add helpful indexes (safe + aligned with query patterns)
-- ----------------------------------------------------------------------
-- Many queries will want: all memberships for a list filtered by type
CREATE INDEX IF NOT EXISTS ix_list_membership_list_type
    ON dyno_crm.list_membership (list_id, member_type);

-- Many queries will want: all lists for a tenant by object_type
CREATE INDEX IF NOT EXISTS ix_list_tenant_object_type
    ON dyno_crm.list (tenant_id, object_type);

