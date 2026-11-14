CREATE TABLE IF NOT EXISTS scaleproof.physical_attempts (
  id TEXT PRIMARY KEY,
  session_hash TEXT NOT NULL REFERENCES scaleproof.sessions(token_hash) ON DELETE CASCADE,
  idem TEXT NOT NULL,
  input_digest TEXT NOT NULL,
  outcome TEXT NOT NULL,
  receipt_id TEXT,
  observed_at TEXT NOT NULL
);
GRANT SELECT, INSERT, UPDATE, DELETE ON scaleproof.physical_attempts TO scaleproof_app;
