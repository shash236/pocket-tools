"""Import rules: for user modules (via pocket_toolkit.checks) and for core itself."""

from pathlib import Path

from pocket_toolkit.checks import check_project, imports
from tests.conftest import NOTES_PROJECT, REPO

PACKAGE = REPO / "src" / "pocket_toolkit"


def write_module(project: Path, module_id: str, code: str) -> None:
    d = project / "modules" / module_id
    d.mkdir(parents=True)
    (d / "manifest.yaml").write_text(f"id: {module_id}\nname: {module_id}\n")
    (d / "services.py").write_text(code)


def test_example_project_passes() -> None:
    assert check_project(NOTES_PROJECT) == []


def test_module_may_use_sdk_interfaces_and_itself(tmp_path: Path) -> None:
    write_module(tmp_path, "notes", "")
    write_module(
        tmp_path,
        "todo",
        "import json\n"
        "from pocket_toolkit.sdk.db import ModuleDB\n"
        "from modules.notes.interface import list_notes\n"
        "from modules.notes import interface\n"
        "from modules.todo.models import Todo\n"
        "from .models import Todo\n",
    )
    assert check_project(tmp_path) == []


def test_module_may_not_reach_into_core_or_other_modules(tmp_path: Path) -> None:
    write_module(tmp_path, "notes", "")
    write_module(
        tmp_path,
        "todo",
        "from pocket_toolkit.config import get_settings\n"
        "import pocket_toolkit.loader\n"
        "from modules.notes.services import db\n"
        "from modules.notes import services\n",
    )
    assert check_project(tmp_path) == [
        "modules/todo/services.py: may not import pocket_toolkit.config.get_settings",
        "modules/todo/services.py: may not import pocket_toolkit.loader",
        "modules/todo/services.py: may not import modules.notes.services.db",
        "modules/todo/services.py: may not import modules.notes.services",
    ]


def test_bad_manifest_is_reported(tmp_path: Path) -> None:
    write_module(tmp_path, "todo", "")
    (tmp_path / "modules" / "todo" / "manifest.yaml").write_text("id: other\nname: x\n")
    assert "must match the folder name" in check_project(tmp_path)[0]


def core_imports(folder: Path) -> list[tuple[str, str]]:
    return [
        (str(path.relative_to(PACKAGE)), name)
        for path in sorted(folder.rglob("*.py"))
        if "templates" not in path.parts
        for name in imports(path)
    ]


def test_core_never_imports_modules() -> None:
    assert [(f, n) for f, n in core_imports(PACKAGE) if n.startswith("modules")] == []


def test_sdk_depends_only_on_itself_and_config() -> None:
    bad = [
        (f, n)
        for f, n in core_imports(PACKAGE / "sdk")
        if n.startswith("pocket_toolkit.")
        and not n.startswith(("pocket_toolkit.sdk", "pocket_toolkit.config"))
    ]
    assert bad == []
