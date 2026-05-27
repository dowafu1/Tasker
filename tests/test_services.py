import pytest
from datetime import datetime, timedelta, timezone

from src.services import AuthService, ProfileService, ProjectService, TaskService, CalendarService
from src.models.user import User, PasswordResetCode
from src.models.task import Task, TaskStatus, ImportanceLevel, Category
from src.models.project import Project
from src.schemas import (
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    VerifyCodeRequest,
    ResetPasswordRequest,
    ProfileUpdateRequest,
    ChangePasswordRequest,
    ProjectCreateRequest,
    CreateTaskRequest,
)
from src.core.security import verify_password, get_password_hash


class TestAuthService:
    
    @pytest.mark.asyncio
    async def test_register_success(self, test_session):
        auth_service = AuthService(test_session)
        
        request = RegisterRequest(
            email="newuser@example.com",
            password="password123",
            password_confirm="password123",
            accept_terms=True,
        )
        
        user, tokens = await auth_service.register(request)
        
        assert user is not None
        assert user.email == "newuser@example.com"
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
    
    @pytest.mark.asyncio
    async def test_register_email_already_exists(self, test_session, test_user):
        auth_service = AuthService(test_session)
        
        request = RegisterRequest(
            email=test_user.email,
            password="password123",
            password_confirm="password123",
            accept_terms=True,
        )
        
        with pytest.raises(Exception) as exc_info:
            await auth_service.register(request)
        
        assert "Почта уже зарегистрирована" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_login_success(self, test_session, test_user):
        auth_service = AuthService(test_session)
        
        request = LoginRequest(
            email=test_user.email,
            password="password123",
        )
        
        user, tokens = await auth_service.login(request)
        
        assert user.id == test_user.id
        assert tokens.access_token is not None
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, test_session, test_user):
        auth_service = AuthService(test_session)
        
        request = LoginRequest(
            email=test_user.email,
            password="wrongpassword",
        )
        
        with pytest.raises(Exception) as exc_info:
            await auth_service.login(request)
        
        assert "Не верный пароль или почта" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_forgot_password(self, test_session, test_user):
        auth_service = AuthService(test_session)
        
        request = ForgotPasswordRequest(email=test_user.email)
        result = await auth_service.forgot_password(request)
        
        assert "detail" in result
        
        from sqlalchemy import select
        result = await test_session.execute(
            select(PasswordResetCode).where(PasswordResetCode.email == test_user.email.lower())
        )
        codes = result.scalars().all()
        assert len(codes) > 0
    
    @pytest.mark.asyncio
    async def test_reset_password(self, test_session, test_user):
        auth_service = AuthService(test_session)
        
        code = "123456"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        reset_code = PasswordResetCode(
            email=test_user.email.lower(),
            code=code,
            expires_at=expires_at,
        )
        test_session.add(reset_code)
        await test_session.flush()
        
        request = ResetPasswordRequest(
            email=test_user.email,
            new_password="newpassword123",
            password_confirm="newpassword123",
        )
        
        result = await auth_service.reset_password(request)
        
        assert "Пароль сброшен" in result["detail"]
        
        await test_session.refresh(test_user)
        assert verify_password("newpassword123", test_user.password_hash)


class TestProfileService:
    
    @pytest.mark.asyncio
    async def test_get_profile(self, test_session, test_user):
        profile_service = ProfileService(test_session)
        
        profile = await profile_service.get_profile(test_user)
        
        assert profile.id == test_user.id
        assert profile.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_update_profile_name(self, test_session, test_user):
        profile_service = ProfileService(test_session)
        
        request = ProfileUpdateRequest(name="Updated Name")
        updated_profile = await profile_service.update_profile(test_user, request)
        
        assert updated_profile.name == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, test_session, test_user):
        profile_service = ProfileService(test_session)
        
        request = ChangePasswordRequest(
            old_password="password123",
            new_password="newpassword456",
            password_confirm="newpassword456",
        )
        
        result = await profile_service.change_password(test_user, request)
        
        assert "Пароль успешно изменен" in result["detail"]
        
        assert verify_password("newpassword456", test_user.password_hash)
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_old(self, test_session, test_user):
        profile_service = ProfileService(test_session)
        
        request = ChangePasswordRequest(
            old_password="wrongpassword",
            new_password="newpassword456",
            password_confirm="newpassword456",
        )
        
        with pytest.raises(Exception) as exc_info:
            await profile_service.change_password(test_user, request)
        
        assert "Текущий пароль не верный" in str(exc_info.value)


class TestProjectService:
    
    @pytest.mark.asyncio
    async def test_get_projects(self, test_session, test_user, test_project):
        project_service = ProjectService(test_session)
        
        projects = await project_service.get_projects(test_user)
        
        assert len(projects) == 1
        assert projects[0].id == test_project.id
    
    @pytest.mark.asyncio
    async def test_delete_project(self, test_session, test_user, test_project):
        project_service = ProjectService(test_session)
        
        result = await project_service.delete_project(test_project.id, test_user)
        
        assert "Проект успешно удален" in result["detail"]


class TestTaskService:
    
    @pytest.mark.asyncio
    async def test_get_assigned_tasks(self, test_session, test_user, test_task):
        task_service = TaskService(test_session)
        
        result = await task_service.get_assigned_tasks(test_user)
        
        assert result["total"] == 1
        assert len(result["tasks"]) == 1
    
    @pytest.mark.asyncio
    async def test_complete_task(self, test_session, test_user, test_task):
        task_service = TaskService(test_session)
        
        result = await task_service.complete_task(test_task.id, test_user)
        
        assert "Задача помечена как выполненая" in result["detail"]
        assert test_task.status == TaskStatus.COMPLETED


class TestCalendarService:
    
    @pytest.mark.asyncio
    async def test_get_calendar_month(self, test_session, test_user, test_task):
        calendar_service = CalendarService(test_session)
        
        now = datetime.now(timezone.utc)
        result = await calendar_service.get_calendar_month(test_user, now.year, now.month)
        
        assert result["year"] == now.year
        assert result["month"] == now.month
