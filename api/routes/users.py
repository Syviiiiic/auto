from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from database.queries import AdQueries, UserQueries
from api.dependencies import get_current_user

router = APIRouter()


class UserUpdate(BaseModel):
    first_name: str | None = Field(None, max_length=255)
    last_name: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=20)


@router.get("/stats")
async def user_stats(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AdQueries.get_user_stats(db, user["id"])


@router.put("/")
async def update_user(
    body: UserUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await UserQueries.update_profile(
        db,
        user["id"],
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
    )
    return {"status": "ok"}
