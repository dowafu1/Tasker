from repositories.user import UserRepository
from schemas.user import UserUpdate, ChangePassword
from fastapi import HTTPException, status

class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_profile(self, user_id: int):
        user = await self.user_repo.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def update_profile(self, user_id: int, data: UserUpdate):
        # Заглушка
        return await self.user_repo.update(user_id, **data.dict(exclude_unset=True))

    async def change_password(self, user_id: int, data: ChangePassword):
        # Заглушка
        pass