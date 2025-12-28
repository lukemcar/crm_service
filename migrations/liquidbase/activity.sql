-- liquibase formatted sql
-- changeset crm:6-create-activities-table runOnChange:true
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