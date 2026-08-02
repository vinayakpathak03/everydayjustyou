from dataclasses import dataclass

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException

from app.core import security
from app.core.security import get_current_user

# Supabase now signs JWTs with rotatable ES256 keys verified via JWKS, not a
# static shared secret — see app/core/security.py's docstring. These tests
# generate a real EC keypair and stub out the JWKS *lookup* (network call),
# not the cryptographic verification itself, so a wrong-key/tampered token
# still has to fail signature verification for real.

_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())
_OTHER_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())


@dataclass
class _FakeSigningKey:
    key: object


class _FakeJWKClient:
    def get_signing_key_from_jwt(self, _token: str) -> _FakeSigningKey:
        return _FakeSigningKey(key=_PRIVATE_KEY.public_key())


@pytest.fixture(autouse=True)
def _stub_jwks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(security, "_jwks_client", lambda: _FakeJWKClient())


def _token(private_key=_PRIVATE_KEY, **claims) -> str:
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "aud": "authenticated",
        "role": "authenticated",
    }
    payload.update(claims)
    return jwt.encode(payload, private_key, algorithm="ES256")


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
    # Signed with a DIFFERENT key than the one the (stubbed) JWKS lookup
    # returns — must fail real ES256 signature verification, not just claims
    # parsing.
    bad_token = _token(private_key=_OTHER_PRIVATE_KEY)
    with pytest.raises(HTTPException) as exc:
        await get_current_user(authorization=f"Bearer {bad_token}")
    assert exc.value.status_code == 401
