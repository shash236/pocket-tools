"""Public contract of the notes module. Other modules import only from here."""

from .models import Note
from .services import get_note, list_notes

__all__ = ["Note", "get_note", "list_notes"]
