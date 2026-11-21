from fastapi import APIRouter, Depends, HTTPException

from pocket_toolkit.sdk.auth import require_owner

from . import services
from .models import Item, ItemCreate

router = APIRouter(dependencies=[Depends(require_owner)])


@router.get("/items")
def list_items() -> list[Item]:
    return services.list_items()


@router.post("/items", status_code=201)
def create_item(data: ItemCreate) -> Item:
    return services.create_item(data)


@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int) -> None:
    if not services.delete_item(item_id):
        raise HTTPException(404, "Item not found")
