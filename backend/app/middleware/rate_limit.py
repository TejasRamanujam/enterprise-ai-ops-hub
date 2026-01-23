from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import structlog

from app.core.redis_client import rate_limit_check
from app.core.config import settings

logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/"):
            client_ip = request.client.host if request.client else "unknown"
            allowed, remaining = await rate_limit_check(
                identifier=f"ip:{client_ip}",
                max_requests=settings.RATE_LIMIT_REQUESTS,
                window=settings.RATE_LIMIT_WINDOW,
            )
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please try again later."},
                    headers={"Retry-After": str(settings.RATE_LIMIT_WINDOW)},
                )

        response = await call_next(request)
        return response
