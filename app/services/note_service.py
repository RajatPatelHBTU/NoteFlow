"""Note service — business logic layer wrapping the repository."""

import logging
import math
from typing import Optional

import motor.motor_asyncio

from app.repositories.note_repository import NoteRepository
from app.schemas.note import (
    NoteCreate,
    NoteListResponse,
    NoteQueryParams,
    NoteResponse,
    NoteUpdate,
)

logger = logging.getLogger(__name__)


class NoteNotFoundError(Exception):
    """Raised when a requested note does not exist."""


class InvalidNoteIdError(Exception):
    """Raised when an invalid MongoDB ObjectId is provided."""


class NoteService:
    """Orchestrates note operations with business logic."""

    def __init__(self, collection: motor.motor_asyncio.AsyncIOMotorCollection):
        self.repo = NoteRepository(collection)

    def _to_response(self, doc: dict) -> NoteResponse:
        """Convert a raw MongoDB document dict to a NoteResponse schema."""
        return NoteResponse(**doc)

    # ── Create ────────────────────────────────────────────────────────────────

    async def create_note(self, note_data: NoteCreate) -> NoteResponse:
        """Create a new note and return it."""
        doc = await self.repo.create(note_data)
        logger.info(f"Created note '{doc['id']}': {doc['title']!r}")
        return self._to_response(doc)

    # ── Read ──────────────────────────────────────────────────────────────────

    async def get_note(self, note_id: str) -> NoteResponse:
        """Get a single note by ID."""
        try:
            doc = await self.repo.get_by_id(note_id)
        except ValueError:
            raise InvalidNoteIdError(note_id)

        if doc is None:
            raise NoteNotFoundError(note_id)

        return self._to_response(doc)

    async def list_notes(self, params: NoteQueryParams) -> NoteListResponse:
        """Return a paginated list of notes matching the given filters."""
        docs, total = await self.repo.list_notes(params)
        notes = [self._to_response(doc) for doc in docs]

        total_pages = max(1, math.ceil(total / params.page_size))

        return NoteListResponse(
            notes=notes,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_prev=params.page > 1,
        )

    async def get_sidebar_stats(self) -> dict:
        """Return data needed to render the sidebar (categories, tag counts, pinned count)."""
        total = await self.repo.get_total_count()
        pinned_count = await self.repo.count_pinned()
        category_counts = await self.repo.count_by_category()
        all_tags = await self.repo.get_all_tags()
        valid_tags = [str(t) for t in all_tags if t is not None and str(t).strip()]
        return {
            "total": total,
            "pinned_count": pinned_count,
            "category_counts": category_counts,
            "tags": sorted(set(valid_tags)),
        }

    # ── Update ────────────────────────────────────────────────────────────────

    async def update_note(self, note_id: str, note_data: NoteUpdate) -> NoteResponse:
        """Update an existing note."""
        try:
            doc = await self.repo.update(note_id, note_data)
        except ValueError:
            raise InvalidNoteIdError(note_id)

        if doc is None:
            raise NoteNotFoundError(note_id)

        logger.info(f"Updated note '{note_id}'")
        return self._to_response(doc)

    async def toggle_pin(self, note_id: str) -> NoteResponse:
        """Toggle pin status of a note."""
        try:
            doc = await self.repo.toggle_pin(note_id)
        except ValueError:
            raise InvalidNoteIdError(note_id)

        if doc is None:
            raise NoteNotFoundError(note_id)

        logger.info(f"Toggled pin on note '{note_id}' → {doc['is_pinned']}")
        return self._to_response(doc)

    # ── Delete ────────────────────────────────────────────────────────────────

    async def delete_note(self, note_id: str) -> None:
        """Delete a note by ID."""
        try:
            deleted = await self.repo.delete(note_id)
        except ValueError:
            raise InvalidNoteIdError(note_id)

        if not deleted:
            raise NoteNotFoundError(note_id)

        logger.info(f"Deleted note '{note_id}'")
