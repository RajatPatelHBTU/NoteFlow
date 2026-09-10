"""Vercel Serverless Function entry point for NoteFlow FastAPI app.

Vercel's @vercel/python runtime detects the ASGI `app` variable
exported from this module and wraps it automatically — no Mangum needed.
"""

import sys
from pathlib import Path

# Add project root directory to sys.path so 'app' package is discoverable.
# Vercel extracts the function into /var/task, so the project root is one
# level up from this file (api/index.py → project root).
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app  # noqa: F401

# Vercel expects an ASGI-compatible `app` (or `handler`) at module level.
# Re-exporting `app` from app.main satisfies this requirement.
