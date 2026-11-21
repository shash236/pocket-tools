import importlib
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from pocket_tools.admin.migrations import run_migrations
from pocket_tools.loader.manifest import Manifest, ManifestError, read_manifest

log = logging.getLogger(__name__)

_project_path: str | None = None


@dataclass(frozen=True)
class LoadedModule:
    manifest: Manifest
    path: Path
    has_api: bool
    has_ui: bool


def discover(modules_dir: Path) -> list[tuple[Path, Manifest]]:
    """Every folder in modules/ not starting with '_' or '.' is a module."""
    if not modules_dir.is_dir():
        return []
    found = [
        (d, read_manifest(d))
        for d in sorted(modules_dir.iterdir())
        if d.is_dir() and not d.name.startswith(("_", "."))
    ]
    ids = {m.id for _, m in found}
    for _, m in found:
        missing = [dep for dep in m.depends_on if dep not in ids]
        if missing:
            raise ManifestError(f"{m.id}: depends on missing modules {missing}")
    return found


def use_project(project_dir: Path) -> None:
    """Make `import modules.<id>` resolve to this project's modules/ package."""
    global _project_path
    path = str(project_dir)
    if _project_path != path:
        if _project_path in sys.path:
            sys.path.remove(_project_path)
        for name in [n for n in sys.modules if n == "modules" or n.startswith("modules.")]:
            del sys.modules[name]
        importlib.invalidate_caches()
        _project_path = path
    if path not in sys.path:
        sys.path.insert(0, path)


def load_modules(app: FastAPI, project_dir: Path, data_dir: Path) -> list[LoadedModule]:
    use_project(project_dir)
    loaded = []
    for module_dir, manifest in discover(project_dir / "modules"):
        run_migrations(data_dir / f"{manifest.id}.db", module_dir / "migrations")

        has_api = (module_dir / "api.py").is_file()
        if has_api:
            api = importlib.import_module(f"modules.{manifest.id}.api")
            router = getattr(api, "router", None)
            if not isinstance(router, APIRouter):
                raise ManifestError(f"{manifest.id}: api.py must define `router = APIRouter()`")
            app.include_router(router, prefix=f"/m/{manifest.id}/api", tags=[manifest.id])

        ui_dir = module_dir / "ui"
        has_ui = (ui_dir / "index.html").is_file()
        if has_ui:
            # Relative fetch("api/...") in the UI needs the trailing slash.
            root = f"/m/{manifest.id}/"
            app.add_api_route(
                root.rstrip("/"),
                lambda root=root: RedirectResponse(root),
                include_in_schema=False,
            )
            app.mount(
                f"/m/{manifest.id}",
                StaticFiles(directory=ui_dir, html=True),
                name=f"module-{manifest.id}",
            )

        loaded.append(LoadedModule(manifest, module_dir, has_api, has_ui))
        log.info("loaded module %s %s", manifest.id, manifest.version)
    return loaded
