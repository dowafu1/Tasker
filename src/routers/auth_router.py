from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from pydantic import BaseModel
import asyncio
from .services.auth_service import AuthService

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/api/v1/auth/register", response_model=Token)
async def register(request: Request, email: str = Form(...), password: str = Form(...), password_confirm: str = Form(...), accept_terms: bool = Form(...)):
    auth_service = AuthService()
    user = await auth_service.register_user(email, password, password_confirm, accept_terms)
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/api/v1/auth/login", response_model=Token)
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    auth_service = AuthService()
    user = await auth_service.login_user(email, password)
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/api/v1/auth/logout", response_model=dict)
async def logout(request: Request):
    # Implement logout logic
    pass

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, app_config.SECRET_KEY, algorithm=app_config.ALGORITHM)
    return encoded_jwt

class TokenData(BaseModel):
    user_id: int