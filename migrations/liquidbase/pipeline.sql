-- liquibase formatted sql
-- changeset crm:3-create-pipelines-table runOnChange:true
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