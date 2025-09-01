from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.enums import ReportStatusTypes


class ReportSchema(BaseModel):
    id: int
    from_user_id: UUID
    to_user_id: UUID
    reason: str
    status: ReportStatusTypes
    created_at: datetime
    updated_at: datetime
