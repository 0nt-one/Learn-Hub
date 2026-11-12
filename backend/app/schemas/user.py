from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer, model_validator


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

class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["student", "teacher", "admin"] | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def require_actual_change(self) ->"UserUpdateRequest":
        if not self.model_fields_set:
            raise ValueError("至少提交 role 或 is_active")
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} 不能为 null")
        return self

class UserEnvelope(BaseModel):
    data: UserPublic
    request_id: str

class UserListData(BaseModel):
    items: list[UserPublic]
    total: int
    page: int
    page_size: int

class UserListEnvelope(BaseModel):
    data: UserListData
    request_id: str