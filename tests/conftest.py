from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pocket_tools.app import create_app
from pocket_tools.config import get_settings

REPO = Path(__file__).resolve().parent.parent
NOTES_PROJECT = REPO / "examples" / "notes"

type MakeClient = Callable[[Path], TestClient]


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    return tmp_path / "data"


@pytest.fixture
def make_client(data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[MakeClient]:
    """Build the app for a given project; data lives in a temp folder."""
    clients: list[TestClient] = []

    def make(project_dir: Path) -> TestClient:
        monkeypatch.setenv("POCKET_PROJECT_DIR", str(project_dir))
        monkeypatch.setenv("POCKET_DATA_DIR", str(data_dir))
        get_settings.cache_clear()
        client = TestClient(create_app())
        client.__enter__()
        clients.append(client)
        return client

    yield make
    for client in clients:
        client.__exit__(None, None, None)
    get_settings.cache_clear()


@pytest.fixture
def client(make_client: MakeClient) -> TestClient:
    return make_client(NOTES_PROJECT)
