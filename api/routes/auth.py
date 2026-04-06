import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from database.queries import UserQueries
from api.dependencies import get_current_user
from api.security import create_access_token, hash_password, verify_password

router = APIRouter()
logger = logging.getLogger(__name__)


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str | None = Field(None, max_length=255)
    last_name: str | None = Field(None, max_length=255)


class LoginBody(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


@router.post("/register")
async def register(body: RegisterBody, db: AsyncSession = Depends(get_db)):
    try:
        email_norm = body.email.lower().strip()
        if await UserQueries.get_by_email(db, email_norm):
            raise HTTPException(status_code=400, detail="Этот email уже зарегистрирован")
        
        ph = hash_password(body.password)
        user = await UserQueries.create_user(
            db,
            email=email_norm,
            password_hash=ph,
            first_name=body.first_name,
            last_name=body.last_name,
        )
        token = create_access_token(user.id)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": _user_public(user),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка регистрации")


@router.post("/login")
async def login(body: LoginBody, db: AsyncSession = Depends(get_db)):
    try:
        email_norm = body.email.lower().strip()
        user = await UserQueries.get_by_email(db, email_norm)
        if not user or not user.password_hash:
            raise HTTPException(status_code=401, detail="Неверный email или пароль")
        if not verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Неверный email или пароль")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Аккаунт отключён")
        
        token = create_access_token(user.id)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": _user_public(user),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка входа")


def _user_public(user):
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_admin": user.is_admin,
    }


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return user
