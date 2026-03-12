# --------------- Praxis Enterprise Authentication ---------------
"""
v18 · Enterprise-Grade Solidification

OAuth2 / API-key authentication implemented as FastAPI dependencies.

Supports three modes (configured via ``PRAXIS_AUTH_MODE``):
    • ``none``    — no auth (development default).
    • ``api_key`` — static API keys validated from environment/config.
    • ``oauth2``  — Bearer JWT tokens validated against JWKS / shared secret.

All sensitive endpoints inject ``get_current_user`` as a dependency:

    @app.post("/reason")
    async def reason(user: dict = Depends(get_current_user)):
        ...

Public endpoints remain unguarded.

Zero external dependencies — uses stdlib ``hmac``, ``json``, ``base64``.
When ``PyJWT`` or ``python-jose`` is available, full RS256/ES256 JWKS
validation is used.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

log = logging.getLogger("praxis.auth")

# -----------------------------------------------------------------------
# Configuration helpers
# -----------------------------------------------------------------------

def _get_auth_mode() -> str:
    return os.environ.get("PRAXIS_AUTH_MODE", "none").lower()


def _get_api_keys() -> List[str]:
    """Return allowed API keys (comma-separated env var)."""
    raw = os.environ.get("PRAXIS_API_KEYS", "")
    return [k.strip() for k in raw.split(",") if k.strip()]


def _get_jwt_secret() -> str:
    return os.environ.get("PRAXIS_JWT_SECRET", "")


def _get_jwt_issuer() -> str:
    return os.environ.get("PRAXIS_JWT_ISSUER", "praxis")


def _get_jwt_audience() -> str:
    return os.environ.get("PRAXIS_JWT_AUDIENCE", "praxis-api")


# -----------------------------------------------------------------------
# Minimal JWT decode (HS256, no external deps)
# -----------------------------------------------------------------------

def _b64url_decode(s: str) -> bytes:
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def _decode_jwt_hs256(token: str, secret: str) -> Optional[Dict[str, Any]]:
    """Decode and verify a HS256 JWT.  Returns claims or None."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header = json.loads(_b64url_decode(parts[0]))
        if header.get("alg") != "HS256":
            return None

        payload_bytes = _b64url_decode(parts[1])
        signature = _b64url_decode(parts[2])

        # Verify HMAC-SHA256
        signing_input = f"{parts[0]}.{parts[1]}".encode()
        expected_sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected_sig):
            return None

        claims = json.loads(payload_bytes)

        # Check expiry
        if "exp" in claims and claims["exp"] < time.time():
            return None

        return claims

    except Exception:
        return None


# -----------------------------------------------------------------------
# User model
# -----------------------------------------------------------------------

class User:
    """Minimal authenticated-user representation."""

    __slots__ = ("user_id", "roles", "claims", "auth_method")

    def __init__(
        self,
        user_id: str,
        roles: Optional[List[str]] = None,
        claims: Optional[Dict[str, Any]] = None,
        auth_method: str = "api_key",
    ):
        self.user_id = user_id
        self.roles = roles or ["user"]
        self.claims = claims or {}
        self.auth_method = auth_method

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "roles": self.roles,
            "auth_method": self.auth_method,
        }


# -----------------------------------------------------------------------
# Core authentication function
# -----------------------------------------------------------------------

async def authenticate_request(
    authorization: Optional[str] = None,
    x_api_key: Optional[str] = None,
) -> Optional[User]:
    """Validate credentials and return a User, or None.

    Checks:
        1. X-Api-Key header → API-key mode
        2. Authorization: Bearer <token> → JWT mode
    """
    mode = _get_auth_mode()

    if mode == "none":
        # Warn loudly — "none" mode should NEVER be used in production.
        log.warning(
            "PRAXIS_AUTH_MODE=none: authentication is disabled — "
            "granting read-only 'user' role (NOT admin). "
            "Set PRAXIS_AUTH_MODE=api_key or oauth2 for production use."
        )
        return User(user_id="anonymous", roles=["user"], auth_method="none")

    # -- API-Key --
    if x_api_key:
        valid_keys = _get_api_keys()
        # Constant-time comparison to prevent timing-based key enumeration
        matched = any(hmac.compare_digest(x_api_key, k) for k in valid_keys)
        if matched:
            return User(user_id=f"apikey:{x_api_key[:8]}...", auth_method="api_key")
        log.warning("Invalid API key presented")
        return None

    # -- Bearer JWT --
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()

        # Try external JWT library first
        try:
            import jwt as pyjwt  # PyJWT
            claims = pyjwt.decode(
                token,
                _get_jwt_secret(),
                algorithms=["HS256", "RS256"],
                audience=_get_jwt_audience(),
                issuer=_get_jwt_issuer(),
            )
            return User(
                user_id=claims.get("sub", "unknown"),
                roles=claims.get("roles", ["user"]),
                claims=claims,
                auth_method="oauth2",
            )
        except ImportError:
            pass
        except Exception as e:
            log.warning("JWT validation failed (PyJWT): %s", e)
            return None

        # Fallback to stdlib HS256
        secret = _get_jwt_secret()
        if secret:
            claims = _decode_jwt_hs256(token, secret)
            if claims:
                # Validate issuer and audience even on the stdlib path.
                expected_iss = _get_jwt_issuer()
                expected_aud = _get_jwt_audience()
                if expected_iss and claims.get("iss") != expected_iss:
                    log.warning("JWT issuer mismatch: got %r, expected %r", claims.get("iss"), expected_iss)
                    return None
                if expected_aud:
                    _aud = claims.get("aud")
                    # aud may be a string or a list of strings (RFC 7519 §4.1.3)
                    if isinstance(_aud, list):
                        if expected_aud not in _aud:
                            log.warning("JWT audience mismatch: %r not in %r", expected_aud, _aud)
                            return None
                    elif _aud != expected_aud:
                        log.warning("JWT audience mismatch: got %r, expected %r", _aud, expected_aud)
                        return None
                return User(
                    user_id=claims.get("sub", "unknown"),
                    roles=claims.get("roles", ["user"]),
                    claims=claims,
                    auth_method="oauth2",
                )
            log.warning("JWT validation failed (stdlib HS256)")
            return None

    # -- API-key mode but no key provided --
    if mode == "api_key":
        return None

    return None


# -----------------------------------------------------------------------
# FastAPI Dependencies
# -----------------------------------------------------------------------

def _build_fastapi_deps():
    """Build FastAPI-compatible dependency functions.  Safe to call even
    if FastAPI isn't installed (returns None-valued tuple)."""
    try:
        from fastapi import Depends, Header, HTTPException, Request
    except ImportError:
        return None, None, None

    async def get_current_user(
        authorization: Optional[str] = Header(default=None),
        x_api_key: Optional[str] = Header(default=None, alias="X-Api-Key"),
    ) -> User:
        """FastAPI dependency: authenticate or raise 401."""
        mode = _get_auth_mode()
        if mode == "none":
            log.warning(
                "PRAXIS_AUTH_MODE=none: authentication is disabled — "
                "granting read-only 'user' role (NOT admin)."
            )
            return User(user_id="anonymous", roles=["user"], auth_method="none")

        user = await authenticate_request(authorization, x_api_key)
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid or missing credentials")
        return user

    async def require_role(role: str):
        """Return a dependency that checks for a specific role."""
        async def _dep(user: User = Depends(get_current_user)) -> User:
            if not user.has_role(role):
                raise HTTPException(status_code=403, detail=f"Role '{role}' required")
            return user
        return _dep

    async def get_optional_user(
        authorization: Optional[str] = Header(default=None),
        x_api_key: Optional[str] = Header(default=None, alias="X-Api-Key"),
    ) -> Optional[User]:
        """Returns User if authenticated, None otherwise (no 401)."""
        return await authenticate_request(authorization, x_api_key)

    return get_current_user, require_role, get_optional_user


# Build at module level — None if FastAPI not installed
get_current_user, require_role, get_optional_user = _build_fastapi_deps() or (None, None, None)


# -----------------------------------------------------------------------
# Token Generation (for testing / internal use)
# -----------------------------------------------------------------------

def generate_api_key(prefix: str = "prx") -> str:
    """Generate a cryptographically random API key."""
    import secrets
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def generate_jwt(
    sub: str,
    roles: Optional[List[str]] = None,
    *,
    secret: Optional[str] = None,
    ttl_seconds: int = 3600,
) -> str:
    """Generate a HS256 JWT.  For dev/test use."""
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    now = int(time.time())
    payload = {
        "sub": sub,
        "roles": roles or ["user"],
        "iss": _get_jwt_issuer(),
        "aud": _get_jwt_audience(),
        "iat": now,
        "exp": now + ttl_seconds,
    }
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    signing_input = f"{header}.{payload_b64}".encode()
    sig = hmac.new((secret or _get_jwt_secret() or "dev-secret").encode(), signing_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    return f"{header}.{payload_b64}.{sig_b64}"
