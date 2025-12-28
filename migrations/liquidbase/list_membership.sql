-- liquibase formatted sql
-- changeset crm:8-create-list-memberships-table runOnChange:true
CREATE TABLE IF NOT EXISTS list_memberships (
    id UUID PRIMARY KEY,
    list_id UUID NOT NULL,
    member_id UUID NOT NULL,
    member_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    CONSTRAINT fk_list_memberships_list FOREIGN KEY (list_id) REFERENCES lists(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_list_memberships_list ON list_memberships(list_id);
CREATE INDEX IF NOT EXISTS ix_list_memberships_member ON list_memberships(member_id);