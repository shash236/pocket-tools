import sqlite3
from pathlib import Path

import pytest

from pocket_toolkit.admin.migrations import run_migrations
from pocket_toolkit.loader import ManifestError
from pocket_toolkit.loader.manifest import read_manifest
from pocket_toolkit.sdk.db import connect


def write_module(root: Path, folder: str, manifest: str) -> Path:
    d = root / folder
    d.mkdir()
    (d / "manifest.yaml").write_text(manifest)
    return d


def test_manifest_id_must_match_folder(tmp_path: Path) -> None:
    d = write_module(tmp_path, "todo", "id: tasks\nname: Tasks\n")
    with pytest.raises(ManifestError, match="must match the folder name"):
        read_manifest(d)


def test_manifest_rejects_unknown_fields(tmp_path: Path) -> None:
    d = write_module(tmp_path, "todo", "id: todo\nname: Todo\nport: 8080\n")
    with pytest.raises(ManifestError, match="invalid manifest"):
        read_manifest(d)


def test_migrations_apply_once_in_order(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_init.sql").write_text("CREATE TABLE t (id INTEGER PRIMARY KEY);")
    (migrations / "002_add.sql").write_text("ALTER TABLE t ADD COLUMN name TEXT;")
    db = tmp_path / "x.db"

    assert run_migrations(db, migrations) == ["001_init.sql", "002_add.sql"]
    assert run_migrations(db, migrations) == []


def test_failed_migration_is_not_recorded(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_bad.sql").write_text("CREATE TABLE t (id INTEGER);\nNOT SQL;")
    db = tmp_path / "x.db"

    with pytest.raises(sqlite3.OperationalError):
        run_migrations(db, migrations)
    conn = connect(db)
    tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master")}
    conn.close()
    assert "t" not in tables
