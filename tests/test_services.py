"""Unit tests for services layer."""

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
    """Tests for AuthService."""
    
    @pytest.mark.asyncio
    async def test_register_success(self, test_session):
        """Test successful user registration."""
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
        """Test registration with existing email."""
        auth_service = AuthService(test_session)
        
        request = RegisterRequest(
            email=test_user.email,
            password="password123",
            password_confirm="password123",
            accept_terms=True,
        )
        
        with pytest.raises(Exception) as exc_info:
            await auth_service.register(request)
        
        assert "Email already registered" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_login_success(self, test_session, test_user):
        """Test successful login."""
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
        """Test login with invalid password."""
        auth_service = AuthService(test_session)
        
        request = LoginRequest(
            email=test_user.email,
            password="wrongpassword",
        )
        
        with pytest.raises(Exception) as exc_info:
            await auth_service.login(request)
        
        assert "Invalid email or password" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_forgot_password(self, test_session, test_user):
        """Test forgot password flow."""
        auth_service = AuthService(test_session)
        
        request = ForgotPasswordRequest(email=test_user.email)
        result = await auth_service.forgot_password(request)
        
        assert "detail" in result
        
        # Check that reset code was created
        from sqlalchemy import select
        result = await test_session.execute(
            select(PasswordResetCode).where(PasswordResetCode.email == test_user.email.lower())
        )
        codes = result.scalars().all()
        assert len(codes) > 0
    
    @pytest.mark.asyncio
    async def test_reset_password(self, test_session, test_user):
        """Test password reset."""
        auth_service = AuthService(test_session)
        
        # First create a reset code
        from datetime import timedelta, timezone
        code = "123456"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        reset_code = PasswordResetCode(
            email=test_user.email.lower(),
            code=code,
            expires_at=expires_at,
        )
        test_session.add(reset_code)
        await test_session.flush()
        
        # Now reset password
        request = ResetPasswordRequest(
            email=test_user.email,
            new_password="newpassword123",
            password_confirm="newpassword123",
        )
        
        result = await auth_service.reset_password(request)
        
        assert "Password reset successfully" in result["detail"]
        
        # Verify password was changed
        await test_session.refresh(test_user)
        assert verify_password("newpassword123", test_user.password_hash)


class TestProfileService:
    """Tests for ProfileService."""
    
    @pytest.mark.asyncio
    async def test_get_profile(self, test_session, test_user):
        """Test getting user profile."""
        profile_service = ProfileService(test_session)
        
        profile = await profile_service.get_profile(test_user)
        
        assert profile.id == test_user.id
        assert profile.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_update_profile_name(self, test_session, test_user):
        """Test updating profile name."""
        profile_service = ProfileService(test_session)
        
        request = ProfileUpdateRequest(name="Updated Name")
        updated_profile = await profile_service.update_profile(test_user, request)
        
        assert updated_profile.name == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, test_session, test_user):
        """Test changing password."""
        profile_service = ProfileService(test_session)
        
        request = ChangePasswordRequest(
            old_password="password123",
            new_password="newpassword456",
            password_confirm="newpassword456",
        )
        
        result = await profile_service.change_password(test_user, request)
        
        assert "Password changed successfully" in result["detail"]
        
        # Verify new password works
        assert verify_password("newpassword456", test_user.password_hash)
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_old(self, test_session, test_user):
        """Test changing password with wrong old password."""
        profile_service = ProfileService(test_session)
        
        request = ChangePasswordRequest(
            old_password="wrongpassword",
            new_password="newpassword456",
            password_confirm="newpassword456",
        )
        
        with pytest.raises(Exception) as exc_info:
            await profile_service.change_password(test_user, request)
        
        assert "Current password is incorrect" in str(exc_info.value)


class TestProjectService:
    """Tests for ProjectService."""
    
    @pytest.mark.asyncio
    async def test_get_projects(self, test_session, test_user, test_project):
        """Test getting user projects."""
        project_service = ProjectService(test_session)
        
        projects = await project_service.get_projects(test_user)
        
        assert len(projects) == 1
        assert projects[0].id == test_project.id
    
    @pytest.mark.asyncio
    async def test_delete_project(self, test_session, test_user, test_project):
        """Test deleting a project."""
        project_service = ProjectService(test_session)
        
        result = await project_service.delete_project(test_project.id, test_user)
        
        assert "Project deleted successfully" in result["detail"]


class TestTaskService:
    """Tests for TaskService."""
    
    @pytest.mark.asyncio
    async def test_get_assigned_tasks(self, test_session, test_user, test_task):
        """Test getting assigned tasks."""
        task_service = TaskService(test_session)
        
        result = await task_service.get_assigned_tasks(test_user)
        
        assert result["total"] == 1
        assert len(result["tasks"]) == 1
    
    @pytest.mark.asyncio
    async def test_complete_task(self, test_session, test_user, test_task):
        """Test completing a task."""
        task_service = TaskService(test_session)
        
        result = await task_service.complete_task(test_task.id, test_user)
        
        assert "Task marked as completed" in result["detail"]
        assert test_task.status == TaskStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_create_calendar_task(self, test_session, test_user, test_category, test_project):
        """Test creating a task via calendar."""
        task_service = TaskService(test_session)
        
        deadline = datetime.now(timezone.utc) + timedelta(days=7)
        
        request = CreateTaskRequest(
            name="New Calendar Task",
            description="Created from calendar",
            category_id=test_category.id,
            project_id=test_project.id,
            deadline=deadline,
            importance=ImportanceLevel.HIGH,
        )
        
        task = await task_service.create_calendar_task(test_user, request)
        
        assert task.name == "New Calendar Task"
        assert task.importance == ImportanceLevel.HIGH
        assert task.created_by_id == test_user.id


class TestCalendarService:
    """Tests for CalendarService."""
    
    @pytest.mark.asyncio
    async def test_get_calendar_month(self, test_session, test_user, test_task):
        """Test getting calendar month view."""
        calendar_service = CalendarService(test_session)
        
        now = datetime.now(timezone.utc)
        result = await calendar_service.get_calendar_month(test_user, now.year, now.month)
        
        assert result["year"] == now.year
        assert result["month"] == now.month
        assert len(result["dates"]) >= 1
    
    @pytest.mark.asyncio
    async def test_get_calendar_day_tasks(self, test_session, test_user, test_task):
        """Test getting tasks for a specific day."""
        calendar_service = CalendarService(test_session)
        
        if test_task.deadline:
            date_str = test_task.deadline.strftime("%Y-%m-%d")
            result = await calendar_service.get_calendar_day_tasks(test_user, date_str)
            
            assert result["date"] == date_str
            assert len(result["tasks"]) >= 1
