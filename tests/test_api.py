import pytest
from datetime import datetime, timedelta, timezone

from src.models.task import TaskStatus, ImportanceLevel


class TestAuthEndpoints:
    
    @pytest.mark.asyncio
    async def test_register_success(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "password_confirm": "password123",
                "accept_terms": True,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    @pytest.mark.asyncio
    async def test_register_email_exists(self, client, test_user):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "password123",
                "password_confirm": "password123",
                "accept_terms": True,
            },
        )
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_register_invalid_password(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "short",
                "password_confirm": "short",
                "accept_terms": True,
            },
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "password123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
            },
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_logout(self, authenticated_client):
        response = await authenticated_client.post("/api/v1/auth/logout")
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_forgot_password(self, client, test_user):
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": test_user.email},
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_reset_password(self, client, test_user):
        from src.models.user import PasswordResetCode
        
        code = "123456"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        reset_code = PasswordResetCode(
            email=test_user.email.lower(),
            code=code,
            expires_at=expires_at,
        )
        
        pass


class TestProfileEndpoints:
    
    @pytest.mark.asyncio
    async def test_get_profile(self, authenticated_client, test_user):
        response = await authenticated_client.get("/api/v1/profile")
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id
    
    @pytest.mark.asyncio
    async def test_update_profile_name(self, authenticated_client, test_user):
        response = await authenticated_client.put(
            "/api/v1/profile",
            json={"name": "Updated Name"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_change_password(self, authenticated_client, test_user):
        response = await authenticated_client.post(
            "/api/v1/profile/change-password",
            json={
                "old_password": "password123",
                "new_password": "newpassword456",
                "password_confirm": "newpassword456",
            },
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        response = await client.get("/api/v1/profile")
        
        assert response.status_code == 401


class TestProjectEndpoints:
    
    @pytest.mark.asyncio
    async def test_get_projects(self, authenticated_client, test_project):
        response = await authenticated_client.get("/api/v1/projects")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == test_project.id
    
    @pytest.mark.asyncio
    async def test_update_project(self, authenticated_client, test_project):
        response = await authenticated_client.put(
            f"/api/v1/projects/{test_project.id}",
            json={"name": "Updated Project", "icon": "📂"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Project"
        assert data["icon"] == "📂"
    
    @pytest.mark.asyncio
    async def test_delete_project(self, authenticated_client, test_project):
        response = await authenticated_client.delete(
            f"/api/v1/projects/{test_project.id}",
        )
        
        assert response.status_code == 200


class TestTaskEndpoints:
    
    @pytest.mark.asyncio
    async def test_get_assigned_tasks(self, authenticated_client, test_task):
        response = await authenticated_client.get("/api/v1/tasks/assigned")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["tasks"]) == 1
    
    @pytest.mark.asyncio
    async def test_get_task_details(self, authenticated_client, test_task):
        response = await authenticated_client.get(f"/api/v1/tasks/{test_task.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_task.id
        assert data["name"] == test_task.name
    
    @pytest.mark.asyncio
    async def test_complete_task(self, authenticated_client, test_task):
        response = await authenticated_client.patch(
            f"/api/v1/tasks/{test_task.id}/complete",
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_assigned_task_conditional_fields(self, authenticated_client, assigned_task):
        response = await authenticated_client.get(f"/api/v1/tasks/{assigned_task.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("project_name") is None
        assert data.get("category_marker") is None


class TestCalendarEndpoints:
    
    @pytest.mark.asyncio
    async def test_get_calendar_month(self, authenticated_client, test_task):
        now = datetime.now(timezone.utc)
        response = await authenticated_client.get(
            f"/api/v1/calendar/{now.year}/{now.month}",
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == now.year
        assert data["month"] == now.month
    
    @pytest.mark.asyncio
    async def test_get_calendar_day_tasks(self, authenticated_client, test_task):
        if test_task.deadline:
            date_str = test_task.deadline.strftime("%Y-%m-%d")
            response = await authenticated_client.get(
                f"/api/v1/calendar/{date_str}/tasks",
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["date"] == date_str
    
    @pytest.mark.asyncio
    async def test_create_calendar_task(self, authenticated_client, test_category, test_project):
        deadline = datetime.now(timezone.utc) + timedelta(days=7)
        
        response = await authenticated_client.post(
            "/api/v1/calendar/tasks",
            json={
                "name": "New Calendar Task",
                "description": "Created from calendar",
                "category_id": test_category.id,
                "project_id": test_project.id,
                "deadline": deadline.isoformat(),
                "importance": "high",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Calendar Task"
        assert data["importance"] == "high"


class TestValidationEdgeCases:
    
    @pytest.mark.asyncio
    async def test_password_too_short(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "abc12",
                "password_confirm": "abc12",
                "accept_terms": True,
            },
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_password_too_long(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "a" * 17,
                "password_confirm": "a" * 17,
                "accept_terms": True,
            },
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_invalid_email_format(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "password123",
                "password_confirm": "password123",
                "accept_terms": True,
            },
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_passwords_do_not_match(self, client):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "password_confirm": "different123",
                "accept_terms": True,
            },
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_name_with_invalid_chars(self, authenticated_client):
        response = await authenticated_client.put(
            "/api/v1/profile",
            json={"name": "Name123!"},
        )
        
        assert response.status_code == 422
