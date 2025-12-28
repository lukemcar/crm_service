-- liquibase formatted sql
-- changeset crm:5-create-deals-table runOnChange:true
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
    CONSTRAINT fk_deals_pipeline FOREIGN KEY (pipeline_id) REFERENCES pipelines(id) ON DELETE CASCADE,
    CONSTRAINT fk_deals_stage FOREIGN KEY (stage_id) REFERENCES pipeline_stages(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_deals_tenant ON deals(tenant_id);
CREATE INDEX IF NOT EXISTS ix_deals_pipeline ON deals(pipeline_id);
CREATE INDEX IF NOT EXISTS ix_deals_stage ON deals(stage_id);