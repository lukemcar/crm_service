-- liquibase formatted sql
-- changeset crm:2-create-companies-table runOnChange:true
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

CREATE UNIQUE INDEX IF NOT EXISTS ux_companies_tenant_company_name ON companies(tenant_id, company_name);
CREATE INDEX IF NOT EXISTS ix_companies_tenant ON companies(tenant_id);