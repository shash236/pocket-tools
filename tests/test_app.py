from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import NOTES_PROJECT, MakeClient


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_lists_project_modules(client: TestClient) -> None:
    modules = client.get("/admin/api/modules").json()
    assert [(m["id"], m["url"]) for m in modules] == [("notes", "/m/notes/")]


def test_serves_shell_admin_and_module_ui(client: TestClient) -> None:
    assert "Apps" in client.get("/").text
    assert "Admin" in client.get("/admin/").text
    assert "Notes" in client.get("/m/notes/").text
    redirect = client.get("/m/notes", follow_redirects=False)
    assert redirect.headers["location"] == "/m/notes/"


def test_data_survives_restart(make_client: MakeClient, data_dir: Path) -> None:
    make_client(NOTES_PROJECT).post("/m/notes/api/notes", json={"title": "Hello"})

    restarted = make_client(NOTES_PROJECT)
    assert [n["title"] for n in restarted.get("/m/notes/api/notes").json()] == ["Hello"]
    assert (data_dir / "notes.db").is_file()


def test_project_without_modules_runs(make_client: MakeClient, tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    assert make_client(empty).get("/admin/api/modules").json() == []
