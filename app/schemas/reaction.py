from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.enums import ReactionType


class ReactionInSchema(BaseModel):
    to_user_id: UUID
    reaction_type: ReactionType


class ReactionSchema(ReactionInSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    is_match_notified: bool
