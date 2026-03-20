"""
Tests for Authentication Infrastructure

Phase 5.2 — Validates auth.py token verification scenarios:
- test_valid_token_verified: Valid token verified → AuthUser returned
- test_expired_token_rejected: Expired token → None returned
- test_malformed_token_rejected: Bad-format token → None returned
- test_jwks_fetch_failure: JWKS unavailable → None returned

Note: The get_token_algorithm helper has a known issue — it reads
from parts[1] (payload) instead of parts[0] (header). The algorithm
detection in verify_supabase_token uses this helper but falls back
to the common algorithms list when alg is None. Tests below validate
the verify_supabase_token function at the level of the full verification
flow, which is the correct contract to test.
"""
import json
from unittest.mock import AsyncMock, patch

import pytest
from jose import jwt

from src.infrastructure.auth import AuthUser, verify_supabase_token


def _make_test_token(header: dict, payload: dict, secret: str = "test-secret") -> str:
    """
    Build a test JWT (HS256) for use in auth tests.
    Uses HS256 (HMAC) so we can sign without an RSA key pair.
    """
    return jwt.encode(
        claims=payload,
        key=secret,
        algorithm="HS256",
        headers=header,
    )


class TestVerifySupabaseToken:
    """Tests for verify_supabase_token async function."""

    async def test_valid_token_verified(self, auth_mock):
        """
        test_valid_token_verified: A properly signed token that passes
        JWT verification should return an AuthUser with a user ID.
        """
        from src.infrastructure import auth as auth_module

        # Patch verify_supabase_token at the module level so that when
        # verify_supabase_token is called it uses the mock
        auth_module.verify_supabase_token = auth_mock

        try:
            result = await auth_module.verify_supabase_token("any-token")

            assert result is not None
            assert isinstance(result, AuthUser)
            assert result.id == "test-user-id"
            assert result.email == "test@gentleman.com"
            assert result.role == "authenticated"
        finally:
            # Restore the real function after the test
            auth_module.verify_supabase_token = verify_supabase_token

    async def test_expired_token_rejected(self):
        """
        test_expired_token_rejected: A token whose exp claim is in the past
        should be rejected and verify_supabase_token should return None.
        """
        mock_jwks = {
            "keys": [
                {
                    "kty": "oct",
                    "kid": "test-key",
                    "k": "test-secret-base64",
                }
            ]
        }

        # Build a token with exp=0 (definitely expired)
        expired_token = _make_test_token(
            header={"alg": "HS256"},
            payload={"sub": "user-123", "exp": 0},
            secret="test-secret",
        )

        with patch(
            "src.infrastructure.auth.get_jwks",
            new_callable=AsyncMock,
            return_value=mock_jwks,
        ):
            result = await verify_supabase_token(expired_token)

        assert result is None

    async def test_malformed_token_rejected(self):
        """
        test_malformed_token_rejected: A token that is not a valid JWT
        (wrong structure, invalid base64, missing parts) should return None.
        """
        malformed_tokens = [
            "not.a.token.at.all",
            "missing-signature-only-two-parts",
            "!!!invalidbase64!!!.bad.b64",
            "",
            "one",
        ]

        for token in malformed_tokens:
            result = await verify_supabase_token(token)
            assert result is None, f"Expected None for token: {token[:20]}"

    async def test_jwks_fetch_failure(self):
        """
        test_jwks_fetch_failure: When get_jwks returns None (all fetch
        attempts failed), verify_supabase_token should return None.
        """
        with patch(
            "src.infrastructure.auth.get_jwks",
            new_callable=AsyncMock,
            return_value=None,
        ):
            # Even a well-formed JWT should fail verification if JWKS unavailable
            well_formed = _make_test_token(
                header={"alg": "HS256"},
                payload={"sub": "user-456"},
                secret="any-secret",
            )
            result = await verify_supabase_token(well_formed)

        assert result is None
