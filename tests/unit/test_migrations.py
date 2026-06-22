from __future__ import annotations

import sqlite3

from forgeos.adapters.storage.sqlite.migrations import current_version, run_migrations


def test_fresh_db_starts_at_zero() -> None:
    conn = sqlite3.connect(":memory:")
    assert current_version(conn) == 0


def test_run_migrations_sets_version() -> None:
    conn = sqlite3.connect(":memory:")
    assert run_migrations(conn) == 1
    assert current_version(conn) == 1


def test_run_migrations_is_idempotent() -> None:
    conn = sqlite3.connect(":memory:")
    run_migrations(conn)
    assert run_migrations(conn) == 1  # no error, stays at 1
    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {"records", "schema_meta"} <= tables
