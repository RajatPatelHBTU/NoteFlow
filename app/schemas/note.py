"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ─── Constants ──────────────────────────────────────────────────────────────

CATEGORIES = ["Personal", "Work", "Study", "Programming", "Ideas", "Other"]

MAX_TITLE_LENGTH = 200
MAX_CONTENT_LENGTH = 50_000
MAX_TAG_LENGTH = 50
MAX_TAGS_COUNT = 20


# ─── Request Schemas ─────────────────────────────────────────────────────────

class NoteCreate(BaseModel):
    """Schema for creating a new note."""

    title: str = Field(..., min_length=1, max_length=MAX_TITLE_LENGTH, description="Note title")
    content: str = Field(..., min_length=1, max_length=MAX_CONTENT_LENGTH, description="Note content")
    category: str = Field(default="Other", description="Note category")
    tags: list[str] = Field(default_factory=list, description="List of tags")
    is_pinned: bool = Field(default=False, description="Whether the note is pinned")

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be blank")
        return v.strip()

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Content cannot be blank")
        return v.strip()

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in CATEGORIES:
            return "Other"
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def clean_tags(cls, v) -> list[str]:
        if isinstance(v, str):
            # Handle comma-separated string from form inputs
            v = [t.strip() for t in v.split(",") if t.strip()]
        if isinstance(v, list):
            cleaned = []
            for tag in v:
                tag = str(tag).strip()[:MAX_TAG_LENGTH]
                if tag and tag not in cleaned:
                    cleaned.append(tag)
            return cleaned[:MAX_TAGS_COUNT]
        return []


class NoteUpdate(BaseModel):
    """Schema for updating an existing note (all fields optional)."""

    title: Optional[str] = Field(None, min_length=1, max_length=MAX_TITLE_LENGTH)
    content: Optional[str] = Field(None, min_length=1, max_length=MAX_CONTENT_LENGTH)
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    is_pinned: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Title cannot be blank")
        return v.strip() if v else v

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Content cannot be blank")
        return v.strip() if v else v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in CATEGORIES:
            return "Other"
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def clean_tags(cls, v) -> Optional[list[str]]:
        if v is None:
            return v
        if isinstance(v, str):
            v = [t.strip() for t in v.split(",") if t.strip()]
        if isinstance(v, list):
            cleaned = []
            for tag in v:
                tag = str(tag).strip()[:MAX_TAG_LENGTH]
                if tag and tag not in cleaned:
                    cleaned.append(tag)
            return cleaned[:MAX_TAGS_COUNT]
        return []


# ─── Response Schemas ─────────────────────────────────────────────────────────

class NoteResponse(BaseModel):
    """Schema for a single note API response."""

    id: str = Field(..., description="Note ID")
    title: str
    content: str
    category: str
    tags: list[str]
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    """Schema for paginated list of notes."""

    notes: list[NoteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


# ─── Query Parameter Schemas ──────────────────────────────────────────────────

class NoteQueryParams(BaseModel):
    """Query parameters for listing/searching notes."""

    q: Optional[str] = Field(None, description="Full-text search query")
    category: Optional[str] = Field(None, description="Filter by category")
    tag: Optional[str] = Field(None, description="Filter by tag")
    is_pinned: Optional[bool] = Field(None, description="Filter by pinned status")
    sort: str = Field("newest", description="Sort order: newest, oldest, updated, alpha_asc, alpha_desc")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
