from fastapi import APIRouter, Depends, HTTPException
from pocket_toolkit.sdk.auth import require_owner

from . import services
from .models import Note, NoteCreate

router = APIRouter(dependencies=[Depends(require_owner)])


@router.get("/notes")
def list_notes() -> list[Note]:
    return services.list_notes()


@router.post("/notes", status_code=201)
def create_note(data: NoteCreate) -> Note:
    return services.create_note(data)


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int) -> None:
    if not services.delete_note(note_id):
        raise HTTPException(404, "Note not found")
