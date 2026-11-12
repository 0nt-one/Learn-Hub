from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_serializer


class OperationLogPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: int
    action: str
    target_type: str
    target_id: int
    request_id: str
    summary: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_utc(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class OperationLogListData(BaseModel):
    items: list[OperationLogPublic]
    total: int
    page: int
    page_size: int


class OperationLogListEnvelope(BaseModel):
    data: OperationLogListData
    request_id: str
