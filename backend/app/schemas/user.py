from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    role: Literal["student", "teacher", "admin"]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # 数据库时间按UTC存储
    @field_serializer("created_at", "updated_at")
    def serialize_utc(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class UserEnvelope(BaseModel):
    data: UserPublic
    request_id: str
