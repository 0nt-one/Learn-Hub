from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class LearningProgressRequest(BaseModel):
    """PUT /users/me/learning-records/{resource_id} 的请求体。

    契约只允许一个字段 progress（0–100 的整数），多余字段直接拒绝。
    """

    model_config = ConfigDict(extra="forbid")

    progress: int = Field(ge=0, le=100)


class LearningRecordPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_id: int
    progress: int
    last_accessed_at: datetime
    created_at: datetime
    updated_at: datetime

    @field_serializer("last_accessed_at", "created_at", "updated_at")
    def serialize_utc(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class LearningRecordEnvelope(BaseModel):
    data: LearningRecordPublic
    request_id: str


class LearningRecordResource(BaseModel):
    """学习记录里对资源的引用（不是完整的 ResourcePublic）。

    与收藏的差别是刻意的：收藏是"我还想再看"的清单，资源没了就该提示失效；
    学习记录是"我学过什么"的历史，资源下架后仍要能认出学过哪一份。
    所以这里**始终**返回标题等识别信息，只在资源不再公开时把 url 置为 null。
    """

    id: int
    title: str
    resource_type: Literal["document", "video", "link"]
    course_id: int
    course_title: str
    category_id: int
    category_name: str
    status: str
    # 资源当前是否仍可公开访问；false 时 url 为 None
    is_available: bool
    url: str | None


class LearningRecordListItem(LearningRecordPublic):
    resource: LearningRecordResource


class LearningRecordListData(BaseModel):
    items: list[LearningRecordListItem]
    total: int
    page: int
    page_size: int


class LearningRecordListEnvelope(BaseModel):
    data: LearningRecordListData
    request_id: str
