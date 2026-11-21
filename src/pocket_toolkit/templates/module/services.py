from pocket_toolkit.sdk.db import ModuleDB

from .models import Item, ItemCreate

db = ModuleDB.for_module(__name__)


def list_items() -> list[Item]:
    rows = db.query("SELECT * FROM items ORDER BY id DESC")
    return [Item.model_validate(row) for row in rows]


def get_item(item_id: int) -> Item | None:
    rows = db.query("SELECT * FROM items WHERE id = ?", (item_id,))
    return Item.model_validate(rows[0]) if rows else None


def create_item(data: ItemCreate) -> Item:
    item_id = db.execute("INSERT INTO items (title, body) VALUES (?, ?)", (data.title, data.body))
    item = get_item(item_id)
    assert item is not None
    return item


def delete_item(item_id: int) -> bool:
    with db.connect() as conn:
        return conn.execute("DELETE FROM items WHERE id = ?", (item_id,)).rowcount > 0
