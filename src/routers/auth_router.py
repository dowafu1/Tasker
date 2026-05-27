"""Ручки аунтификации"""

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
    summary="Регистрация нововго пользователя",
    description="Регистрация нового пользователя с помошью почты и пароля ",
    responses={
        200: {"description": "Успех"},
        400: {"model": ErrorResponse, "description": "Ошибка валидации или почты"},
    },
)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_db),
):
    auth_service = AuthService(session)
    user, tokens = await auth_service.register(request)
    return tokens


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход",
    description="Аунтификация аккаунта и возварщение JWT токена",
    responses={
        200: {"description": "Вход прошел успешно"},
        401: {"model": ErrorResponse, "description": "Ошибка"},
    },
)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db),
):
    auth_service = AuthService(session)
    user, tokens = await auth_service.login(request)
    return tokens


@router.post(
    "/logout",
    summary="Выход из аккаунта",
    description="Анулировать все рефреш токены для этого пользователя",
    responses={
        200: {"description": "Успешный выход"},
        401: {"model": ErrorResponse, "description": "Ошибка выхода"},
    },
)
async def logout(
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auth_service = AuthService(session)
    result = await auth_service.logout(current_user, "")
    return result


@router.post(
    "/forgot-password",
    summary="Востановление пароля",
    description="Отправка кода для востановления пароля на почту",
    responses={
        200: {"description": "Код отправлен"},
    },
)
async def forgot_password(
    request: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_db),
):
    auth_service = AuthService(session)
    return await auth_service.forgot_password(request)


@router.post(
    "/verify-code",
    summary="Верификация кода для востановления пароля",
    description="Верификация кода для востонавления пароля отправлен на email.",
    responses={
        200: {"description": "Код успешно прошел верификацию"},
        400: {"model": ErrorResponse, "description": "Ошибка"},
    },
)
async def verify_code(
    request: VerifyCodeRequest,
    session: AsyncSession = Depends(get_db),
):
    auth_service = AuthService(session)
    return await auth_service.verify_code(request)


@router.post(
    "/reset-password",
    summary="Сброс пароля",
    description="Сброс пароля после код верификации",
    responses={
        200: {"description": "Пароль сброшен"},
        400: {"model": ErrorResponse, "description": "Ошибка валидации"},
        404: {"model": ErrorResponse, "description": "Пользователь не найден"},
    },
)
async def reset_password(
    request: ResetPasswordRequest,
    session: AsyncSession = Depends(get_db),
):
    auth_service = AuthService(session)
    return await auth_service.reset_password(request)
