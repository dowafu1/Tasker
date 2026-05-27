"""Уровень репозитория для операций с БД"""

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
        
    def __init__(self, session: AsyncSession, model: Type[ModelT]):
        self.session = session
        self.model = model
    
    async def get_by_id(self, id: int) -> Optional[ModelT]:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[ModelT]:
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
    
    async def create(self, **kwargs) -> ModelT:
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        return entity
    
    async def update(self, entity: ModelT, **kwargs) -> ModelT:
        for key, value in kwargs.items():
            setattr(entity, key, value)
        await self.session.flush()
        return entity
    
    async def delete(self, entity: ModelT) -> None:
        await self.session.delete(entity)
        await self.session.flush()


class UserRepository(BaseRepository[User]):
        
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
    
    async def get_by_email(self, email: str) -> Optional[User]:
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
        existing = await self.get_by_email(email)
        return existing is not None


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, RefreshToken)
    
    async def get_by_token_hash(self, token_hash: str) -> Optional[RefreshToken]:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()
    
    async def revoke_token(self, token_hash: str) -> bool:
        token = await self.get_by_token_hash(token_hash)
        if token:
            token.is_revoked = True
            await self.session.flush()
            return True
        return False
    
    async def revoke_all_user_tokens(self, user_id: int) -> int:
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
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, PasswordResetCode)
    
    async def get_valid_code(self, email: str, code: str) -> Optional[PasswordResetCode]:
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
        code_entity.is_used = True
        await self.session.flush()


class ProjectRepository(BaseRepository[Project]):
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Project)
    
    async def get_user_projects(self, user_id: int) -> List[Project]:
        result = await self.session.execute(
            select(Project)
            .where(Project.owner_id == user_id)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_project_with_tasks(self, project_id: int) -> Optional[Project]:
        result = await self.session.execute(
            select(Project)
            .options(selectinload(Project.tasks))
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()


class CategoryRepository(BaseRepository[Category]):
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Category)
    
    async def get_user_categories(self, user_id: int) -> List[Category]:
        result = await self.session.execute(
            select(Category)
            .where(Category.user_id == user_id)
            .order_by(Category.name)
        )
        return list(result.scalars().all())
    
    async def get_by_id_and_user(self, category_id: int, user_id: int) -> Optional[Category]:
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
        
        conditions = [Task.assignee_id == user_id]
        
        if status_filter:
            conditions.append(Task.status == status_filter)
        if importance_filter:
            conditions.append(Task.importance == importance_filter)
        
        count_query = select(func.count()).select_from(Task).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0
        
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
        from datetime import date
        import calendar
        
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
        conditions = [Task.assignee_id == user_id]
        if status_filter:
            conditions.append(Task.status == status_filter)
        
        result = await self.session.execute(
            select(func.count()).select_from(Task).where(and_(*conditions))
        )
        return result.scalar() or 0
