"""
Heritage Monument Recognition System - Production Security & Hardening Module
Project No. 30 (SIH 2025): Visual Heritage Recognition & Grounded Cultural Discovery Platform
Phase 11: Production Hardening, Security Headers, Rate Limiting & Input Validation

Provides:
  - SecurityHeadersMiddleware: HSTS, X-Content-Type-Options, X-Frame-Options, CSP, etc.
  - RateLimitMiddleware: Thread-safe sliding-window rate limiter per client IP.
  - Input validation & magic byte checking for image uploads (JPEG, PNG, WebP).
  - Decompression bomb mitigation (Pillow max image pixels clamp).
  - Path traversal and IDOR protection via regex sanitization.
  - Constant-time timing-attack mitigation for curator keys (hmac.compare_digest).
  - Central exception sanitization to prevent internal stack trace leakage.
"""

import hmac
import logging
import os
import re
import threading
import time
import uuid
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Set, Tuple

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from PIL import Image

# Enforce Pillow Decompression Bomb protection limit (25 Megapixels max)
Image.MAX_IMAGE_PIXELS = 25_000_000

logger = logging.getLogger("heritage_security")

# --- 1. Allowed Production Origins ---
DEFAULT_PRODUCTION_ORIGINS = [
    "https://heritage-monuments.vercel.app",
    "https://backend-production-b023b.up.railway.app",
    "http://localhost:5173",
    "http://localhost:5175",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8001",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8001",
]


def get_allowed_cors_origins() -> List[str]:
    """
    Returns the hardened allowlist of CORS origins.
    Prioritizes CORS_ORIGINS env var if explicitly set; otherwise uses default production set.
    """
    raw_env = os.environ.get("CORS_ORIGINS", "").strip()
    if raw_env:
        if raw_env == "*":
            # If explicitly set to wildcard in dev
            return ["*"]
        custom_origins = [o.strip() for o in raw_env.split(",") if o.strip()]
        # Merge with default origins to avoid breaking Vercel/Railway communication
        merged = set(DEFAULT_PRODUCTION_ORIGINS + custom_origins)
        return sorted(list(merged))
    return DEFAULT_PRODUCTION_ORIGINS


# --- 2. Security Headers Middleware ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects essential defensive security headers into all HTTP responses:
      - X-Content-Type-Options: nosniff (Prevents MIME sniffing)
      - X-Frame-Options: DENY (Prevents clickjacking)
      - X-XSS-Protection: 1; mode=block
      - Strict-Transport-Security: max-age=31536000; includeSubDomains (Enforces HTTPS)
      - Referrer-Policy: strict-origin-when-cross-origin
      - Permissions-Policy: camera=(self), geolocation=(), microphone=()
      - Content-Security-Policy: Restricts framing and insecure scripts
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Basic defensive headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(self), geolocation=(), microphone=()"

        # Enforce HSTS on HTTPS connections (or all non-local requests)
        if request.url.scheme == "https" or not ("localhost" in request.url.netloc or "127.0.0.1" in request.url.netloc):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Content Security Policy for API responses
        if not response.headers.get("Content-Security-Policy"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "img-src 'self' data: blob: https:; "
                "font-src 'self' https://fonts.gstatic.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "frame-ancestors 'none';"
            )

        return response


# --- 3. Thread-Safe Sliding-Window Rate Limiter Middleware ---
class RateLimiter:
    """
    In-memory, thread-safe sliding window rate limiter.
    Zero external dependencies (no Redis required for single-container Railway).
    """

    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, client_ip: str, max_requests: int) -> Tuple[bool, int, int]:
        """
        Checks if client_ip is within max_requests limit.
        Returns: (is_allowed, remaining_requests, retry_after_seconds)
        """
        now = time.time()
        window_start = now - self.window_seconds

        with self._lock:
            timestamps = self._requests[client_ip]
            # Prune timestamps older than window
            valid_timestamps = [t for t in timestamps if t > window_start]
            self._requests[client_ip] = valid_timestamps

            if len(valid_timestamps) >= max_requests:
                earliest = valid_timestamps[0]
                retry_after = max(1, int(self.window_seconds - (now - earliest)))
                return False, 0, retry_after

            valid_timestamps.append(now)
            remaining = max_requests - len(valid_timestamps)
            return True, remaining, 0

    def cleanup_idle_clients(self, max_idle_seconds: int = 300) -> None:
        """Periodic cleanup of old IPs to keep memory usage minimal."""
        now = time.time()
        cutoff = now - max_idle_seconds
        with self._lock:
            idle_keys = [k for k, v in self._requests.items() if not v or v[-1] < cutoff]
            for k in idle_keys:
                del self._requests[k]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enforces multi-tiered rate limits based on endpoint sensitivity and compute intensity:
      - Admin Authentication (Brute-force protection): 5 requests / minute
      - Gemini VLM & Historical Q&A: 15 requests / minute
      - Heavy Visual Inference (CLIP + FAISS Vector Scan): 30 requests / minute
      - General Metadata & Read Queries: 150 requests / minute
    """

    def __init__(
        self,
        app,
        admin_limit: int = 5,
        gemini_limit: int = 15,
        heavy_limit: int = 30,
        general_limit: int = 150,
        window_seconds: int = 60,
    ):
        super().__init__(app)
        self.admin_limit = admin_limit
        self.gemini_limit = gemini_limit
        self.heavy_limit = heavy_limit
        self.general_limit = general_limit
        self.window_seconds = window_seconds
        self.limiter = RateLimiter(window_seconds=window_seconds)

        self.heavy_paths = {
            "/api/verify-monument",
            "/api/recognition/local-features",
        }

    def _get_client_ip(self, request: Request) -> str:
        # Check forwarded headers (Railway / Cloudflare / Vercel proxies)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return cf_ip.strip()
        return request.client.host if request.client else "127.0.0.1"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Allow disabling rate limiting during specific test suites
        if os.environ.get("DISABLE_RATE_LIMIT") == "1" or os.environ.get("TESTING") == "1":
            return await call_next(request)

        # Allow OPTIONS preflight requests without rate limiting
        if request.method == "OPTIONS":
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        # Whitelist local health checks from Railway container
        path = request.url.path
        if path == "/api/health" and client_ip in ("127.0.0.1", "localhost", "::1"):
            return await call_next(request)

        # Determine rate limit tier for path
        if path.startswith("/api/admin/login"):
            tier_name = "admin_auth"
            max_req = self.admin_limit
        elif path.startswith("/api/monuments/") and ("/ask" in path or "/explain" in path):
            tier_name = "gemini_vlm"
            max_req = self.gemini_limit
        elif path in self.heavy_paths:
            tier_name = "heavy_compute"
            max_req = self.heavy_limit
        else:
            tier_name = "standard"
            max_req = self.general_limit

        allowed, remaining, retry_after = self.limiter.is_allowed(f"{client_ip}:{tier_name}", max_req)
        if not allowed:
            logger.warning(f"Rate limit exceeded for IP {client_ip} on path '{path}' [{tier_name}] (retry_after={retry_after}s)")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Too many requests submitted. Please slow down.",
                    "retry_after_seconds": retry_after,
                    "endpoint_tier": tier_name,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_req),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(self.window_seconds),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_req)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(self.window_seconds)
        return response


# --- 4. Input Sanitization & IDOR Mitigation ---
IDENTIFIER_REGEX = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")


def sanitize_identifier(raw_id: str, field_name: str = "identifier") -> str:
    """
    Validates that monument_id or exception_id conforms strictly to safe alphanumeric identifiers.
    Prevents directory traversal attacks (e.g. '../../etc/passwd').
    """
    if not raw_id or not isinstance(raw_id, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}: cannot be empty.",
        )
    cleaned = raw_id.strip()
    if not IDENTIFIER_REGEX.match(cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}: must be 1-64 alphanumeric characters, underscores, or hyphens.",
        )
    return cleaned


def sanitize_inquiry_text(raw_text: str, max_length: int = 500) -> str:
    """
    Sanitizes questions asked to the knowledge engine or Gemini.
    Strips raw HTML tags and truncates excessive payload lengths.
    """
    if not raw_text or not isinstance(raw_text, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inquiry text cannot be empty.",
        )
    cleaned = raw_text.strip()
    # Remove HTML tags to prevent stored/reflected injection
    cleaned = re.sub(r"<[^>]*>", "", cleaned)
    if len(cleaned) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inquiry question is too short (minimum 3 characters).",
        )
    if len(cleaned) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Inquiry question exceeds maximum allowed length of {max_length} characters.",
        )
    return cleaned


# --- 5. Image Upload Magic Byte Validation & Streaming Limit ---
ALLOWED_IMAGE_MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp",  # WebP files start with 'RIFF....WEBP'
}

MAX_IMAGE_BYTES = 15 * 1024 * 1024  # 15 MB limit


def validate_image_payload(image_bytes: bytes) -> str:
    """
    Validates raw uploaded bytes against genuine image magic signatures.
    Rejects scripts, SVGs (XSS risk), executables, and empty files.
    Returns: Detected MIME format string ('image/jpeg', 'image/png', 'image/webp')
    """
    if not image_bytes or len(image_bytes) < 16:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty or too small to be a valid image.",
        )

    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Payload too large: Image exceeds 15 MB limit.",
        )

    # Magic byte matching
    for header, mime in ALLOWED_IMAGE_MAGIC.items():
        if image_bytes.startswith(header):
            if mime == "image/webp" and image_bytes[8:12] != b"WEBP":
                continue
            return mime

    # SVG rejection (explicit security check)
    if b"<svg" in image_bytes[:1024].lower() or b"<?xml" in image_bytes[:1024].lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SVG vector uploads are prohibited for security reasons. Please upload JPEG, PNG, or WebP.",
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported image format. Only authentic JPEG, PNG, and WebP images are permitted.",
    )


# --- 6. Constant-Time Curator Authentication ---
def verify_curator_key(provided_key: Optional[str]) -> bool:
    """
    Secure constant-time comparison against the configured CURATOR_API_KEY.
    Prevents side-channel timing attacks.
    """
    expected_key = os.environ.get("CURATOR_API_KEY", "").strip()
    if not expected_key:
        # If no key is configured on server, lock administrative operations
        logger.warning("CURATOR_API_KEY is not configured in server environment; curator actions locked.")
        return False

    if not provided_key or not isinstance(provided_key, str):
        return False

    return hmac.compare_digest(provided_key.strip().encode("utf-8"), expected_key.encode("utf-8"))


# --- 7. Central Exception Handler ---
def create_central_exception_handler(logger_instance: logging.Logger):
    """
    Generates a centralized unhandled exception handler that logs full tracebacks
    with unique correlation IDs while returning safe, sanitized responses to callers.
    """
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        error_ref = f"SEC-{uuid.uuid4().hex[:8].upper()}"
        logger_instance.exception(f"Unhandled server error [Ref: {error_ref}] on path {request.url.path}: {exc}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred while processing your request.",
                "error_reference": error_ref,
                "status_code": 500,
            },
        )

    return unhandled_exception_handler

