"""Rules a user project must pass before it runs or deploys. Exposed as `pocket check`."""

import ast
from collections.abc import Iterator
from pathlib import Path

from pocket_toolkit.loader.loader import discover
from pocket_toolkit.loader.manifest import ManifestError


def imports(path: Path) -> Iterator[str]:
    """Absolute dotted names imported by a file (relative imports are module-internal)."""
    for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
        if isinstance(node, ast.Import):
            yield from (a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            # `from modules.x import interface` counts as importing modules.x.interface
            for a in node.names:
                yield f"{node.module}.{a.name}"


def import_allowed(module_id: str, name: str) -> bool:
    """A module imports only pocket_toolkit.sdk, itself, and other modules' interface."""
    parts = name.split(".")
    if parts[0] == "pocket_toolkit":
        return parts[1:2] == ["sdk"]
    if parts[0] == "modules":
        return len(parts) >= 2 and (parts[1] == module_id or parts[2:3] == ["interface"])
    return True


def check_project(project_dir: Path) -> list[str]:
    """Return a list of problems; empty means the project passes."""
    modules_dir = project_dir / "modules"
    try:
        found = discover(modules_dir)
    except ManifestError as e:
        return [str(e)]
    problems = []
    for module_dir, manifest in found:
        for path in sorted(module_dir.rglob("*.py")):
            rel = path.relative_to(project_dir)
            try:
                names = list(imports(path))
            except SyntaxError as e:
                problems.append(f"{rel}: syntax error: {e.msg} (line {e.lineno})")
                continue
            problems += [
                f"{rel}: may not import {name}"
                for name in names
                if not import_allowed(manifest.id, name)
            ]
    return problems
