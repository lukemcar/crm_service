-- liquibase formatted sql
-- changeset crm:4-create-pipeline-stages-table runOnChange:true
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
    CONSTRAINT fk_pipeline_stages_pipeline FOREIGN KEY (pipeline_id) REFERENCES pipelines(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_pipeline_stages_pipeline_order ON pipeline_stages(pipeline_id, stage_order);
CREATE UNIQUE INDEX IF NOT EXISTS ux_pipeline_stages_pipeline_name ON pipeline_stages(pipeline_id, name);