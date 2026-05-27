"""Ручки профиля"""

from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File
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
    summary="Получить профиль пользователя",
    description="Получить информацию из профиля текущего пользователя.",
    responses={
        200: {"description": "Профиль успешно получен."},
        401: {"model": ErrorResponse, "description": "Не подтверждено"},
    },
)
async def get_profile(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProfileService(session)
    profile = await service.get_profile(current_user)
    return profile


@router.put(
    "",
    response_model=ProfileResponse,
    summary="Обновить профиль",
    description="Обновите информацию в профиле текущего пользователя.",
    responses={
        200: {"description": "Профиль успешно обновлен."},
        400: {"model": ErrorResponse, "description": "Ошибка проверки"},
        401: {"model": ErrorResponse, "description": "Не подтверждено"},
    },
)
async def update_profile(
    request: ProfileUpdateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProfileService(session)
    profile = await service.update_profile(current_user, request)
    return profile


@router.post(
    "/change-password",
    summary="Изменить пароль",
    description="Изменить пароль текущего пользователя.",
    responses={
        200: {"description": "Пароль успешно изменен."},
        400: {"model": ErrorResponse, "description": "Ошибка проверки"},
        401: {"model": ErrorResponse, "description": "Не подтверждено"},
    },
)
async def change_password(
    request: ChangePasswordRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProfileService(session)
    return await service.change_password(current_user, request)


@router.post(
    "/logout",
    summary="Выйти из профиля",
    description="Выйти из системы текущего пользователя.",
    responses={
        200: {"description": "Выход из системы пройден успешно."},
        401: {"model": ErrorResponse, "description": "Не подтверждено"},
    },
)
async def logout(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProfileService(session)
    return await service.logout(current_user)
