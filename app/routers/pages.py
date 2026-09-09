import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database import get_notes_collection
from app.schemas.note import CATEGORIES, NoteCreate, NoteQueryParams, NoteUpdate
from app.services.note_service import InvalidNoteIdError, NoteNotFoundError, NoteService

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _toast_headers(message: str, toast_type: str = "success") -> dict:
    return {
        "HX-Trigger": json.dumps({"showToast": {"message": message, "type": toast_type}})
    }


def get_note_service(collection=Depends(get_notes_collection)) -> NoteService:
    return NoteService(collection)


@router.get("/", response_class=HTMLResponse, summary="Dashboard")
async def dashboard(
    request: Request,
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    is_pinned: Optional[bool] = Query(None),
    sort: str = Query("newest"),
    page: int = Query(1, ge=1),
    service: NoteService = Depends(get_note_service),
):
    """Main dashboard page with notes grid."""
    params = NoteQueryParams(
        q=q, category=category, tag=tag, is_pinned=is_pinned,
        sort=sort, page=page, page_size=20,
    )
    notes_page = await service.list_notes(params)
    stats = await service.get_sidebar_stats()

    return templates.TemplateResponse(
        "dashboard.html",
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


@router.get("/notes/create", response_class=HTMLResponse, summary="Create Note page")
async def create_note_page(request: Request):
    """Render the create note form page."""
    return templates.TemplateResponse(
        "note_form.html",
        {
            "request": request,
            "note": None,
            "categories": CATEGORIES,
            "form_action": "/notes/create",
            "form_method": "post",
            "page_title": "Create Note",
        },
    )


@router.post("/notes/create", response_class=HTMLResponse, summary="Create Note submit")
async def create_note_submit(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form("Other"),
    tags: str = Form(""),
    is_pinned: bool = Form(False),
    service: NoteService = Depends(get_note_service),
):
    """Handle create note form submission via POST."""
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
        logger.error(f"Create note form error: {e}")
        return templates.TemplateResponse(
            "note_form.html",
            {
                "request": request,
                "note": {
                    "title": title,
                    "content": content,
                    "category": category,
                    "tags": [t.strip() for t in tags.split(",") if t.strip()],
                    "is_pinned": is_pinned,
                },
                "categories": CATEGORIES,
                "form_action": "/notes/create",
                "form_method": "post",
                "page_title": "Create Note",
                "error_message": str(e),
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if request.headers.get("HX-Request"):
        return HTMLResponse(
            content="",
            headers={
                **_toast_headers("Note created successfully!", "success"),
                "HX-Redirect": "/",
            },
        )
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/notes/{note_id}", response_class=HTMLResponse, summary="Note detail page")
async def note_detail_page(
    note_id: str,
    request: Request,
    service: NoteService = Depends(get_note_service),
):
    """Render the full note detail page."""
    try:
        note = await service.get_note(note_id)
    except InvalidNoteIdError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid note ID")
    except NoteNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    return templates.TemplateResponse(
        "note_detail.html",
        {"request": request, "note": note, "categories": CATEGORIES},
    )


@router.get("/notes/{note_id}/edit", response_class=HTMLResponse, summary="Edit Note page")
async def edit_note_page(
    note_id: str,
    request: Request,
    service: NoteService = Depends(get_note_service),
):
    """Render the edit note form page."""
    try:
        note = await service.get_note(note_id)
    except InvalidNoteIdError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid note ID")
    except NoteNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")

    return templates.TemplateResponse(
        "note_form.html",
        {
            "request": request,
            "note": note,
            "categories": CATEGORIES,
            "form_action": f"/notes/{note_id}/edit",
            "form_method": "post",
            "page_title": "Edit Note",
        },
    )


@router.post("/notes/{note_id}/edit", response_class=HTMLResponse, summary="Edit Note submit")
async def edit_note_submit(
    note_id: str,
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form("Other"),
    tags: str = Form(""),
    is_pinned: bool = Form(False),
    service: NoteService = Depends(get_note_service),
):
    """Handle edit note form submission via POST."""
    try:
        note_data = NoteUpdate(
            title=title,
            content=content,
            category=category,
            tags=tags,
            is_pinned=is_pinned,
        )
        await service.update_note(note_id, note_data)
    except Exception as e:
        logger.error(f"Edit note form error: {e}")
        return templates.TemplateResponse(
            "note_form.html",
            {
                "request": request,
                "note": {
                    "id": note_id,
                    "title": title,
                    "content": content,
                    "category": category,
                    "tags": [t.strip() for t in tags.split(",") if t.strip()],
                    "is_pinned": is_pinned,
                },
                "categories": CATEGORIES,
                "form_action": f"/notes/{note_id}/edit",
                "form_method": "post",
                "page_title": "Edit Note",
                "error_message": str(e),
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if request.headers.get("HX-Request"):
        return HTMLResponse(
            content="",
            headers={
                **_toast_headers("Note updated successfully!", "success"),
                "HX-Redirect": f"/notes/{note_id}",
            },
        )
    return RedirectResponse(url=f"/notes/{note_id}", status_code=status.HTTP_303_SEE_OTHER)

