from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from pocket_toolkit.admin.api import router as admin_router
from pocket_toolkit.config import get_settings
from pocket_toolkit.loader import load_modules
from pocket_toolkit.log import configure_logging

PACKAGE_DIR = Path(__file__).resolve().parent


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    app = FastAPI(title="Pocket Toolkit")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(admin_router, prefix="/admin/api", tags=["admin"])
    app.state.modules = load_modules(app, settings.project_dir, settings.data_dir)

    # Static mounts go last so API routes match first.
    app.mount(
        "/admin", StaticFiles(directory=PACKAGE_DIR / "admin" / "ui", html=True), name="admin"
    )
    app.mount("/", StaticFiles(directory=PACKAGE_DIR / "shell", html=True), name="shell")
    return app
