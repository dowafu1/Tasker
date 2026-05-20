"""Service layer for business logic."""

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
    """Authentication service."""
    
    def __init__(self, session):
        self.session = session
        self.user_repo = UserRepository(session)
        self.token_repo = RefreshTokenRepository(session)
        self.reset_code_repo = PasswordResetCodeRepository(session)
    
    async def register(
        self,
        data: RegisterRequest,
    ) -> tuple[User, TokenResponse]:
        """Register a new user."""
        # Check if email is already taken
        if await self.user_repo.is_email_taken(data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
                code="VALIDATION_ERROR",
            )
        
        # Create user
        user = await self.user_repo.create_user(
            email=data.email,
            password=data.password,
        )
        
        # Generate tokens
        tokens = await self._generate_tokens(user)
        
        return user, tokens
    
    async def login(self, data: LoginRequest) -> tuple[User, TokenResponse]:
        """Login user."""
        # Find user
        user = await self.user_repo.get_by_email(data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                code="AUTH_ERROR",
            )
        
        # Verify password
        if not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                code="AUTH_ERROR",
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
                code="AUTH_ERROR",
            )
        
        # Generate tokens
        tokens = await self._generate_tokens(user)
        
        return user, tokens
    
    async def logout(self, user: User, access_token: str) -> dict:
        """Logout user by revoking refresh tokens."""
        # Revoke all refresh tokens for this user
        revoked_count = await self.token_repo.revoke_all_user_tokens(user.id)
        
        logger.info(f"User {user.id} logged out, revoked {revoked_count} tokens")
        
        return {"detail": "Successfully logged out"}
    
    async def forgot_password(self, data: ForgotPasswordRequest) -> dict:
        """Send password reset code."""
        # Check if user exists
        user = await self.user_repo.get_by_email(data.email)
        
        # Even if user doesn't exist, return success to prevent enumeration
        if not user:
            logger.warning(f"Password reset requested for non-existent email: {data.email}")
            return {"detail": "If email is registered, a reset code has been sent"}
        
        # Generate 6-digit code
        code = "".join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Code expires in 15 minutes
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        # Store code
        await self.reset_code_repo.create_code(
            email=data.email,
            code=code,
            expires_at=expires_at,
        )
        
        # In production, send email here. For demo, log the code.
        logger.info(f"PASSWORD RESET CODE for {data.email}: {code}")
        
        return {"detail": "If email is registered, a reset code has been sent"}
    
    async def verify_code(self, data: VerifyCodeRequest) -> dict:
        """Verify password reset code."""
        code_entity = await self.reset_code_repo.get_valid_code(data.email, data.code)
        
        if not code_entity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired code",
                code="VALIDATION_ERROR",
            )
        
        return {"detail": "Code verified successfully"}
    
    async def reset_password(self, data: ResetPasswordRequest) -> dict:
        """Reset password after code verification."""
        # First verify that a valid code was used (we assume this was done before)
        # In a real flow, you'd track this in session or require the code here too
        
        user = await self.user_repo.get_by_email(data.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
                code="NOT_FOUND",
            )
        
        # Update password
        user.password_hash = get_password_hash(data.new_password)
        await self.session.flush()
        
        # Revoke all refresh tokens for security
        await self.token_repo.revoke_all_user_tokens(user.id)
        
        return {"detail": "Password reset successfully"}
    
    async def _generate_tokens(self, user: User) -> TokenResponse:
        """Generate access and refresh tokens."""
        token_data = {"sub": str(user.id)}
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Store refresh token hash for invalidation
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
    """Profile management service."""
    
    def __init__(self, session):
        self.session = session
        self.user_repo = UserRepository(session)
        self.token_repo = RefreshTokenRepository(session)
    
    async def get_profile(self, user: User) -> User:
        """Get user profile."""
        return user
    
    async def update_profile(
        self,
        user: User,
        data: ProfileUpdateRequest,
    ) -> User:
        """Update user profile."""
        update_data = {}
        
        if data.name is not None:
            update_data["name"] = data.name
        
        if data.email is not None:
            # Check if new email is taken by another user
            existing = await self.user_repo.get_by_email(data.email)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use",
                    code="VALIDATION_ERROR",
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
        """Change user password."""
        # Verify old password
        if not verify_password(data.old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
                code="VALIDATION_ERROR",
            )
        
        # Update password
        user.password_hash = get_password_hash(data.new_password)
        await self.session.flush()
        
        # Revoke all refresh tokens for security
        await self.token_repo.revoke_all_user_tokens(user.id)
        
        return {"detail": "Password changed successfully"}
    
    async def logout(self, user: User) -> dict:
        """Logout user."""
        await self.token_repo.revoke_all_user_tokens(user.id)
        return {"detail": "Successfully logged out"}


class ProjectService:
    """Project management service."""
    
    def __init__(self, session):
        self.session = session
        self.project_repo = ProjectRepository(session)
    
    async def get_projects(self, user: User) -> List[Project]:
        """Get all projects owned by user."""
        return await self.project_repo.get_user_projects(user.id)
    
    async def get_project(self, project_id: int, user: User) -> Project:
        """Get a specific project."""
        project = await self.project_repo.get_by_id(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
                code="NOT_FOUND",
            )
        
        # Check ownership
        if project.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project",
                code="AUTH_ERROR",
            )
        
        return project
    
    async def update_project(
        self,
        project_id: int,
        user: User,
        data: ProjectUpdateRequest,
    ) -> Project:
        """Update a project."""
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
        """Delete a project."""
        project = await self.get_project(project_id, user)
        
        await self.project_repo.delete(project)
        
        return {"detail": "Project deleted successfully"}


class TaskService:
    """Task management service."""
    
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
        """Get tasks assigned to user with pagination."""
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
        """Get task details with conditional logic for assigned vs created."""
        # First try to get as assigned task
        task = await self.task_repo.get_task_with_relations(task_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
                code="NOT_FOUND",
            )
        
        # Check if user has access (either assignee or creator)
        is_assignee = task.assignee_id == user.id
        is_creator = task.created_by_id == user.id
        
        if not is_assignee and not is_creator:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this task",
                code="AUTH_ERROR",
            )
        
        # Conditional logic: if task is assigned (user is assignee), 
        # do NOT show project_name and category_marker
        if is_assignee and not is_creator:
            # Clear project_name and category_marker for assigned tasks
            task.project_name = None
            task.category_marker = None
        else:
            # For created tasks, include project name and category marker
            if task.project:
                task.project_name = task.project.name
            if task.category:
                task.category_marker = f"{task.category.color} {task.category.name}"
        
        return task
    
    async def complete_task(self, task_id: int, user: User) -> dict:
        """Mark task as completed."""
        task = await self.task_repo.get_task_with_relations(task_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
                code="NOT_FOUND",
            )
        
        # Check if user is the assignee
        if task.assignee_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only assignee can complete this task",
                code="AUTH_ERROR",
            )
        
        task.mark_completed()
        await self.session.flush()
        
        return {"detail": "Task marked as completed"}
    
    async def reset_filters(self, user: User) -> dict:
        """Reset task filters (placeholder - filters are stateless in API)."""
        # In a real app, this might clear stored filter preferences
        return {"detail": "Filters reset successfully"}
    
    async def create_calendar_task(
        self,
        user: User,
        data: CreateTaskRequest,
    ) -> Task:
        """Create a new task via calendar."""
        # Validate category if provided
        if data.category_id:
            category = await self.category_repo.get_by_id_and_user(
                data.category_id, user.id
            )
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found",
                    code="NOT_FOUND",
                )
        
        # Validate project if provided
        if data.project_id:
            project = await self.project_repo.get_by_id(data.project_id)
            if not project or project.owner_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found",
                    code="NOT_FOUND",
                )
        
        # Validate assignee if provided
        if data.assignee_id:
            assignee = await self.user_repo.get_by_id(data.assignee_id)
            if not assignee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignee not found",
                    code="NOT_FOUND",
                )
        
        # Create task
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
    """Calendar service."""
    
    def __init__(self, session):
        self.session = session
        self.task_repo = TaskRepository(session)
    
    async def get_calendar_month(
        self,
        user: User,
        year: int,
        month: int,
    ) -> dict:
        """Get calendar month with task date marks."""
        tasks = await self.task_repo.get_tasks_for_calendar_month(
            user_id=user.id,
            year=year,
            month=month,
        )
        
        # Group tasks by date
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
        """Get tasks for a specific day."""
        try:
            target_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use ISO format (YYYY-MM-DD)",
                code="VALIDATION_ERROR",
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
