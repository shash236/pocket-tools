import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from pocket_toolkit.config import get_settings


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


class ModuleDB:
    """A module's own SQLite file at data/<module_id>.db.

    In a module: `db = ModuleDB.for_module(__name__)`.
    """

    def __init__(self, module_id: str) -> None:
        self.module_id = module_id

    @classmethod
    def for_module(cls, dotted_name: str) -> "ModuleDB":
        # "modules.notes.services" -> "notes"
        return cls(dotted_name.split(".")[1])

    @property
    def path(self) -> Path:
        return get_settings().data_dir / f"{self.module_id}.db"

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = connect(self.path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def query(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params)]

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        """Run a write; returns lastrowid."""
        with self.connect() as conn:
            return conn.execute(sql, params).lastrowid or 0
