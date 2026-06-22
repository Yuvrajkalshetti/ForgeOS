"""Forward-only SQLite migrations.

The database is a rebuildable index, so migrations are simple and additive. The
current version lives in ``schema_meta``; ``run_migrations`` applies any pending
steps idempotently. Later phases append migrations (e.g. typed tables and edge
indexes) without touching earlier ones.
"""

from __future__ import annotations

import sqlite3

_SCHEMA_META = "schema_meta"
_SCHEMA_VERSION_KEY = "schema_version"

# (version, SQL). Applied in order when version > current.
_MIGRATIONS: list[tuple[int, str]] = [
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS schema_meta (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS records (
            collection TEXT NOT NULL,
            id         TEXT NOT NULL,
            data       TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (collection, id)
        );
        CREATE INDEX IF NOT EXISTS idx_records_collection ON records (collection);
        """,
    ),
]


def current_version(conn: sqlite3.Connection) -> int:
    """Return the applied schema version, or 0 if uninitialized."""
    try:
        row = conn.execute(
            f"SELECT value FROM {_SCHEMA_META} WHERE key = ?", (_SCHEMA_VERSION_KEY,)
        ).fetchone()
    except sqlite3.OperationalError:
        return 0
    return int(row[0]) if row is not None else 0


def run_migrations(conn: sqlite3.Connection) -> int:
    """Apply all pending migrations and return the resulting version."""
    version = current_version(conn)
    for target, sql in _MIGRATIONS:
        if target > version:
            conn.executescript(sql)
            conn.execute(
                f"INSERT OR REPLACE INTO {_SCHEMA_META} (key, value) VALUES (?, ?)",
                (_SCHEMA_VERSION_KEY, str(target)),
            )
            version = target
    conn.commit()
    return version
