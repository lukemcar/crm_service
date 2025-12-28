-- liquibase formatted sql
-- changeset crm:9-create-associations-table runOnChange:true
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