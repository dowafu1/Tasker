"""Бизнес логика аутентификации."""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status

from src.repositories import (
    UserRepository,
    RefreshTokenRepository,
    PasswordResetCodeRepository,
)
from src.models.user import User
from src.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from src.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    ForgotPasswordRequest,
    VerifyCodeRequest,
    ResetPasswordRequest,
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
