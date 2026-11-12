from datetime import datetime, timezone

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

class CourseCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code:str = Field(
        min_length=1,
        max_length=32,
        pattern=r"^[A-Z0-9-]+$",
    )
    title:str = Field(
        min_length=1,
        max_length=200,
    )
    description:str = Field(
        default="",
        max_length=5000
    )
    teacher_id: int | None = Field(default=None, gt=0)

    @field_validator('code',mode='before')
    @classmethod
    def normalize_code(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator('title',mode='before')
    @classmethod
    def strip_title(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class CourseUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=32,
        pattern=r"^[A-Z0-9-]+$",
    )
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    is_active: bool | None = None
    teacher_id: int | None = Field(default=None, gt=0)

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def require_actual_change(self) -> "CourseUpdateRequest":
        if not self.model_fields_set:
            raise ValueError("至少提交一个修改字段")
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} 不能为 null")
        return self


class CoursePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    description: str
    teacher_id: int
    teacher_display_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_utc(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class CourseEnvelope(BaseModel):
    data: CoursePublic
    request_id: str


class CourseListData(BaseModel):
    items: list[CoursePublic]
    total: int
    page: int
    page_size: int


class CourseListEnvelope(BaseModel):
    data: CourseListData
    request_id: str
