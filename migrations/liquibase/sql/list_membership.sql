-- ----------------------------------------------------------------------
-- Enum Definitions: List types and membership content rules
-- ----------------------------------------------------------------------

DO $$ BEGIN
    -- List may be STATIC (manual members) or DYNAMIC (criteria-driven).
    CREATE TYPE dyno_crm.crm_list_type AS ENUM ('STATIC', 'DYNAMIC');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    -- Determines whether a list allows one object type or multiple types.
    CREATE TYPE dyno_crm.crm_list_content_type AS ENUM ('SINGLE', 'MIXED');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    -- The supported CRM object types that can be members of a list.
    CREATE TYPE dyno_crm.crm_member_type AS ENUM ('CONTACT', 'COMPANY', 'LEAD', 'DEAL', 'TICKET', 'ACTIVITY');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;


-- ----------------------------------------------------------------------
-- Table: dyno_crm.list
-- Defines a CRM list. May be static or dynamic, single-type or mixed-type.
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_crm.list (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    name VARCHAR(255) NOT NULL,              -- Display name of the list
    slug VARCHAR(255) NOT NULL,              -- URL/key-safe identifier

    list_type dyno_crm.crm_list_type NOT NULL,               -- STATIC or DYNAMIC
    list_content_type dyno_crm.crm_list_content_type NOT NULL, -- SINGLE or MIXED
    restricted_member_type dyno_crm.crm_member_type,         -- Required if SINGLE-type

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Enforces that if the list is SINGLE-type, a restricted_member_type must be specified
    CONSTRAINT chk_single_list_has_type CHECK (
        list_content_type = 'MIXED' OR restricted_member_type IS NOT NULL
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_lists_tenant_slug ON dyno_crm.list(tenant_id, slug);
CREATE INDEX IF NOT EXISTS ix_lists_tenant ON dyno_crm.list(tenant_id);


-- ----------------------------------------------------------------------
-- Table: dyno_crm.list_membership
-- Holds all entries in a list. Each row maps a member record to a list.
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_crm.list_membership (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    list_id UUID NOT NULL,

    member_id UUID NOT NULL,                            -- ID of the CRM record (Contact, Company, Lead, etc.)
    member_type dyno_crm.crm_member_type NOT NULL,      -- Type of the member record

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    CONSTRAINT fk_list_memberships_list
        FOREIGN KEY (list_id) REFERENCES dyno_crm.list(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_list_memberships_list ON dyno_crm.list_membership(list_id);
CREATE INDEX IF NOT EXISTS ix_list_memberships_member ON dyno_crm.list_membership(member_id);
CREATE INDEX IF NOT EXISTS ix_list_memberships_list_type ON dyno_crm.list_membership(list_id, member_type);


-- ----------------------------------------------------------------------
-- Trigger: Enforce SINGLE-type list integrity
-- Ensures that only allowed member types are added to SINGLE-type lists.
-- ----------------------------------------------------------------------

CREATE OR REPLACE FUNCTION dyno_crm.enforce_single_type_list()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT list_content_type FROM dyno_crm.list WHERE id = NEW.list_id) = 'SINGLE' THEN
        IF (SELECT restricted_member_type FROM dyno_crm.list WHERE id = NEW.list_id) IS DISTINCT FROM NEW.member_type THEN
            RAISE EXCEPTION 'List % only accepts member_type %', NEW.list_id, 
                (SELECT restricted_member_type FROM dyno_crm.list WHERE id = NEW.list_id);
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ----------------------------------------------------------------------
-- Table: dyno_crm.membership_config
-- Defines how to render or evaluate a list member of a certain type.
-- Used for customizing list display, filtering, and sorting by type.
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_crm.membership_config (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    member_type dyno_crm.crm_member_type NOT NULL,           -- CONTACT, COMPANY, or LEAD

    member_display_template TEXT,                            -- Template string (e.g. for UI rendering)
    member_display_template_type VARCHAR(50),                -- Rendering engine type (e.g. HANDLEBARS, LIQUID)

    filter_criteria JSON,                                  -- Optional structured filter metadata

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),


    CONSTRAINT chk_filter_criteria_schema CHECK (
        public.jsonb_matches_schema(
            $$
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "additionalProperties": false,
                "properties": {
                        "clauses": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "additionalProperties": false,
                                "properties": {
                                "logical_operator": {
                                    "type": "string",
                                    "enum": ["AND", "OR"]
                                },
                                "components": {
                                    "type": "array",
                                    "minItems": 1,
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": false,
                                        "properties": {
                                            "expression": {
                                                "type": "string",
                                                "minLength": 1,
                                                "description": "SQL-safe expression or column reference"
                                            },
                                            "operator": {
                                                "type": "string",
                                                "enum": [
                                                    "=",
                                                    "!=",
                                                    "<",
                                                    "<=",
                                                    ">",
                                                    ">=",
                                                    "IN",
                                                    "NOT IN",
                                                    "LIKE",
                                                    "ILIKE",
                                                    "IS NULL",
                                                    "IS NOT NULL"
                                                ]
                                            },
                                            "value": {
                                                "oneOf": [
                                                    { "type": "string" },
                                                    { "type": "number" },
                                                    { "type": "boolean" },
                                                    {
                                                    "type": "array",
                                                    "minItems": 1,
                                                    "items": {
                                                        "oneOf": [
                                                        { "type": "string" },
                                                        { "type": "number" },
                                                        { "type": "boolean" }
                                                        ]
                                                    }
                                                    }
                                                ]
                                            },
                                            "flags": {
                                                "type": "object",
                                                "additionalProperties": false,
                                                "properties": {
                                                    "case_sensitive": {
                                                        "type": "boolean"
                                                    }
                                                }
                                            }
                                        },
                                        "required": ["expression", "operator"]
                                    }
                                }
                            },
                            "required": ["logical_operator", "components"]
                        }
                    }
                },
                "required": ["clauses"]
            }

            $$::json,
            filter_config
        )
    
);


-- ----------------------------------------------------------------------
-- Table: dyno_crm.membership_config_sort
-- Defines a named sort for a membership_config, with SQL-safe sort logic.
-- The sort_config contains one or more expressions (in order) and directions.
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_crm.membership_config_sort (
    sort_name VARCHAR(100) NOT NULL,              -- Human-readable name (e.g. "Alphabetical")
    sort_key VARCHAR(100) NOT NULL,               -- Programmatic ID (snake_case)

    membership_config_id UUID NOT NULL,           -- Links to CONTACT/COMPANY/LEAD membership_config
    tenant_id UUID NOT NULL,

    sort_config JSON NOT NULL,                    -- Ordered array of { expression, direction }

    CONSTRAINT chk_sort_config_schema CHECK (
        public.jsonb_matches_schema(
            $$
            {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": false,
                    "properties": {
                        "expression": { "type": "string" },
                        "direction": {
                            "type": "string",
                            "enum": ["ASC", "DESC"]
                        }
                    },
                    "required": ["expression", "direction"]
                }
            }
            $$::json,
            sort_config
        )
    )
);


-- ----------------------------------------------------------------------
-- Table: dyno_crm.membership_config_filter
-- Defines a filter pattern for applying a search value to a membership type.
-- The filter_config uses value injection via "$(value)" and optional flags.
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_crm.membership_config_filter (
    filter_name VARCHAR(100) NOT NULL,             -- Human-readable filter name (e.g. "Name")
    filter_key VARCHAR(100) NOT NULL,              -- Programmatic key (e.g. "name")

    membership_config_id UUID NOT NULL,
    tenant_id UUID NOT NULL,

    filter_config JSONB NOT NULL,                  -- Defines clause expressions with a value placeholder

    CONSTRAINT chk_filter_config_schema CHECK (
        public.jsonb_matches_schema(
            $$
            {
                "type": "object",
                "required": ["clauses"],
                "properties": {
                    "clauses": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "anyOf": [
                                {
                                    "required": ["expression", "operator", "value"],
                                    "properties": {
                                        "expression": { "type": "string" },
                                        "operator": {
                                            "type": "string",
                                            "enum": ["=", "!=", "<", "<=", ">", ">=", "LIKE", "NOT LIKE", "ILIKE", "NOT ILIKE"]
                                        },
                                        "value": { "type": "string" },
                                        "flags": {
                                            "type": "object",
                                            "properties": {
                                                "case_sensitive": { "type": "boolean" }
                                            },
                                            "additionalProperties": false
                                        }
                                    },
                                    "additionalProperties": false
                                },
                                {
                                    "required": ["logical_operator", "components"],
                                    "properties": {
                                        "logical_operator": {
                                            "type": "string",
                                            "enum": ["AND", "OR"]
                                        },
                                        "components": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "required": ["expression", "operator", "value"],
                                                "properties": {
                                                    "expression": { "type": "string" },
                                                    "operator": { "type": "string" },
                                                    "value": { "type": "string" },
                                                    "flags": {
                                                        "type": "object",
                                                        "properties": {
                                                            "case_sensitive": { "type": "boolean" }
                                                        },
                                                        "additionalProperties": false
                                                    }
                                                },
                                                "additionalProperties": false
                                            }
                                        }
                                    },
                                    "additionalProperties": false
                                }
                            ]
                        }
                    }
                },
                "additionalProperties": false
            }
            $$::json,
            filter_config
        )
    )
);


-- ----------------------------------------------------------------------
-- Table: dyno_crm.list_membership_config
-- Associates a list with a specific membership_config (per type),
-- including the last evaluation timestamp for dynamic list criteria.
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_crm.list_membership_config (
    id UUID PRIMARY KEY,

    list_id UUID NOT NULL,
    membership_config_id UUID NOT NULL,

    refreshed_at TIMESTAMPTZ NULL, -- Optional: last evaluation time for dynamic list

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT fk_list_membership_config_list
        FOREIGN KEY (list_id) REFERENCES dyno_crm.list(id) ON DELETE CASCADE,
    CONSTRAINT fk_list_membership_config_config
        FOREIGN KEY (membership_config_id) REFERENCES dyno_crm.membership_config(id) ON DELETE CASCADE
);


-- ======================================================================
-- Dyno CRM - List Membership Validation (Single + Mixed Lists)
-- ======================================================================
-- PURPOSE
--   Enforce business rules when adding/updating rows in dyno_crm.list_membership:
--     1) SINGLE lists: member_type must match list.restricted_member_type
--     2) MIXED lists: member_type must be allowed by the list's configured member types
--        (via dyno_crm.list_membership_config -> dyno_crm.membership_config.member_type)
--     3) member_id must actually exist in the correct entity table for member_type,
--        and must belong to the same tenant_id
--
-- DESIGN NOTES
--   - This validation is performed at the database layer to guarantee integrity even if
--     multiple services write membership rows.
--   - The "allowed types for mixed lists" are driven by configuration:
--       list_membership_config(list_id, membership_config_id)
--       membership_config(id, tenant_id, member_type, ...)
--   - Existence checks are implemented via a single helper function that uses a CASE
--     switch over the enum type. This keeps the trigger function readable and makes
--     it easy to extend when you add new CRM member types.
--
-- ======================================================================


-- ----------------------------------------------------------------------
-- Helper Function: assert_member_exists
-- ----------------------------------------------------------------------
-- Validates that the (tenant_id, member_type, member_id) refers to a real record
-- in the correct table, scoped to the same tenant.
--
-- Raises:
--   - exception if the member_type is unsupported
--   - exception if the member_id does not exist in the expected table for that tenant
-- ----------------------------------------------------------------------

CREATE OR REPLACE FUNCTION dyno_crm.assert_member_exists(
    p_tenant_id   UUID,
    p_member_type dyno_crm.crm_member_type,
    p_member_id   UUID
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    v_exists BOOLEAN;
BEGIN
    IF p_member_id IS NULL THEN
        RAISE EXCEPTION 'member_id cannot be null';
    END IF;

    IF p_tenant_id IS NULL THEN
        RAISE EXCEPTION 'tenant_id cannot be null';
    END IF;

    v_exists := FALSE;

    CASE p_member_type
        WHEN 'CONTACT' THEN
            SELECT EXISTS (
                SELECT 1
                FROM dyno_crm.contact c
                WHERE c.id = p_member_id
                  AND c.tenant_id = p_tenant_id
            ) INTO v_exists;

        WHEN 'COMPANY' THEN
            SELECT EXISTS (
                SELECT 1
                FROM dyno_crm.company c
                WHERE c.id = p_member_id
                  AND c.tenant_id = p_tenant_id
            ) INTO v_exists;

        WHEN 'LEAD' THEN
            SELECT EXISTS (
                SELECT 1
                FROM dyno_crm.lead l
                WHERE l.id = p_member_id
                  AND l.tenant_id = p_tenant_id
            ) INTO v_exists;

        WHEN 'DEAL' THEN
            SELECT EXISTS (
                SELECT 1
                FROM dyno_crm.deal d
                WHERE d.id = p_member_id
                  AND d.tenant_id = p_tenant_id
            ) INTO v_exists;

        WHEN 'TICKET' THEN
            SELECT EXISTS (
                SELECT 1
                FROM dyno_crm.ticket t
                WHERE t.id = p_member_id
                  AND t.tenant_id = p_tenant_id
            ) INTO v_exists;

        ELSE
            RAISE EXCEPTION 'Unsupported member_type: %', p_member_type;
    END CASE;

    IF v_exists IS DISTINCT FROM TRUE THEN
        RAISE EXCEPTION
            'Invalid list member reference: tenant_id %, member_type %, member_id % does not exist',
            p_tenant_id, p_member_type, p_member_id;
    END IF;
END;
$$;


-- ----------------------------------------------------------------------
-- Trigger Function: validate_list_membership
-- ----------------------------------------------------------------------
-- Enforces:
--   A) Tenant consistency: list_membership.tenant_id must match list.tenant_id
--   B) SINGLE list rule: restricted_member_type must match NEW.member_type
--   C) MIXED list rule: NEW.member_type must be enabled for that list via
--      list_membership_config -> membership_config (for the same tenant)
--   D) Referential existence: NEW.member_id must exist in the correct table for
--      NEW.member_type and NEW.tenant_id
--
-- Notes:
--   - This function is intended to be used BEFORE INSERT OR UPDATE on list_membership.
--   - The allowed-type check for MIXED lists is intentionally strict: if no config exists
--     for a member_type, that type cannot be inserted into the list.
-- ----------------------------------------------------------------------

CREATE OR REPLACE FUNCTION dyno_crm.validate_list_membership()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_list_tenant_id           UUID;
    v_list_content_type        dyno_crm.crm_list_content_type;
    v_restricted_member_type   dyno_crm.crm_member_type;
    v_type_allowed             BOOLEAN;
BEGIN
    -- Basic non-null expectations (table already enforces NOT NULL for these, but
    -- keep explicit checks for clearer error messages in case of future changes).
    IF NEW.list_id IS NULL THEN
        RAISE EXCEPTION 'list_id cannot be null';
    END IF;

    IF NEW.tenant_id IS NULL THEN
        RAISE EXCEPTION 'tenant_id cannot be null';
    END IF;

    IF NEW.member_type IS NULL THEN
        RAISE EXCEPTION 'member_type cannot be null';
    END IF;

    IF NEW.member_id IS NULL THEN
        RAISE EXCEPTION 'member_id cannot be null';
    END IF;

    -- Load list metadata once. If the list does not exist, fail fast.
    SELECT
        l.tenant_id,
        l.list_content_type,
        l.restricted_member_type
    INTO
        v_list_tenant_id,
        v_list_content_type,
        v_restricted_member_type
    FROM dyno_crm.list l
    WHERE l.id = NEW.list_id;

    IF v_list_tenant_id IS NULL THEN
        RAISE EXCEPTION 'List % does not exist', NEW.list_id;
    END IF;

    -- Enforce tenant consistency between membership row and list row.
    IF v_list_tenant_id IS DISTINCT FROM NEW.tenant_id THEN
        RAISE EXCEPTION
            'Tenant mismatch: list_membership.tenant_id % does not match list.tenant_id % (list_id %)',
            NEW.tenant_id, v_list_tenant_id, NEW.list_id;
    END IF;

    -- Enforce SINGLE vs MIXED behavior.
    IF v_list_content_type = 'SINGLE' THEN
        -- SINGLE: member_type must equal list.restricted_member_type
        IF v_restricted_member_type IS NULL THEN
            -- Should not happen because of chk_single_list_has_type, but keep a guard.
            RAISE EXCEPTION
                'List % is SINGLE but restricted_member_type is null (data integrity error)',
                NEW.list_id;
        END IF;

        IF v_restricted_member_type IS DISTINCT FROM NEW.member_type THEN
            RAISE EXCEPTION
                'List % only accepts member_type % (attempted %)',
                NEW.list_id, v_restricted_member_type, NEW.member_type;
        END IF;

    ELSE
        -- MIXED: the member_type must be explicitly enabled by the list's membership configuration.
        --
        -- The rule implemented here:
        --   A member type is allowed for a list if there exists at least one
        --   membership_config linked to the list whose member_type == NEW.member_type,
        --   and the membership_config is owned by the same tenant.
        SELECT EXISTS (
            SELECT 1
            FROM dyno_crm.list_membership_config lmc
            JOIN dyno_crm.membership_config mc
              ON mc.id = lmc.membership_config_id
            WHERE lmc.list_id = NEW.list_id
              AND mc.tenant_id = NEW.tenant_id
              AND mc.member_type = NEW.member_type
        ) INTO v_type_allowed;

        IF v_type_allowed IS DISTINCT FROM TRUE THEN
            RAISE EXCEPTION
                'List % does not allow member_type % (no membership_config configured for this type)',
                NEW.list_id, NEW.member_type;
        END IF;
    END IF;

    -- Validate that the member_id actually exists in the correct table for member_type,
    -- and is owned by the same tenant.
    PERFORM dyno_crm.assert_member_exists(NEW.tenant_id, NEW.member_type, NEW.member_id);

    RETURN NEW;
END;
$$;


-- ----------------------------------------------------------------------
-- Trigger: trg_validate_list_membership
-- ----------------------------------------------------------------------
-- Applies validation on both INSERT and UPDATE because:
--   - INSERT adds new members
--   - UPDATE could change member_type/member_id/list_id/tenant_id and must be re-validated
-- ----------------------------------------------------------------------

DROP TRIGGER IF EXISTS trg_validate_list_membership ON dyno_crm.list_membership;

CREATE TRIGGER trg_validate_list_membership
BEFORE INSERT OR UPDATE ON dyno_crm.list_membership
FOR EACH ROW
EXECUTE FUNCTION dyno_crm.validate_list_membership();


-- ======================================================================
-- Python SQLAlchemy Patterns for Mixed-Type Sorted Lists
-- ======================================================================
-- Yes. You can do it in one round trip, and still sort, but there are tradeoffs. The core idea is: you cannot `UNION` two SELECTs that return different shapes unless you make them the same shape. So you either:

-- 1. project both tables into a common "envelope" (recommended), or
-- 2. query IDs/types in one query, then fetch the ORM objects in a second query (still clean, but not one query).

-- Below are the practical patterns.

-- ---

-- ## Option A (recommended): One SQL query returning a unified "envelope" row shape

-- You `SELECT` a common set of columns for every entity, then `UNION ALL` them, then `ORDER BY` the unified sort keys.

-- Typical envelope fields:

-- * `entity_type` (literal: "company" / "contact")
-- * `entity_id`
-- * `display_name` (or whatever you sort by)
-- * `created_at` / `updated_at`
-- * `payload` (JSON with type-specific fields), optional

-- This gives you a single result list that looks like:
-- `[{type, id, display_name, sort_dt, payload}, ...]`

-- ### SQLAlchemy 2.x example

-- ```python
-- from sqlalchemy import select, literal, union_all, func, cast
-- from sqlalchemy.dialects.postgresql import JSONB

-- # Assume ORM models: Company, Contact
-- # Company: id, name, created_at, ...
-- # Contact: id, first_name, last_name, created_at, ...

-- company_q = (
--     select(
--         literal("company").label("entity_type"),
--         Company.id.label("entity_id"),
--         Company.name.label("display_name"),
--         Company.created_at.label("sort_dt"),
--         # Optional: type-specific details
--         cast(
--             func.jsonb_build_object(
--                 "name", Company.name,
--                 "domain", Company.domain,  # if exists
--             ),
--             JSONB
--         ).label("payload"),
--     )
-- )

-- contact_q = (
--     select(
--         literal("contact").label("entity_type"),
--         Contact.id.label("entity_id"),
--         (Contact.first_name + literal(" ") + Contact.last_name).label("display_name"),
--         Contact.created_at.label("sort_dt"),
--         cast(
--             func.jsonb_build_object(
--                 "first_name", Contact.first_name,
--                 "last_name", Contact.last_name,
--                 "email", Contact.email,  # if exists
--             ),
--             JSONB
--         ).label("payload"),
--     )
-- )

-- mixed = union_all(company_q, contact_q).subquery("mixed")

-- stmt = (
--     select(
--         mixed.c.entity_type,
--         mixed.c.entity_id,
--         mixed.c.display_name,
--         mixed.c.sort_dt,
--         mixed.c.payload,
--     )
--     .order_by(mixed.c.display_name.asc(), mixed.c.entity_id.asc())
--     .limit(100)
-- )

-- rows = session.execute(stmt).all()
-- ```

-- What you get is a single sorted list of rows, each tagged with type.

-- ### Pros

-- * True single query.
-- * Full control over sorting/paging.
-- * Works great with your Dyno-style mixed lists: store `entity_type`, `entity_id`, and define per-type config for `display_name` and sort expression.

-- ### Cons

-- * You do not get actual ORM instances (`Company(...)`, `Contact(...)`) in that list.
-- * You must decide the shared columns. Type-specific fields go in `payload` (JSON) or nullable columns.

-- ---

-- ## Option B: One query that returns the mixed list, but as a polymorphic "union mapping"

-- SQLAlchemy can map a `UNION` to an ORM class. However, if your underlying entities have different columns, the mapped class still needs a consistent set of columns. So it ends up very similar to Option A (an envelope model), just mapped as an ORM class.

-- Use this if you want something that feels like ORM objects but you accept they are not real `Company` / `Contact` instances.

-- ---

-- ## Option C: Keep real ORM entities, but it becomes at least two queries (best UX sometimes)

-- If you truly want:
-- `[Company(...), Contact(...), Contact(...), Company(...)]`
-- as real ORM instances, you typically do:

-- 1. One query to get an ordered list of `(type, id)` (and maybe sort keys).
-- 2. Two bulk queries to fetch companies and contacts by those IDs.
-- 3. Reassemble in Python preserving order.

-- This is how many high-performance systems do it, because it keeps ORM behavior, relationships, lazy loading, etc.

-- It is not "one query", but it is still efficient and often simpler operationally.

-- ---

-- ## Sorting when fields differ

-- You pick a sorting strategy that can be applied across types. Common patterns:

-- * Sort by a unified `display_name` (Company.name vs Contact.full_name).
-- * Sort by unified timestamps (`updated_at`).
-- * Sort by "relevance score" from a search subsystem.
-- * Type-weighted sort: `ORDER BY entity_type, display_name` (or vice versa).

-- If you want deterministic ordering across types, always add a stable tie-breaker like `(entity_type, entity_id)`.

-- ---

-- ## What I would do for your Dyno CRM "mixed list"

-- Given your schema already has `member_type` and `member_id`, and you have membership config for display templates and sorts, the cleanest is:

-- * Build a *query generator per member_type* that outputs the shared envelope fields and optional JSON payload.
-- * `UNION ALL` them.
-- * Apply the list-level sort_config to the envelope fields (or type-specific sort expressions that you normalize into the envelope).

-- This matches your design where `membership_config_sort` stores expressions and directions.

-- ---

-- If you tell me your target DB (Postgres?) and what sorting you want (name vs updated date vs arbitrary membership_config_sort expressions), I can give you a concrete, production-ready SQLAlchemy function like:

-- `build_mixed_list_query(tenant_id, member_types, filter_config, sort_config, limit, offset)`


