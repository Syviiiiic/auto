import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image
from io import BytesIO

from api.dependencies import get_current_user

router = APIRouter()

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
MAX_BYTES = 10 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Допустимы только JPEG, PNG, WebP")
    raw = await file.read()
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="Файл больше 10 МБ")
    try:
        Image.open(BytesIO(raw)).verify()
    except Exception:
        raise HTTPException(status_code=400, detail="Некорректное изображение")

    ext = { "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp" }[file.content_type]
    name = f"{uuid.uuid4().hex}{ext}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = UPLOAD_DIR / name
    path.write_bytes(raw)

    return {"url": f"/media/{name}"}
