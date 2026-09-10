"""HTMX partial routes — return HTML fragments for dynamic interactions."""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database import get_notes_collection
from app.schemas.note import CATEGORIES, NoteCreate, NoteQueryParams, NoteUpdate
from app.services.note_service import InvalidNoteIdError, NoteNotFoundError, NoteService

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
router = APIRouter(prefix="/htmx", tags=["HTMX"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def get_note_service(collection=Depends(get_notes_collection)) -> NoteService:
    return NoteService(collection)


def _toast_headers(message: str, toast_type: str = "success") -> dict:
    """Return HTMX response headers that trigger a toast notification."""
    import json
    return {
        "HX-Trigger": json.dumps({"showToast": {"message": message, "type": toast_type}})
    }


# ── Notes List ────────────────────────────────────────────────────────────────

@router.get("/notes", response_class=HTMLResponse)
async def htmx_notes_list(
    request: Request,
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    is_pinned: Optional[bool] = Query(None),
    sort: str = Query("newest"),
    page: int = Query(1, ge=1),
    service: NoteService = Depends(get_note_service),
):
    """Return the notes list partial (used for filtering/sorting)."""
    params = NoteQueryParams(
        q=q, category=category, tag=tag, is_pinned=is_pinned,
        sort=sort, page=page, page_size=20,
    )
    notes_page = await service.list_notes(params)
    stats = await service.get_sidebar_stats()

    return templates.TemplateResponse(
        "partials/notes_list.html",
        {
            "request": request,
            "notes_page": notes_page,
            "stats": stats,
            "categories": CATEGORIES,
            "current_q": q or "",
            "current_category": category or "",
            "current_tag": tag or "",
            "current_sort": sort,
            "current_pinned": is_pinned,
        },
    )


# ── Create Note ───────────────────────────────────────────────────────────────

@router.post("/notes", response_class=HTMLResponse)
async def htmx_create_note(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form("Other"),
    tags: str = Form(""),
    is_pinned: bool = Form(False),
    service: NoteService = Depends(get_note_service),
):
    """Create a note and return the updated notes list."""
    try:
        note_data = NoteCreate(
            title=title,
            content=content,
            category=category,
            tags=tags,
            is_pinned=is_pinned,
        )
        await service.create_note(note_data)
    except Exception as e:
        logger.error(f"Create note error: {e}")
        return templates.TemplateResponse(
            "partials/toast.html",
            {"request": request, "message": str(e), "toast_type": "error"},
            headers=_toast_headers(f"Error: {e}", "error"),
        )

    # Return updated list + redirect signal
    params = NoteQueryParams()
    notes_page = await service.list_notes(params)
    stats = await service.get_sidebar_stats()
    headers = {
        **_toast_headers("Note created successfully!", "success"),
        "HX-Redirect": "/",
    }
    return templates.TemplateResponse(
        "partials/notes_list.html",
        {
            "request": request,
            "notes_page": notes_page,
            "stats": stats,
            "categories": CATEGORIES,
            "current_q": "",
            "current_category": "",
            "current_tag": "",
            "current_sort": "newest",
            "current_pinned": None,
        },
        headers=headers,
    )


# ── Update Note ───────────────────────────────────────────────────────────────

@router.put("/notes/{note_id}", response_class=HTMLResponse)
async def htmx_update_note(
    note_id: str,
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form("Other"),
    tags: str = Form(""),
    is_pinned: bool = Form(False),
    service: NoteService = Depends(get_note_service),
):
    """Update a note and return the updated note card."""
    try:
        note_data = NoteUpdate(
            title=title,
            content=content,
            category=category,
            tags=tags,
            is_pinned=is_pinned,
        )
        note = await service.update_note(note_id, note_data)
    except (InvalidNoteIdError, NoteNotFoundError) as exc:
        msg = "Invalid note ID" if isinstance(exc, InvalidNoteIdError) else "Note not found"
        return templates.TemplateResponse(
            "partials/toast.html",
            {"request": request, "message": msg, "toast_type": "error"},
            headers=_toast_headers(msg, "error"),
        )
    except Exception as e:
        return templates.TemplateResponse(
            "partials/toast.html",
            {"request": request, "message": str(e), "toast_type": "error"},
            headers=_toast_headers(str(e), "error"),
        )

    headers = {
        **_toast_headers("Note updated successfully!", "success"),
        "HX-Push-Url": f"/notes/{note_id}",
    }
    return templates.TemplateResponse(
        "partials/note_card.html",
        {"request": request, "note": note},
        headers=headers,
    )


# ── Delete Note ───────────────────────────────────────────────────────────────

@router.delete("/notes/{note_id}", response_class=HTMLResponse)
async def htmx_delete_note(
    note_id: str,
    request: Request,
    service: NoteService = Depends(get_note_service),
):
    """Delete a note and return an empty response (HTMX removes the card)."""
    try:
        await service.delete_note(note_id)
    except (InvalidNoteIdError, NoteNotFoundError) as exc:
        msg = "Invalid note ID" if isinstance(exc, InvalidNoteIdError) else "Note not found"
        return HTMLResponse(
            content="",
            status_code=200,
            headers=_toast_headers(msg, "error"),
        )

    return HTMLResponse(
        content="",
        status_code=200,
        headers=_toast_headers("Note deleted successfully!", "success"),
    )


# ── Toggle Pin ────────────────────────────────────────────────────────────────

@router.patch("/notes/{note_id}/pin", response_class=HTMLResponse)
async def htmx_toggle_pin(
    note_id: str,
    request: Request,
    service: NoteService = Depends(get_note_service),
):
    """Toggle note pin and return updated note card."""
    try:
        note = await service.toggle_pin(note_id)
    except (InvalidNoteIdError, NoteNotFoundError) as exc:
        msg = "Invalid note ID" if isinstance(exc, InvalidNoteIdError) else "Note not found"
        return HTMLResponse(content="", headers=_toast_headers(msg, "error"))

    pin_msg = "Note pinned!" if note.is_pinned else "Note unpinned."
    return templates.TemplateResponse(
        "partials/note_card.html",
        {"request": request, "note": note},
        headers=_toast_headers(pin_msg, "info"),
    )


# ── Search ────────────────────────────────────────────────────────────────────

@router.get("/search", response_class=HTMLResponse)
async def htmx_search(
    request: Request,
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    is_pinned: Optional[bool] = Query(None),
    sort: str = Query("newest"),
    service: NoteService = Depends(get_note_service),
):
    """Return notes list partial filtered by search query."""
    params = NoteQueryParams(
        q=q or None,
        category=category,
        tag=tag,
        is_pinned=is_pinned,
        sort=sort,
        page=1,
        page_size=20,
    )
    notes_page = await service.list_notes(params)
    stats = await service.get_sidebar_stats()

    return templates.TemplateResponse(
        "partials/notes_list.html",
        {
            "request": request,
            "notes_page": notes_page,
            "stats": stats,
            "categories": CATEGORIES,
            "current_q": q or "",
            "current_category": category or "",
            "current_tag": tag or "",
            "current_sort": sort,
            "current_pinned": is_pinned,
        },
    )


# ── Note Detail Modal ─────────────────────────────────────────────────────────

@router.get("/notes/{note_id}/detail", response_class=HTMLResponse)
async def htmx_note_detail(
    note_id: str,
    request: Request,
    service: NoteService = Depends(get_note_service),
):
    """Return note detail modal partial."""
    try:
        note = await service.get_note(note_id)
    except (InvalidNoteIdError, NoteNotFoundError) as exc:
        msg = "Invalid note ID" if isinstance(exc, InvalidNoteIdError) else "Note not found"
        raise HTTPException(status_code=404, detail=msg)

    return templates.TemplateResponse(
        "partials/note_detail_modal.html",
        {"request": request, "note": note},
    )


# ── Confirm Delete Modal ─────────────────────────────────────────────────────

@router.get("/notes/{note_id}/confirm-delete", response_class=HTMLResponse)
async def htmx_confirm_delete(
    note_id: str,
    request: Request,
    service: NoteService = Depends(get_note_service),
):
    """Return confirm-delete modal partial."""
    try:
        note = await service.get_note(note_id)
    except (InvalidNoteIdError, NoteNotFoundError):
        raise HTTPException(status_code=404, detail="Note not found")

    return templates.TemplateResponse(
        "partials/confirm_delete.html",
        {"request": request, "note_id": note_id, "note_title": note.title},
    )


# ── Sidebar Stats ─────────────────────────────────────────────────────────────

@router.get("/sidebar-stats", response_class=HTMLResponse)
async def htmx_sidebar_stats(
    request: Request,
    service: NoteService = Depends(get_note_service),
):
    """Return updated sidebar stats partial."""
    stats = await service.get_sidebar_stats()
    return templates.TemplateResponse(
        "partials/sidebar_stats.html",
        {"request": request, "stats": stats, "categories": CATEGORIES},
    )
