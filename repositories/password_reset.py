from repositories.base import BaseRepository
from models.password_reset import PasswordReset

class PasswordResetRepository(BaseRepository[PasswordReset]):
    def __init__(self, db):
        super().__init__(PasswordReset, db)