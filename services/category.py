from repositories.category import CategoryRepository
from schemas.category import CategoryCreate, CategoryUpdate

class CategoryService:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    async def get_categories(self, user_id: int):
        return await self.category_repo.get_by_user(user_id)

    async def create_category(self, user_id: int, data: CategoryCreate):
        return await self.category_repo.create(user_id=user_id, **data.dict())

    async def update_category(self, category_id: int, data: CategoryUpdate):
        return await self.category_repo.update(category_id, **data.dict())

    async def delete_category(self, category_id: int):
        return await self.category_repo.delete(category_id)