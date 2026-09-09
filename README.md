# 📝 NoteFlow

> **Capture ideas. Organize thoughts. Get things done.**

NoteFlow is a modern, production-quality **Notes Management Web Application** built with **FastAPI**, **MongoDB**, **HTMX**, and **Tailwind CSS**. It demonstrates a clean, full-stack Python architecture suitable for real-world portfolios and software engineering interviews.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📋 Dashboard | Responsive card grid with pinned + all notes |
| ✏️ Create/Edit | Full form with tag preview & character count |
| 🔍 Real-time Search | HTMX-powered search across title, content, tags |
| 🗂️ Categories | Personal, Work, Study, Programming, Ideas, Other |
| 🏷️ Tags | Multi-tag support with badge display |
| 📌 Pin Notes | Pinned notes float to the top |
| 🔽 Sort & Filter | Newest, Oldest, Updated, A-Z, Z-A |
| 🌙 Dark Mode | Persisted in localStorage, smooth transitions |
| 🔔 Toast Notifications | Success/Error/Info toasts via HTMX triggers |
| ❌ Confirm Delete | Modal confirmation before deletion |
| 📱 Responsive | Mobile-first with collapsible sidebar |
| 📖 API Docs | Auto-generated Swagger at `/docs` and ReDoc at `/redoc` |
| 🐳 Docker | One-command `docker compose up --build` |
| 🧪 Tests | pytest async test suite (35+ tests) |

---

## 🛠️ Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** — async web framework
- **Uvicorn** — ASGI server
- **Motor** — async MongoDB driver
- **PyMongo** — MongoDB index creation
- **Pydantic v2 + pydantic-settings** — data validation & env config
- **Jinja2** — server-side HTML templating

### Frontend
- **HTMX** — dynamic interactions without React/Vue
- **Tailwind CSS** (Play CDN) — utility-first styling
- **Vanilla JS** (< 150 lines) — dark mode, toasts, sidebar

### Infrastructure
- **MongoDB 7** — document database
- **Docker + Docker Compose** — containerization
- **pytest + pytest-asyncio** — async testing

---

## 🏗️ Architecture

```
noteflow/
│
├── app/
│   ├── main.py              # FastAPI app factory, lifespan, middleware, routers
│   ├── config.py            # Pydantic Settings (loads .env)
│   ├── database.py          # Motor async client, indexes, connection management
│   │
│   ├── models/
│   │   └── note.py          # MongoDB document model with PyObjectId
│   │
│   ├── schemas/
│   │   └── note.py          # Pydantic v2 request/response schemas
│   │
│   ├── repositories/
│   │   └── note_repository.py   # Raw async MongoDB operations (CRUD, search, aggregation)
│   │
│   ├── services/
│   │   └── note_service.py      # Business logic layer (orchestrates repository)
│   │
│   ├── routers/
│   │   ├── api/
│   │   │   └── notes.py     # REST API endpoints (JSON)
│   │   ├── pages.py         # Full-page Jinja2 routes
│   │   └── htmx.py          # HTMX partial routes (HTML fragments)
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── note_detail.html
│   │   ├── note_form.html
│   │   ├── error.html
│   │   └── partials/
│   │       ├── note_card.html
│   │       ├── notes_list.html
│   │       ├── confirm_delete.html
│   │       ├── note_detail_modal.html
│   │       ├── sidebar_stats.html
│   │       └── toast.html
│   │
│   └── static/
│       ├── css/custom.css
│       └── js/app.js
│
├── tests/
│   ├── conftest.py
│   ├── test_notes.py
│   └── test_pages.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
└── README.md
```

---

## 🍃 MongoDB Schema

**Database:** `notes_db`  
**Collection:** `notes`

```json
{
  "_id":        "ObjectId",
  "title":      "String (required, max 200)",
  "content":    "String (required, max 50000)",
  "category":   "String (enum: Personal|Work|Study|Programming|Ideas|Other)",
  "tags":       "[String] (max 20 tags, each max 50 chars)",
  "is_pinned":  "Boolean (default: false)",
  "created_at": "DateTime (UTC)",
  "updated_at": "DateTime (UTC)"
}
```

### Indexes

| Index | Type | Purpose |
|---|---|---|
| `created_at` | Descending | Newest-first sorting |
| `updated_at` | Descending | Recently updated sorting |
| `category` | Ascending | Category filtering |
| `tags` | Ascending | Tag filtering |
| `is_pinned` | Descending | Pinned filter |
| `title + content + tags + category` | **Text** | Full-text search |

---

## 🌐 API Endpoints

### Notes API (`/api/notes`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/notes` | List notes (search, filter, sort, paginate) |
| `GET` | `/api/notes/{id}` | Get single note |
| `POST` | `/api/notes` | Create note |
| `PUT` | `/api/notes/{id}` | Update note |
| `DELETE` | `/api/notes/{id}` | Delete note |
| `PATCH` | `/api/notes/{id}/pin` | Toggle pin |
| `GET` | `/api/notes/search?q=` | Full-text search |
| `GET` | `/api/notes/category/{cat}` | Filter by category |
| `GET` | `/api/notes/categories` | List categories |

### Query Parameters for `GET /api/notes`

| Param | Type | Description |
|---|---|---|
| `q` | string | Full-text search query |
| `category` | string | Filter by category |
| `tag` | string | Filter by tag |
| `is_pinned` | bool | Filter pinned notes |
| `sort` | string | `newest\|oldest\|updated\|alpha_asc\|alpha_desc` |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page (default: 20, max: 100) |

### Page Routes

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Dashboard |
| `GET` | `/notes/create` | Create note form |
| `GET` | `/notes/{id}` | Note detail page |
| `GET` | `/notes/{id}/edit` | Edit note form |

### HTMX Partial Routes (`/htmx`)

| Method | Path | Returns |
|---|---|---|
| `GET` | `/htmx/notes` | Notes grid partial |
| `POST` | `/htmx/notes` | Create + return updated grid |
| `PUT` | `/htmx/notes/{id}` | Update + return note card |
| `DELETE` | `/htmx/notes/{id}` | Delete + empty response |
| `PATCH` | `/htmx/notes/{id}/pin` | Pin toggle + return card |
| `GET` | `/htmx/search` | Search results partial |
| `GET` | `/htmx/notes/{id}/detail` | Note detail modal |
| `GET` | `/htmx/notes/{id}/confirm-delete` | Delete confirmation modal |

---

## ⚙️ Environment Variables

```bash
# .env
MONGODB_URL=mongodb://localhost:27017    # MongoDB connection string
DATABASE_NAME=notes_db                  # Database name
APP_ENV=development                     # development | production
SECRET_KEY=change-this-in-production    # App secret key
```

---

## 🚀 Local Setup

### Prerequisites
- Python 3.11+
- MongoDB running locally (or use Docker)

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/noteflow.git
cd noteflow
```

### 2. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Start MongoDB (if not already running)

```bash
# Using Docker (simplest):
docker run -d -p 27017:27017 --name mongo mongo:7.0

# Or install MongoDB locally: https://www.mongodb.com/docs/manual/installation/
```

### 6. Run the application

```bash
uvicorn app.main:app --reload
```

Visit: **http://localhost:8000**

API docs: **http://localhost:8000/docs**

---

## 🐳 Docker Setup

> Runs the full stack (FastAPI + MongoDB) with a single command.

```bash
# Build and start
docker compose up --build

# Run in background
docker compose up -d --build

# Stop
docker compose down

# Stop and remove volumes (clears all data)
docker compose down -v
```

Visit: **http://localhost:8000**

---

## 🧪 Running Tests

```bash
# Ensure MongoDB is running (tests use a separate 'noteflow_test_db')
# then:

pytest tests/ -v

# Run specific file
pytest tests/test_notes.py -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=app --cov-report=term-missing
```

> **Note:** Tests require a live MongoDB instance. The test suite uses `noteflow_test_db` and cleans up after each test.

---

## 📸 Screenshots

*Add screenshots of your running application here.*

| Dashboard | Create Note | Dark Mode |
|---|---|---|
| `screenshot-dashboard.png` | `screenshot-create.png` | `screenshot-dark.png` |

---

## 🔮 Future Improvements

- [ ] User authentication (JWT / OAuth2)
- [ ] Note sharing with public links
- [ ] Markdown rendering in note content
- [ ] Rich text editor (Quill / TipTap)
- [ ] File/image attachments
- [ ] Export notes as PDF / Markdown
- [ ] Note templates
- [ ] Collaborative notes (WebSocket)
- [ ] Mobile PWA support
- [ ] Full Tailwind CLI build (remove Play CDN for production)
- [ ] Redis caching for search results
- [ ] CI/CD with GitHub Actions

---

## 🎤 Interview Questions

**Q: Why FastAPI over Flask/Django?**
> FastAPI is async-native, has automatic OpenAPI docs generation, uses Pydantic for validation, and is significantly faster due to Starlette/ASGI. For a notes app with async MongoDB operations, it's the natural choice.

**Q: Why Motor instead of PyMongo?**
> Motor is the async version of PyMongo built for asyncio. Since FastAPI uses async/await, using Motor allows non-blocking database calls, enabling FastAPI to handle many concurrent requests efficiently.

**Q: How does HTMX work here?**
> Instead of a separate React SPA, HTMX intercepts user actions (clicks, form submits, input events) and makes fetch requests to the server. The server returns HTML fragments (partials) rather than JSON. HTMX then swaps these fragments into the DOM — giving SPA-like interactivity with server-side simplicity.

**Q: How does search work?**
> MongoDB text indexes are created on `title`, `content`, `tags`, and `category` with different weights (title=10, tags=5, category=3, content=1). When the user types in the search box, HTMX fires a debounced GET request to `/htmx/search?q=...`. The server runs a `$text` search query and returns an updated notes grid HTML partial.

**Q: How is dark mode implemented?**
> Dark mode uses Tailwind's `class` strategy. On page load, a blocking script checks `localStorage.getItem('theme')` and adds `class="dark"` to `<html>` if needed — preventing any flash of unstyled content. Toggling calls `toggleDarkMode()` which adds/removes the class and saves to localStorage.

**Q: What is the repository pattern and why use it?**
> The repository pattern abstracts all database operations into a single class (`NoteRepository`). The service layer (`NoteService`) contains business logic and calls the repository. This separation makes testing easier (mock the repository), enables database swapping, and keeps route handlers thin.

**Q: How does pagination work?**
> Pagination uses `skip()` and `limit()` in MongoDB queries. The API accepts `page` and `page_size` parameters. The service calculates `total_pages`, `has_next`, and `has_prev` for the response. The frontend renders pagination buttons that use HTMX to load the next page without full reload.

**Q: How are toast notifications triggered?**
> The HTMX router sets a custom `HX-Trigger` response header with JSON: `{"showToast": {"message": "...", "type": "success"}}`. HTMX fires this as a DOM event, which `app.js` listens for via `document.addEventListener('showToast', ...)` and creates a styled toast element.

---

## 📄 License

MIT License — free to use for learning, portfolio, and commercial projects.

---

*Built with ❤️ using FastAPI, MongoDB, HTMX, and Tailwind CSS.*
