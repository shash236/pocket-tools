"""Applies each module's numbered SQL migrations to its own database."""

import logging
from pathlib import Path

from pocket_toolkit.sdk.db import connect

log = logging.getLogger(__name__)


def run_migrations(db_path: Path, migrations_dir: Path) -> list[str]:
    """Apply migrations/*.sql not yet recorded in _migrations, in name order."""
    if not migrations_dir.is_dir():
        return []
    conn = connect(db_path)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS _migrations ("
            " name TEXT PRIMARY KEY,"
            " applied_at TEXT NOT NULL DEFAULT (datetime('now')))"
        )
        done = {row["name"] for row in conn.execute("SELECT name FROM _migrations")}
        applied = []
        for path in sorted(migrations_dir.glob("*.sql")):
            if path.name in done:
                continue
            # One transaction for the migration and its record, so a failure leaves neither.
            name = path.name.replace("'", "''")
            conn.executescript(
                f"BEGIN;\n{path.read_text()}\n"
                f"INSERT INTO _migrations (name) VALUES ('{name}');\nCOMMIT;"
            )
            applied.append(path.name)
            log.info("applied %s to %s", path.name, db_path.name)
        return applied
    finally:
        conn.close()
