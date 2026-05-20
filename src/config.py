from pydantic import BaseSettings

class AppConfig(BaseSettings):
    DATABASE_URL: str = 'postgresql+asyncpg://user:password@localhost/task_manager'
    SECRET_KEY: str = 'your_secret_key_here'
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

app_config = AppConfig()