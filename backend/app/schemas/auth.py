from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.user import UserPublic


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^[A-Za-z0-9_]+$",
    )
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(
        min_length=1,
        max_length=64,
    )
    @field_validator("username",mode="before")
    @classmethod
    def normalize_username(cls, value:object) -> object:
        if isinstance(value,str):
            return value.strip().lower()
        return value

class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str

    @field_validator("username",mode="before")
    @classmethod
    def normalize_username(cls, value:object) -> object:
        if isinstance(value,str):
            return value.strip().lower()
        return value

class TokenPublic(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic

class TokenEnvelope(BaseModel):
    data: TokenPublic
    request_id: str