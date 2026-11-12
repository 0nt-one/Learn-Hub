from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas.resource import ResourcePublic


class FavoritePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resource_id: int
    created_at: datetime

    @field_serializer("created_at")
    def serialize_utc(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class FavoriteEnvelope(BaseModel):
    data: FavoritePublic
    request_id: str


class FavoriteListItem(FavoritePublic):
    resource: ResourcePublic | None


class FavoriteListData(BaseModel):
    items: list[FavoriteListItem]
    total: int
    page: int
    page_size: int


class FavoriteListEnvelope(BaseModel):
    data: FavoriteListData
    request_id: str


class FavoriteDeleteData(BaseModel):
    resource_id: int
    favorited: bool = False


class FavoriteDeleteEnvelope(BaseModel):
    data: FavoriteDeleteData
    request_id: str
