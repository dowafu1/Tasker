from pydantic import BaseModel

class User(BaseModel):
    id: int
    email: str
    password_hash: str
    created_at: datetime = datetime.utcnow()