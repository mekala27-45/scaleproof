CREATE SCHEMA IF NOT EXISTS scaleproof;
CREATE TABLE IF NOT EXISTS scaleproof.sessions (
  token_hash TEXT PRIMARY KEY,
  expires DOUBLE PRECISION NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0 AND attempts <= 50)
);
CREATE TABLE IF NOT EXISTS scaleproof.receipts (
  id TEXT PRIMARY KEY,
  session_hash TEXT NOT NULL REFERENCES scaleproof.sessions(token_hash) ON DELETE CASCADE,
  idem TEXT NOT NULL,
  input_digest TEXT NOT NULL,
  body TEXT NOT NULL,
  UNIQUE(session_hash, idem)
);
