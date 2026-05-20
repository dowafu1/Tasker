from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from api.deps import get_db
from schemas.user import UserCreate, UserResponse
from services.auth import AuthService
from repositories.user import UserRepository

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(UserRepository(db))
    return await auth_service.register(user_data)

@router.post("/login")
async def login(email: str, password: str, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(UserRepository(db))
    token = await auth_service.login(email, password)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/password-reset/request")
async def request_password_reset(email: str, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(UserRepository(db))
    await auth_service.request_password_reset(email)
    return {"message": "Password reset code sent"}

@router.post("/password-reset/verify")
async def verify_password_reset(code: str, new_password: str, confirm_password: str, db: AsyncSession = Depends(get_db)):
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    auth_service = AuthService(UserRepository(db))
    await auth_service.verify_password_reset(code, new_password)
    return {"message": "Password reset successful"}