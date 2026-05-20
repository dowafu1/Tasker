from repositories.task import TaskRepository
from schemas.task import TaskCreate, TaskUpdate, TaskComplete
from datetime import date

class TaskService:
    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo

    async def get_assigned_tasks(self, user_id: int, completed: bool = None):
        return await self.task_repo.get_by_assignee(user_id, completed)

    async def get_task(self, task_id: int):
        return await self.task_repo.get(task_id)

    async def complete_task(self, task_id: int, data: TaskComplete):
        return await self.task_repo.update(task_id, is_completed=data.is_completed)

    async def create_task(self, author_id: int, data: TaskCreate):
        return await self.task_repo.create(author_id=author_id, **data.dict())

    async def get_tasks_by_date(self, user_id: int, date: date):
        from sqlalchemy import select
        return []
    
# Добавить update