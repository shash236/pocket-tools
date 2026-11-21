from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = ""


class Note(NoteCreate):
    id: int
    created_at: str
