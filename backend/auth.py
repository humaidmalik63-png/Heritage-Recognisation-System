"""
Heritage & Monument Recognition System - Administrator Authentication Module
Project No. 30 (SIH 2025): Visual Heritage Recognition & Grounded Cultural Discovery Platform
Phase 13: Genuine Server-Side Administrator Authentication, Password Hashing & Signed Sessions
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from typing import Any, Dict, Optional, Tuple

from fastapi import Depends, Header, HTTPException, Request, status

logger = logging.getLogger("heritage_auth")

# Session secret for cryptographically signing administrative tokens
# Persisted via environment variable or initialized securely on server startup
_ENV_SECRET = os.environ.get("SESSION_SECRET", "").strip()
if not _ENV_SECRET or len(_ENV_SECRET) < 16:
    _ENV_SECRET = secrets.token_hex(32)
    os.environ["SESSION_SECRET"] = _ENV_SECRET

_EPHEMERAL_SECRET = _ENV_SECRET


def get_session_secret() -> bytes:
    env_secret = os.environ.get("SESSION_SECRET", "").strip()
    if env_secret and len(env_secret) >= 16:
        return env_secret.encode("utf-8")
    return _EPHEMERAL_SECRET.encode("utf-8")


def hash_password(password: str) -> str:
    """
    Hashes a password using standard memory-hard scrypt (OWASP recommendation).
    Output format: scrypt$16384$8$1$<salt_hex>$<hash_hex>
    """
    salt = secrets.token_bytes(16)
    n, r, p = 16384, 8, 1
    key = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, maxmem=32 * 1024 * 1024)
    return f"scrypt${n}${r}${p}${salt.hex()}${key.hex()}"


def verify_password(password: str, stored_hash_or_secret: str) -> bool:
    """
    Verifies a plaintext password against an scrypt hash or server-side secret using
    constant-time comparison to prevent timing attacks.
    """
    if not password or not stored_hash_or_secret:
        return False

    stored = stored_hash_or_secret.strip()

    # Case 1: scrypt format
    if stored.startswith("scrypt$"):
        parts = stored.split("$")
        if len(parts) == 6:
            try:
                _, n_str, r_str, p_str, salt_hex, key_hex = parts
                n, r, p = int(n_str), int(r_str), int(p_str)
                salt = bytes.fromhex(salt_hex)
                expected_key = bytes.fromhex(key_hex)
                computed = hashlib.scrypt(
                    password.encode("utf-8"),
                    salt=salt,
                    n=n,
                    r=r,
                    p=p,
                    maxmem=32 * 1024 * 1024,
                )
                return hmac.compare_digest(computed, expected_key)
            except Exception as e:
                logger.error(f"scrypt verification error: {e}")
                return False

    # Case 2: Plaintext secret fallback from environment configuration (CURATOR_API_KEY / ADMIN_PASSWORD)
    return hmac.compare_digest(password.encode("utf-8"), stored.encode("utf-8"))


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    padding = 4 - (len(s) % 4)
    if padding and padding < 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s.encode("utf-8"))


def create_session_token(username: str, role: str = "curator_admin", expiry_seconds: int = 86400) -> Tuple[str, str]:
    """
    Issues an HMAC-SHA256 cryptographically signed session token.
    Returns: (session_token, csrf_token)
    """
    now = int(time.time())
    csrf_token = secrets.token_hex(16)
    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": now + expiry_seconds,
        "csrf": csrf_token,
    }
    payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = _b64url_encode(payload_json)

    secret = get_session_secret()
    sig = hmac.new(secret, payload_b64.encode("utf-8"), hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)

    token = f"{payload_b64}.{sig_b64}"
    return token, csrf_token


def verify_session_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Verifies the HMAC-SHA256 signature and expiration timestamp of a session token.
    Returns payload dictionary if valid, None otherwise.
    """
    if not token or not isinstance(token, str) or "." not in token:
        return None

    try:
        payload_b64, sig_b64 = token.split(".", 1)
        secret = get_session_secret()
        expected_sig = hmac.new(secret, payload_b64.encode("utf-8"), hashlib.sha256).digest()
        provided_sig = _b64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, provided_sig):
            return None

        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Verify expiration
        exp = payload.get("exp", 0)
        if time.time() > exp:
            return None

        return payload
    except Exception as e:
        logger.debug(f"Session token verification failed: {e}")
        return None


def get_configured_admin_credentials() -> Tuple[Optional[str], Optional[str]]:
    """
    Retrieves administrator username and stored hash/secret from environment variables.
    Fails safely if no credentials are configured (never returns default demo passwords).
    """
    username = os.environ.get("ADMIN_USERNAME", "").strip() or "curator_admin"
    password_hash = os.environ.get("ADMIN_PASSWORD_HASH", "").strip()
    if not password_hash:
        # Fall back to ADMIN_PASSWORD or CURATOR_API_KEY if explicitly set
        password_hash = os.environ.get("ADMIN_PASSWORD", "").strip() or os.environ.get("CURATOR_API_KEY", "").strip()

    if not password_hash:
        return None, None
    return username, password_hash


def authenticate_admin_credentials(username_attempt: str, password_attempt: str) -> bool:
    """
    Authenticates administrator credentials against environment-configured settings.
    """
    expected_user, expected_hash = get_configured_admin_credentials()
    if not expected_user or not expected_hash:
        logger.warning("Administrative authentication attempted but no administrator credentials are configured in server environment.")
        return False

    if not hmac.compare_digest(username_attempt.strip().lower().encode("utf-8"), expected_user.lower().encode("utf-8")):
        return False

    return verify_password(password_attempt, expected_hash)


async def get_current_admin(
    request: Request,
    x_curator_key: Optional[str] = Header(None, alias="X-Curator-Key"),
) -> Dict[str, Any]:
    """
    FastAPI dependency that enforces administrator authentication via:
      1. Bearer Token in Authorization header
      2. HttpOnly admin_session cookie
      3. X-Curator-Key header (backwards compatibility for automated pipelines / testing)
    """
    # 1. Check Authorization Bearer header
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        payload = verify_session_token(token)
        if payload:
            return {"username": payload.get("sub", "admin"), "role": payload.get("role", "admin"), "auth_method": "bearer_token"}

    # 2. Check admin_session Cookie
    cookie_token = request.cookies.get("admin_session")
    if cookie_token:
        payload = verify_session_token(cookie_token)
        if payload:
            # If state-changing request (POST, PUT, DELETE), verify CSRF token
            if request.method in ("POST", "PUT", "DELETE", "PATCH"):
                csrf_header = request.headers.get("x-csrf-token", "")
                if not csrf_header or not hmac.compare_digest(csrf_header.encode("utf-8"), payload.get("csrf", "").encode("utf-8")):
                    # If Authorization Bearer was also supplied, accept it; otherwise reject CSRF mismatch
                    if not auth_header.startswith("Bearer "):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="CSRF token validation failed for administrative cookie session.",
                        )
            return {"username": payload.get("sub", "admin"), "role": payload.get("role", "admin"), "auth_method": "cookie_session"}

    # 3. Check X-Curator-Key Header (CLI / testing legacy support)
    expected_user, expected_hash = get_configured_admin_credentials()
    if x_curator_key and expected_hash:
        if verify_password(x_curator_key, expected_hash):
            return {"username": expected_user or "curator_key", "role": "admin", "auth_method": "api_key"}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Valid administrator authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )
