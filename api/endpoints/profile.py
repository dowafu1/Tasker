from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.deps import get_current_user, get_db
from models.user import User
from schemas.user import UserResponse, UserUpdate, ChangePassword
from services.user import UserService
from repositories.user import UserRepository

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_profile(data: UserUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = UserService(UserRepository(db))
    return await service.update_profile(current_user.id, data)

@router.post("/me/change-password")
async def change_password(data: ChangePassword, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = UserService(UserRepository(db))
    await service.change_password(current_user.id, data)
    return {"message": "Password changed"}