from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = ""


class Item(ItemCreate):
    id: int
    created_at: str
