-- liquibase formatted sql
-- changeset crm:7-create-lists-table runOnChange:true
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

CREATE UNIQUE INDEX IF NOT EXISTS ux_lists_tenant_name_object ON lists(tenant_id, name, object_type);
CREATE INDEX IF NOT EXISTS ix_lists_tenant ON lists(tenant_id);