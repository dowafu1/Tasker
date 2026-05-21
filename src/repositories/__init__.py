"""Repository layer for database operations."""

from typing import Optional, List, Generic, TypeVar, Type
from datetime import datetime, timezone

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.user import User, RefreshToken, PasswordResetCode
from src.models.task import Task, Category, TaskStatus, ImportanceLevel
from src.models.project import Project
from src.core.security import get_password_hash


ModelT = TypeVar("ModelT", bound=type)


class BaseRepository(Generic[ModelT]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, session: AsyncSession, model: Type[ModelT]):
        self.session = session
        self.model = model
    
    async def get_by_id(self, id: int) -> Optional[ModelT]:
        """Get entity by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[ModelT]:
        """Get all entities with pagination."""
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
    
    async def create(self, **kwargs) -> ModelT:
        """Create a new entity."""
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        return entity
    
    async def update(self, entity: ModelT, **kwargs) -> ModelT:
        """Update an entity."""
        for key, value in kwargs.items():
            setattr(entity, key, value)
        await self.session.flush()
        return entity
    
    async def delete(self, entity: ModelT) -> None:
        """Delete an entity."""
        await self.session.delete(entity)
        await self.session.flush()


class UserRepository(BaseRepository[User]):
    """Repository for User operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()
    
    async def create_user(
        self,
        email: str,
        password: str,
        name: Optional[str] = None,
    ) -> User:
        """Create a new user with hashed password."""
        password_hash = get_password_hash(password)
        user = User(
            email=email.lower(),
            password_hash=password_hash,
            name=name,
        )
        self.session.add(user)
        await self.session.flush()
        return user
    
    async def is_email_taken(self, email: str) -> bool:
        """Check if email is already registered."""
        existing = await self.get_by_email(email)
        return existing is not None


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository for refresh token operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, RefreshToken)
    
    async def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by hash."""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()
    
    async def revoke_token(self, token_hash: str) -> bool:
        """Revoke a refresh token."""
        token = await self.get_by_token_hash(token_hash)
        if token:
            token.is_revoked = True
            await self.session.flush()
            return True
        return False
    
    async def revoke_all_user_tokens(self, user_id: int) -> int:
        """Revoke all refresh tokens for a user."""
        result = await self.session.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_revoked == False,
                )
            )
        )
        tokens = list(result.scalars().all())
        for token in tokens:
            token.is_revoked = True
        await self.session.flush()
        return len(tokens)
    
    async def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens from database."""
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(RefreshToken).where(
                or_(
                    RefreshToken.expires_at < now,
                    RefreshToken.is_revoked == True,
                )
            )
        )
        tokens = list(result.scalars().all())
        for token in tokens:
            await self.session.delete(token)
        await self.session.flush()
        return len(tokens)


class PasswordResetCodeRepository(BaseRepository[PasswordResetCode]):
    """Repository for password reset code operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, PasswordResetCode)
    
    async def get_valid_code(self, email: str, code: str) -> Optional[PasswordResetCode]:
        """Get valid (non-expired, non-used) reset code."""
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(PasswordResetCode).where(
                and_(
                    PasswordResetCode.email == email.lower(),
                    PasswordResetCode.code == code,
                    PasswordResetCode.is_used == False,
                    PasswordResetCode.expires_at > now,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def create_code(
        self,
        email: str,
        code: str,
        expires_at: datetime,
    ) -> PasswordResetCode:
        """Create a new password reset code."""
        # Invalidate any existing codes for this email
        await self.session.execute(
            __import__('sqlalchemy').update(PasswordResetCode)
            .where(PasswordResetCode.email == email.lower())
            .values(is_used=True)
        )
        
        reset_code = PasswordResetCode(
            email=email.lower(),
            code=code,
            expires_at=expires_at,
        )
        self.session.add(reset_code)
        await self.session.flush()
        return reset_code
    
    async def mark_code_used(self, code_entity: PasswordResetCode) -> None:
        """Mark a reset code as used."""
        code_entity.is_used = True
        await self.session.flush()


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Project)
    
    async def get_user_projects(self, user_id: int) -> List[Project]:
        """Get all projects owned by a user."""
        result = await self.session.execute(
            select(Project)
            .where(Project.owner_id == user_id)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_project_with_tasks(self, project_id: int) -> Optional[Project]:
        """Get project with its tasks loaded."""
        result = await self.session.execute(
            select(Project)
            .options(selectinload(Project.tasks))
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()


class CategoryRepository(BaseRepository[Category]):
    """Repository for Category operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Category)
    
    async def get_user_categories(self, user_id: int) -> List[Category]:
        """Get all categories for a user."""
        result = await self.session.execute(
            select(Category)
            .where(Category.user_id == user_id)
            .order_by(Category.name)
        )
        return list(result.scalars().all())
    
    async def get_by_id_and_user(self, category_id: int, user_id: int) -> Optional[Category]:
        """Get category by ID ensuring it belongs to the user."""
        result = await self.session.execute(
            select(Category).where(
                and_(
                    Category.id == category_id,
                    Category.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()


class TaskRepository(BaseRepository[Task]):
    """Repository for Task operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Task)
    
    async def get_assigned_tasks(
        self,
        user_id: int,
        status_filter: Optional[TaskStatus] = None,
        importance_filter: Optional[ImportanceLevel] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List[Task], int]:
        """
        Get tasks assigned to a user with filters and pagination.
        
        Returns:
            Tuple of (tasks list, total count)
        """
        # Build base query
        conditions = [Task.assignee_id == user_id]
        
        if status_filter:
            conditions.append(Task.status == status_filter)
        if importance_filter:
            conditions.append(Task.importance == importance_filter)
        
        # Get total count
        count_query = select(func.count()).select_from(Task).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Get tasks with relationships
        query = (
            select(Task)
            .options(
                selectinload(Task.category),
                selectinload(Task.project),
                selectinload(Task.assignee),
                selectinload(Task.creator),
            )
            .where(and_(*conditions))
            .order_by(Task.deadline.asc().nullslast(), Task.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(query)
        tasks = list(result.scalars().all())
        
        return tasks, total
    
    async def get_task_with_relations(self, task_id: int) -> Optional[Task]:
        """Get task with all relationships loaded."""
        result = await self.session.execute(
            select(Task)
            .options(
                selectinload(Task.category),
                selectinload(Task.project),
                selectinload(Task.assignee),
                selectinload(Task.creator),
            )
            .where(Task.id == task_id)
        )
        return result.scalar_one_or_none()
    
    async def get_tasks_for_calendar_month(
        self,
        user_id: int,
        year: int,
        month: int,
    ) -> List[Task]:
        """Get tasks with deadlines in a specific month for calendar view."""
        from datetime import date
        import calendar
        
        # Get first and last day of month
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        result = await self.session.execute(
            select(Task)
            .where(
                and_(
                    Task.assignee_id == user_id,
                    Task.deadline >= first_day,
                    Task.deadline <= last_day,
                    Task.status != TaskStatus.CANCELLED,
                )
            )
        )
        return list(result.scalars().all())
    
    async def get_tasks_for_calendar_day(
        self,
        user_id: int,
        target_date: datetime,
        importance_filter: Optional[ImportanceLevel] = None,
        status_filter: Optional[TaskStatus] = None,
    ) -> List[Task]:
        """Get tasks for a specific day."""
        from datetime import date
        
        conditions = [
            Task.assignee_id == user_id,
            func.date(Task.deadline) == target_date.date() if hasattr(target_date, 'date') else func.date(Task.deadline) == target_date,
        ]
        
        if importance_filter:
            conditions.append(Task.importance == importance_filter)
        if status_filter:
            conditions.append(Task.status == status_filter)
        
        result = await self.session.execute(
            select(Task)
            .where(and_(*conditions))
            .order_by(Task.importance.asc(), Task.deadline.asc())
        )
        return list(result.scalars().all())
    
    async def get_created_task_with_relations(self, task_id: int, user_id: int) -> Optional[Task]:
        """Get task created by user with all relationships loaded."""
        result = await self.session.execute(
            select(Task)
            .options(
                selectinload(Task.category),
                selectinload(Task.project),
                selectinload(Task.assignee),
                selectinload(Task.creator),
            )
            .where(
                and_(
                    Task.id == task_id,
                    Task.created_by_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def count_assigned_tasks(
        self,
        user_id: int,
        status_filter: Optional[TaskStatus] = None,
    ) -> int:
        """Count tasks assigned to user."""
        conditions = [Task.assignee_id == user_id]
        if status_filter:
            conditions.append(Task.status == status_filter)
        
        result = await self.session.execute(
            select(func.count()).select_from(Task).where(and_(*conditions))
        )
        return result.scalar() or 0
