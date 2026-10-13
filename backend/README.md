# OneSpace Backend

FastAPI backend for the OneSpace application.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Configuration using pydantic-settings
│   └── db/
│       ├── __init__.py
│       └── session.py       # SQLAlchemy async engine and session
├── tests/
│   ├── __init__.py
│   └── test_health.py       # Health endpoint tests
├── alembic/
│   ├── versions/            # Migration scripts (empty initially)
│   ├── env.py               # Alembic environment configuration
│   └── script.py.mako       # Migration template
├── alembic.ini              # Alembic configuration
├── pyproject.toml           # Project configuration and dependencies
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## Features

- **FastAPI** application with clean architecture
- **Configuration** via environment variables using pydantic-settings
- **Database** configured for PostgreSQL with asyncpg and SQLAlchemy 2.x async
- **Alembic** migration setup (configured but not executed)
- **Health endpoint** at `GET /health`
- **Tests** with pytest and httpx
- **Linting** with Ruff

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL (for production, not required for Phase 0 tests)

### Installation

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Environment Configuration

Copy `.env.example` to `.env` and adjust values:

```bash
cp .env.example .env
```

### Running the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Health Check

```bash
curl http://localhost:8000/health
# Response: {"status": "ok", "service": "onespace-api"}
```

## Testing

```bash
pytest -v
```

Tests use an in-memory test client and do not require a running PostgreSQL instance.

## Linting & Formatting

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .
```

## Database & Migrations

**Phase 0 Note:** Database connectivity and migrations are intentionally deferred.

- SQLAlchemy async engine and session are configured in `app/db/session.py`
- Alembic is configured in `alembic/` and `alembic.ini`
- No migration files have been generated yet
- No database connection is made during application startup in Phase 0
- Tests run without a database connection

When ready to enable database operations:
1. Ensure PostgreSQL is running
2. Create the database: `createdb onespace`
3. Generate initial migration: `alembic revision --autogenerate -m "initial"`
4. Run migrations: `alembic upgrade head`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Phase 0 Scope

This phase establishes the clean foundation only. The following are **not** implemented:
- Authentication / JWT
- User management
- Workspaces, tasks, notes, resources, files
- Search functionality
- Dashboard / activity
- Rate limiting
- Any business logic

These will be added in subsequent phases.