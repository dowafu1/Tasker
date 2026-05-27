"""Бизнес логика профиля пользователя."""

import logging
from typing import Optional

from fastapi import HTTPException, status

from src.repositories import (
    UserRepository,
    RefreshTokenRepository,
)
from src.models.user import User
from src.core.security import (
    verify_password,
    get_password_hash,
)
from src.schemas import (
    ProfileUpdateRequest,
    ChangePasswordRequest,
)


logger = logging.getLogger(__name__)


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
