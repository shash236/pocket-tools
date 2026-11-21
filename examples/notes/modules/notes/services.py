from pocket_toolkit.sdk.db import ModuleDB

from .models import Note, NoteCreate

db = ModuleDB.for_module(__name__)


def list_notes() -> list[Note]:
    rows = db.query("SELECT * FROM notes ORDER BY id DESC")
    return [Note.model_validate(row) for row in rows]


def get_note(note_id: int) -> Note | None:
    rows = db.query("SELECT * FROM notes WHERE id = ?", (note_id,))
    return Note.model_validate(rows[0]) if rows else None


def create_note(data: NoteCreate) -> Note:
    note_id = db.execute("INSERT INTO notes (title, body) VALUES (?, ?)", (data.title, data.body))
    note = get_note(note_id)
    assert note is not None
    return note


def delete_note(note_id: int) -> bool:
    with db.connect() as conn:
        return conn.execute("DELETE FROM notes WHERE id = ?", (note_id,)).rowcount > 0
