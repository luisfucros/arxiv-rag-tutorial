import time
from http.client import responses
from typing import Optional

import jwt
from api.handlers.instances import redis_client
from config import settings
from fastapi import status
from fastapi.responses import JSONResponse
from loguru import logger
from services.rate_limit import RateLimiter
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

SKIP_BODY_MEDIA_TYPES = {"text/event-stream", "text/plain"}
SKIP_BODY_PATHS = {"/chat/stream"}  # exact paths
SKIP_BODY_PATH_PREFIXES = {"/stream/"}  # prefix match for /stream/{task_id}

# Paths that skip rate limiting (health, docs, openapi)
RATE_LIMIT_SKIP_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}

_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(redis_client, settings.redis)
    return _rate_limiter


def _client_ip(scope: dict) -> str:
    """Resolve client IP from headers (when behind proxy) or scope."""
    headers = scope.get("headers") or []
    header_dict = {k.decode().lower(): v for k, v in headers}

    # Prefer leftmost (client) IP in X-Forwarded-For
    def _str(v):
        return v.decode() if isinstance(v, bytes) else v

    forwarded = header_dict.get("x-forwarded-for")
    if forwarded:
        return _str(forwarded).split(",")[0].strip()
    real_ip = header_dict.get("x-real-ip")
    if real_ip:
        return _str(real_ip).strip()
    client = scope.get("client")
    if client:
        return client[0]
    return "unknown"


def _user_id_from_scope(scope: dict) -> Optional[str]:
    """Extract user id from Bearer token if present and valid."""
    headers = scope.get("headers") or []
    header_dict = {k.decode().lower(): v for k, v in headers}
    auth = header_dict.get("authorization")
    if not auth:
        return None
    auth = auth.decode() if isinstance(auth, bytes) else str(auth)
    if not auth.lower().startswith("bearer "):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        sub = payload.get("sub")
        return str(sub) if sub is not None else None
    except Exception:
        return None


class RateLimitMiddleware:
    """Enforces global, per-IP, and per-user rate limits using Redis."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in RATE_LIMIT_SKIP_PATHS:
            await self.app(scope, receive, send)
            return

        limiter = get_rate_limiter()
        ip = _client_ip(scope)
        user_id = _user_id_from_scope(scope)
        err = limiter.check(ip=ip, user_id=user_id)
        if err:
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": err},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def should_skip_body(scope: dict, media_type: str | None) -> bool:
    path = scope.get("path", "")
    if path in SKIP_BODY_PATHS:
        return True
    if any(path.startswith(p) for p in SKIP_BODY_PATH_PREFIXES):
        return True
    if media_type and any(media_type.startswith(mt) for mt in SKIP_BODY_MEDIA_TYPES):
        return True
    return False


class LoggingMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()
        status_code = 500
        media_type = None
        response_body = b""
        skip_body = False

        async def send_wrapper(message):
            nonlocal status_code, media_type, response_body, skip_body

            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = MutableHeaders(scope=message)
                content_type = headers.get("content-type", "")
                media_type = content_type.split(";")[0].strip()
                skip_body = should_skip_body(scope, media_type)

            elif message["type"] == "http.response.body":
                if not skip_body:
                    response_body += message.get("body", b"")

                # Log on the final chunk
                if not message.get("more_body", False):
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    method = scope.get("method", "")
                    path = scope.get("path", "")
                    scheme = scope.get("scheme", "")
                    status_text = responses.get(status_code, "Unknown")

                    if skip_body:
                        logger.debug(
                            '{} "{} {}" {} {} [streaming] {:.2f}ms',
                            method,
                            scheme,
                            path,
                            status_code,
                            status_text,
                            duration_ms,
                        )
                    else:
                        logger.debug(
                            '{} "{} {}" {} {} {} {:.2f}ms',
                            method,
                            scheme,
                            path,
                            status_code,
                            status_text,
                            response_body.decode("utf-8", errors="replace"),
                            duration_ms,
                        )

            await send(message)

        await self.app(scope, receive, send_wrapper)
