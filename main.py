from fastapi import FastAPI
from api.endpoints import auth, categories, profile, projects, tasks

app = FastAPI(title="Multitasker API", version="1.0.0")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(profile.router, prefix="/api/users", tags=["profile"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])