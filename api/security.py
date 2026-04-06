import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# Используем argon2 вместо bcrypt (нет ограничения 72 байта)
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

SECRET_KEY = os.getenv("JWT_SECRET", "5QY7Nnt17PEDparg6DPV4RTI8sAcYCbn")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


def create_access_token(user_id: int) -> str:
    """Создание JWT токена"""
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": str(user_id), "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_user_id(token: str) -> Optional[int]:
    """Декодирование user_id из токена"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except JWTError:
        return None
