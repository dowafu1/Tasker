"""Test configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.core.database import Base, get_db
from src.models.user import User
from src.models.task import Task, Category, TaskStatus, ImportanceLevel
from src.models.project import Project
from src.core.security import get_password_hash
from src.repositories import UserRepository


# Test database URL - using SQLite for simplicity in tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    
    async def override_get_db():
        yield test_session
    
    async def override_get_db_dependency():
        yield test_session
    
    from src.core.database import get_db
    from src.core.security import get_db_dependency
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_db_dependency] = override_get_db_dependency
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(test_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("password123"),
        name="Test User",
        is_active=True,
        is_verified=False,
    )
    test_session.add(user)
    await test_session.flush()
    return user


@pytest.fixture
async def test_user_token(test_user: User) -> str:
    """Create a test JWT token for the test user."""
    from src.core.security import create_access_token
    
    token_data = {"sub": str(test_user.id)}
    return create_access_token(token_data)


@pytest.fixture
async def authenticated_client(
    client: AsyncClient,
    test_user_token: str,
) -> AsyncClient:
    """Create an authenticated test client."""
    client.headers["Authorization"] = f"Bearer {test_user_token}"
    return client


@pytest.fixture
async def test_project(test_session: AsyncSession, test_user: User) -> Project:
    """Create a test project."""
    project = Project(
        name="Test Project",
        icon="📁",
        description="Test project description",
        owner_id=test_user.id,
    )
    test_session.add(project)
    await test_session.flush()
    return project


@pytest.fixture
async def test_category(test_session: AsyncSession, test_user: User) -> Category:
    """Create a test category."""
    category = Category(
        name="Work",
        color="#FF5733",
        user_id=test_user.id,
    )
    test_session.add(category)
    await test_session.flush()
    return category


@pytest.fixture
async def test_task(
    test_session: AsyncSession,
    test_user: User,
    test_project: Project,
    test_category: Category,
) -> Task:
    """Create a test task."""
    task = Task(
        name="Test Task",
        description="Test task description",
        status=TaskStatus.PENDING,
        importance=ImportanceLevel.MEDIUM,
        category_id=test_category.id,
        project_id=test_project.id,
        created_by_id=test_user.id,
        assignee_id=test_user.id,
    )
    test_session.add(task)
    await test_session.flush()
    return task


@pytest.fixture
async def assigned_task(
    test_session: AsyncSession,
    test_user: User,
    other_user: User,
) -> Task:
    """Create a task assigned to test_user but created by other_user."""
    task = Task(
        name="Assigned Task",
        description="Task assigned to me",
        status=TaskStatus.PENDING,
        importance=ImportanceLevel.HIGH,
        created_by_id=other_user.id,
        assignee_id=test_user.id,
    )
    test_session.add(task)
    await test_session.flush()
    return task


@pytest.fixture
async def other_user(test_session: AsyncSession) -> User:
    """Create another test user."""
    user = User(
        email="other@example.com",
        password_hash=get_password_hash("password456"),
        name="Other User",
        is_active=True,
        is_verified=False,
    )
    test_session.add(user)
    await test_session.flush()
    return user
