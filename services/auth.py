from repositories.user import UserRepository
from schemas.user import UserCreate, UserResponse
from core.security import get_password_hash, verify_password, create_access_token
from fastapi import HTTPException, status

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, user_data: UserCreate) -> UserResponse:
        if user_data.password != user_data.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        existing = await self.user_repo.get_by_email(user_data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed = get_password_hash(user_data.password)
        user = await self.user_repo.create(
            email=user_data.email,
            hashed_password=hashed,
            name=None,
            avatar_url=None,
            agreed_to_privacy=False,
            agreed_to_terms=False
        )
        return user

    async def login(self, email: str, password: str) -> str:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token({"sub": str(user.id)})
        return token

    async def request_password_reset(self, email: str):
        pass

    async def verify_password_reset(self, code: str, new_password: str):
        pass