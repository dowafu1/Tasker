import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.core.database import init_db, close_db
from src.routers.auth_router import router as auth_router
from src.routers.profile_router import router as profile_router
from src.routers.project_router import router as project_router
from src.routers.task_router import router as task_router


logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск Task Manager API...")
    await init_db()
    logger.info("БД инициализована")
    
    yield
    
    logger.info("Останавливается Task Manager API...")
    await close_db()
    logger.info("Подключение к БД закрыто")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## API менеджера задач

Комплексная панель управления задачами, включающая:

### Аутентификация и авторизация
- Регистрация и вход пользователей с помощью JWT-токенов
- Восстановление пароля с помощью кодов электронной почты
- Обновление токенов

### Управление профилем
- Просмотр и обновление профиля пользователя
- Смена пароля
- Поддержка загрузки аватара

### Проекты
- Создание, обновление и удаление проектов
- Владение проектом и контроль доступа

### Задачи
- Назначенные задачи с фильтрацией и пагинацией
- Отслеживание выполнения задач
- Интеграция с календарем

### Календарь
- Ежемесячный календарь с маркерами задач
- Ежедневный просмотр задач с фильтрами
- Создание задач из календаря

**Важность:**
- Критический (очень срочно)
- Высокий (срочно)
- Средний (может учитывать)
- Низкий (несрочно)
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Ошибка срвера",
            "code": "INTERNAL_ERROR",
        },
    )


app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(project_router)
app.include_router(task_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "Здоровый"}
