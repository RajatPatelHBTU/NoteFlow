"""REST API router for Notes — JSON endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import get_notes_collection
from app.schemas.note import (
    CATEGORIES,
    NoteCreate,
    NoteListResponse,
    NoteQueryParams,
    NoteResponse,
    NoteUpdate,
)
from app.services.note_service import InvalidNoteIdError, NoteNotFoundError, NoteService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notes", tags=["Notes"])


def get_note_service(collection=Depends(get_notes_collection)) -> NoteService:
    """Dependency: return a NoteService bound to the active DB collection."""
    return NoteService(collection)


# ── Helper ────────────────────────────────────────────────────────────────────

def _handle_service_errors(exc: Exception, note_id: str = ""):
    """Convert service-layer errors to HTTP exceptions."""
    if isinstance(exc, InvalidNoteIdError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid note ID: '{note_id}'",
        )
    if isinstance(exc, NoteNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note not found: '{note_id}'",
        )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred.",
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=NoteListResponse,
    summary="List all notes",
    description="Retrieve a paginated, filtered, and sorted list of notes.",
)
async def list_notes(
    q: Optional[str] = Query(None, description="Full-text search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    is_pinned: Optional[bool] = Query(None, description="Filter by pinned status"),
    sort: str = Query("newest", description="Sort: newest | oldest | updated | alpha_asc | alpha_desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: NoteService = Depends(get_note_service),
):
    params = NoteQueryParams(
        q=q, category=category, tag=tag, is_pinned=is_pinned,
        sort=sort, page=page, page_size=page_size,
    )
    return await service.list_notes(params)


@router.get(
    "/categories",
    response_model=list[str],
    summary="Get available categories",
    description="Return the predefined list of note categories.",
)
async def get_categories():
    return CATEGORIES


@router.get(
    "/search",
    response_model=NoteListResponse,
    summary="Search notes",
    description="Full-text search across title, content, tags, and category.",
)
async def search_notes(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: NoteService = Depends(get_note_service),
):
    params = NoteQueryParams(q=q, page=page, page_size=page_size)
    return await service.list_notes(params)


@router.get(
    "/category/{category}",
    response_model=NoteListResponse,
    summary="Filter notes by category",
    description="Return notes belonging to the specified category.",
)
async def notes_by_category(
    category: str,
    sort: str = Query("newest"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: NoteService = Depends(get_note_service),
):
    params = NoteQueryParams(category=category, sort=sort, page=page, page_size=page_size)
    return await service.list_notes(params)


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Get a single note",
    description="Retrieve a note by its MongoDB ObjectId.",
    responses={
        400: {"description": "Invalid note ID"},
        404: {"description": "Note not found"},
    },
)
async def get_note(note_id: str, service: NoteService = Depends(get_note_service)):
    try:
        return await service.get_note(note_id)
    except (InvalidNoteIdError, NoteNotFoundError) as exc:
        _handle_service_errors(exc, note_id)


@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new note",
    description="Create and persist a new note to MongoDB.",
)
async def create_note(note_data: NoteCreate, service: NoteService = Depends(get_note_service)):
    return await service.create_note(note_data)


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Update a note",
    description="Update an existing note's fields.",
    responses={400: {"description": "Invalid ID"}, 404: {"description": "Not found"}},
)
async def update_note(
    note_id: str,
    note_data: NoteUpdate,
    service: NoteService = Depends(get_note_service),
):
    try:
        return await service.update_note(note_id, note_data)
    except (InvalidNoteIdError, NoteNotFoundError) as exc:
        _handle_service_errors(exc, note_id)


@router.patch(
    "/{note_id}/pin",
    response_model=NoteResponse,
    summary="Toggle note pin status",
    description="Pin or unpin a note.",
    responses={400: {"description": "Invalid ID"}, 404: {"description": "Not found"}},
)
async def toggle_pin(note_id: str, service: NoteService = Depends(get_note_service)):
    try:
        return await service.toggle_pin(note_id)
    except (InvalidNoteIdError, NoteNotFoundError) as exc:
        _handle_service_errors(exc, note_id)


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a note",
    description="Permanently delete a note from MongoDB.",
    responses={400: {"description": "Invalid ID"}, 404: {"description": "Not found"}},
)
async def delete_note(note_id: str, service: NoteService = Depends(get_note_service)):
    try:
        await service.delete_note(note_id)
    except (InvalidNoteIdError, NoteNotFoundError) as exc:
        _handle_service_errors(exc, note_id)
