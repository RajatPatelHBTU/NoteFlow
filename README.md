# 📝 NoteFlow

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python_3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)
![HTMX](https://img.shields.io/badge/HTMX-336699?style=for-the-badge&logo=htmx&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-44%20Passing-brightgreen?style=for-the-badge&logo=pytest)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

**Capture ideas. Organize thoughts. Get things done.**

*A modern, production-grade Notes Management Web Application and REST API built with FastAPI, Motor (Async MongoDB), HTMX, and Tailwind CSS.*

[Live Demo](#-quick-start) • [Features](#-features) • [Tech Stack](#%EF%B8%8F-tech-stack) • [Architecture](#%EF%B8%8F-architecture) • [API Docs](#-api-documentation) • [Testing](#-running-tests)

</div>

---

## ✨ Features

- 📋 **Responsive Dashboard**: Dynamic note cards grid with pinned and unpinned sections.
- 📌 **Pin Notes**: Keep your most important notes pinned to the top of your board.
- 🔍 **Instant Full-Text Search**: HTMX-powered debounced search across title, content, tags, and categories using MongoDB text indexes.
- 🗂️ **Categorization & Filtering**: Filter notes by categories (*Personal, Work, Study, Programming, Ideas, Other*) and tags.
- 🏷️ **Multi-Tag System**: Add comma-separated tags with smart sanitization and automatic badges.
- 🔽 **Multi-field Sorting**: Sort notes by Newest, Oldest, Recently Updated, Alphabetical (A-Z and Z-A).
- 🌙 **Theme Switcher**: Smooth Light/Dark mode toggle persisted in `localStorage` without unstyled flash.
- 🔔 **Real-Time Toast Notifications**: Dynamic server-driven notifications powered by `HX-Trigger`.
- ❌ **Safe Modal Deletion**: Confirmation modals before permanent deletion.
- 📖 **Self-Documenting API**: Interactive OpenAPI Swagger documentation at `/docs` and ReDoc at `/redoc`.
- 🐳 **Container Ready**: Complete Docker & Docker Compose setup with health checks.
- 🧪 **Comprehensive Test Suite**: 44 async tests covering unit, repository, service, and full HTTP endpoints with 100% pass rate.

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) | Modern, high-performance async Python web framework |
| **ASGI Server** | [Uvicorn](https://www.uvicorn.org/) | Lightning-fast ASGI web server implementation |
| **Database** | [MongoDB](https://www.mongodb.com/) / Atlas | Scalable document-oriented NoSQL database |
| **Async DB Driver** | [Motor](https://motor.readthedocs.io/) | Official non-blocking async Python driver for MongoDB |
| **Data Validation** | [Pydantic v2](https://docs.pydantic.dev/) | Strict data schemas, typing, and environment management |
| **Templating** | [Jinja2](https://palletsprojects.com/p/jinja/) | Expressive server-side HTML templating |
| **Frontend Interactivity** | [HTMX](https://htmx.org/) | High-power AJAX, CSS transitions, and WebSockets directly in HTML |
| **Styling** | [Tailwind CSS](https://tailwindcss.com/) | Modern utility-first responsive styling with dark mode |
| **Testing** | [pytest](https://pytest.org/) + [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) | Full asynchronous test harness and fixtures |

---

## 🏗️ Architecture

NoteFlow follows the **Repository & Service Layer Pattern** for clean separation of concerns:

```
noteflow/
├── app/
│   ├── config.py              # Pydantic Settings & environment variables
│   ├── database.py            # Motor async client, indexing, and connection lifecycle
│   ├── main.py                # FastAPI app factory, lifespan, error handlers
│   ├── models/
│   │   └── note.py            # MongoDB ODM Document models with PyObjectId
│   ├── schemas/
│   │   └── note.py            # Pydantic v2 request & response schemas
│   ├── repositories/
│   │   └── note_repository.py # Async MongoDB CRUD, search filters, aggregations
│   ├── services/
│   │   └── note_service.py    # Business logic layer (validation, stats calculation)
│   ├── routers/
│   │   ├── api/
│   │   │   └── notes.py       # REST API endpoints (JSON responses)
│   │   ├── htmx.py            # HTMX partial routes (HTML fragments)
│   │   └── pages.py           # Full-page Jinja2 routes
│   ├── templates/             # Jinja2 HTML templates & HTMX partials
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── note_form.html
│   │   └── partials/
│   └── static/                # CSS styles and JavaScript helpers
├── tests/
│   ├── conftest.py            # Pytest fixtures & isolated test DB setup
│   ├── test_notes.py          # CRUD, search, filter, and validation tests
│   └── test_pages.py          # Page and HTMX route integration tests
├── Dockerfile                 # Container image specification
├── docker-compose.yml         # Multi-container orchestration (App + Mongo)
├── requirements.txt           # Production dependencies
├── pytest.ini                 # Pytest configuration
├── run.ps1                    # One-click Windows PowerShell launcher
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/RajatPatelHBTU/NoteFlow.git
cd NoteFlow
```

### 2. Create and Activate a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your MongoDB connection details:

```bash
cp .env.example .env
```

Example configuration (`.env`):
```env
MONGODB_URL=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?appName=Cluster0
DATABASE_NAME=Notes
APP_ENV=development
SECRET_KEY=your-secret-key-here
```

### 5. Run the Application

**Using the Windows Launcher Script:**
```powershell
.\run.ps1
```

**Or directly with Uvicorn:**
```bash
uvicorn app.main:app --reload --port 8000
```

Open your browser and visit:
- **Web App**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Swagger UI Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🐳 Docker Deployment

Run the complete application stack including MongoDB with a single command:

```bash
# Build and run containers
docker compose up --build

# Run in detached background mode
docker compose up -d --build

# Stop the application
docker compose down
```

---

## 🧪 Running Tests

The test suite runs against an isolated test database with automatic cleanup:

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test modules
pytest tests/test_notes.py -v
pytest tests/test_pages.py -v
```

**Test Coverage Summary:**
- ✅ Note Creation, Validation, and Character Limits
- ✅ Note Updating, Deletion, and Pinning
- ✅ Full-Text Search and Category/Tag Filtering
- ✅ Error Handling (404 Not Found, 422 Unprocessable Content)
- ✅ HTMX and Full Page Template Rendering
- **44 Passed out of 44 tests**

---

## 🌐 API Documentation

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/notes` | List notes (supports `q`, `category`, `tag`, `sort`, `page`, `page_size`) |
| `POST` | `/api/notes` | Create a new note |
| `GET` | `/api/notes/{id}` | Get note details by ID |
| `PUT` | `/api/notes/{id}` | Update existing note |
| `DELETE` | `/api/notes/{id}` | Delete a note |
| `PATCH` | `/api/notes/{id}/pin` | Toggle pin status of a note |
| `GET` | `/api/notes/categories` | Retrieve all active categories |
| `GET` | `/api/notes/category/{category}` | Filter notes by category |
| `GET` | `/api/notes/search?q={query}` | Execute full-text search |

---

## 📄 License

This project is licensed under the **MIT License** — feel free to use it for personal projects, portfolios, or commercial applications.

---

<div align="center">
  Developed by <a href="https://github.com/RajatPatelHBTU">Rajat Patel</a>
</div>
