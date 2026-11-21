"""The `pocket` command: init a project, add modules, run, check."""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from string import Template

from pocket_toolkit import __version__
from pocket_toolkit.checks import check_project

TEMPLATES = Path(__file__).resolve().parent / "templates"
MODULE_ID = re.compile(r"^[a-z][a-z0-9_]*$")


def init(target: Path, core_path: str | None) -> int:
    """Create a new project folder from templates/project."""
    if target.exists() and any(target.iterdir()):
        print(f"{target} is not empty", file=sys.stderr)
        return 1
    shutil.copytree(TEMPLATES / "project", target, dirs_exist_ok=True)
    # Stored under other names so packaging tools don't treat them as real config.
    (target / "gitignore").rename(target / ".gitignore")
    pyproject = target / "pyproject.toml.tmpl"
    sources = ""
    if core_path:
        sources = (
            f'\n[tool.uv.sources]\npocket-toolkit = {{ path = "{core_path}", editable = true }}\n'
        )
    major_minor = ".".join(__version__.split(".")[:2])
    pyproject.with_suffix("").write_text(
        Template(pyproject.read_text()).substitute(
            name=re.sub(r"[^a-z0-9-]", "-", target.resolve().name.lower()),
            core_requirement=f"pocket-toolkit~={major_minor}",
            sources=sources,
        )
    )
    pyproject.unlink()
    print(f"Created {target}. Next: cd {target} && uv sync && uv run pocket new <id>")
    return 0


def new_module(project: Path, module_id: str) -> int:
    """Copy templates/module to modules/<id>."""
    if not MODULE_ID.match(module_id):
        print(
            "module id must be lowercase letters, digits and _, starting with a letter",
            file=sys.stderr,
        )
        return 1
    target = project / "modules" / module_id
    if target.exists():
        print(f"{target} already exists", file=sys.stderr)
        return 1
    shutil.copytree(TEMPLATES / "module", target, ignore=shutil.ignore_patterns("__pycache__"))
    manifest = target / "manifest.yaml"
    name = module_id.replace("_", " ").title()
    manifest.write_text(
        manifest.read_text()
        .replace("id: your_id", f"id: {module_id}")
        .replace("name: Items", f"name: {name}")
    )
    print(f"Created {target.relative_to(project)}. Rename the `items` entity to your own.")
    return 0


def check(project: Path) -> int:
    problems = check_project(project)
    for p in problems:
        print(p, file=sys.stderr)
    if not problems:
        print("ok")
    return 1 if problems else 0


def dev(project: Path, host: str, port: int) -> int:
    import uvicorn

    os.environ["POCKET_PROJECT_DIR"] = str(project)
    uvicorn.run(
        "pocket_toolkit.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=True,
        reload_dirs=[str(project / "modules")],
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pocket")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--project", type=Path, default=Path.cwd(), help="project folder (default: current)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create a new project")
    p.add_argument("target", type=Path)
    p.add_argument("--core-path", help="use a local pocket-toolkit checkout (for development)")
    p = sub.add_parser("new", help="add a module from the template")
    p.add_argument("id")
    sub.add_parser("check", help="validate manifests and module import rules")
    p = sub.add_parser("dev", help="run the app with auto-reload")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)
    project = args.project.resolve()
    match args.command:
        case "init":
            return init(args.target, args.core_path)
        case "new":
            return new_module(project, args.id)
        case "check":
            return check(project)
        case "dev":
            return dev(project, args.host, args.port)
    return 2


if __name__ == "__main__":
    sys.exit(main())
