"""Authentication router."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer

from src.core.database import AsyncSession, get_db
from src.core.security import get_current_user
from src.models.user import User
from src.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    ForgotPasswordRequest,
    VerifyCodeRequest,
    ResetPasswordRequest,
    ErrorResponse,
)
from src.services import AuthService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    summary="Register new user",
    description="Register a new user account with email and password.",
    responses={
        200: {"description": "Successfully registered"},
        400: {"model": ErrorResponse, "description": "Validation error or email already exists"},
    },
)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Register a new user.
    
    - **email**: Valid email address
    - **password**: 8-16 characters, allowed: A-Za-z0-9!#$%&*+.<=>?@^_-
    - **password_confirm**: Must match password
    - **accept_terms**: Must be true
    """
    auth_service = AuthService(session)
    user, tokens = await auth_service.register(request)
    return tokens


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user",
    description="Authenticate user and return JWT tokens.",
    responses={
        200: {"description": "Successfully logged in"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
    },
)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Login with email and password.
    
    Returns access token (15 min) and refresh token (7 days).
    """
    auth_service = AuthService(session)
    user, tokens = await auth_service.login(request)
    return tokens


@router.post(
    "/logout",
    summary="Logout user",
    description="Invalidate all refresh tokens for the current user.",
    responses={
        200: {"description": "Successfully logged out"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def logout(
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Logout the current user by revoking all refresh tokens.
    """
    auth_service = AuthService(session)
    result = await auth_service.logout(current_user, "")
    return result


@router.post(
    "/forgot-password",
    summary="Request password reset",
    description="Send a password reset code to the user's email.",
    responses={
        200: {"description": "Reset code sent (if email exists)"},
    },
)
async def forgot_password(
    request: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Request a password reset code.
    
    For security, always returns success even if email doesn't exist.
    The code is logged for demo purposes (in production, it would be emailed).
    """
    auth_service = AuthService(session)
    return await auth_service.forgot_password(request)


@router.post(
    "/verify-code",
    summary="Verify password reset code",
    description="Verify the password reset code sent to email.",
    responses={
        200: {"description": "Code verified successfully"},
        400: {"model": ErrorResponse, "description": "Invalid or expired code"},
    },
)
async def verify_code(
    request: VerifyCodeRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Verify the password reset code.
    """
    auth_service = AuthService(session)
    return await auth_service.verify_code(request)


@router.post(
    "/reset-password",
    summary="Reset password",
    description="Reset password after code verification.",
    responses={
        200: {"description": "Password reset successfully"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
async def reset_password(
    request: ResetPasswordRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Reset password with new password.
    
    Should be called after verify-code endpoint returns success.
    """
    auth_service = AuthService(session)
    return await auth_service.reset_password(request)
