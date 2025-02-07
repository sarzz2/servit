-- up
-- Enable the TimescaleDB extension (run once per database)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create the audit_logs table with a composite primary key
CREATE TABLE audit_logs (
    id SERIAL,
    user_uuid UUID,
    entity TEXT NOT NULL,
    entity_uuid UUID,
    action TEXT NOT NULL,
    changes JSONB,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, timestamp)  -- Composite primary key
);

-- Create the hypertable
SELECT create_hypertable('audit_logs', 'timestamp', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX idx_audit_entity ON audit_logs(entity);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);

-- down

-- Drop the hypertable
DROP TABLE audit_logs;

-- Drop indexes
DROP INDEX IF EXISTS idx_audit_entity;
DROP INDEX IF EXISTS idx_audit_timestamp;
DROP INDEX IF EXISTS idx_unique_entity_id_timestamp;

-- Drop the audit_logs table
DROP TABLE IF EXISTS audit_logs;
