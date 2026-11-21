"""Pytest helpers for user projects. Enable with `pytest_plugins = ["pocket_toolkit.testing"]`."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pocket_toolkit.app import create_app
from pocket_toolkit.config import get_settings


@pytest.fixture
def client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pytestconfig: pytest.Config
) -> Iterator[TestClient]:
    """The project's app, with a fresh empty data folder per test."""
    monkeypatch.setenv("POCKET_PROJECT_DIR", str(pytestconfig.rootpath))
    monkeypatch.setenv("POCKET_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    with TestClient(create_app()) as c:
        yield c
    get_settings.cache_clear()
