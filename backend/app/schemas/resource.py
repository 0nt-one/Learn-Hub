from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, model_validator


class ResourceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    resource_type: Literal["document", "video", "link"]
    url: str = Field(min_length=1, max_length=2048)
    duration_seconds: int | None = Field(default=None, gt=0)
    page_count: int | None = Field(default=None, gt=0)
    course_id: int = Field(gt=0)
    category_id: int = Field(gt=0)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("url")
    @classmethod
    def require_https_url(cls, value: str) -> str:
        try:
            parsed = urlsplit(value)
            _ = parsed.port
        except ValueError as exc:
            raise ValueError("资源 URL 格式无效") from exc
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or any(character.isspace() for character in value)
        ):
            raise ValueError("资源 URL 必须是无用户名密码的 HTTPS 地址")
        return value


class ResourcePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    resource_type: Literal["document", "video", "link"]
    url: str
    duration_seconds: int | None
    page_count: int | None
    course_id: int
    course_title: str
    course_teacher_id: int
    course_teacher_display_name: str
    category_id: int
    category_name: str
    owner_id: int
    owner_display_name: str
    is_favorited: bool
    status: str
    version_id: int
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_utc(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class ResourceEnvelope(BaseModel):
    data: ResourcePublic
    request_id: str


class ResourceListData(BaseModel):
    items: list[ResourcePublic]
    total: int
    page: int
    page_size: int

class ResourceListEnvelope(BaseModel):
    data: ResourceListData
    request_id: str

class ResourceSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(gt=0)


class ResourceWithdrawRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(gt=0)


class ResourceArchiveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(gt=0)
    reason: str = Field(min_length=1, max_length=2000)

    @field_validator("reason", mode="before")
    @classmethod
    def strip_reason(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class ResourceUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(gt=0)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    resource_type: Literal["document", "video", "link"] | None = None
    url: str | None = Field(default=None, min_length=1, max_length=2048)
    duration_seconds: int | None = Field(default=None, gt=0)
    page_count: int | None = Field(default=None, gt=0)
    course_id: int | None = Field(default=None, gt=0)
    category_id: int | None = Field(default=None, gt=0)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def require_change(self) -> "ResourceUpdateRequest":
        changed = self.model_fields_set - {"expected_version"}
        if not changed:
            raise ValueError("至少提交一个修改字段")
        for field_name in changed - {"duration_seconds", "page_count"}:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} 不能为 null")
        return self
