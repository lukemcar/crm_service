-- ======================================================================
-- Dyno CRM – CRM Service Schema (public)
-- ======================================================================
-- liquibase formatted sql
-- changeset crm_service:001_init_schema

SET search_path TO dyno_crm;

--- schema definition starts here

-- ----------------------------------------------------------------------
-- pipelines
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pipelines (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_pipelines_tenant_name ON pipelines(tenant_id, name);
CREATE INDEX IF NOT EXISTS ix_pipelines_tenant ON pipelines(tenant_id);

-- ----------------------------------------------------------------------
-- pipeline_stages (depends on pipelines)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pipeline_stages (
    id UUID PRIMARY KEY,
    pipeline_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    stage_order INTEGER NOT NULL,
    probability NUMERIC(5,2),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    CONSTRAINT fk_pipeline_stages_pipeline
        FOREIGN KEY (pipeline_id) REFERENCES pipelines(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_pipeline_stages_pipeline_order
    ON pipeline_stages(pipeline_id, stage_order);

CREATE UNIQUE INDEX IF NOT EXISTS ux_pipeline_stages_pipeline_name
    ON pipeline_stages(pipeline_id, name);

-- ----------------------------------------------------------------------
-- contacts
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

-- ensure emails are unique per tenant (Postgres allows multiple NULLs in UNIQUE indexes)
CREATE UNIQUE INDEX IF NOT EXISTS ux_contacts_tenant_email ON contacts(tenant_id, email);

-- index on tenant for queries
CREATE INDEX IF NOT EXISTS ix_contacts_tenant ON contacts(tenant_id);

-- ----------------------------------------------------------------------
-- companies
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    industry VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_companies_tenant_company_name
    ON companies(tenant_id, company_name);

CREATE INDEX IF NOT EXISTS ix_companies_tenant ON companies(tenant_id);

-- ----------------------------------------------------------------------
-- deals (depends on pipelines + pipeline_stages)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deals (
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
    created_by UUID,
    updated_by UUID,
    CONSTRAINT fk_deals_pipeline
        FOREIGN KEY (pipeline_id) REFERENCES pipelines(id) ON DELETE CASCADE,
    CONSTRAINT fk_deals_stage
        FOREIGN KEY (stage_id) REFERENCES pipeline_stages(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_deals_tenant ON deals(tenant_id);
CREATE INDEX IF NOT EXISTS ix_deals_pipeline ON deals(pipeline_id);
CREATE INDEX IF NOT EXISTS ix_deals_stage ON deals(stage_id);

-- ----------------------------------------------------------------------
-- activities
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activities (
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
    created_by UUID,
    updated_by UUID
);

CREATE INDEX IF NOT EXISTS ix_activities_tenant ON activities(tenant_id);
CREATE INDEX IF NOT EXISTS ix_activities_assigned_user ON activities(assigned_user_id);

-- ----------------------------------------------------------------------
-- associations
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS associations (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    from_object_type VARCHAR(50) NOT NULL,
    from_object_id UUID NOT NULL,
    to_object_type VARCHAR(50) NOT NULL,
    to_object_id UUID NOT NULL,
    association_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID
);

CREATE INDEX IF NOT EXISTS ix_associations_tenant ON associations(tenant_id);
CREATE INDEX IF NOT EXISTS ix_associations_from ON associations(from_object_id);
CREATE INDEX IF NOT EXISTS ix_associations_to ON associations(to_object_id);

-- ----------------------------------------------------------------------
-- lists
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lists (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    list_type VARCHAR(50) NOT NULL,
    filter_definition JSON,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_lists_tenant_name_object
    ON lists(tenant_id, name, object_type);

CREATE INDEX IF NOT EXISTS ix_lists_tenant ON lists(tenant_id);

-- ----------------------------------------------------------------------
-- list_memberships (depends on lists)
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS list_memberships (
    id UUID PRIMARY KEY,
    list_id UUID NOT NULL,
    member_id UUID NOT NULL,
    member_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    CONSTRAINT fk_list_memberships_list
        FOREIGN KEY (list_id) REFERENCES lists(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_list_memberships_list ON list_memberships(list_id);
CREATE INDEX IF NOT EXISTS ix_list_memberships_member ON list_memberships(member_id);
