from repositories.base import BaseRepository
from models.task import Task

class TaskRepository(BaseRepository[Task]):
    def __init__(self, db):
        super().__init__(Task, db)

    async def get_by_assignee(self, assignee_id: int, completed: bool = False):
        from sqlalchemy import select
        query = select(Task).where(Task.assignee_id == assignee_id)
        if completed is not None:
            query = query.where(Task.is_completed == completed)
        result = await self.db.execute(query)
        return result.scalars().all()