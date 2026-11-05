from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import Settings

JWT_ALGORITHM = "HS256"
JWT_ISSUER = "learn-hub"
JWT_AUDIENCE = "learn-hub-api"
ACCESS_TOKEN_EXPIRE_SECONDS = 30 * 60

def create_access_token(user_id: int, settings: Settings) -> tuple[str, int]:
    if settings.jwt_secret_key is None:
        raise ValueError("JWT_SECRET_KEY is required")

    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS)

    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": expires_at,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
    }

    access_token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=JWT_ALGORITHM,
    )
    return access_token, ACCESS_TOKEN_EXPIRE_SECONDS


class InvalidAccessTokenError(Exception):
    pass


def decode_access_token(access_token: str, settings: Settings) -> int:
    if settings.jwt_secret_key is None:
        raise ValueError("JWT_SECRET_KEY is required")

    try:
        claims = jwt.decode(
            access_token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
            options={"require": ["sub", "iat", "exp", "iss", "aud"]},
        )
    except jwt.InvalidTokenError as exc:
        raise InvalidAccessTokenError from exc

    try:
        user_id = int(claims["sub"])
    except (TypeError, ValueError) as exc:
        raise InvalidAccessTokenError from exc

    if user_id <= 0:
        raise InvalidAccessTokenError

    return user_id
