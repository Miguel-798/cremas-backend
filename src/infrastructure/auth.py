"""
Authentication - Infrastructure Layer

JWT verification and Supabase auth integration.
"""
import asyncio
from dataclasses import dataclass
from typing import Optional
import httpx
import base64
import json

from jose import jwt, JWTError
from cachetools import TTLCache

from src.infrastructure.config import settings
from src.infrastructure.logging import get_logger

log = get_logger(__name__)

# JWKS in-memory cache with TTL
jwks_cache: Optional[TTLCache] = None


def get_jwks_cache() -> TTLCache:
    """Get or create the JWKS cache with TTL."""
    global jwks_cache
    if jwks_cache is None:
        jwks_cache = TTLCache(maxsize=1, ttl=settings.jwks_cache_ttl)
    return jwks_cache


def _safe_token_log(token: str) -> str:
    """Log token safely - only first 10 chars + '...'"""
    return token[:10] + "..." if len(token) > 10 else token


@dataclass
class AuthUser:
    """Authenticated user from JWT token."""
    id: str
    email: Optional[str] = None
    role: Optional[str] = None
    raw_token: Optional[str] = None

    @property
    def is_authenticated(self) -> bool:
        return self.id is not None


def get_token_algorithm(token: str) -> Optional[str]:
    """Extract the algorithm from a JWT token header."""
    try:
        parts = token.split('.')
        if len(parts) < 2:
            return None
        # Add padding if needed
        payload = parts[1] + '=' * (4 - len(parts[1]) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        header = json.loads(decoded)
        return header.get('alg')
    except Exception as e:
        log.warning("auth.algorithm_extract_failed", error=str(e))
        return None


async def fetch_jwks_with_retry(client: httpx.AsyncClient, url: str) -> Optional[dict]:
    """
    Fetch JWKS with retry and exponential backoff.
    
    Retry 3 times with exponential backoff (1s, 2s, 4s).
    """
    max_retries = 3
    base_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            log.debug("auth.jwks_fetch_attempt", endpoint=url, attempt=attempt + 1)
            response = await client.get(
                url, 
                timeout=settings.jwks_fetch_timeout
            )
            if response.status_code == 200:
                jwks = response.json()
                log.info("auth.jwks_fetched", endpoint=url, key_count=len(jwks.get("keys", [])))
                return jwks
            else:
                log.warning(
                    "auth.jwks_fetch_http_error",
                    endpoint=url,
                    status_code=response.status_code
                )
        except httpx.TimeoutException:
            log.warning("auth.jwks_fetch_timeout", endpoint=url, attempt=attempt + 1)
        except Exception as e:
            log.warning("auth.jwks_fetch_error", endpoint=url, attempt=attempt + 1, error=str(e))
        
        if attempt < max_retries - 1:
            delay = base_delay * (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
            log.debug("auth.jwks_retry_delay", delay=delay)
            await asyncio.sleep(delay)
    
    return None


async def get_jwks() -> Optional[dict]:
    """
    Get JWKS from cache or fetch from Supabase.
    
    Uses in-memory cache with TTL. If fetch fails and no cache, returns None.
    """
    cache = get_jwks_cache()
    
    # Check cache first
    if "jwks" in cache:
        log.debug("auth.jwks_cache_hit")
        return cache["jwks"]
    
    log.debug("auth.jwks_cache_miss")
    
    jwks_endpoints = [
        f"{settings.supabase_url}/auth/v1/jwks",
        f"{settings.supabase_url}/auth/v1/.well-known/jwks.json",
    ]
    
    async with httpx.AsyncClient() as client:
        jwks = None
        for url in jwks_endpoints:
            jwks = await fetch_jwks_with_retry(client, url)
            if jwks:
                break
        
        if jwks:
            cache["jwks"] = jwks
            return jwks
        else:
            log.error("auth.jwks_fetch_all_failed", endpoints=jwks_endpoints)
            return None


async def verify_supabase_token(token: str) -> Optional[AuthUser]:
    """
    Verify a Supabase JWT token.
    
    Supabase tokens are RS256 JWTs signed with the Supabase project's keys.
    We verify against Supabase's JWKS endpoint.
    
    Args:
        token: The JWT token string
        
    Returns:
        AuthUser if valid, None if invalid
    """
    if not token:
        log.warning("auth.token_missing")
        return None
    
    log.debug("auth.token_verifying", token_prefix=_safe_token_log(token))
    
    # First, check what algorithm the token uses
    alg = get_token_algorithm(token)
    log.debug("auth.token_algorithm", algorithm=alg)
    
    # Get JWKS (from cache or fetch)
    jwks = await get_jwks()
    
    if not jwks:
        log.error("auth.jwks_unavailable")
        return None
    
    try:
        # Common algorithms used by Supabase
        common_algorithms = ["RS256", "RS384", "RS512", "ES256", "ES384", "ES512", "PS256"]
        
        # Use the token's algorithm if it's in our common list, otherwise try RS256
        if alg in common_algorithms:
            algorithms = [alg]
        else:
            algorithms = ["RS256", "RS384", "RS512", "ES256"]
        
        log.debug("auth.decoding_with_algorithms", algorithms=algorithms)
        
        # Decode and verify the token
        payload = jwt.decode(
            token,
            jwks,
            algorithms=algorithms,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": False,  # Supabase doesn't always set aud
            },
            audience=None,
            issuer=f"{settings.supabase_url}/auth/v1",
        )
        log.info("auth.token_verified", user_id=payload.get("sub"))
        
        # Extract user info from Supabase JWT claims
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role", "authenticated")
        
        if not user_id:
            log.warning("auth.token_no_user_id")
            return None
        
        return AuthUser(
            id=user_id,
            email=email,
            role=role,
            raw_token=token,
        )
        
    except JWTError as e:
        log.warning("auth.jwt_error", error=str(e))
        return None
    except httpx.HTTPError as e:
        log.warning("auth.http_error", error=str(e))
        return None
    except Exception as e:
        log.error("auth.unexpected_error", error=str(e))
        return None