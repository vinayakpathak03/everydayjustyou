import jwt
import pytest
from fastapi import HTTPException

from app.core.security import get_current_user


def _token(secret: str = "test-secret", **claims) -> str:
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "aud": "authenticated",
        "role": "authenticated",
    }
    payload.update(claims)
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.mark.asyncio
async def test_valid_token_resolves_user() -> None:
    user = await get_current_user(authorization=f"Bearer {_token(email='a@example.com')}")
    assert user.id == "11111111-1111-1111-1111-111111111111"
    assert user.email == "a@example.com"
    assert user.role == "authenticated"


@pytest.mark.asyncio
async def test_missing_header_rejected() -> None:
    with pytest.raises(HTTPException) as exc:
        await get_current_user(authorization=None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_bad_signature_rejected() -> None:
    bad_token = _token(secret="wrong-secret")
    with pytest.raises(HTTPException) as exc:
        await get_current_user(authorization=f"Bearer {bad_token}")
    assert exc.value.status_code == 401
