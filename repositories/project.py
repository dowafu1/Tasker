from repositories.base import BaseRepository
from models.project import Project

class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db):
        super().__init__(Project, db)

    async def get_by_user(self, user_id: int):
        from sqlalchemy import select
        result = await self.db.execute(select(Project).where(Project.user_id == user_id))
        return result.scalars().all()

    async def get_by_category(self, category_id: int):
        from sqlalchemy import select
        result = await self.db.execute(select(Project).where(Project.category_id == category_id))
        return result.scalars().all()