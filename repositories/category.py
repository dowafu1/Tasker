from repositories.base import BaseRepository
from models.category import Category

class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db):
        super().__init__(Category, db)

    async def get_by_user(self, user_id: int):
        from sqlalchemy import select
        result = await self.db.execute(select(Category).where(Category.user_id == user_id))
        return result.scalars().all()