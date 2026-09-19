"""Unit tests for security utilities: hashing and JWT tokens."""

from datetime import timedelta
import pytest
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_password_hashing_and_verification():
    raw_password = "SecretPassword123!"
    hashed = get_password_hash(raw_password)

    assert hashed != raw_password
    assert hashed.startswith("pbkdf2:sha256:")
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password("", hashed) is False


def test_jwt_create_and_decode():
    sub = "user-uuid-12345"
    role = "reviewer"
    token = create_access_token(subject=sub, role=role)

    assert isinstance(token, str)
    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == sub
    assert payload["role"] == role
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_expired_token():
    sub = "user-uuid-expired"
    # Create token already expired in the past
    token = create_access_token(
        subject=sub,
        expires_delta=timedelta(seconds=-10),
    )

    payload = decode_access_token(token)
    assert payload is None


def test_jwt_invalid_token():
    assert decode_access_token("invalid.token.structure") is None
    assert decode_access_token("") is None
