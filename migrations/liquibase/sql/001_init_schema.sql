-- ======================================================================
-- Dyno CRM – CRM Service Schema (public)
-- ======================================================================
-- liquibase formatted sql
-- changeset crm_service:001_init_schema

SET search_path TO public, dyno_crm;

-- ----------------------------------------------------------------------
-- Enable pg_jsonschema (requires Supabase Postgres image or extension installed)
-- ----------------------------------------------------------------------
-- CREATE EXTENSION IF NOT EXISTS dyno_crm.pg_jsonschema;

--- schema definition starts here

-- ----------------------------------------------------------------------
-- pipeline
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.pipeline (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Supports composite FKs from child tables (tenant consistency)
    CONSTRAINT ux_pipeline_id_tenant UNIQUE (id, tenant_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_pipeline_tenant_name
    ON dyno_crm.pipeline(tenant_id, name);

CREATE INDEX IF NOT EXISTS ix_pipeline_tenant
    ON dyno_crm.pipeline(tenant_id);

-- ----------------------------------------------------------------------
-- pipeline_stage (depends on pipeline)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.pipeline_stage (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    pipeline_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    stage_order INTEGER NOT NULL,
    probability NUMERIC(5,2),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Enforce pipeline existence
    CONSTRAINT fk_pipeline_stage_pipeline
        FOREIGN KEY (pipeline_id)
        REFERENCES pipeline(id)
        ON DELETE CASCADE,

    -- Enforce tenant consistency (CRITICAL)
    CONSTRAINT fk_pipeline_stage_pipeline_tenant
        FOREIGN KEY (pipeline_id, tenant_id)
        REFERENCES pipeline(id, tenant_id)
        ON DELETE CASCADE
);

-- Ordering is tenant-safe via pipeline
CREATE UNIQUE INDEX IF NOT EXISTS ux_pipeline_stage_pipeline_order
    ON dyno_crm.pipeline_stage(pipeline_id, stage_order);

-- Names are tenant-safe via pipeline
CREATE UNIQUE INDEX IF NOT EXISTS ux_pipeline_stage_pipeline_name
    ON dyno_crm.pipeline_stage(pipeline_id, name);

-- Direct tenant access (queries, partition pruning)
CREATE INDEX IF NOT EXISTS ix_pipeline_stage_tenant
    ON dyno_crm.pipeline_stage(tenant_id);

-- ----------------------------------------------------------------------
-- Lead simplified model, loose constraints but similar to contact
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.lead (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    first_name  VARCHAR(100),
    middle_name VARCHAR(100),
    last_name   VARCHAR(100),
    source      VARCHAR(255),
    lead_data   JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_lead_id_tenant UNIQUE (id, tenant_id),

    -- pg_jsonschema-based JSON validation.
    -- NOTE: pg_jsonschema function signature is:
    --   jsonb_matches_schema(schema json, instance jsonb)
    -- The only fix applied here is casting the schema literal to ::json (not ::jsonb).
    CONSTRAINT chk_lead_lead_data_schema CHECK (
        lead_data IS NULL OR public.jsonb_matches_schema(
            $$
            {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "phone_numbers": {
                  "type": "object",
                  "patternProperties": {
                    ".*": { "type": "string" }
                  },
                  "additionalProperties": false
                },
                "emails": {
                  "type": "object",
                  "patternProperties": {
                    ".*": { "type": "string" }
                  },
                  "additionalProperties": false
                },
                "social_profiles": {
                  "type": "object",
                  "patternProperties": {
                    ".*": { "type": "string" }
                  },
                  "additionalProperties": false
                },
                "addresses": {
                  "type": "object",
                  "patternProperties": {
                    ".*": {
                      "type": "object",
                      "additionalProperties": false,
                      "properties": {
                        "line1":       { "type": "string" },
                        "line2":       { "type": "string" },
                        "city":        { "type": "string" },
                        "region":      { "type": "string" },
                        "postal_code": { "type": "string" },
                        "country":     { "type": "string" }
                      }
                    }
                  },
                  "additionalProperties": false
                },
                "notes": {
                  "type": "object",
                  "patternProperties": {
                    ".*": {
                      "type": "object",
                      "additionalProperties": false,
                      "properties": {
                        "created_at": { "type": "string" },
                        "updated_at": { "type": "string" },
                        "text":       { "type": "string" }
                      },
                      "required": ["created_at", "updated_at", "text"]
                    }
                  },
                  "additionalProperties": false
                }
              }
            }
            $$::json,
            lead_data
        )
    )
);

CREATE INDEX IF NOT EXISTS ix_lead_tenant
    ON dyno_crm.lead(tenant_id);

CREATE INDEX IF NOT EXISTS ix_lead_tenant_last_first
    ON dyno_crm.lead(tenant_id, last_name, first_name);

-- =====================================================================
-- CONTACT DOMAIN
-- =====================================================================

-- ----------------------------------------------------------------------
-- contact
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.contact (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    first_name  VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name   VARCHAR(100) NOT NULL,
    maiden_name VARCHAR(100),
    prefix      VARCHAR(20),
    suffix      VARCHAR(20),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Supports composite FKs from child tables
    CONSTRAINT ux_contact_id_tenant UNIQUE (id, tenant_id)
);

CREATE INDEX IF NOT EXISTS ix_contact_tenant
    ON dyno_crm.contact(tenant_id);

CREATE INDEX IF NOT EXISTS ix_contact_tenant_last_first
    ON dyno_crm.contact(tenant_id, last_name, first_name);

-- ----------------------------------------------------------------------
-- contact_email (depends on contact)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.contact_email (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    contact_id UUID NOT NULL,

    email VARCHAR(255) NOT NULL,
    email_type VARCHAR(50) NOT NULL DEFAULT 'work', -- work|personal|other
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT fk_contact_email_contact
        FOREIGN KEY (contact_id) REFERENCES contact(id) ON DELETE CASCADE,

    CONSTRAINT fk_contact_email_contact_tenant
        FOREIGN KEY (contact_id, tenant_id) REFERENCES contact(id, tenant_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_contact_email_tenant_contact
    ON dyno_crm.contact_email(tenant_id, contact_id);

CREATE INDEX IF NOT EXISTS ix_contact_email_tenant_email
    ON dyno_crm.contact_email(tenant_id, lower(email));

-- Dedupe within a contact
CREATE UNIQUE INDEX IF NOT EXISTS ux_contact_email_contact_email
    ON dyno_crm.contact_email(tenant_id, contact_id, lower(email));

-- One primary per contact
CREATE UNIQUE INDEX IF NOT EXISTS ux_contact_email_primary_per_contact
    ON dyno_crm.contact_email(tenant_id, contact_id)
    WHERE is_primary = TRUE;

-- ----------------------------------------------------------------------
-- contact_phone (depends on contact)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.contact_phone (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    contact_id UUID NOT NULL,

    phone_raw VARCHAR(50) NOT NULL,
    phone_e164 VARCHAR(20), -- canonical normalized number, e.g. +13215551212

    phone_type VARCHAR(50) NOT NULL DEFAULT 'mobile', -- mobile|work|home|other
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,

    is_sms_capable BOOLEAN NOT NULL DEFAULT FALSE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT fk_contact_phone_contact
        FOREIGN KEY (contact_id) REFERENCES contact(id) ON DELETE CASCADE,

    CONSTRAINT fk_contact_phone_contact_tenant
        FOREIGN KEY (contact_id, tenant_id) REFERENCES contact(id, tenant_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_contact_phone_tenant_contact
    ON dyno_crm.contact_phone(tenant_id, contact_id);

-- Prefer searching by normalized phone when available
CREATE INDEX IF NOT EXISTS ix_contact_phone_tenant_phone_e164
    ON dyno_crm.contact_phone(tenant_id, phone_e164)
    WHERE phone_e164 IS NOT NULL;

-- Fallback search (raw)
CREATE INDEX IF NOT EXISTS ix_contact_phone_tenant_phone_raw
    ON dyno_crm.contact_phone(tenant_id, phone_raw);

-- Dedupe within a contact (use e164 when available)
CREATE UNIQUE INDEX IF NOT EXISTS ux_contact_phone_contact_phone_e164
    ON dyno_crm.contact_phone(tenant_id, contact_id, phone_e164)
    WHERE phone_e164 IS NOT NULL;

-- One primary per contact
CREATE UNIQUE INDEX IF NOT EXISTS ux_contact_phone_primary_per_contact
    ON dyno_crm.contact_phone(tenant_id, contact_id)
    WHERE is_primary = TRUE;

-- ----------------------------------------------------------------------
-- contact_address (depends on contact)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.contact_address (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    contact_id UUID NOT NULL,

    address_type VARCHAR(50) NOT NULL DEFAULT 'home', -- home|work|billing|shipping|other
    label VARCHAR(100),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,

    line1 VARCHAR(255) NOT NULL,
    line2 VARCHAR(255),
    line3 VARCHAR(255),
    city  VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    postal_code VARCHAR(20),
    country_code CHAR(2) NOT NULL DEFAULT 'US',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT fk_contact_address_contact
        FOREIGN KEY (contact_id) REFERENCES contact(id) ON DELETE CASCADE,

    CONSTRAINT fk_contact_address_contact_tenant
        FOREIGN KEY (contact_id, tenant_id) REFERENCES contact(id, tenant_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_contact_address_tenant_contact
    ON dyno_crm.contact_address(tenant_id, contact_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_contact_address_primary_per_contact
    ON dyno_crm.contact_address(tenant_id, contact_id)
    WHERE is_primary = TRUE;

-- ----------------------------------------------------------------------
-- contact_social_profile (depends on contact)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.contact_social_profile (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    contact_id UUID NOT NULL,

    profile_type VARCHAR(50) NOT NULL,
    profile_url VARCHAR(255) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT fk_contact_social_profile_contact
        FOREIGN KEY (contact_id) REFERENCES contact(id) ON DELETE CASCADE,

    CONSTRAINT fk_contact_social_profile_contact_tenant
        FOREIGN KEY (contact_id, tenant_id) REFERENCES contact(id, tenant_id) ON DELETE CASCADE,

    -- Optional URL sanity: require http(s)
    CONSTRAINT ck_contact_social_profile_url
        CHECK (profile_url ~* '^https?://'),

    CONSTRAINT ck_contact_social_profile_profile_type
        CHECK (profile_type IN (
            'facebook','instagram','tiktok','snapchat','x','twitter','threads','bluesky','mastodon','reddit',
            'pinterest','tumblr','discord','telegram','whatsapp','signal','wechat','line','kakaotalk','viber','skype',
            'linkedin','github','gitlab','bitbucket','stack_overflow','medium','substack','devto','hashnode',
            'behance','dribbble','figma_community','product_hunt',
            'youtube','twitch','kick','vimeo','rumble','dailymotion',
            'spotify','soundcloud','bandcamp','apple_music',
            'etsy','ebay','amazon_storefront','shopify_store','depop','poshmark','mercari',
            'google_business_profile','yelp','tripadvisor','trustpilot','angies_list','bbb',
            'website','blog','portfolio','calendly','linktree','patreon','onlyfans','other'
        ))
);

CREATE INDEX IF NOT EXISTS ix_contact_social_profile_tenant_contact
    ON dyno_crm.contact_social_profile(tenant_id, contact_id);

-- Case-insensitive uniqueness by type per contact (recommended)
CREATE UNIQUE INDEX IF NOT EXISTS ux_contact_social_profile_contact_type
    ON dyno_crm.contact_social_profile(tenant_id, contact_id, lower(profile_type));

-- ----------------------------------------------------------------------
-- contact_note (depends on contact)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.contact_note (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    contact_id UUID NOT NULL,

    note_type VARCHAR(50) NOT NULL DEFAULT 'note',  -- note|call|meeting|email|sms|other
    title VARCHAR(255),
    body TEXT NOT NULL,
    noted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_system VARCHAR(100),
    source_ref VARCHAR(255),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT fk_contact_note_contact
        FOREIGN KEY (contact_id) REFERENCES contact(id) ON DELETE CASCADE,

    CONSTRAINT fk_contact_note_contact_tenant
        FOREIGN KEY (contact_id, tenant_id) REFERENCES contact(id, tenant_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_contact_note_tenant_contact_noted_at
    ON dyno_crm.contact_note(tenant_id, contact_id, noted_at DESC);

CREATE INDEX IF NOT EXISTS ix_contact_note_tenant_noted_at
    ON dyno_crm.contact_note(tenant_id, noted_at DESC);

CREATE INDEX IF NOT EXISTS ix_contact_note_tenant_note_type
    ON dyno_crm.contact_note(tenant_id, note_type);

-- ======================================================================
-- COMPANY DOMAIN
-- ======================================================================

-- ----------------------------------------------------------------------
-- company
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.company (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    company_name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    industry VARCHAR(255),

    is_internal BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT ux_company_id_tenant UNIQUE (id, tenant_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_company_tenant_company_name
    ON dyno_crm.company(tenant_id, company_name);

CREATE INDEX IF NOT EXISTS ix_company_tenant
    ON dyno_crm.company(tenant_id);

CREATE INDEX IF NOT EXISTS ix_company_tenant_name
    ON dyno_crm.company(tenant_id, company_name);

CREATE INDEX IF NOT EXISTS ix_company_tenant_domain
    ON dyno_crm.company(tenant_id, lower(domain))
    WHERE domain IS NOT NULL;

-- ----------------------------------------------------------------------
-- company_email (depends on company)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.company_email (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    company_id UUID NOT NULL,

    email VARCHAR(255) NOT NULL,
    email_type VARCHAR(50) NOT NULL DEFAULT 'work',
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT fk_company_email_company
        FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,

    CONSTRAINT fk_company_email_company_tenant
        FOREIGN KEY (company_id, tenant_id) REFERENCES company(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT ck_company_email_type
        CHECK (email_type IN ('work','billing','support','sales','other'))
);

CREATE INDEX IF NOT EXISTS ix_company_email_tenant_company
    ON dyno_crm.company_email(tenant_id, company_id);

CREATE INDEX IF NOT EXISTS ix_company_email_tenant_email
    ON dyno_crm.company_email(tenant_id, lower(email));

CREATE UNIQUE INDEX IF NOT EXISTS ux_company_email_company_email
    ON dyno_crm.company_email(tenant_id, company_id, lower(email));

CREATE UNIQUE INDEX IF NOT EXISTS ux_company_email_primary_per_company
    ON dyno_crm.company_email(tenant_id, company_id)
    WHERE is_primary = TRUE;

-- ----------------------------------------------------------------------
-- company_phone (depends on company)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.company_phone (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    company_id UUID NOT NULL,

    phone_raw VARCHAR(50) NOT NULL,
    phone_e164 VARCHAR(20),
    phone_ext VARCHAR(20),

    phone_type VARCHAR(50) NOT NULL DEFAULT 'main',
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,

    is_sms_capable BOOLEAN NOT NULL DEFAULT FALSE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT fk_company_phone_company
        FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,

    CONSTRAINT fk_company_phone_company_tenant
        FOREIGN KEY (company_id, tenant_id) REFERENCES company(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT ck_company_phone_type
        CHECK (phone_type IN ('main','support','sales','billing','fax','other'))
);

CREATE INDEX IF NOT EXISTS ix_company_phone_tenant_company
    ON dyno_crm.company_phone(tenant_id, company_id);

CREATE INDEX IF NOT EXISTS ix_company_phone_tenant_phone_raw
    ON dyno_crm.company_phone(tenant_id, phone_raw);

CREATE INDEX IF NOT EXISTS ix_company_phone_tenant_phone_e164
    ON dyno_crm.company_phone(tenant_id, phone_e164)
    WHERE phone_e164 IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_company_phone_company_phone_e164
    ON dyno_crm.company_phone(tenant_id, company_id, phone_e164)
    WHERE phone_e164 IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_company_phone_primary_per_company
    ON dyno_crm.company_phone(tenant_id, company_id)
    WHERE is_primary = TRUE;

-- ----------------------------------------------------------------------
-- company_address (depends on company)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.company_address (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    company_id UUID NOT NULL,

    address_type VARCHAR(50) NOT NULL DEFAULT 'office',
    label VARCHAR(100),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,

    line1 VARCHAR(255) NOT NULL,
    line2 VARCHAR(255),
    line3 VARCHAR(255),
    city  VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    postal_code VARCHAR(20),
    country_code CHAR(2) NOT NULL DEFAULT 'US',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT fk_company_address_company
        FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,

    CONSTRAINT fk_company_address_company_tenant
        FOREIGN KEY (company_id, tenant_id) REFERENCES company(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT ck_company_address_type
        CHECK (address_type IN ('office','billing','shipping','warehouse','receivings','other'))
);

CREATE INDEX IF NOT EXISTS ix_company_address_tenant_company
    ON dyno_crm.company_address(tenant_id, company_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_company_address_primary_per_company
    ON dyno_crm.company_address(tenant_id, company_id)
    WHERE is_primary = TRUE;

-- ----------------------------------------------------------------------
-- company_social_profile (depends on company)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.company_social_profile (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    company_id UUID NOT NULL,

    profile_type VARCHAR(50) NOT NULL,
    profile_url VARCHAR(255) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT fk_company_social_profile_company
        FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,

    CONSTRAINT fk_company_social_profile_company_tenant
        FOREIGN KEY (company_id, tenant_id) REFERENCES company(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT ck_company_social_profile_url
        CHECK (profile_url ~* '^https?://'),

    CONSTRAINT ck_company_social_profile_profile_type
        CHECK (profile_type IN (
            'facebook','instagram','tiktok','snapchat','x','twitter','threads','bluesky','mastodon','reddit',
            'pinterest','tumblr','discord','telegram','whatsapp','signal','wechat','line','kakaotalk','viber','skype',
            'linkedin','github','gitlab','bitbucket','stack_overflow','medium','substack','devto','hashnode',
            'behance','dribbble','figma_community','product_hunt',
            'youtube','twitch','kick','vimeo','rumble','dailymotion',
            'spotify','soundcloud','bandcamp','apple_music',
            'etsy','ebay','amazon_storefront','shopify_store','depop','poshmark','mercari',
            'google_business_profile','yelp','tripadvisor','trustpilot','angies_list','bbb',
            'website','blog','portfolio','calendly','linktree','patreon','onlyfans','other'
        ))
);

CREATE INDEX IF NOT EXISTS ix_company_social_profile_tenant_company
    ON dyno_crm.company_social_profile(tenant_id, company_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_company_social_profile_company_type
    ON dyno_crm.company_social_profile(tenant_id, company_id, lower(profile_type));

-- ----------------------------------------------------------------------
-- company_note (depends on company)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.company_note (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    company_id UUID NOT NULL,

    note_type VARCHAR(50) NOT NULL DEFAULT 'note',
    title VARCHAR(255),
    body TEXT NOT NULL,
    noted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_system VARCHAR(100),
    source_ref VARCHAR(255),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT fk_company_note_company
        FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,

    CONSTRAINT fk_company_note_company_tenant
        FOREIGN KEY (company_id, tenant_id) REFERENCES company(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT ck_company_note_type
        CHECK (note_type IN ('note','call','meeting','email','sms','other'))
);

CREATE INDEX IF NOT EXISTS ix_company_note_tenant_company_noted_at
    ON dyno_crm.company_note(tenant_id, company_id, noted_at DESC);

CREATE INDEX IF NOT EXISTS ix_company_note_tenant_noted_at
    ON dyno_crm.company_note(tenant_id, noted_at DESC);

CREATE INDEX IF NOT EXISTS ix_company_note_tenant_note_type
    ON dyno_crm.company_note(tenant_id, note_type);

-- ----------------------------------------------------------------------
-- company_relationship (company-to-company)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.company_relationship (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    from_company_id UUID NOT NULL,
    to_company_id UUID NOT NULL,

    from_role VARCHAR(50) NOT NULL,
    to_role VARCHAR(50) NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    start_date DATE,
    end_date DATE,
    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT fk_company_relationship_from
        FOREIGN KEY (from_company_id) REFERENCES company(id) ON DELETE CASCADE,

    CONSTRAINT fk_company_relationship_to
        FOREIGN KEY (to_company_id) REFERENCES company(id) ON DELETE CASCADE,

    CONSTRAINT fk_company_relationship_from_tenant
        FOREIGN KEY (from_company_id, tenant_id) REFERENCES company(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT fk_company_relationship_to_tenant
        FOREIGN KEY (to_company_id, tenant_id) REFERENCES company(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT ck_company_relationship_not_self
        CHECK (from_company_id <> to_company_id),

    CONSTRAINT ck_company_relationship_dates
        CHECK (start_date IS NULL OR end_date IS NULL OR end_date >= start_date),

    CONSTRAINT ck_company_relationship_role_values
        CHECK (
            from_role IN (
                'client','supplier','vendor','partner','reseller','manufacturer','parent','subsidiary','competitor',
                'investor','portfolio_company','franchisee','franchisor','affiliate','buyer','seller','advisor',
                'client_company','consultant','lender','borrower','donor','nonprofit','sponsor','sponsee','debtor',
                'creditor','other'
            )
            AND
            to_role IN (
                'client','supplier','vendor','partner','reseller','manufacturer','parent','subsidiary','competitor',
                'investor','portfolio_company','franchisee','franchisor','affiliate','buyer','seller','advisor',
                'client_company','consultant','lender','borrower','donor','nonprofit','sponsor','sponsee','debtor',
                'creditor','other'
            )
        )
);

CREATE INDEX IF NOT EXISTS ix_company_relationship_tenant_from
    ON dyno_crm.company_relationship(tenant_id, from_company_id);

CREATE INDEX IF NOT EXISTS ix_company_relationship_tenant_to
    ON dyno_crm.company_relationship(tenant_id, to_company_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_company_relationship_unique
    ON dyno_crm.company_relationship(tenant_id, from_company_id, to_company_id, from_role, to_role);

-- ----------------------------------------------------------------------
-- contact_company_relationship
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.contact_company_relationship (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    contact_id UUID NOT NULL,
    company_id UUID NOT NULL,

    relationship_type VARCHAR(50) NOT NULL,

    department VARCHAR(100),
    job_title VARCHAR(255),

    work_email VARCHAR(255),
    work_phone_raw VARCHAR(50),
    work_phone_e164 VARCHAR(20),
    work_phone_ext VARCHAR(20),

    is_primary BOOLEAN NOT NULL DEFAULT FALSE,

    start_date DATE,
    end_date DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT fk_contact_company_relationship_contact
        FOREIGN KEY (contact_id) REFERENCES contact(id) ON DELETE CASCADE,

    CONSTRAINT fk_contact_company_relationship_company
        FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,

    CONSTRAINT fk_contact_company_relationship_contact_tenant
        FOREIGN KEY (contact_id, tenant_id) REFERENCES contact(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT fk_contact_company_relationship_company_tenant
        FOREIGN KEY (company_id, tenant_id) REFERENCES company(id, tenant_id) ON DELETE CASCADE,

    CONSTRAINT ck_contact_company_relationship_dates
        CHECK (start_date IS NULL OR end_date IS NULL OR end_date >= start_date),

    CONSTRAINT ck_contact_company_relationship_type
        CHECK (relationship_type IN (
            'employee',
            'contractor',
            'client_manager',
            'vendor_manager',
            'sales_rep',
            'executive_sponsor',
            'billing_contact',
            'support_contact',
            'debtor',
            'creditor',
            'other'
        ))
);

CREATE INDEX IF NOT EXISTS ix_contact_company_relationship_tenant_contact
    ON dyno_crm.contact_company_relationship(tenant_id, contact_id);

CREATE INDEX IF NOT EXISTS ix_contact_company_relationship_tenant_company
    ON dyno_crm.contact_company_relationship(tenant_id, company_id);

CREATE UNIQUE INDEX IF NOT EXISTS ux_contact_company_relationship_primary_per_contact
    ON dyno_crm.contact_company_relationship(tenant_id, contact_id)
    WHERE is_primary = TRUE;

CREATE UNIQUE INDEX IF NOT EXISTS ux_contact_company_relationship_unique
    ON dyno_crm.contact_company_relationship(tenant_id, contact_id, company_id, relationship_type);


-- ----------------------------------------------------------------------
-- dyno_crm.deal (depends on dyno_crm.pipeline + dyno_crm.pipeline_stage)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.deal (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    amount NUMERIC(12,2),
    expected_close_date DATE,
    pipeline_id UUID NOT NULL,
    stage_id UUID NOT NULL,
    probability NUMERIC(5,2),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    CONSTRAINT fk_deals_pipeline
        FOREIGN KEY (pipeline_id) REFERENCES dyno_crm.pipeline(id) ON DELETE CASCADE,
    CONSTRAINT fk_deals_stage
        FOREIGN KEY (stage_id) REFERENCES dyno_crm.pipeline_stage(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_deals_tenant ON dyno_crm.deal(tenant_id);
CREATE INDEX IF NOT EXISTS ix_deals_pipeline ON dyno_crm.deal(pipeline_id);
CREATE INDEX IF NOT EXISTS ix_deals_stage ON dyno_crm.deal(stage_id);

-- ----------------------------------------------------------------------
-- dyno_crm.activity
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.activity (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    type VARCHAR(20) NOT NULL,
    title VARCHAR(255),
    description TEXT,
    due_date DATE,
    status VARCHAR(20),
    assigned_user_id UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS ix_activities_tenant ON dyno_crm.activity(tenant_id);
CREATE INDEX IF NOT EXISTS ix_activities_assigned_user ON dyno_crm.activity(assigned_user_id);

-- ----------------------------------------------------------------------
-- dyno_crm.association
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.association (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    from_object_type VARCHAR(50) NOT NULL,
    from_object_id UUID NOT NULL,
    to_object_type VARCHAR(50) NOT NULL,
    to_object_id UUID NOT NULL,
    association_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS ix_associations_tenant ON dyno_crm.association(tenant_id);
CREATE INDEX IF NOT EXISTS ix_associations_from ON dyno_crm.association(from_object_id);
CREATE INDEX IF NOT EXISTS ix_associations_to ON dyno_crm.association(to_object_id);

-- ----------------------------------------------------------------------
-- dyno_crm.list
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.list (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    list_type VARCHAR(50) NOT NULL,
    filter_definition JSON,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_lists_tenant_name_object
    ON dyno_crm.list(tenant_id, name, object_type);

CREATE INDEX IF NOT EXISTS ix_lists_tenant ON dyno_crm.list(tenant_id);

-- ----------------------------------------------------------------------
-- dyno_crm.list_membership (depends on dyno_crm.list)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dyno_crm.list_membership (
    id UUID PRIMARY KEY,
    list_id UUID NOT NULL,
    member_id UUID NOT NULL,
    member_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    CONSTRAINT fk_list_memberships_list
        FOREIGN KEY (list_id) REFERENCES dyno_crm.list(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_list_memberships_list ON dyno_crm.list_membership(list_id);
CREATE INDEX IF NOT EXISTS ix_list_memberships_member ON dyno_crm.list_membership(member_id);
