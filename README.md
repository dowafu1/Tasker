# Task Manager API

FastAPI-based task management system with authentication, projects, tasks, and calendar features.

## Project Structure

```
src/
├── main.py                 # Application entry point
├── config.py              # Configuration settings
├── core/                  # Core functionality
│   ├── database.py        # Database connection
│   └── security.py        # JWT & password hashing
├── models/                # SQLAlchemy models
│   ├── user.py
│   ├── project.py
│   └── task.py
├── repositories/          # Data access layer
│   └── __init__.py
├── routers/               # API endpoints
│   ├── auth_router.py
│   ├── profile_router.py
│   ├── project_router.py
│   └── task_router.py
├── schemas/               # Pydantic schemas
│   ├── __init__.py
│   └── token.py
└── services/              # Business logic
    ├── __init__.py
    ├── auth_service.py
    ├── profile_service.py
    ├── project_service.py
    └── task_service.py

tests/
├── conftest.py           # Test configuration
├── test_api.py           # API integration tests
└── test_services.py      # Service unit tests
```

## Quick Start

### Using Docker Compose (Recommended)

1. **Create environment file** (optional):
```bash
cp .env.example .env
```

2. **Start all services**:
```bash
docker-compose up -d
```

3. **Access the API**:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

4. **View logs**:
```bash
docker-compose logs -f api
```

5. **Stop services**:
```bash
docker-compose down
```

### Manual Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set environment variables**:
```bash
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/taskmanager"
export SECRET_KEY="your-secret-key"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES=30
export REFRESH_TOKEN_EXPIRE_DAYS=7
```

3. **Run migrations** (if using Alembic):
```bash
alembic upgrade head
```

4. **Start the server**:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_api.py -v

# Run specific test
pytest tests/test_services.py::TestAuthService::test_register_success -v
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT secret key | Required |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry | 7 |

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/verify-code` - Verify reset code
- `POST /api/v1/auth/reset-password` - Reset password

### Profile
- `GET /api/v1/profile` - Get profile
- `PUT /api/v1/profile` - Update profile
- `POST /api/v1/profile/change-password` - Change password
- `POST /api/v1/profile/logout` - Logout

### Projects
- `GET /api/v1/projects` - List projects
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Tasks
- `GET /api/v1/tasks/assigned` - Get assigned tasks
- `GET /api/v1/tasks/{id}` - Get task details
- `PATCH /api/v1/tasks/{id}/complete` - Complete task
- `POST /api/v1/tasks/filters/reset` - Reset filters
- `POST /api/v1/calendar/tasks` - Create task

### Calendar
- `GET /api/v1/calendar/{year}/{month}` - Month view
- `GET /api/v1/calendar/{date}/tasks` - Day tasks

## Architecture

This project follows a layered architecture:

1. **Routers** (`src/routers/`) - HTTP endpoints and request validation
2. **Services** (`src/services/`) - Business logic
3. **Repositories** (`src/repositories/`) - Data access layer
4. **Models** (`src/models/`) - Database entities
5. **Schemas** (`src/schemas/`) - Pydantic models for validation

## Development

### Code Style
- Use type hints
- Follow PEP 8
- Write docstrings for public methods

### Adding New Features
1. Create/update model in `src/models/`
2. Add repository methods in `src/repositories/`
3. Implement business logic in `src/services/`
4. Create endpoint in `src/routers/`
5. Add tests in `tests/`
