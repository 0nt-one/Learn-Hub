from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_serializer


class NotificationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    review_record_id: int | None
    # 审核类通知关联的资源：查询时从 review_records 反查，不加库字段
    resource_id: int | None = None
    resource_title: str | None = None
    kind: str
    title: str
    content: str
    read_at: datetime | None
    created_at: datetime

    @field_serializer("read_at", "created_at")
    def serialize_utc(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class NotificationEnvelope(BaseModel):
    data: NotificationPublic
    request_id: str


class NotificationListData(BaseModel):
    items: list[NotificationPublic]
    total: int
    page: int
    page_size: int


class NotificationListEnvelope(BaseModel):
    data: NotificationListData
    request_id: str
