from datetime import datetime

from pydantic import BaseModel

from app.enums import FileTypes


class FileInSchema(BaseModel):
    telegram_id: str | None = None
    telegram_unique_id: str | None = None
    file_type: FileTypes
    file_size: int | None = None
    mime_type: str | None = None
    thumbnail: "FileInSchema | None" = None
    duration: int | None = None


class FileSchema(BaseModel):
    id: int
    telegram_id: str | None = None
    telegram_unique_id: str | None = None
    file_type: FileTypes
    file_size: int | None = None
    mime_type: str | None = None
    duration: int | None = None
    uploaded_at: datetime
    path: str | None
    thumbnail: "FileSchema | None" = None
