"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ── Starlette >= 0.36 Jinja2Templates Compatibility Patch ────────────────────
_orig_template_response = Jinja2Templates.TemplateResponse


def _compatible_template_response(self, *args, **kwargs):
    if len(args) >= 2 and isinstance(args[0], str) and isinstance(args[1], dict) and "request" in args[1]:
        name = args[0]
        context = args[1]
        req = context.get("request")
        return _orig_template_response(self, request=req, name=name, context=context, **kwargs)
    return _orig_template_response(self, *args, **kwargs)


Jinja2Templates.TemplateResponse = _compatible_template_response

from app.config import get_settings
from app.database import close_mongo_connection, connect_to_mongo
from app.routers import pages
from app.routers.api import notes as notes_api
from app.routers import htmx

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()
templates = Jinja2Templates(directory="app/templates")


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""
    logger.info(f"Starting {settings.app_name} ({settings.app_env})")
    await connect_to_mongo()
    yield
    await close_mongo_connection()
    logger.info(f"{settings.app_name} shut down.")


# ── App Factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    description=f"{settings.app_tagline} — A modern notes management API.",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static Files ──────────────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(notes_api.router)
app.include_router(htmx.router)
app.include_router(pages.router)

# ── Exception Handlers ────────────────────────────────────────────────────────

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 page."""
    if request.headers.get("HX-Request"):
        return HTMLResponse(
            content="<p class='text-red-500'>Not found.</p>",
            status_code=404,
        )
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": 404, "message": "Page not found."},
        status_code=404,
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """Custom 500 page."""
    logger.error(f"Internal server error: {exc}")
    if request.headers.get("HX-Request"):
        return HTMLResponse(
            content="<p class='text-red-500'>Server error. Please try again.</p>",
            status_code=500,
        )
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": 500, "message": "Something went wrong on our end."},
        status_code=500,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Return structured validation errors."""
    errors = [
        {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": "Validation failed", "errors": errors},
    )
