import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from database.queries import AdQueries, FavoriteQueries
from api.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class FavoriteBody(BaseModel):
    ad_id: int


@router.get("/")
async def list_favorites(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ads = await FavoriteQueries.get_user_favorites(db, user["id"])
    items = []
    for ad in ads:
        items.append({
            "id": ad.id,
            "brand": ad.brand,
            "model": ad.model,
            "year": ad.year,
            "price": ad.price,
            "mileage": ad.mileage,
            "engine_type": ad.engine_type,
            "transmission": ad.transmission,
            "photos": json.loads(ad.photos) if ad.photos else [],
            "views_count": ad.views_count,
        })
    return items


@router.post("/")
async def add_favorite(
    body: FavoriteBody,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ad = await AdQueries.get_ad_by_id(db, body.ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    ok = await FavoriteQueries.add_favorite(db, user["id"], body.ad_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Уже в избранном")
    return {"status": "added"}


@router.delete("/{ad_id}")
async def remove_favorite(
    ad_id: int,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await FavoriteQueries.remove_favorite(db, user["id"], ad_id)
    return {"status": "removed"}
