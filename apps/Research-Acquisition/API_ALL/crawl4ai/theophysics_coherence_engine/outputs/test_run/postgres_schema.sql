-- Minimal Postgres schema (adjust types/indexes as needed)
CREATE TABLE IF NOT EXISTS inputs (
  doc_id TEXT PRIMARY KEY,
  timestamp TIMESTAMPTZ,
  filename TEXT,
  path TEXT,
  sha256 TEXT,
  bytes INTEGER
);

CREATE TABLE IF NOT EXISTS chi_delta_grace (
  doc_id TEXT,
  timestamp TIMESTAMPTZ,
  filename TEXT,
  chi DOUBLE PRECISION,
  t_days DOUBLE PRECISION,
  chi_slope DOUBLE PRECISION,
  drift_delta DOUBLE PRECISION,
  grace_G DOUBLE PRECISION,
  drift_z DOUBLE PRECISION,
  grace_z DOUBLE PRECISION,
  is_drift_spike BOOLEAN,
  is_grace_spike BOOLEAN
);

-- Suggested indexes
CREATE INDEX IF NOT EXISTS idx_cdg_time ON chi_delta_grace(timestamp);
CREATE INDEX IF NOT EXISTS idx_cdg_doc ON chi_delta_grace(doc_id);
