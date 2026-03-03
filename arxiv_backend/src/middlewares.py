import time
from http.client import responses

from loguru import logger
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

SKIP_BODY_MEDIA_TYPES = {"text/event-stream", "text/plain"}
SKIP_BODY_PATHS = {"/chat/stream"}  # exact paths
SKIP_BODY_PATH_PREFIXES = {"/stream/"}  # prefix match for /stream/{task_id}


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
