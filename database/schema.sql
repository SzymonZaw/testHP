CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS subjects (
    subject_id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS hands (
    hand_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    laterality TEXT NOT NULL DEFAULT 'unknown' CHECK (laterality IN ('left','right','unknown')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS timepoints (
    timepoint_id TEXT NOT NULL,
    subject_id TEXT NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
    acquisition_time TIMESTAMPTZ,
    subject_age_years NUMERIC(5,2) CHECK (subject_age_years >= 0 AND subject_age_years <= 130),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (subject_id, timepoint_id)
);

CREATE TABLE IF NOT EXISTS datasets (
    dataset_id TEXT PRIMARY KEY,
    subject_id TEXT REFERENCES subjects(subject_id) ON DELETE SET NULL,
    hand_id TEXT REFERENCES hands(hand_id) ON DELETE SET NULL,
    timepoint_id TEXT,
    modality TEXT NOT NULL,
    source TEXT NOT NULL,
    acquisition_time TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    quality JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence DOUBLE PRECISION CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    CHECK (timepoint_id IS NULL OR subject_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS observations (
    observation_id TEXT PRIMARY KEY,
    dataset_id TEXT REFERENCES datasets(dataset_id) ON DELETE SET NULL,
    subject_id TEXT REFERENCES subjects(subject_id) ON DELETE SET NULL,
    hand_id TEXT REFERENCES hands(hand_id) ON DELETE SET NULL,
    timepoint_id TEXT,
    spatial_frame TEXT,
    modality TEXT NOT NULL,
    observation_type TEXT NOT NULL,
    value JSONB NOT NULL DEFAULT '{}'::jsonb,
    geometry geometry(GeometryZ, 0),
    source TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acquisition_time TIMESTAMPTZ,
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    quality JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence DOUBLE PRECISION CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
);

CREATE TABLE IF NOT EXISTS stage_records (
    record_id TEXT PRIMARY KEY,
    stage INTEGER NOT NULL CHECK (stage BETWEEN 1 AND 32),
    stage_name TEXT NOT NULL,
    subject_id TEXT,
    hand_id TEXT,
    timepoint_id TEXT,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    source TEXT,
    evidence_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    provenance JSONB NOT NULL DEFAULT '{}'::jsonb,
    quality JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence DOUBLE PRECISION CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
);

CREATE INDEX IF NOT EXISTS idx_hands_subject ON hands(subject_id);
CREATE INDEX IF NOT EXISTS idx_timepoints_subject ON timepoints(subject_id);
CREATE INDEX IF NOT EXISTS idx_datasets_subject_timepoint ON datasets(subject_id, timepoint_id);
CREATE INDEX IF NOT EXISTS idx_observations_subject_timepoint ON observations(subject_id, timepoint_id);
CREATE INDEX IF NOT EXISTS idx_observations_geometry ON observations USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_stage_records_subject_timepoint ON stage_records(subject_id, timepoint_id);
CREATE INDEX IF NOT EXISTS idx_stage_records_stage ON stage_records(stage);
