"""Бизнес логика"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import hashlib

from fastapi import HTTPException, status

from src.repositories import (
    UserRepository,
    RefreshTokenRepository,
    PasswordResetCodeRepository,
    ProjectRepository,
    TaskRepository,
    CategoryRepository,
)
from src.models.user import User
from src.models.task import Task, TaskStatus, ImportanceLevel
from src.models.project import Project
from src.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from src.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    ForgotPasswordRequest,
    VerifyCodeRequest,
    ResetPasswordRequest,
    ProfileUpdateRequest,
    ChangePasswordRequest,
    ProjectUpdateRequest,
    CreateTaskRequest,
)


logger = logging.getLogger(__name__)


class AuthService:
    
    def __init__(self, session):
        self.session = session
        self.user_repo = UserRepository(session)
        self.token_repo = RefreshTokenRepository(session)
        self.reset_code_repo = PasswordResetCodeRepository(session)
    
    async def register(
        self,
        data: RegisterRequest,
    ) -> tuple[User, TokenResponse]:
        if await self.user_repo.is_email_taken(data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Почта уже зарегистрирована",
                
            )
        
        user = await self.user_repo.create_user(
            email=data.email,
            password=data.password,
        )
        
        tokens = await self._generate_tokens(user)
        
        return user, tokens
    
    async def login(self, data: LoginRequest) -> tuple[User, TokenResponse]:
        user = await self.user_repo.get_by_email(data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Не верный пароль или почта",
                
            )
        
        if not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Не верный пароль или почта",
                
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Аккаунт не активный",
                
            )
        
        tokens = await self._generate_tokens(user)
        
        return user, tokens
    
    async def logout(self, user: User, access_token: str) -> dict:
        revoked_count = await self.token_repo.revoke_all_user_tokens(user.id)
        
        logger.info(f"User {user.id} logged out, revoked {revoked_count} tokens")
        
        return {"detail": "Успешныый выход"}
    
    async def forgot_password(self, data: ForgotPasswordRequest) -> dict:
        user = await self.user_repo.get_by_email(data.email)
        
        if not user:
            logger.warning(f"Password reset requested for non-existent email: {data.email}")
            return {"detail": "Если почта уже зараегистрирована сбрось пароль через код на почту"}
        
        code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
        
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        await self.reset_code_repo.create_code(
            email=data.email,
            code=code,
            expires_at=expires_at,
        )
        
        logger.info(f"PASSWORD RESET CODE for {data.email}: {code}")
        
        return {"detail": "Если почта уже зараегистрирована сбрось пароль через код на почту"}
    
    async def verify_code(self, data: VerifyCodeRequest) -> dict:
        code_entity = await self.reset_code_repo.get_valid_code(data.email, data.code)
        
        if not code_entity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired code",
                
            )
        
        return {"detail": "Код успешно верефицирован"}
    
    async def reset_password(self, data: ResetPasswordRequest) -> dict:
        
        user = await self.user_repo.get_by_email(data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден",
                
            )
        
        user.password_hash = get_password_hash(data.new_password)
        await self.session.flush()
        
        await self.token_repo.revoke_all_user_tokens(user.id)
        
        return {"detail": "Пароль сброшен"}
    
    async def _generate_tokens(self, user: User) -> TokenResponse:
        token_data = {"sub": str(user.id)}
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        await self.token_repo.create(
            token_hash=token_hash,
            user_id=user.id,
            expires_at=expires_at,
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )


class ProfileService:
    
    def __init__(self, session):
        self.session = session
        self.user_repo = UserRepository(session)
        self.token_repo = RefreshTokenRepository(session)
    
    async def get_profile(self, user: User) -> User:
        return user
    
    async def update_profile(
        self,
        user: User,
        data: ProfileUpdateRequest,
    ) -> User:
        update_data = {}
        
        if data.name is not None:
            update_data["name"] = data.name
        
        if data.email is not None:
            existing = await self.user_repo.get_by_email(data.email)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Почта уже используется",
                    
                )
            update_data["email"] = data.email
        
        if update_data:
            await self.user_repo.update(user, **update_data)
        
        return user
    
    async def change_password(
        self,
        user: User,
        data: ChangePasswordRequest,
    ) -> dict:
        if not verify_password(data.old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Текущий пароль не верный",
                
            )
        
        user.password_hash = get_password_hash(data.new_password)
        await self.session.flush()
        
        await self.token_repo.revoke_all_user_tokens(user.id)
        
        return {"detail": "Пароль успешно изменен"}
    
    async def logout(self, user: User) -> dict:
        await self.token_repo.revoke_all_user_tokens(user.id)
        return {"detail": "Успешный выход"}


class ProjectService:
    
    def __init__(self, session):
        self.session = session
        self.project_repo = ProjectRepository(session)
    
    async def get_projects(self, user: User) -> List[Project]:
        return await self.project_repo.get_user_projects(user.id)
    
    async def get_project(self, project_id: int, user: User) -> Project:
        project = await self.project_repo.get_by_id(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Проект не найден",
                
            )
        
        if project.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ к проекту запрещен",
                
            )
        
        return project
    
    async def update_project(
        self,
        project_id: int,
        user: User,
        data: ProjectUpdateRequest,
    ) -> Project:
        project = await self.get_project(project_id, user)
        
        update_data = {}
        if data.name is not None:
            update_data["name"] = data.name
        if data.icon is not None:
            update_data["icon"] = data.icon
        
        if update_data:
            await self.project_repo.update(project, **update_data)
        
        return project
    
    async def delete_project(self, project_id: int, user: User) -> dict:
        project = await self.get_project(project_id, user)
        
        await self.project_repo.delete(project)
        
        return {"detail": "Проект успешно удален"}


class TaskService:
    
    def __init__(self, session):
        self.session = session
        self.task_repo = TaskRepository(session)
        self.category_repo = CategoryRepository(session)
        self.project_repo = ProjectRepository(session)
        self.user_repo = UserRepository(session)
    
    async def get_assigned_tasks(
        self,
        user: User,
        status_filter: Optional[TaskStatus] = None,
        importance_filter: Optional[ImportanceLevel] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        offset = (page - 1) * page_size
        
        tasks, total = await self.task_repo.get_assigned_tasks(
            user_id=user.id,
            status_filter=status_filter,
            importance_filter=importance_filter,
            limit=page_size,
            offset=offset,
        )
        
        completed_count = await self.task_repo.count_assigned_tasks(
            user_id=user.id,
            status_filter=TaskStatus.COMPLETED,
        )
        
        return {
            "total": total,
            "completed": completed_count,
            "tasks": tasks,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
    
    async def get_task(
        self,
        task_id: int,
        user: User,
    ) -> Task:
        task = await self.task_repo.get_task_with_relations(task_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена",
                
            )
        
        is_assignee = task.assignee_id == user.id
        is_creator = task.created_by_id == user.id
        
        if not is_assignee and not is_creator:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ к задаче запрещен",
                
            )
        
        if is_assignee and not is_creator:
            task.project_name = None
            task.category_marker = None
        else:
            if task.project:
                task.project_name = task.project.name
            if task.category:
                task.category_marker = f"{task.category.color} {task.category.name}"
        
        return task
    
    async def complete_task(self, task_id: int, user: User) -> dict:
        task = await self.task_repo.get_task_with_relations(task_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задача не найдена",
                
            )
        
        if task.assignee_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Выполнить эту задачу может только назначенный сотрудник",
                
            )
        
        task.mark_completed()
        await self.session.flush()
        
        return {"detail": "Задача помечена как выполненая"}
    
    async def reset_filters(self, user: User) -> dict:
        return {"detail": "Фильтры успешно сброшены"}
    
    async def create_calendar_task(
        self,
        user: User,
        data: CreateTaskRequest,
    ) -> Task:
        if data.category_id:
            category = await self.category_repo.get_by_id_and_user(
                data.category_id, user.id
            )
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Категория не найдена",
                    
                )
        
        if data.project_id:
            project = await self.project_repo.get_by_id(data.project_id)
            if not project or project.owner_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Проект не найден",
                    
                )
        
        if data.assignee_id:
            assignee = await self.user_repo.get_by_id(data.assignee_id)
            if not assignee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Исполнитель не найден",
                    
                )
        
        task = await self.task_repo.create(
            name=data.name,
            description=data.description,
            category_id=data.category_id,
            project_id=data.project_id,
            assignee_id=data.assignee_id,
            created_by_id=user.id,
            deadline=data.deadline,
            importance=data.importance,
            status=TaskStatus.PENDING,
        )
        
        return task


class CalendarService:

    def __init__(self, session):
        self.session = session
        self.task_repo = TaskRepository(session)
    
    async def get_calendar_month(
        self,
        user: User,
        year: int,
        month: int,
    ) -> dict:
        tasks = await self.task_repo.get_tasks_for_calendar_month(
            user_id=user.id,
            year=year,
            month=month,
        )
        
        date_marks = {}
        for task in tasks:
            if task.deadline:
                date_str = task.deadline.strftime("%Y-%m-%d")
                if date_str not in date_marks:
                    date_marks[date_str] = {
                        "date": date_str,
                        "task_count": 0,
                        "has_important": False,
                    }
                date_marks[date_str]["task_count"] += 1
                if task.importance in [ImportanceLevel.CRITICAL, ImportanceLevel.HIGH]:
                    date_marks[date_str]["has_important"] = True
        
        return {
            "year": year,
            "month": month,
            "dates": list(date_marks.values()),
        }
    
    async def get_calendar_day_tasks(
        self,
        user: User,
        date: str,
        importance_filter: Optional[ImportanceLevel] = None,
        status_filter: Optional[TaskStatus] = None,
    ) -> dict:
        try:
            target_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не верный формат даты. (YYYY-MM-DD)",
                
            )
        
        tasks = await self.task_repo.get_tasks_for_calendar_day(
            user_id=user.id,
            target_date=target_date,
            importance_filter=importance_filter,
            status_filter=status_filter,
        )
        
        return {
            "date": date,
            "tasks": tasks,
        }
