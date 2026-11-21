import tomllib
from pathlib import Path

from pocket_tools.cli import main
from tests.conftest import MakeClient


def test_init_new_check_and_run(tmp_path: Path, make_client: MakeClient) -> None:
    project = tmp_path / "my-apps"
    assert main(["init", str(project)]) == 0
    assert (project / ".gitignore").is_file()
    assert (project / "AGENTS.md").is_file()
    pyproject = tomllib.loads((project / "pyproject.toml").read_text())
    assert pyproject["project"]["name"] == "my-apps"
    assert pyproject["project"]["dependencies"] == ["pocket-tools~=0.1"]

    assert main(["--project", str(project), "new", "todo_list"]) == 0
    manifest = (project / "modules" / "todo_list" / "manifest.yaml").read_text()
    assert "id: todo_list" in manifest
    assert "name: Todo List" in manifest
    assert main(["--project", str(project), "check"]) == 0

    client = make_client(project)
    created = client.post("/m/todo_list/api/items", json={"title": "Ship it"})
    assert created.status_code == 201
    assert client.get("/m/todo_list/api/items").json()[0]["title"] == "Ship it"


def test_init_with_core_path_adds_uv_source(tmp_path: Path) -> None:
    assert main(["init", str(tmp_path / "p"), "--core-path", "../core"]) == 0
    pyproject = tomllib.loads((tmp_path / "p" / "pyproject.toml").read_text())
    assert pyproject["tool"]["uv"]["sources"]["pocket-tools"]["path"] == "../core"


def test_init_refuses_non_empty_folder(tmp_path: Path) -> None:
    (tmp_path / "file").write_text("x")
    assert main(["init", str(tmp_path)]) == 1


def test_new_rejects_bad_or_duplicate_ids(tmp_path: Path) -> None:
    (tmp_path / "modules").mkdir()
    assert main(["--project", str(tmp_path), "new", "Bad-Id"]) == 1
    assert main(["--project", str(tmp_path), "new", "todo"]) == 0
    assert main(["--project", str(tmp_path), "new", "todo"]) == 1
