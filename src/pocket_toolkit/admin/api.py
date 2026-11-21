from typing import Any

from fastapi import APIRouter, Depends, Request

from pocket_toolkit.loader import LoadedModule
from pocket_toolkit.sdk.auth import require_owner

router = APIRouter(dependencies=[Depends(require_owner)])


@router.get("/modules")
def list_modules(request: Request) -> list[dict[str, Any]]:
    modules: list[LoadedModule] = request.app.state.modules
    return [
        {
            **m.manifest.model_dump(include={"id", "name", "version", "icon", "description"}),
            "url": f"/m/{m.manifest.id}/" if m.has_ui else None,
        }
        for m in modules
    ]
