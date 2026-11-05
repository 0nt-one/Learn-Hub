from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import Settings
from app.core.tokens import (
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
)


TEST_SECRET = "test-only-secret-key-for-tokens-1234"


def test_created_token_returns_user_id() -> None:
    settings = Settings(
        _env_file=None,
        database_url="sqlite:///:memory:",
        jwt_secret_key=TEST_SECRET,
    )

    access_token, expires_in = create_access_token(42, settings)

    assert expires_in == 1800
    assert decode_access_token(access_token, settings) == 42


def test_token_signed_with_another_key_is_rejected() -> None:
    settings = Settings(
        _env_file=None,
        database_url="sqlite:///:memory:",
        jwt_secret_key=TEST_SECRET,
    )
    access_token, _ = create_access_token(42, settings)

    other_settings = Settings(
        _env_file=None,
        database_url="sqlite:///:memory:",
        jwt_secret_key="another-test-secret-key-for-tokens-1234",
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(access_token, other_settings)


def test_expired_token_is_rejected() -> None:
    settings = Settings(
        _env_file=None,
        database_url="sqlite:///:memory:",
        jwt_secret_key=TEST_SECRET,
    )
    issued_at = datetime.now(timezone.utc) - timedelta(hours=1)
    expired_at = issued_at + timedelta(minutes=30)

    expired_token = jwt.encode(
        {
            "sub": "42",
            "iat": issued_at,
            "exp": expired_at,
            "iss": "learn-hub",
            "aud": "learn-hub-api",
        },
        TEST_SECRET,
        algorithm="HS256",
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(expired_token, settings)