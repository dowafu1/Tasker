from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.deps import get_current_user, get_db
from models.user import User
from schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from services.category import CategoryService
from repositories.category import CategoryRepository

router = APIRouter()

@router.get("/", response_model=list[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = CategoryService(CategoryRepository(db))
    return await service.get_categories(current_user.id)

@router.post("/", response_model=CategoryResponse)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = CategoryService(CategoryRepository(db))
    return await service.create_category(current_user.id, data)

@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: int, data: CategoryUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = CategoryService(CategoryRepository(db))
    return await service.update_category(category_id, data)

@router.delete("/{category_id}")
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = CategoryService(CategoryRepository(db))
    await service.delete_category(category_id)
    return {"message": "Category deleted"}