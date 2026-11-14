"""Atomic, session-scoped receipts. SQLite is local only; PostgreSQL is live."""
import hashlib
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from .common import canonical, now, revision
from .policy import check


class StoreError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message
        super().__init__(message)


class Store:
    def __init__(self, dsn, live=False):
        self.dsn, self.live = dsn, live
        self.pg = dsn.startswith("postgres")
        if live and not self.pg:
            raise ValueError("Live receipts require PostgreSQL.")

    @contextmanager
    def connection(self, write=False):
        if self.pg:
            import psycopg
            from psycopg.rows import dict_row
            c = psycopg.connect(self.dsn, row_factory=dict_row, connect_timeout=5)
            c.execute("SET search_path TO scaleproof")
            c.execute("SET statement_timeout = '5s'")
        else:
            c = sqlite3.connect(self.dsn, timeout=5)
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA foreign_keys = ON")
            c.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        try:
            yield c
            c.commit()
        except BaseException:
            c.rollback()
            raise
        finally:
            c.close()

    def sql(self, c, query, params=()):
        return c.execute(query.replace("?", "%s") if self.pg else query, params)

    def migrate(self):
        # Administrative setup only. Never called by a public route.
        with self.connection(True) as c:
            if self.pg:
                c.execute("CREATE SCHEMA IF NOT EXISTS scaleproof")
            c.execute("CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, expires DOUBLE PRECISION NOT NULL, attempts INTEGER NOT NULL DEFAULT 0)")
            c.execute("CREATE TABLE IF NOT EXISTS receipts (id TEXT PRIMARY KEY, session_hash TEXT NOT NULL REFERENCES sessions(token_hash) ON DELETE CASCADE, idem TEXT NOT NULL, input_digest TEXT NOT NULL, body TEXT NOT NULL, UNIQUE(session_hash, idem))")

    @staticmethod
    def token_hash(token):
        return hashlib.sha256(token.encode()).hexdigest()

    def new_session(self):
        token = secrets.token_urlsafe(32)
        with self.connection(True) as c:
            if self.pg:
                c.execute("SELECT pg_advisory_xact_lock(310031)")
            self.sql(c, "DELETE FROM sessions WHERE expires < ?", (time.time(),))
            if self.sql(c, "SELECT COUNT(*) AS n FROM sessions").fetchone()["n"] >= 1000:
                raise StoreError(429, "Session capacity reached. Try again after expiry.")
            self.sql(c, "INSERT INTO sessions(token_hash, expires) VALUES (?, ?)", (self.token_hash(token), time.time() + 86400))
        return token

    def session(self, c, token, lock=False):
        query = "SELECT * FROM sessions WHERE token_hash = ?"
        if self.pg and lock:
            query += " FOR UPDATE"
        row = self.sql(c, query, (self.token_hash(token),)).fetchone()
        if row is None or row["expires"] <= time.time():
            raise StoreError(401, "Session missing or expired. Start a new session.")
        return row

    def create(self, token, key, payload):
        result = check(payload)
        if not 8 <= len(key) <= 64 or not all(ch.isascii() and (ch.isalnum() or ch in "-_") for ch in key):
            raise StoreError(400, "Idempotency key must contain 8 to 64 ASCII letters, digits, underscores or hyphens.")
        with self.connection(True) as c:
            session = self.session(c, token, True)
            old = self.sql(c, "SELECT * FROM receipts WHERE session_hash = ? AND idem = ?", (session["token_hash"], key)).fetchone()
            if old:
                if old["input_digest"] != result["input_digest"]:
                    raise StoreError(409, "This idempotency key already identifies a different plan.")
                return {**json.loads(old["body"]), "replay": True}
            if session["attempts"] >= 50:
                raise StoreError(429, "Session budget of 50 workload checks reached.")
            body = {**result, "plan_check_id": secrets.token_hex(16), "persisted_at": now(),
                    "execution_mode": "deterministic_live" if self.live else "deterministic_local",
                    "source_revision": revision(), "replay": False}
            self.sql(c, "INSERT INTO receipts VALUES (?, ?, ?, ?, ?)", (body["plan_check_id"], session["token_hash"], key, result["input_digest"], canonical(body).decode()))
            self.sql(c, "UPDATE sessions SET attempts = attempts + 1 WHERE token_hash = ?", (session["token_hash"],))
        return body

    def get(self, token, receipt_id):
        with self.connection() as c:
            session = self.session(c, token)
            row = self.sql(c, "SELECT body FROM receipts WHERE id = ? AND session_hash = ?", (receipt_id, session["token_hash"])).fetchone()
            if row is None:
                raise StoreError(404, "Receipt not found in this session.")
            return json.loads(row["body"])

    def ready(self):
        with self.connection() as c:
            c.execute("SELECT id FROM receipts LIMIT 1")
        return True
