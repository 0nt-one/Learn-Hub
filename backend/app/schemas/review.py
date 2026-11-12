from typing import Literal
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator

from app.schemas.resource import ResourcePublic


class ReviewCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(gt=0)
    decision: Literal["approved", "rejected"]
    comment: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def require_rejection_comment(self) -> "ReviewCreateRequest":
        self.comment = self.comment.strip()
        if self.decision == "rejected" and not self.comment:
            raise ValueError("拒绝资源时必须填写审核意见")
        return self


class ReviewPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_id: int
    reviewer_id: int
    resource_version: int
    decision: Literal["approved", "rejected"]
    comment: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_utc(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class ReviewResult(BaseModel):
    review: ReviewPublic
    resource: ResourcePublic


class ReviewEnvelope(BaseModel):
    data: ReviewResult
    request_id: str


class ReviewListData(BaseModel):
    items: list[ReviewPublic]
    total: int
    page: int
    page_size: int


class ReviewListEnvelope(BaseModel):
    data: ReviewListData
    request_id: str
