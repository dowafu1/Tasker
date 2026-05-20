from repositories.base import BaseRepository
from models.user import User

class UserRepository(BaseRepository[User]):
    def __init__(self, db):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> User | None:
        from sqlalchemy import select
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()