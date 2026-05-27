import asyncio
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import BaseModel
from src.models.user import User

class AuthService:
    async def register_user(self, email: str, password: str, password_confirm: str, accept_terms: bool):
        pass

    async def login_user(self, email: str, password: str):
        pass