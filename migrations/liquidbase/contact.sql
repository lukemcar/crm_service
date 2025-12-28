-- liquibase formatted sql
-- changeset crm:1-create-contacts-table runOnChange:true
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

-- ensure emails are unique per tenant
CREATE UNIQUE INDEX IF NOT EXISTS ux_contacts_tenant_email ON contacts(tenant_id, email);

-- index on tenant for queries
CREATE INDEX IF NOT EXISTS ix_contacts_tenant ON contacts(tenant_id);