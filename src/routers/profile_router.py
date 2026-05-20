"""Profile router."""

from fastapi import APIRouter, Depends, UploadFile, File, Optional
from fastapi.responses import JSONResponse

from src.core.database import AsyncSession, get_db
from src.core.security import get_current_user
from src.models.user import User
from src.schemas import (
    ProfileResponse,
    ProfileUpdateRequest,
    ChangePasswordRequest,
    ErrorResponse,
)
from src.services import ProfileService


router = APIRouter(prefix="/api/v1/profile", tags=["Profile"])


@router.get(
    "",
    response_model=ProfileResponse,
    summary="Get user profile",
    description="Get current user's profile information.",
    responses={
        200: {"description": "Profile retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def get_profile(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user profile."""
    service = ProfileService(session)
    profile = await service.get_profile(current_user)
    return profile


@router.put(
    "",
    response_model=ProfileResponse,
    summary="Update profile",
    description="Update current user's profile information.",
    responses={
        200: {"description": "Profile updated successfully"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def update_profile(
    request: ProfileUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user profile."""
    service = ProfileService(session)
    profile = await service.update_profile(current_user, request)
    return profile


@router.post(
    "/change-password",
    summary="Change password",
    description="Change current user's password.",
    responses={
        200: {"description": "Password changed successfully"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def change_password(
    request: ChangePasswordRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change user password."""
    service = ProfileService(session)
    return await service.change_password(current_user, request)


@router.post(
    "/logout",
    summary="Logout from profile",
    description="Logout current user (alternative logout endpoint).",
    responses={
        200: {"description": "Successfully logged out"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def logout(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Logout user."""
    service = ProfileService(session)
    return await service.logout(current_user)
